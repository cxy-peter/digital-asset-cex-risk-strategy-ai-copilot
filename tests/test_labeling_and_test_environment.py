from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from risk_copilot.features.registry import FeatureRegistry
from risk_copilot.governance.simulation_gate import TestEnvironmentGate
from risk_copilot.labeling import RiskLabelingService


ROOT = Path(__file__).resolve().parents[1]


def test_label_maturity_excludes_future_outcomes_and_filing_target():
    records = pd.DataFrame(
        {
            "event_time": pd.to_datetime(
                ["2026-01-01", "2026-01-15", "2026-02-01"], utc=True
            ),
            "label_observed_at": pd.to_datetime(
                ["2026-01-20", "2026-02-20", "2026-03-01"], utc=True
            ),
            "case_disposition": [
                "confirmed_suspicious",
                "confirmed_suspicious",
                "cleared",
            ],
            "aml_suspicion_confirmed": [1, 1, 0],
            "sar_str_filed": [1, 0, 0],
        }
    )
    service = RiskLabelingService(ROOT / "configs/labeling.yaml")
    mature, audit = service.mature_training_view(
        records,
        target="aml_suspicion_confirmed",
        cutoff="2026-02-01",
    )

    assert len(mature) == 1
    assert audit["point_in_time_safe"] is True
    assert audit["filing_outcome_used_as_target"] is False
    with pytest.raises(ValueError, match="filing outcome"):
        service.mature_training_view(
            records,
            target="sar_str_filed",
            cutoff="2026-04-01",
        )


def test_test_environment_requires_registration_confirmation_and_no_production():
    registry = FeatureRegistry(
        ROOT / "configs/features.yaml",
        ROOT / "configs/events.yaml",
    )
    gate = TestEnvironmentGate(
        ROOT / "configs/test_environment.yaml",
        registry,
    )
    accepted = gate.assess(
        event_code="ChainWithdraw",
        feature_names=[
            "fraud_graph_score",
            "strategy_avoidance_ratio_30d",
            "chain_out_5min_count_30d",
        ],
        requested_status="SIMULATION",
        payload_confirmed=True,
    )
    assert accepted["allowed"] is True
    assert accepted["production_connection"] is False

    blocked = gate.assess(
        event_code="UnknownEvent",
        feature_names=["made_up_feature"],
        requested_status="ONLINE",
        payload_confirmed=False,
        production_connection=True,
    )
    assert blocked["allowed"] is False
    assert "payload_confirmation_required" in blocked["blockers"]
    assert "production_connection_forbidden" in blocked["blockers"]
