from fastapi.testclient import TestClient

from risk_copilot.api import app


def test_console_exposes_ai_strategy_workbench():
    client = TestClient(app)
    response = client.get("/console")
    assert response.status_code == 200
    assert "Digital Asset & Payment Risk Strategy AI Copilot" in response.text
    assert "AI专业顾问组" in response.text
    assert "支付责任与治理" in response.text
    assert "Agent只检索、规划、解释和质检" in response.text


def test_health_exposes_focused_boundary():
    client = TestClient(app)
    payload = client.get("/health").json()
    assert payload["status"] == "ok"
    assert payload["version"] == "0.9.0"
    assert payload["scope"] == "risk_strategy_test_platform_with_payment_extension"
    assert payload["payment_extension"] is True
    assert payload["payment_extension_is_post_internship_research"] is True
    assert payload["production_connection"] is False
    assert payload["kep_included"] is False
    assert payload["anti_fraud_metrics_included"] is False
