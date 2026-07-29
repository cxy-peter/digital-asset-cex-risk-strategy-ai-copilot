import asyncio
import json
from pathlib import Path

import pytest

from risk_copilot.agents import AgentContext, ScenarioKnowledgeAgent
from risk_copilot.knowledge.retriever import HybridKnowledgeRetriever
from risk_copilot.langgraph_app import build_strategy_graph
from risk_copilot.runtime import RuntimeContext
from risk_copilot.schemas import StrategyRequest
from risk_copilot.state import CopilotState
from risk_copilot.tools import build_tool_registry

ROOT = Path(__file__).resolve().parents[1]


def test_retriever_searches_scenarios_and_sops_as_separate_corpora():
    retriever = HybridKnowledgeRetriever(ROOT / "data/knowledge/risk_scenarios.yaml", ROOT / "data/sop")
    scenarios = retriever.search_scenarios("法币入金后快速提币 资金闭环", industry="digital_asset", top_k=3)
    sops = retriever.search_sops("策略生命周期 审批 回测 STR 保密", top_k=3)
    assert scenarios and sops
    assert all(hit.metadata["type"] == "scenario" for hit in scenarios)
    assert all(hit.metadata["type"] == "sop" for hit in sops)


def test_scenario_agent_keeps_sop_evidence_metadata():
    runtime = RuntimeContext.create(ROOT)
    context = AgentContext(runtime=runtime, tools=build_tool_registry(runtime))
    state = CopilotState(
        request=StrategyRequest(request_id="KNOWLEDGE-TEST", query="法币入金后快速链上提币"),
        context={"routing": {"domain": "fund_security", "event_code": "ChainWithdraw"}},
    )
    asyncio.run(ScenarioKnowledgeAgent(context).run(state))
    analysis = state.context["knowledge_analysis"]
    assert analysis["top_scenarios"] and analysis["sop_hits"]
    assert all(hit["document_type"] == "sop" for hit in analysis["sop_hits"])


def test_langgraph_topology_uses_company_test_environment_nodes():
    pytest.importorskip("langgraph")
    app = build_strategy_graph(ROOT)
    graph = app.get_graph()
    nodes = set(graph.nodes)
    edges = {(edge.source, edge.target) for edge in graph.edges}
    assert {"router", "graph", "scenario", "products"}.issubset(nodes)
    assert {"features", "behavior", "models", "scoring"}.issubset(nodes)
    assert {"test_environment", "effectiveness", "cms_str", "report"}.issubset(nodes)
    assert ("governance", "test_environment") in edges
    assert ("test_environment", "effectiveness") in edges
    assert ("effectiveness", "cms_str") in edges
    assert ("cms_str", "report") in edges


def test_react_event_contract_uses_feature_registry_event(monkeypatch):
    pytest.importorskip("langchain_core")
    from risk_copilot import react_app
    runtime = RuntimeContext.create(ROOT)
    class Dummy: pass
    dummy=Dummy(); dummy.runtime=runtime
    monkeypatch.setattr(react_app, "_package_context", lambda package: {})
    tools = react_app.build_react_tools(dummy, object())
    event_tool = next(tool for tool in tools if tool.name == "list_event_contract")
    payload = json.loads(event_tool.invoke({"event_code": "ChainWithdraw"}))
    assert payload["event"]["code"] == "ChainWithdraw"
    assert len(payload["contract_hash"]) == 64
