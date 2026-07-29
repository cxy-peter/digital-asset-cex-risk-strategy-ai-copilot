from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from risk_copilot.mcp_server import create_server
from risk_copilot.runtime import RuntimeContext
from risk_copilot.tools.builtin import build_tool_registry

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _registry():
    return build_tool_registry(RuntimeContext.create(PROJECT_ROOT))


def test_registry_is_focused_on_strategy_platform():
    discovered = {item["name"]: item for item in _registry().discover()}
    assert len(discovered) >= 20
    for name in {
        "catalog.write_products",
        "knowledge.build_system",
        "scoring.assess_users",
        "governance.persist_strategy",
        "governance.create_effectiveness_ticket",
        "integration.prepare_cms_str_candidates",
    }:
        assert discovered[name]["read_only"] is False
    assert "ops.calculate_metrics" not in discovered
    assert "casework.draft_sar_str" not in discovered
    assert "regulatory.build_control_pack" not in discovered
    assert "governance.evaluate_company_test_environment" in discovered


def test_contract_tools_expose_versioned_schema_and_validation():
    registry = _registry()
    contract = asyncio.run(registry.execute("test_agent", "catalog.get_event_contract", event_code="ChainWithdraw"))
    report = asyncio.run(registry.execute("test_agent", "catalog.validate_contracts"))
    assert contract.value["event"]["code"] == "ChainWithdraw"
    assert len(contract.value["contract_hash"]) == 64
    assert report.value["valid"] is True


def test_fastmcp_surface_is_focused():
    pytest.importorskip("mcp.server")
    server = create_server(PROJECT_ROOT)
    names = set(server._tool_manager._tools)
    assert names == {
        "list_risk_events",
        "search_registered_features",
        "map_risk_products",
        "search_risk_sop",
        "explain_risk_graph_user",
        "run_strategy_test",
    }
