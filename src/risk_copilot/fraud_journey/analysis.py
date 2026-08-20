from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .catalog import (
    BUSINESS_EVENT_CODES,
    COHORT_DEFINITIONS,
    FEATURE_MAPPINGS,
    MODEL_GRID,
    SOURCE_ANALYSIS_STEPS,
    CoverageStatus,
    mappings_for_columns,
    model_grid_records,
)


def _safe_numeric(frame: pd.DataFrame, name: str) -> pd.Series:
    if name not in frame:
        return pd.Series(np.nan, index=frame.index, dtype=float)
    return pd.to_numeric(frame[name], errors="coerce")


def derive_supported_journey_features(users: pd.DataFrame) -> pd.DataFrame:
    """Derive only source-aligned features that are supportable from the public demo.

    The function intentionally does not manufacture pair, bank-identity, account-role or label-source
    fields that are absent from the public synthetic data.
    """

    result = users.copy()
    aligned = pd.concat(
        [
            _safe_numeric(result, "fiat_deposit_amount_24h").rename("fiat_in"),
            _safe_numeric(result, "chain_out_amount_24h").rename("chain_out"),
            _safe_numeric(result, "spot_trade_amount_24h").rename("spot_trade"),
        ],
        axis=1,
    )
    mean = aligned.mean(axis=1)
    result["fund_flow_cv_proxy"] = aligned.std(axis=1, ddof=1).div(mean.replace(0, np.nan))
    result["fund_flow_range_ratio_proxy"] = (
        aligned.max(axis=1).sub(aligned.min(axis=1)).div(mean.replace(0, np.nan))
    )
    count_columns = [
        "fiat_deposit_count_24h",
        "fiat_withdraw_count_24h",
        "chain_withdraw_count_24h",
        "spot_trade_count_24h",
        "convert_count_24h",
        "internal_transfer_count_24h",
    ]
    counts = pd.concat([_safe_numeric(result, name).fillna(0).rename(name) for name in count_columns], axis=1)
    result["has_any_behavior_proxy"] = counts.sum(axis=1).gt(0).astype(int)
    result["silent_user_proxy"] = counts.sum(axis=1).eq(0).astype(int)
    fast_count = _safe_numeric(result, "chain_out_5min_count_30d").fillna(0)
    minutes = _safe_numeric(result, "minutes_deposit_to_first_chain_out")
    result["rapid_chain_out_proxy"] = (fast_count.gt(0) | minutes.le(5)).astype(int)
    return result


def sessionize_user_events(
    events: pd.DataFrame,
    *,
    gap_minutes: int = 60,
    user_column: str = "user_id",
    time_column: str = "event_time",
    event_column: str = "event_type",
    origin_column: str = "event_origin",
    user_origins: Iterable[str] = ("USER", "USER_INITIATED", "user", "user_initiated"),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build sessions only after removing system-derived events.

    This directly addresses the source finding that a raw 60-minute session metric was polluted by
    automatic follow-up events. If ``event_origin`` is unavailable, the source business-event allowlist
    is used and the caller should treat the result as a weaker approximation.
    """

    required = {user_column, time_column, event_column}
    missing = required.difference(events.columns)
    if missing:
        raise KeyError(f"missing event columns: {sorted(missing)}")
    work = events.copy()
    work[time_column] = pd.to_datetime(work[time_column], errors="coerce")
    work = work.dropna(subset=[user_column, time_column])
    if origin_column in work:
        work = work[work[origin_column].astype(str).isin(set(user_origins))]
    else:
        work = work[work[event_column].astype(str).isin(set(BUSINESS_EVENT_CODES))]
    work = work.sort_values([user_column, time_column]).copy()
    previous = work.groupby(user_column)[time_column].shift(1)
    gap = work[time_column].sub(previous).dt.total_seconds().div(60)
    work["gap_minutes_from_previous_user_event"] = gap
    work["new_session"] = previous.isna() | gap.gt(gap_minutes)
    work["session_number"] = work.groupby(user_column)["new_session"].cumsum().astype(int)
    work["session_id"] = work[user_column].astype(str) + "::" + work["session_number"].astype(str)

    session = (
        work.groupby([user_column, "session_id"], as_index=False)
        .agg(
            session_start=(time_column, "min"),
            session_end=(time_column, "max"),
            user_event_count=(event_column, "size"),
            distinct_user_event_count=(event_column, "nunique"),
            median_gap_minutes=("gap_minutes_from_previous_user_event", "median"),
        )
    )
    session["session_duration_minutes"] = (
        session["session_end"].sub(session["session_start"]).dt.total_seconds().div(60)
    )
    return work.reset_index(drop=True), session


def feature_coverage_frame(columns: Iterable[str]) -> pd.DataFrame:
    rows = [asdict(item) for item in mappings_for_columns(columns)]
    frame = pd.DataFrame(rows)
    frame["status"] = frame["status"].map(lambda value: value.value if isinstance(value, CoverageStatus) else str(value))
    return frame


def model_grid_frame() -> pd.DataFrame:
    return pd.DataFrame(model_grid_records())


def source_playbook_frame() -> pd.DataFrame:
    return pd.DataFrame([asdict(step) for step in SOURCE_ANALYSIS_STEPS])


def cohort_contract_frame() -> pd.DataFrame:
    return pd.DataFrame(list(COHORT_DEFINITIONS))


def audit_summary(coverage: pd.DataFrame) -> dict[str, int]:
    counts = coverage["status"].value_counts().to_dict()
    return {status.value: int(counts.get(status.value, 0)) for status in CoverageStatus}


def write_analysis_artifacts(
    *,
    output_dir: str | Path,
    users: pd.DataFrame | None = None,
    transactions: pd.DataFrame | None = None,
) -> dict[str, Path]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    columns = users.columns if users is not None else []
    coverage = feature_coverage_frame(columns)
    coverage_path = target / "fraud_journey_feature_coverage.csv"
    coverage.to_csv(coverage_path, index=False)
    playbook_path = target / "fraud_journey_analysis_steps.csv"
    source_playbook_frame().to_csv(playbook_path, index=False)
    cohort_path = target / "fraud_journey_cohort_contract.csv"
    cohort_contract_frame().to_csv(cohort_path, index=False)
    grid_path = target / "fraud_journey_model_grid.csv"
    model_grid_frame().to_csv(grid_path, index=False)

    paths: dict[str, Path] = {
        "coverage": coverage_path,
        "playbook": playbook_path,
        "cohorts": cohort_path,
        "model_grid": grid_path,
    }
    if users is not None:
        derived = derive_supported_journey_features(users)
        preview_columns = [
            name
            for name in [
                "user_id",
                "fraud_label",
                "fund_flow_cv_proxy",
                "fund_flow_range_ratio_proxy",
                "has_any_behavior_proxy",
                "silent_user_proxy",
                "rapid_chain_out_proxy",
            ]
            if name in derived
        ]
        derived_path = target / "fraud_journey_derived_feature_preview.csv"
        derived[preview_columns].head(500).to_csv(derived_path, index=False)
        paths["derived_preview"] = derived_path
    if transactions is not None:
        try:
            user_events, sessions = sessionize_user_events(transactions)
            event_path = target / "fraud_journey_user_events_preview.csv"
            session_path = target / "fraud_journey_sessions_preview.csv"
            user_events.head(1000).to_csv(event_path, index=False)
            sessions.head(1000).to_csv(session_path, index=False)
            paths["event_preview"] = event_path
            paths["session_preview"] = session_path
        except KeyError:
            pass
    return paths
