from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from risk_copilot.governance.repository import StrategyRegistryRepository
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


def _candidate() -> StrategyCandidate:
    return StrategyCandidate(
        strategy_id="CONCURRENT-STRATEGY",
        name="Concurrent version test",
        domain=RiskDomain.FUND_SECURITY,
        event_code="ChainWithdraw",
        description="test",
        rule=RuleGroup(
            conditions=[
                Condition(
                    feature="fraud_graph_score",
                    operator=">",
                    value=0.8,
                )
            ]
        ),
        action=ActionType.MANUAL_REVIEW,
        required_features=["fraud_graph_score"],
    )


def _metrics() -> BacktestMetrics:
    return BacktestMetrics(
        sample_size=100,
        positives=10,
        alerts=8,
        true_positives=6,
        false_positives=2,
        false_negatives=4,
        true_negatives=88,
        precision=0.75,
        recall=0.60,
        f1=2 * 0.75 * 0.60 / (0.75 + 0.60),
        false_positive_rate=2 / 90,
        alert_rate=0.08,
        lift=7.5,
        captured_loss_rate=0.50,
        alert_amount=1000,
        captured_loss_amount=600,
        monthly_precision_std=0.01,
        monthly_alert_rate_std=0.01,
        stability_score=0.95,
        explainability_score=1.0,
        operational_score=0.9,
    )


def _governance() -> GovernanceDecision:
    return GovernanceDecision(
        strategy_id="CONCURRENT-STRATEGY",
        current_status=StrategyStatus.DRAFT,
        next_status=StrategyStatus.PENDING_REVIEW,
        decision="hold",
        reasons=["test"],
        required_approvals=["risk_owner"],
    )


def test_concurrent_version_allocation_is_atomic(tmp_path):
    database = tmp_path / "registry.sqlite"
    candidate = _candidate()
    metrics = _metrics()
    governance = _governance()

    def persist(_):
        return StrategyRegistryRepository(database).persist_candidate(
            candidate,
            metrics,
            governance,
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(persist, range(8)))

    versions = sorted(record["version"] for record in records)
    assert versions == list(range(1, 9))
