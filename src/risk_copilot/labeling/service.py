from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..config import load_yaml


@dataclass
class RiskLabelingService:
    """Create leakage-safe training views from mature investigation labels."""

    config_path: str | Path
    config: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        self.config = load_yaml(self.config_path)

    def mature_training_view(
        self,
        records: pd.DataFrame,
        *,
        target: str,
        cutoff: str | datetime | pd.Timestamp,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        allowed = set(self.config["training_targets"]["allowed"])
        prohibited = set(self.config["training_targets"]["prohibited"])
        if target in prohibited:
            raise ValueError(
                f"{target} is a downstream filing outcome and cannot be used as a training target"
            )
        if target not in allowed:
            raise ValueError(f"target is not approved by the label taxonomy: {target}")

        event_field = str(self.config["event_time_field"])
        observed_field = str(self.config["label_observed_at_field"])
        disposition_field = str(self.config["disposition_field"])
        required = {event_field, observed_field, disposition_field, target}
        missing = sorted(required.difference(records.columns))
        if missing:
            raise ValueError(f"label dataset missing columns: {missing}")

        work = records.copy()
        work[event_field] = pd.to_datetime(work[event_field], utc=True)
        work[observed_field] = pd.to_datetime(work[observed_field], utc=True)
        cutoff_time = pd.Timestamp(cutoff)
        if cutoff_time.tzinfo is None:
            cutoff_time = cutoff_time.tz_localize("UTC")
        else:
            cutoff_time = cutoff_time.tz_convert("UTC")
        accepted = set(self.config["accepted_dispositions"])
        mature_mask = (
            (work[event_field] <= cutoff_time)
            & (work[observed_field] <= cutoff_time)
            & (work[disposition_field].astype(str).isin(accepted))
            & work[target].notna()
        )
        mature = work.loc[mature_mask].sort_values(
            [event_field, observed_field],
            kind="stable",
        )
        audit = {
            "schema_version": self.config["schema_version"],
            "target": target,
            "cutoff": cutoff_time.isoformat(),
            "input_rows": int(len(work)),
            "mature_rows": int(len(mature)),
            "excluded_rows": int((~mature_mask).sum()),
            "latest_event_time": (
                mature[event_field].max().isoformat() if not mature.empty else None
            ),
            "latest_label_observed_at": (
                mature[observed_field].max().isoformat() if not mature.empty else None
            ),
            "filing_outcome_used_as_target": False,
            "point_in_time_safe": bool(
                mature.empty
                or (
                    mature[event_field].max() <= cutoff_time
                    and mature[observed_field].max() <= cutoff_time
                )
            ),
        }
        return mature.reset_index(drop=True), audit

    def suspected_mislabel_queue(
        self,
        records: pd.DataFrame,
        *,
        scores: list[float] | np.ndarray,
        row_indices: list[Any] | pd.Index,
        target: str,
        model_name: str,
        evidence_columns: list[str],
        top_n: int = 70,
    ) -> list[dict[str, Any]]:
        """Return high-score negative samples for human label-quality review.

        The queue does not relabel any record.  It only prioritizes mature negative examples for
        a reviewer, mirroring the high-score negative-sample review described in the materials.
        """

        if target not in set(self.config.get("review_targets", [])):
            raise ValueError(f"target is not approved for label review: {target}")
        indices = list(row_indices)
        score_values = np.asarray(scores, dtype=float)
        if len(indices) != len(score_values):
            raise ValueError("row_indices and scores must have the same length")
        missing = sorted({target}.difference(records.columns))
        if missing:
            raise ValueError(f"review dataset missing columns: {missing}")

        selected = records.reindex(indices).copy()
        selected["model_score"] = score_values
        selected = selected[selected[target].fillna(0).astype(int) == 0]
        selected = selected.sort_values("model_score", ascending=False).head(top_n)
        rows: list[dict[str, Any]] = []
        for source_index, row in selected.iterrows():
            evidence: dict[str, Any] = {}
            for name in evidence_columns:
                if name not in selected.columns or pd.isna(row[name]):
                    continue
                value = row[name]
                if isinstance(value, pd.Timestamp):
                    value = value.isoformat()
                elif hasattr(value, "item"):
                    value = value.item()
                evidence[name] = value
            rows.append(
                {
                    "source_index": str(source_index),
                    "user_id": str(row.get("user_id", source_index)),
                    "event_date": (
                        pd.Timestamp(row["event_date"]).isoformat()
                        if "event_date" in row and pd.notna(row["event_date"])
                        else None
                    ),
                    "current_label": int(row[target]),
                    "model_score": round(float(row["model_score"]), 8),
                    "model_name": model_name,
                    "review_reason": "high_score_negative_requires_human_label_review",
                    "review_status": "PENDING",
                    "automatic_relabel_allowed": False,
                    "evidence_snapshot": evidence,
                }
            )
        return rows
