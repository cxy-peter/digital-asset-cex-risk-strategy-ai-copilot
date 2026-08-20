from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from .models import DistributionAudit, DistributionCheck, GateStatus, LabelMaturitySummary


def _status_for_range(value: float, minimum: float | None, maximum: float | None) -> GateStatus:
    if minimum is not None and value < minimum:
        return GateStatus.FAIL
    if maximum is not None and value > maximum:
        return GateStatus.FAIL
    return GateStatus.PASS


def _smd(frame: pd.DataFrame, feature: str, target: str) -> float | None:
    if feature not in frame or target not in frame:
        return None
    x = pd.to_numeric(frame[feature], errors="coerce")
    y = pd.to_numeric(frame[target], errors="coerce")
    valid = x.notna() & y.notna()
    if valid.sum() < 50 or y[valid].nunique() < 2:
        return None
    bad = x[valid & y.eq(1)]
    good = x[valid & y.eq(0)]
    if len(bad) < 10 or len(good) < 10:
        return None
    pooled = np.sqrt((bad.var(ddof=1) + good.var(ddof=1)) / 2)
    if not np.isfinite(pooled) or pooled <= 1e-12:
        return None
    return float((bad.mean() - good.mean()) / pooled)


def _read_csv(path: Path, parse_dates: list[str] | None = None) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path, parse_dates=parse_dates or [], low_memory=False)


