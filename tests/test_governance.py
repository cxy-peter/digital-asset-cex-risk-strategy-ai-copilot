from pathlib import Path

from risk_copilot.features.registry import FeatureRegistry
from risk_copilot.governance.workflow import StrategyGovernanceWorkflow
from risk_copilot.schemas import (
    ActionType,
    BacktestMetrics,
    Condition,
    RiskDomain,
    RuleGroup,
    StrategyCandidate,
    StrategyRequest,
)

ROOT = Path(__file__).resolve().parents[1]


def metrics(precision=0.8, recall=0.2, alert_rate=0.02):
    return BacktestMetrics(
        sample_size=3000, positives=200, alerts=60, true_positives=40, false_positives=20,
        false_negatives=160, true_negatives=2780, precision=precision, recall=recall, f1=0.32,
        false_positive_rate=0.007, alert_rate=alert_rate, lift=10, captured_loss_rate=0.25,
        alert_amount=1000, captured_loss_amount=500, monthly_precision_std=0.02,
        monthly_alert_rate_std=0.01, stability_score=0.97, explainability_score=0.9,
        operational_score=1.0,
    )


def test_governance_never_directly_goes_online():
    registry = FeatureRegistry(ROOT / "configs/features.yaml", ROOT / "configs/events.yaml")
    workflow = StrategyGovernanceWorkflow(ROOT / "configs/governance.yaml", registry)
    strategy = StrategyCandidate(
        strategy_id="S1", name="test", domain=RiskDomain.FUND_SECURITY, event_code="ChainWithdraw",
        description="test", rule=RuleGroup(conditions=[Condition(feature="fiat_in_crypto_out_ratio", operator=">=", value=0.8)]),
        action=ActionType.MANUAL_REVIEW, required_features=["fiat_in_crypto_out_ratio"],
    )
    request = StrategyRequest(request_id="R1", query="test", domain=RiskDomain.FUND_SECURITY, event_code="ChainWithdraw")
    decision = workflow.review(strategy, metrics(), request)
    assert decision.next_status.value == "PENDING_REVIEW"
    payload = workflow.build_engine_payload(strategy, decision, metrics())
    assert payload["eventContract"]["version"].startswith(
        "ChainWithdraw@sha256:"
    )
    assert len(payload["eventContract"]["sha256"]) == 64
    assert payload["eventContract"]["errorCount"] == 0
