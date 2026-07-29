from __future__ import annotations

import pandas as pd

from risk_copilot.scoring.repository import RiskSnapshotRepository, T1RiskBatchRunner
from risk_copilot.scoring.service import UserRiskScoringService


def _row(risk_score: float) -> dict:
    return {
        "user_id": "U_PERSIST",
        "age_risk_score": 0.8,
        "occupation_risk_score": 0.9,
        "nationality_risk_score": 0.8,
        "address_risk_score": 0.7,
        "kyc_country_risk": 0.8,
        "kyc_level": "L1",
        "risk_score_t1": risk_score,
        "fiat_in_crypto_out_ratio": risk_score,
        "high_risk_chain_exposure": risk_score,
        "counterparty_fraud_ratio": risk_score,
        "fraud_graph_score": risk_score,
        "bank_fraud_ratio_max": risk_score,
        "proxy_flag": 1,
        "new_device_flag": 1,
    }


def test_manual_override_survives_subsequent_t1_batches(tmp_path):
    repository = RiskSnapshotRepository(tmp_path / "risk_snapshots.sqlite")
    runner = T1RiskBatchRunner(repository, UserRiskScoringService())
    repository.set_manual_override(
        "U_PERSIST",
        "L3.2",
        reason="EDD reviewer decision",
        actor="risk_reviewer",
    )

    first, first_manifest = runner.run(
        pd.DataFrame([_row(0.95)]),
        batch_id="T1-2026-07-27",
        as_of_date="2026-07-27",
    )
    second, second_manifest = runner.run(
        pd.DataFrame([_row(0.10)]),
        batch_id="T1-2026-07-28",
        as_of_date="2026-07-28",
    )

    assert first.iloc[0]["final_tier"] == "L3.2"
    assert second.iloc[0]["final_tier"] == "L3.2"
    assert second.iloc[0]["risk_source"] == "manual_override"
    assert first.iloc[0]["automatic_tier"] != second.iloc[0]["automatic_tier"]
    assert first_manifest["manual_override_count"] == 1
    assert second_manifest["manual_override_count"] == 1

    current = repository.current_profile("U_PERSIST")
    assert current is not None
    assert current["final_tier"] == "L3.2"
    assert current["str_details"] is None
    assert len(repository.history("U_PERSIST")["snapshots"]) == 2


def test_batch_is_idempotent_per_batch_and_user(tmp_path):
    repository = RiskSnapshotRepository(tmp_path / "risk_snapshots.sqlite")
    runner = T1RiskBatchRunner(repository, UserRiskScoringService())
    frame = pd.DataFrame([_row(0.75)])

    runner.run(frame, batch_id="T1-SAME", as_of_date="2026-07-28")
    runner.run(frame, batch_id="T1-SAME", as_of_date="2026-07-28")

    assert len(repository.history("U_PERSIST")["snapshots"]) == 1
