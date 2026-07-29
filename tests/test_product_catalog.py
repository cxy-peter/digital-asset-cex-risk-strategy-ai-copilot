from risk_copilot.orchestrator import RiskStrategyCopilot


def test_product_catalog_has_full_landscape_and_dependency_closure(tmp_path):
    copilot = RiskStrategyCopilot.create('.')
    catalog = copilot.runtime.product_catalog
    assert len(catalog.products) >= 25
    stack = catalog.map_stack(
        domain='fund_security',
        event_code='ChainWithdraw',
        query='快速提币 风险策略 规则 回溯 处罚',
    )
    ids = {item['product_id'] for item in stack['products']}
    assert 'risk_event_hub' in ids
    assert 'realtime_feature_platform' in ids
    assert 'rule_engine' in ids
    assert 'strategy_simulation' in ids
    assert any(item['prototype_status'] == 'implemented' for item in stack['products'])

    paths = catalog.write(tmp_path)
    assert all(path.exists() for path in paths.values())
