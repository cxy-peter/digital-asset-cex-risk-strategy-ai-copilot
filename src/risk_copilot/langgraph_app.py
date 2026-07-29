from __future__ import annotations

"""Optional LangGraph implementation of the focused strategy workflow."""

from pathlib import Path
from typing import Any, TypedDict

from .agents import (
    AgentContext,
    BacktestRankingAgent,
    AIStrategyProposalAgent,
    StrategyStabilityAgent,
    StrategyConflictAgent,
    AIAdvisoryBoardAgent,
    CMSSTRIntegrationAgent,
    DispositionPlanningAgent,
    FeatureIntelligenceAgent,
    FraudBehaviorAgent,
    GovernanceAgent,
    IntentRouterAgent,
    ModelBenchmarkAgent,
    ProductCapabilityAgent,
    RiskGraphAgent,
    ScenarioKnowledgeAgent,
    StrategyEffectivenessAgent,
    StrategyGenerationAgent,
    StrategyReportAgent,
    StrategyTestEnvironmentAgent,
    UserRiskScoringAgent,
)
from .orchestrator import RiskStrategyCopilot
from .schemas import StrategyRequest
from .state import CopilotState


class GraphState(TypedDict):
    state: CopilotState


async def _run(graph_state: GraphState, agent, ctx: AgentContext) -> GraphState:
    await agent(ctx).run(graph_state["state"])
    return graph_state


def build_strategy_graph(project_root: str | Path | None = None):
    try:
        from langgraph.graph import END, StateGraph
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install optional LangGraph dependencies") from exc

    copilot = RiskStrategyCopilot.create(project_root)
    ctx = copilot._agent_context()
    graph = StateGraph(GraphState)

    graph.add_node("router", lambda s: _run(s, IntentRouterAgent, ctx))
    graph.add_node("graph", lambda s: _run(s, RiskGraphAgent, ctx))
    graph.add_node("scenario", lambda s: _run(s, ScenarioKnowledgeAgent, ctx))
    graph.add_node("products", lambda s: _run(s, ProductCapabilityAgent, ctx))
    graph.add_node("features", lambda s: _run(s, FeatureIntelligenceAgent, ctx))
    graph.add_node("behavior", lambda s: _run(s, FraudBehaviorAgent, ctx))
    graph.add_node("models", lambda s: _run(s, ModelBenchmarkAgent, ctx))
    graph.add_node("scoring", lambda s: _run(s, UserRiskScoringAgent, ctx))
    graph.add_node("ai_proposal", lambda s: _run(s, AIStrategyProposalAgent, ctx))
    graph.add_node("strategy", lambda s: _run(s, StrategyGenerationAgent, ctx))
    graph.add_node("backtest", lambda s: _run(s, BacktestRankingAgent, ctx))
    graph.add_node("stability", lambda s: _run(s, StrategyStabilityAgent, ctx))
    graph.add_node("conflict", lambda s: _run(s, StrategyConflictAgent, ctx))
    graph.add_node("ai_board", lambda s: _run(s, AIAdvisoryBoardAgent, ctx))
    graph.add_node("disposition", lambda s: _run(s, DispositionPlanningAgent, ctx))
    graph.add_node("governance", lambda s: _run(s, GovernanceAgent, ctx))
    graph.add_node("test_environment", lambda s: _run(s, StrategyTestEnvironmentAgent, ctx))
    graph.add_node("effectiveness", lambda s: _run(s, StrategyEffectivenessAgent, ctx))
    graph.add_node("cms_str", lambda s: _run(s, CMSSTRIntegrationAgent, ctx))
    graph.add_node("report", lambda s: _run(s, StrategyReportAgent, ctx))

    graph.set_entry_point("router")
    for node in ["graph", "scenario", "products"]:
        graph.add_edge("router", node)
    for upstream in ["graph", "scenario", "products"]:
        for downstream in ["features", "behavior", "models", "scoring"]:
            graph.add_edge(upstream, downstream)
    for upstream in ["features", "behavior", "models", "scoring"]:
        graph.add_edge(upstream, "ai_proposal")
    graph.add_edge("ai_proposal", "strategy")
    graph.add_edge("strategy", "backtest")
    graph.add_edge("backtest", "stability")
    graph.add_edge("stability", "conflict")
    graph.add_edge("conflict", "ai_board")
    graph.add_edge("ai_board", "disposition")
    graph.add_edge("disposition", "governance")
    graph.add_edge("governance", "test_environment")
    graph.add_edge("test_environment", "effectiveness")
    graph.add_edge("effectiveness", "cms_str")
    graph.add_edge("cms_str", "report")
    graph.add_edge("report", END)
    return graph.compile()


async def run_langgraph_strategy(request: StrategyRequest, project_root: str | Path | None = None) -> CopilotState:
    app = build_strategy_graph(project_root)
    result: dict[str, Any] = await app.ainvoke({"state": CopilotState(request=request)})
    return result["state"]
