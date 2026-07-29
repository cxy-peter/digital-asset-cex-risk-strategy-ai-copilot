from fastapi.testclient import TestClient

from risk_copilot.api import app


def test_console_exposes_ai_strategy_workbench():
    client = TestClient(app)
    response = client.get("/console")
    assert response.status_code == 200
    assert "Digital Asset Risk Strategy AI Copilot" in response.text
    assert "AI专业顾问组" in response.text
    assert "P0治理结果" in response.text


def test_health_exposes_focused_boundary():
    client = TestClient(app)
    payload = client.get("/health").json()
    assert payload["status"] == "ok"
    assert payload["version"] == "0.7.0"
    assert payload["kep_included"] is False
    assert payload["anti_fraud_metrics_included"] is False