@dataclass
class SyntheticDistributionAuditor:
    """Audit qualitative similarity between the public synthetic demo and a sanitized profile.

    Broad ranges prevent the demo from becoming a balanced, linearly separable toy dataset. They
    are not a reconstruction of production prevalence, volume, loss or investigation outcomes.
    """

    profile: dict[str, Any]

    @classmethod
    def from_yaml(cls, path: str | Path) -> "SyntheticDistributionAuditor":
        with Path(path).open("r", encoding="utf-8") as handle:
            return cls(profile=yaml.safe_load(handle))

    def audit_directory(self, data_dir: str | Path) -> DistributionAudit:
        root = Path(data_dir)
        frames = {
            "users": _read_csv(root / "users.csv", parse_dates=["event_date"]),
            "transactions": _read_csv(root / "transactions.csv", parse_dates=["event_time", "label_observed_at"]),
            "cases": _read_csv(root / "cases_enhanced.csv", parse_dates=["created_at", "status_enter_at", "completed_at"]),
        }
        return self.audit(frames)

    def audit(self, frames: dict[str, pd.DataFrame | None]) -> DistributionAudit:
        checks: list[DistributionCheck] = []
        for dataset, dataset_spec in self.profile.get("datasets", {}).items():
            frame = frames.get(dataset)
            if frame is None:
                checks.append(DistributionCheck(dataset=dataset, check_id=f"{dataset}.dataset_present", description=f"{dataset} dataset exists", status=GateStatus.WATCH, observed="missing", expected="present", notes=["The check is skipped because the demo file is absent."]))
                continue
            for spec in dataset_spec.get("checks", []):
                checks.append(self._run_check(dataset, frame, spec))
        return DistributionAudit(profile_version=str(self.profile.get("version", "unknown")), overall_status=GateStatus.PASS, checks=checks, disclaimer=str(self.profile.get("disclaimer", "Synthetic profile only; not a production distribution estimate.")))

    def _run_check(self, dataset: str, frame: pd.DataFrame, spec: dict[str, Any]) -> DistributionCheck:
        check_type = str(spec["type"])
        check_id = str(spec.get("id", check_type))
        description = str(spec.get("description", check_id))
        critical = bool(spec.get("critical", False))
        notes = [str(item) for item in spec.get("notes", [])]
        expected = {key: value for key, value in spec.items() if key not in {"type", "id", "description", "critical", "notes"}}
        try:
            if check_type == "row_count":
                value = float(len(frame))
                status = _status_for_range(value, spec.get("min"), spec.get("max"))
            elif check_type == "rate":
                column = str(spec["column"])
                if column not in frame:
                    return self._missing_column(dataset, check_id, description, column, critical)
                series = frame[column]
                value = float(series.astype(str).eq(str(spec["value"])).mean()) if "value" in spec else float(pd.to_numeric(series, errors="coerce").mean())
                status = _status_for_range(value, spec.get("min"), spec.get("max"))
            elif check_type == "span_days":
                column = str(spec["column"])
                if column not in frame:
                    return self._missing_column(dataset, check_id, description, column, critical)
                dates = pd.to_datetime(frame[column], errors="coerce").dropna()
                value = float((dates.max() - dates.min()).days) if len(dates) else 0.0
                status = _status_for_range(value, spec.get("min"), spec.get("max"))
            elif check_type == "quantile_ratio":
                column = str(spec["column"])
                if column not in frame:
                    return self._missing_column(dataset, check_id, description, column, critical)
                values = pd.to_numeric(frame[column], errors="coerce").dropna()
                denominator = float(values.quantile(float(spec.get("q_low", 0.50)))) if len(values) else 0.0
                value = float(values.quantile(float(spec.get("q_high", 0.95))) / max(abs(denominator), 1e-9)) if len(values) else 0.0
                status = _status_for_range(value, spec.get("min"), spec.get("max"))
            elif check_type == "median_delay_days":
                start_column, end_column = str(spec["start_column"]), str(spec["end_column"])
                missing = [col for col in [start_column, end_column] if col not in frame]
                if missing:
                    return self._missing_column(dataset, check_id, description, ",".join(missing), critical)
                delay = (pd.to_datetime(frame[end_column], errors="coerce") - pd.to_datetime(frame[start_column], errors="coerce")).dt.total_seconds() / 86400
                value = float(delay.dropna().median()) if delay.notna().any() else 0.0
                status = _status_for_range(value, spec.get("min"), spec.get("max"))
            elif check_type == "mean_gap_smd":
                feature, target = str(spec["feature"]), str(spec["target"])
                missing = [col for col in [feature, target] if col not in frame]
                if missing:
                    return self._missing_column(dataset, check_id, description, ",".join(missing), critical)
                value = _smd(frame, feature, target)
                if value is None:
                    status = GateStatus.WATCH
                    notes.append("Insufficient variation or sample size for a stable SMD.")
                else:
                    minimum_abs = float(spec.get("min_abs", 0.15))
                    direction = str(spec.get("direction", "either"))
                    if direction == "positive":
                        status = GateStatus.PASS if value >= minimum_abs else GateStatus.FAIL
                    elif direction == "negative":
                        status = GateStatus.PASS if value <= -minimum_abs else GateStatus.FAIL
                    else:
                        status = GateStatus.PASS if abs(value) >= minimum_abs else GateStatus.FAIL
            elif check_type == "nunique":
                column = str(spec["column"])
                if column not in frame:
                    return self._missing_column(dataset, check_id, description, column, critical)
                value = float(frame[column].nunique(dropna=True))
                status = _status_for_range(value, spec.get("min"), spec.get("max"))
            elif check_type == "missing_rate":
                column = str(spec["column"])
                if column not in frame:
                    return self._missing_column(dataset, check_id, description, column, critical)
                value = float(frame[column].isna().mean())
                status = _status_for_range(value, spec.get("min"), spec.get("max"))
            else:
                value, status = None, GateStatus.WATCH
                notes.append(f"Unsupported check type: {check_type}")
        except Exception as exc:
            value, status = None, GateStatus.WATCH
            notes.append(f"{type(exc).__name__}: {exc}")
        if status == GateStatus.FAIL and not critical:
            status = GateStatus.WATCH
            notes.append("Non-critical profile mismatch; inspect before using the demo as a validation claim.")
        return DistributionCheck(dataset=dataset, check_id=f"{dataset}.{check_id}", description=description, status=status, observed=value, expected=expected, critical=critical, notes=notes)

    @staticmethod
    def _missing_column(dataset: str, check_id: str, description: str, column: str, critical: bool) -> DistributionCheck:
        return DistributionCheck(dataset=dataset, check_id=f"{dataset}.{check_id}", description=description, status=GateStatus.FAIL if critical else GateStatus.WATCH, observed=f"missing column(s): {column}", expected="column present", critical=critical, notes=["Distribution alignment cannot be evaluated for this item."])


