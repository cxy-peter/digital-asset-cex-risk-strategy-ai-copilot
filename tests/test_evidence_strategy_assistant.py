from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from risk_copilot.evidence_assistant import AssistantRequest, EvidenceGroundedStrategyAssistant, LabelMaturitySimulator, SyntheticDistributionAuditor
from risk_copilot.evidence_assistant.models import GateStatus


def _users(n: int = 1500) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    fraud = rng.binomial(1, 0.07, n)
    event_date = pd.Timestamp("2026-01-01") + pd.to_timedelta(rng.integers(0, 180, n), unit="D")
    return pd.DataFrame({
        "user_id": [f"U{i:06d}" for i in range(n)],
        "event_date": event_date,
        "kyc_level": rng.choice(["L1", "L2"], n, p=[0.16, 0.84]),
        "fraud_label": fraud,
        "latent_rapid_cashout": rng.binomial(1, 0.055, n),
        "latent_ato": rng.binomial(1, 0.025, n),
        "latent_campaign": rng.binomial(1, 0.045, n),
        "latent_aml": rng.binomial(1, 0.035, n),
        "latent_graph_ring": rng.binomial(1, 0.045, n),
        "sanctions_screening_hit": rng.binomial(1, 0.006, n),
        "pep_flag": rng.binomial(1, 0.008, n),
        "fiat_deposit_amount_24h": rng.lognormal(7.0, 1.25, n),
        "estimated_loss_amount": rng.lognormal(6.5, 1.35, n) * (0.3 + 3.0 * fraud),
        "fiat_in_crypto_out_ratio": np.clip(rng.beta(2, 4, n) + 0.55 * fraud, 0, 1.5),
        "high_risk_chain_exposure": np.clip(rng.beta(1, 12, n) + 0.35 * fraud, 0, 1),
        "failed_login_count_1h": rng.poisson(0.3 + 2.0 * fraud, n),
        "counterparty_fraud_ratio": np.clip(rng.beta(1, 15, n) + 0.45 * fraud, 0, 1),
        "risk_score_t1": np.clip(rng.beta(2, 8, n) + 0.35 * fraud, 0, 1),
        "strategy_hit_count_30d": rng.poisson(0.3 + 3.0 * fraud, n),
    })


def _transactions(n: int = 2500) -> pd.DataFrame:
    rng = np.random.default_rng(43)
    event_time = pd.Timestamp("2026-01-01") + pd.to_timedelta(rng.integers(0, 210, n), unit="D")
    return pd.DataFrame({"event_time": event_time, "label_observed_at": event_time + pd.Timedelta(days=30), "event_type": rng.choice(["FIAT_DEPOSIT", "FIAT_WITHDRAW", "CONVERT", "SPOT_TRADE", "CHAIN_DEPOSIT", "CHAIN_WITHDRAW", "INTERNAL_TRANSFER"], n), "label_suspicious": rng.binomial(1, 0.035, n), "amount_usdt": rng.lognormal(6.5, 1.2, n)})


def _cases(n: int = 1200) -> pd.DataFrame:
    rng = np.random.default_rng(44)
    return pd.DataFrame({"status": rng.choice(["completed", "pending", "reviewing", "cancelled"], n, p=[0.62, 0.14, 0.20, 0.04]), "priority": rng.choice(["P0", "P1", "P2", "P3"], n, p=[0.05, 0.20, 0.55, 0.20]), "duplicate_flag": rng.binomial(1, 0.075, n), "handling_hours": rng.lognormal(3.8, 0.9, n), "status_history": ["[]"] * n})


def _assistant(tmp_path: Path) -> EvidenceGroundedStrategyAssistant:
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    (config_dir / "evidence_strategy_assistant.yaml").write_text(yaml.safe_dump({"public_boundary": ["synthetic only"]}), encoding="utf-8")
    (config_dir / "synthetic_distribution_profile.yaml").write_text(yaml.safe_dump({"version": "test", "disclaimer": "synthetic", "datasets": {}}), encoding="utf-8")
    return EvidenceGroundedStrategyAssistant.create(tmp_path)


