from pathlib import Path

import pandas as pd
import yaml

from risk_copilot.governance.company_lifecycle import CompanyStrategyTestPlanner
from risk_copilot.governance.effectiveness import StrategyEffectivenessService
from risk_copilot.integrations.cms_str import CMSSTRIntegrationService
from risk_copilot.schemas import (
    ActionType,
    BacktestMetrics,
    Condition,
    GovernanceDecision,
    RiskDomain,
    RuleGroup,
    StrategyCandidate,
    StrategyStatus,
)

ROOT = Path(__file__).resolve().parents[1]


def _strategy(tag3="CMS_STR_CANDIDATE"):
    return StrategyCandidate(
        strategy_id="TEST-001",
        name="test",
        domain=RiskDomain.FUND_SECURITY,
        event_code="ChainWithdraw",
        description="test",
        rule=RuleGroup(conditions=[Condition(feature="fiat_in_crypto_out_ratio", operator=">=", value=0.8)]),
        action=ActionType.RFI,
        required_features=["fiat_in_crypto_out_ratio"],
        tag_level_1="fund_security",
        tag_level_2="rapid_fiat_convert_chain_out",
        tag_level_3=tag3,
    )


def _metrics():
    return BacktestMetrics(
        sample_size=1000, positives=100, alerts=50, true_positives=35, false_positives=15,
        false_negatives=65, true_negatives=885, precision=0.7, recall=0.35, f1=0.4667,
        false_positive_rate=0.0167, alert_rate=0.05, lift=7.0, captured_loss_rate=0.55,
        alert_amount=1000, captured_loss_amount=550, monthly_precision_std=0.02,
        monthly_alert_rate_std=0.01, stability_score=0.97, explainability_score=0.95,
        operational_score=1.0, reward=0.8, relative_advantage=1.2,
    )


def _governance():
    return GovernanceDecision(
        strategy_id="TEST-001",
        current_status=StrategyStatus.SIMULATION,
        next_status=StrategyStatus.PENDING_REVIEW,
        decision="approve",
        reasons=["passed"],
        required_approvals=["risk_strategy", "risk_operations"],
        audit_fields={"event_contract_error_count":0,"event_contract_hash":"a"*64},
    )


def test_company_plan_and_effectiveness_ticket(tmp_path):
    plan = CompanyStrategyTestPlanner(ROOT / "configs/test_environment.yaml").build_plan(
        strategy=_strategy(), strategy_version=1, engine_payload={"x":1}, metrics=_metrics(),
        governance=_governance(), data_snapshot_id="SNAP-1", feature_catalog_version="FEP-1"
    )
    assert plan.release_status == "PENDING_SECOND_REVIEW"
    assert plan.monitoring_workdays == 3
    assert {stage.name for stage in plan.stages} >= {"independent_second_review","post_launch_observation"}
    ticket = StrategyEffectivenessService(tmp_path / "eff.sqlite").create_simulation_ticket(plan=plan, metrics=_metrics())
    assert ticket.label == "EFFECTIVE"
    assert ticket.synthetic_demo is True


def test_cms_str_one_click_is_internal_only(tmp_path):
    data = pd.DataFrame({
        "user_id":["U1","U2"],
        "fiat_in_crypto_out_ratio":[0.9,0.2],
        "fraud_label":[1,0],
        "final_tier":["L3.2","L1"],
    })
    out = CMSSTRIntegrationService(ROOT/"configs/cms_str_integration.yaml", tmp_path/"cms.sqlite").prepare_candidates(
        strategy=_strategy(), strategy_version=1, data=data, data_snapshot_id="SNAP-1"
    )
    assert out["enabled"] is True
    assert out["case_count"] == 1
    case = out["cases"][0]
    assert case.external_submission_allowed is False
    assert case.automatic_filing_performed is False
    assert case.masak_feedback_status == "NOT_SUBMITTED"


def test_three_workday_observation_template_is_blank_and_not_production(tmp_path):
    plan = CompanyStrategyTestPlanner(ROOT / "configs/test_environment.yaml").build_plan(
        strategy=_strategy(), strategy_version=2, engine_payload={"x": 2}, metrics=_metrics(),
        governance=_governance(), data_snapshot_id="SNAP-2", feature_catalog_version="FEP-2"
    )
    service = StrategyEffectivenessService(tmp_path / "eff.sqlite")
    rows = service.create_three_workday_observation_template(plan=plan, baseline_metrics=_metrics())
    assert len(rows) == 3
    assert [row["workday_index"] for row in rows] == [1, 2, 3]
    assert all(row["status"] == "PLANNED_NOT_EXECUTED" for row in rows)
    assert all(row["production_observation_performed"] is False for row in rows)
    assert all(row["hit_count"] is None and row["false_positive_rate"] is None for row in rows)


def test_strategy_knowledge_scope_excludes_operations_dashboard_scenario():
    scenarios = yaml.safe_load((ROOT / "data/knowledge/risk_scenarios.yaml").read_text(encoding="utf-8"))
    assert all(item.get("scenario_id") != "CEX-OPS" for item in scenarios)
    assert not (ROOT / "data/sop/compliance_knowledge_qa.md").exists()
    assert not (ROOT / "data/sop/regulatory_reporting.md").exists()
    assert not (ROOT / "data/sop/sar_str_drafting.md").exists()