@dataclass
class LabelMaturitySimulator:
    """Create a realistic observed-label view without changing hidden synthetic truth."""

    random_seed: int = 20260820
    median_lag_days: int = 45

    def transform(self, users: pd.DataFrame, cutoff_date: str | pd.Timestamp | None = None) -> tuple[pd.DataFrame, LabelMaturitySummary]:
        required = {"event_date", "fraud_label"}
        missing = required - set(users.columns)
        if missing:
            raise KeyError(f"label maturity simulation missing columns: {sorted(missing)}")
        rng = np.random.default_rng(self.random_seed)
        frame = users.copy()
        event_date = pd.to_datetime(frame["event_date"], errors="coerce")
        truth = pd.to_numeric(frame["fraud_label"], errors="coerce").fillna(0).astype(int)
        risk_score = pd.to_numeric(frame.get("risk_score_t1", pd.Series(0.15, index=frame.index)), errors="coerce").fillna(0.15)
        strategy_hits = pd.to_numeric(frame.get("strategy_hit_count_30d", pd.Series(0, index=frame.index)), errors="coerce").fillna(0)
        lag = np.maximum(7, rng.lognormal(mean=np.log(max(self.median_lag_days, 8)), sigma=0.55, size=len(frame))).round().astype(int)
        label_observed_at = event_date + pd.to_timedelta(lag, unit="D")
        selection_logit = -2.7 + 3.2 * risk_score + 0.45 * np.log1p(strategy_hits) + 1.2 * truth
        selection_probability = 1 / (1 + np.exp(-selection_logit))
        selected = rng.binomial(1, np.clip(selection_probability, 0.01, 0.95)).astype(int)
        inconclusive = (rng.random(len(frame)) < np.clip(0.04 + 0.12 * (1 - risk_score), 0.02, 0.20)) & selected.astype(bool)
        cutoff = pd.Timestamp(cutoff_date) if cutoff_date is not None else event_date.max() + pd.Timedelta(days=30)
        mature = selected.astype(bool) & label_observed_at.le(cutoff) & ~inconclusive
        observed = pd.Series(pd.NA, index=frame.index, dtype="Int64")
        observed.loc[mature] = truth.loc[mature].astype("Int64")
        status = np.full(len(frame), "NOT_SELECTED", dtype=object)
        status[selected.astype(bool)] = "PENDING"
        status[inconclusive] = "INCONCLUSIVE"
        status[mature & truth.eq(1)] = "MATURE_CONFIRMED"
        status[mature & truth.eq(0)] = "MATURE_CLEARED"
        frame["label_observed_at_simulated"] = label_observed_at
        frame["investigation_selected_flag"] = selected
        frame["observed_fraud_label"] = observed
        frame["observed_label_status"] = status
        frame["label_maturity_lag_days"] = lag
        mature_count = int(mature.sum())
        summary = LabelMaturitySummary(cutoff_date=str(cutoff.date()), total_rows=int(len(frame)), ground_truth_positive_rate=float(truth.mean()), investigation_selected_rate=float(selected.mean()), mature_label_rate=float(mature.mean()), observed_positive_rate_among_mature=float(observed.dropna().astype(int).mean()) if mature_count else None, pending_label_rate=float(pd.Series(status).eq("PENDING").mean()), inconclusive_rate=float(pd.Series(status).eq("INCONCLUSIVE").mean()), notes=["Synthetic observation model only; lag and selection are not production estimates.", "Use observed_fraud_label for realistic discovery simulations and fraud_label only as hidden evaluation truth."])
        return frame, summary
