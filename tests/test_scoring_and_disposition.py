import pandas as pd

from risk_copilot.governance.disposition import DispositionPlanner
from risk_copilot.scoring.service import UserRiskScoringService
from risk_copilot.schemas import ActionType, Condition, RiskDomain, RuleGroup, StrategyCandidate


def _high_risk_row():
    return pd.Series({
        'user_id': 'U_TEST',
        'age_risk_score': 0.8,
        'occupation_risk_score': 0.9,
        'nationality_risk_score': 0.8,
        'address_risk_score': 0.7,
        'kyc_country_risk': 0.8,
        'kyc_level': 'L1',
        'risk_score_t1': 0.95,
        'fiat_in_crypto_out_ratio': 0.98,
        'high_risk_chain_exposure': 0.9,
        'counterparty_fraud_ratio': 0.8,
        'fraud_graph_score': 0.9,
        'bank_fraud_ratio_max': 0.8,
        'proxy_flag': 1,
        'new_device_flag': 1,
    })


def test_scoring_preserves_manual_override_and_hides_str():
    service = UserRiskScoringService()
    automatic = service.assess(_high_risk_row())
    assert automatic['automatic_tier'] in {'L3.3', 'L4'}
    assert automatic['str_details'] is None

    manual = service.assess(
        _high_risk_row(),
        manual_tier='L3.2',
        manual_reason='reviewed',
        actor='reviewer',
    )
    assert manual['final_tier'] == 'L3.2'
    assert manual['risk_source'] == 'manual_override'
    assert manual['risk_history'][-1]['preserve_on_next_t1_run'] is True
    assert manual['str_details'] is None


def test_disposition_is_propose_only_and_requires_high_impact_approval():
    strategy = StrategyCandidate(
        strategy_id='S-HIGH',
        name='High impact strategy',
        domain=RiskDomain.FUND_SECURITY,
        event_code='ChainWithdraw',
        description='demo',
        rule=RuleGroup(conditions=[Condition(feature='fraud_graph_score', operator='>', value=0.8)]),
        action=ActionType.FREEZE,
        required_features=['fraud_graph_score'],
    )
    plan = DispositionPlanner().selected_strategy_plan(strategy)
    assert plan['execution_mode'] == 'PROPOSE_ONLY'
    assert plan['direct_execution_allowed'] is False
    assert 'compliance' in plan['required_approvals']
    assert 'risk_owner' in plan['required_approvals']
    assert plan['customer_segment_gate']['extra_approval'] is True
