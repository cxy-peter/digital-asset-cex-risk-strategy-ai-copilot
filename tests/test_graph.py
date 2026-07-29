import pandas as pd

from risk_copilot.graph.analyzer import RiskGraphAnalyzer


def test_ip_is_weaker_than_device():
    users = pd.DataFrame({"user_id": ["A", "B", "C"], "fraud_label": [0, 1, 1]})
    edges = pd.DataFrame([
        {"user_id": "A", "relation_type": "device", "identifier": "D1", "relation_weight": 1.0},
        {"user_id": "B", "relation_type": "device", "identifier": "D1", "relation_weight": 1.0},
        {"user_id": "A", "relation_type": "ip", "identifier": "IP1", "relation_weight": 0.25},
        {"user_id": "C", "relation_type": "ip", "identifier": "IP1", "relation_weight": 0.25},
    ])
    analyzer = RiskGraphAnalyzer().fit(users, edges)
    features = analyzer.user_features("A")
    assert features["device_fraud_1hop_count"] == 1
    assert features["ip_fraud_1hop_count"] == 1
    assert features["strong_relation_fraud_1hop_count"] == 1
