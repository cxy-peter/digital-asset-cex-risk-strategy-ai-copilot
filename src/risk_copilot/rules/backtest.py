from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score

from ..schemas import BacktestMetrics, StrategyCandidate
from .dsl import evaluate_rule


@dataclass
class StrategyBacktester:
    target: str = "fraud_label"
    loss_column: str = "estimated_loss_amount"
    time_column: str = "event_date"
    review_capacity: int = 300

    def evaluate(self, data: pd.DataFrame, strategy: StrategyCandidate) -> BacktestMetrics:
        alert = evaluate_rule(data, strategy.rule).to_numpy(dtype=bool)
        y = data[self.target].astype(int).to_numpy()
        tn, fp, fn, tp = confusion_matrix(y, alert.astype(int), labels=[0, 1]).ravel()
        precision = precision_score(y, alert, zero_division=0)
        recall = recall_score(y, alert, zero_division=0)
        f1 = f1_score(y, alert, zero_division=0)
        fpr = fp / max(fp + tn, 1)
        alert_rate = alert.mean()
        base_rate = y.mean()
        lift = (y[alert].mean() / base_rate) if alert.any() and base_rate > 0 else 0.0
        loss = data[self.loss_column].fillna(0).to_numpy(dtype=float) if self.loss_column in data else np.ones(len(data))
        captured_loss = loss[(alert) & (y == 1)].sum()
        total_loss = loss[y == 1].sum()
        captured_loss_rate = captured_loss / max(total_loss, 1e-9)
        alert_amount = loss[alert].sum()

        monthly_precision = []
        monthly_alert_rate = []
        if self.time_column in data:
            periods = pd.to_datetime(data[self.time_column]).dt.to_period("M")
            temp = pd.DataFrame({"period": periods, "y": y, "alert": alert})
            for _, group in temp.groupby("period"):
                monthly_alert_rate.append(float(group["alert"].mean()))
                if group["alert"].sum() > 0:
                    monthly_precision.append(float(group.loc[group["alert"], "y"].mean()))
        precision_std = float(np.std(monthly_precision)) if monthly_precision else 1.0
        alert_std = float(np.std(monthly_alert_rate)) if monthly_alert_rate else 1.0
        stability = float(np.clip(1 - precision_std - alert_std, 0, 1))
        condition_count = len(strategy.required_features) or 1
        explainability = float(np.clip(1.15 - 0.09 * condition_count, 0.25, 1.0))
        operational = float(np.clip(self.review_capacity / max(int(alert.sum()), self.review_capacity), 0, 1))

        return BacktestMetrics(
            sample_size=len(data), positives=int(y.sum()), alerts=int(alert.sum()),
            true_positives=int(tp), false_positives=int(fp), false_negatives=int(fn), true_negatives=int(tn),
            precision=float(precision), recall=float(recall), f1=float(f1), false_positive_rate=float(fpr),
            alert_rate=float(alert_rate), lift=float(lift), captured_loss_rate=float(captured_loss_rate),
            alert_amount=float(alert_amount), captured_loss_amount=float(captured_loss),
            monthly_precision_std=precision_std, monthly_alert_rate_std=alert_std,
            stability_score=stability, explainability_score=explainability, operational_score=operational,
        )


@dataclass
class MultiObjectiveRanker:
    weights: dict[str, float]
    max_alert_rate: float = 0.05

    def score(self, metrics: BacktestMetrics) -> float:
        w = self.weights
        alert_penalty = max(metrics.alert_rate - self.max_alert_rate, 0) / max(self.max_alert_rate, 1e-6)
        reward = (
            w.get("precision", 0) * metrics.precision
            + w.get("recall", 0) * metrics.recall
            + w.get("f1", 0) * metrics.f1
            + w.get("captured_loss_rate", 0) * metrics.captured_loss_rate
            + w.get("stability", 0) * metrics.stability_score
            + w.get("explainability", 0) * metrics.explainability_score
            + w.get("operational", 0) * metrics.operational_score
            - w.get("false_positive_rate_penalty", 0) * metrics.false_positive_rate
            - w.get("alert_rate_penalty", 0) * alert_penalty
        )
        return float(reward)

    def rank(self, results: list[tuple[StrategyCandidate, BacktestMetrics]]) -> list[tuple[StrategyCandidate, BacktestMetrics]]:
        rewards = np.array([self.score(metrics) for _, metrics in results], dtype=float)
        mean, std = rewards.mean(), max(rewards.std(), 1e-9)
        ranked = []
        for (strategy, metrics), reward in zip(results, rewards):
            metrics.reward = float(reward)
            metrics.relative_advantage = float((reward - mean) / std)
            ranked.append((strategy, metrics))
        return sorted(ranked, key=lambda item: item[1].reward, reverse=True)
