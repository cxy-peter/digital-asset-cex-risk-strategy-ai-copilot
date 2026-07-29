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


def _strategy():
    return StrategyCandidate(
        strategy_id='REGISTRY-DEMO',
        name='Registry demo',
        domain=RiskDomain.FUND_SECURITY,
        event_code='ChainWithdraw',
        description='demo',
        rule=RuleGroup(conditions=[Condition(feature='fiat_in_crypto_out_ratio', operator='>', value=0.9)]),
        action=ActionType.RFI,
        required_features=['fiat_in_crypto_out_ratio'],
        status=StrategyStatus.SIMULATION,
    )


def _metrics():
    return BacktestMetrics(
        sample_size=100,
        positives=10,
        alerts=8,
        true_positives=6,
        false_positives=2,
        false_negatives=4,
        true_negatives=88,
        precision=0.75,
        recall=0.6,
        f1=0.6667,
        false_positive_rate=2/90,
        alert_rate=0.08,
        lift=7.5,
        captured_loss_rate=0.7,
        alert_amount=1000,
        captured_loss_amount=700,
        monthly_precision_std=0.02,
        monthly_alert_rate_std=0.01,
        stability_score=0.95,
        explainability_score=1.0,
        operational_score=0.9,
        reward=0.8,
        relative_advantage=1.2,
    )


def _decision():
    return GovernanceDecision(
        strategy_id='REGISTRY-DEMO',
        current_status=StrategyStatus.SIMULATION,
        next_status=StrategyStatus.PENDING_REVIEW,
        decision='approve',
        reasons=['demo passed'],
        required_approvals=['risk_strategy', 'compliance'],
        audit_fields={'mode': 'synthetic'},
    )


def test_registry_versions_and_audit_history(tmp_path):
    repository = StrategyRegistryRepository(tmp_path / 'registry.sqlite')
    first = repository.persist_candidate(_strategy(), _metrics(), _decision())
    second = repository.persist_candidate(_strategy(), _metrics(), _decision())
    repository.record_approval('REGISTRY-DEMO', 2, 'risk_strategy', 'approve', 'alice', 'reviewed')

    history = repository.history('REGISTRY-DEMO')
    assert first['version'] == 1
    assert second['version'] == 2
    assert len(history['versions']) == 2
    assert history['approvals'][0]['actor'] == 'alice'
    assert len(history['audit_events']) == 2
