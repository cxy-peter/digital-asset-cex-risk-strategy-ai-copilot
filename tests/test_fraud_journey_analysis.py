from __future__ import annotations

import numpy as np
import pandas as pd

from risk_copilot.fraud_journey import (
    derive_supported_journey_features,
    feature_coverage_frame,
    model_grid_frame,
    render_focused_report,
    sessionize_user_events,
)


def test_model_grid_does_not_hardcode_one_to_four() -> None:
    grid = model_grid_frame()
    ratios = set(grid["negative_to_positive_ratio"].dropna().astype(int))
    assert ratios == {3, 4, 5}
    assert grid["negative_to_positive_ratio"].isna().any()


def test_sessionization_excludes_system_events_before_gap_calculation() -> None:
    events = pd.DataFrame(
        {
            "user_id": ["U1", "U1", "U1", "U1"],
            "event_time": [
                "2026-01-01 10:00:00",
                "2026-01-01 10:00:01",
                "2026-01-01 10:05:00",
                "2026-01-01 11:10:00",
            ],
            "event_type": ["FIAT_DEPOSIT", "ReconciliationCheck", "CONVERT", "CHAIN_WITHDRAW"],
            "event_origin": ["USER", "SYSTEM", "USER", "USER"],
        }
    )
    filtered, sessions = sessionize_user_events(events, gap_minutes=60)
    assert "ReconciliationCheck" not in set(filtered["event_type"])
    assert sessions.shape[0] == 2
    assert sessions.iloc[0]["user_event_count"] == 2


def test_fund_flow_consistency_features_follow_source_formula() -> None:
    users = pd.DataFrame(
        {
            "user_id": ["U1"],
            "fiat_deposit_amount_24h": [100.0],
            "chain_out_amount_24h": [100.0],
            "spot_trade_amount_24h": [100.0],
            "fiat_deposit_count_24h": [1],
            "fiat_withdraw_count_24h": [0],
            "chain_withdraw_count_24h": [1],
            "spot_trade_count_24h": [1],
            "convert_count_24h": [0],
            "internal_transfer_count_24h": [0],
            "chain_out_5min_count_30d": [1],
            "minutes_deposit_to_first_chain_out": [4.0],
        }
    )
    derived = derive_supported_journey_features(users)
    assert np.isclose(derived.loc[0, "fund_flow_cv_proxy"], 0.0)
    assert np.isclose(derived.loc[0, "fund_flow_range_ratio_proxy"], 0.0)
    assert derived.loc[0, "rapid_chain_out_proxy"] == 1


def test_coverage_distinguishes_exact_approximate_and_missing() -> None:
    coverage = feature_coverage_frame(
        [
            "registration_channel",
            "kyc_level",
            "trade_pair_count_30d",
            "strategy_hit_count_30d",
        ]
    )
    status = coverage.set_index("source_feature")["status"].to_dict()
    assert status["registration_device_side"] == "EXACT"
    assert status["USDTTRY_TRXTRY_BTCTRY_flags"] == "MISSING"
    assert status["strategy_hit_frequency"] == "LINEAGE_RISK"


def test_report_preserves_white_sample_and_sampling_boundaries() -> None:
    report = render_focused_report()
    assert "Curated white users are not equivalent" in report
    assert "1:4 is a candidate, not a fixed default" in report
