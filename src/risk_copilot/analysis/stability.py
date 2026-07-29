from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
from scipy.stats import spearmanr

from ..rules.dsl import evaluate_rule
from ..schemas import StrategyCandidate, StrategyRequest


def _metric_snapshot(y: np.ndarray, alert: np.ndarray) -> dict[str, float | int]:
    tn, fp, fn, tp = confusion_matrix(y, alert.astype(int), labels=[0, 1]).ravel()
    precision = precision_score(y, alert, zero_division=0)
    recall = recall_score(y, alert, zero_division=0)
    f1 = f1_score(y, alert, zero_division=0)
    fpr = fp / max(fp + tn, 1)
    return {
        "sample_size": int(len(y)),
        "positives": int(y.sum()),
        "alerts": int(alert.sum()),
        "true_positives": int(tp),
        "false_positives": int(fp),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "false_positive_rate": float(fpr),
        "alert_rate": float(alert.mean()) if len(alert) else 0.0,
    }


@dataclass
class StrategyStabilityAnalyzer:
    target: str = "fraud_label"
    time_column: str = "event_date"
    bootstrap_rounds: int = 200
    random_seed: int = 42

    def analyze(
        self,
        data: pd.DataFrame,
        strategy: StrategyCandidate,
        request: StrategyRequest,
    ) -> dict[str, Any]:
        if data.empty:
            raise ValueError("stability input is empty")
        if self.target not in data:
            raise KeyError(f"missing target column: {self.target}")
        working = data.copy()
        working[self.time_column] = pd.to_datetime(working[self.time_column], errors="coerce")
        working = working.dropna(subset=[self.time_column]).sort_values(self.time_column)
        if working.empty:
            raise ValueError("no valid timestamps available for stability analysis")

        alert = evaluate_rule(working, strategy.rule).to_numpy(dtype=bool)
        y = working[self.target].astype(int).to_numpy()
        working = working.assign(_alert=alert, _target=y)

        monthly: list[dict[str, Any]] = []
        for period, group in working.groupby(working[self.time_column].dt.to_period("M")):
            snapshot = _metric_snapshot(
                group["_target"].to_numpy(dtype=int),
                group["_alert"].to_numpy(dtype=bool),
            )
            snapshot["period"] = str(period)
            monthly.append(snapshot)

        rng = np.random.default_rng(self.random_seed)
        boot_metrics: dict[str, list[float]] = {
            "precision": [],
            "recall": [],
            "f1": [],
            "false_positive_rate": [],
            "alert_rate": [],
        }
        n = len(working)
        for _ in range(self.bootstrap_rounds):
            index = rng.integers(0, n, size=n)
            snapshot = _metric_snapshot(y[index], alert[index])
            for name in boot_metrics:
                boot_metrics[name].append(float(snapshot[name]))

        bootstrap_summary: dict[str, dict[str, float]] = {}
        for name, values in boot_metrics.items():
            arr = np.asarray(values, dtype=float)
            bootstrap_summary[name] = {
                "mean": float(arr.mean()),
                "std": float(arr.std(ddof=0)),
                "ci_lower_95": float(np.quantile(arr, 0.025)),
                "ci_upper_95": float(np.quantile(arr, 0.975)),
            }

        feature_direction: list[dict[str, Any]] = []
        for feature in strategy.required_features:
            if feature.startswith("model_score__") or feature not in working:
                continue
            series = pd.to_numeric(working[feature], errors="coerce")
            valid = series.notna()
            if valid.sum() < 50 or series[valid].nunique() < 2:
                continue
            overall_corr = spearmanr(series[valid], working.loc[valid, "_target"]).statistic
            overall_sign = 0 if np.isnan(overall_corr) or abs(overall_corr) < 1e-9 else int(np.sign(overall_corr))
            signs: list[int] = []
            month_rows: list[dict[str, Any]] = []
            for period, group in working.groupby(working[self.time_column].dt.to_period("M")):
                g = pd.to_numeric(group[feature], errors="coerce")
                mask = g.notna()
                if mask.sum() < 20 or g[mask].nunique() < 2 or group.loc[mask, "_target"].nunique() < 2:
                    continue
                corr = spearmanr(g[mask], group.loc[mask, "_target"]).statistic
                sign = 0 if np.isnan(corr) or abs(corr) < 1e-9 else int(np.sign(corr))
                signs.append(sign)
                month_rows.append({"period": str(period), "spearman": float(0.0 if np.isnan(corr) else corr), "sign": sign})
            comparable = [sign for sign in signs if sign != 0 and overall_sign != 0]
            consistency = (
                float(sum(sign == overall_sign for sign in comparable) / len(comparable))
                if comparable
                else 0.0
            )
            feature_direction.append(
                {
                    "feature": feature,
                    "overall_spearman": float(0.0 if np.isnan(overall_corr) else overall_corr),
                    "overall_sign": overall_sign,
                    "monthly_direction_consistency": consistency,
                    "months_evaluated": len(month_rows),
                    "monthly": month_rows,
                }
            )

        monthly_precisions = np.asarray([row["precision"] for row in monthly if row["alerts"] > 0], dtype=float)
        monthly_alert_rates = np.asarray([row["alert_rate"] for row in monthly], dtype=float)
        precision_cv = float(monthly_precisions.std() / max(monthly_precisions.mean(), 1e-9)) if len(monthly_precisions) > 1 else 0.0
        alert_rate_cv = float(monthly_alert_rates.std() / max(monthly_alert_rates.mean(), 1e-9)) if len(monthly_alert_rates) > 1 else 0.0
        direction_scores = [row["monthly_direction_consistency"] for row in feature_direction if row["months_evaluated"] >= 2]
        direction_consistency = float(np.mean(direction_scores)) if direction_scores else 0.0

        gates = {
            "minimum_months": len(monthly) >= 3,
            "monthly_precision_cv_le_0_50": precision_cv <= 0.50,
            "monthly_alert_rate_cv_le_0_60": alert_rate_cv <= 0.60,
            "bootstrap_precision_lower_bound": bootstrap_summary["precision"]["ci_lower_95"] >= request.minimum_precision * 0.75,
            "bootstrap_recall_lower_bound": bootstrap_summary["recall"]["ci_lower_95"] >= request.minimum_recall * 0.75,
            "feature_direction_consistency_ge_0_60": direction_consistency >= 0.60 if direction_scores else True,
        }
        passed = sum(bool(value) for value in gates.values())
        if passed == len(gates):
            status = "STABLE"
        elif passed >= len(gates) - 2:
            status = "WATCH"
        else:
            status = "UNSTABLE"

        return {
            "strategy_id": strategy.strategy_id,
            "status": status,
            "monthly": monthly,
            "bootstrap_rounds": self.bootstrap_rounds,
            "bootstrap": bootstrap_summary,
            "feature_direction": feature_direction,
            "summary": {
                "months": len(monthly),
                "months_with_alerts": int(sum(row["alerts"] > 0 for row in monthly)),
                "monthly_precision_cv": precision_cv,
                "monthly_alert_rate_cv": alert_rate_cv,
                "feature_direction_consistency": direction_consistency,
                "gates_passed": passed,
                "gates_total": len(gates),
            },
            "gates": gates,
            "recommendation": (
                "可进入独立复核，但上线后仍需连续3个工作日观察。"
                if status == "STABLE"
                else "在模拟环境扩大月份和样本验证，并检查阈值与特征漂移后再提交上线评审。"
            ),
            "synthetic_demo": True,
        }