def test_label_maturity_keeps_truth_separate() -> None:
    observed, summary = LabelMaturitySimulator(random_seed=7).transform(_users(), cutoff_date="2026-07-31")
    assert observed["observed_fraud_label"].isna().any()
    assert observed["observed_fraud_label"].notna().any()
    assert 0 < summary.investigation_selected_rate < 1
    assert 0 < summary.mature_label_rate < 1
    assert set(observed["observed_label_status"].unique()) <= {"NOT_SELECTED", "PENDING", "INCONCLUSIVE", "MATURE_CONFIRMED", "MATURE_CLEARED"}


def test_distribution_auditor_reports_instead_of_crashing(tmp_path: Path) -> None:
    profile = {"version": "test.v1", "disclaimer": "synthetic", "datasets": {"users": {"checks": [{"id": "rows", "type": "row_count", "min": 1000, "critical": True}, {"id": "rate", "type": "rate", "column": "fraud_label", "min": 0.02, "max": 0.15, "critical": True}, {"id": "gap", "type": "mean_gap_smd", "feature": "fiat_in_crypto_out_ratio", "target": "fraud_label", "direction": "positive", "min_abs": 0.1}]}, "transactions": {"checks": [{"id": "events", "type": "nunique", "column": "event_type", "min": 6, "critical": True}, {"id": "delay", "type": "median_delay_days", "start_column": "event_time", "end_column": "label_observed_at", "min": 20, "max": 40, "critical": True}]}, "cases": {"checks": [{"id": "dupes", "type": "rate", "column": "duplicate_flag", "min": 0.03, "max": 0.15}]}}}
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text(yaml.safe_dump(profile), encoding="utf-8")
    audit = SyntheticDistributionAuditor.from_yaml(profile_path).audit({"users": _users(), "transactions": _transactions(), "cases": _cases()})
    assert audit.overall_status in {GateStatus.PASS, GateStatus.WATCH}
    assert audit.failed == 0
    assert len(audit.checks) == 6


def test_assistant_builds_5716_and_full_delivery_workflow(tmp_path: Path) -> None:
    assistant = _assistant(tmp_path)
    request = AssistantRequest(request_id="REQ-ATO-001", query="Detect account takeover after a new device and password change before withdrawal", business_objective="Reduce account-takeover loss while keeping user friction within review capacity.", risk_domain="account_security", event_code="ChainWithdraw")
    plan = assistant.build_plan(request)
    assert plan.inferred_scenario == "account_takeover"
    assert len(plan.problem_decomposition) == 7
    assert len(plan.delivery_workflow) == 11
    assert len(plan.model_analysis_playbook) == 13
    assert plan.problem_decomposition[0].layer == "Macro objective"
    assert plan.delivery_workflow[-1].stage == "Post-release RCA and iteration"
    assert any(item.family == "authentication_and_security_change" for item in plan.feature_families)


def test_outputs_include_existing_strategy_request(tmp_path: Path) -> None:
    assistant = _assistant(tmp_path)
    request = AssistantRequest(request_id="REQ-CASHOUT-001", query="Rapid cashout after fiat deposit and conversion", business_objective="Reduce suspicious fund-flow exposure.")
    plan = assistant.build_plan(request)
    paths = assistant.write_outputs(plan, output_dir=tmp_path / "outputs")
    assert paths["plan_json"].exists()
    assert paths["plan_markdown"].exists()
    payload = paths["strategy_request"].read_text(encoding="utf-8")
    assert '"require_human_review": true' in payload
    assert '"event_code": "ChainWithdraw"' in payload


def test_repository_demo_matches_public_profile_when_available() -> None:
    root = Path(__file__).resolve().parents[1]
    profile = root / "configs" / "synthetic_distribution_profile.yaml"
    data_dir = root / "data" / "demo"
    if not profile.exists() or not (data_dir / "users.csv").exists():
        return
    audit = SyntheticDistributionAuditor.from_yaml(profile).audit_directory(data_dir)
    assert audit.overall_status != GateStatus.FAIL, [item.model_dump() for item in audit.checks if item.status == GateStatus.FAIL]
