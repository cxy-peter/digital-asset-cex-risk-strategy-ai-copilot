from __future__ import annotations

"""FastMCP adapter for the focused risk-strategy test platform.

The module is import-safe when the optional MCP package is absent. ``create_server`` raises only
when the caller actually requests a server instance.
"""

import asyncio
import json
from pathlib import Path
from uuid import uuid4

from .orchestrator import RiskStrategyCopilot
from .schemas import RiskDomain, StrategyRequest

try:  # pragma: no cover - optional dependency
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None


def create_server(project_root: str | Path | None = None):
    if FastMCP is None:  # pragma: no cover
        raise RuntimeError("Install the optional 'agent' dependencies to run the MCP server")
    copilot = RiskStrategyCopilot.create(project_root)
    app = FastMCP("cointr-risk-strategy-test-platform")

    @app.tool()
    def list_risk_events(domain: str = "") -> str:
        events = copilot.runtime.feature_registry.events
        if domain:
            events = [item for item in events if item.domain.value == domain]
        return json.dumps([item.model_dump(mode="json") for item in events], ensure_ascii=False)

    @app.tool()
    def search_registered_features(query: str = "", domain: str = "", event_code: str = "") -> str:
        rows = copilot.runtime.feature_registry.search(
            text=query,
            domain=domain or None,
            event_code=event_code or None,
            tags=None,
        )
        return json.dumps([item.model_dump(mode="json") for item in rows], ensure_ascii=False)

    @app.tool()
    def map_risk_products(query: str, domain: str = "", event_code: str = "") -> str:
        return json.dumps(
            copilot.runtime.product_catalog.map_stack(
                query=query,
                domain=domain or None,
                event_code=event_code or None,
            ),
            ensure_ascii=False,
        )

    @app.tool()
    def search_risk_sop(query: str, top_k: int = 6) -> str:
        hits = copilot.runtime.knowledge_retriever.search(query, top_k=top_k)
        return json.dumps(
            [
                {
                    "doc_id": item.doc_id,
                    "title": item.title,
                    "score": item.score,
                    "text": item.text,
                    "metadata": item.metadata,
                }
                for item in hits
            ],
            ensure_ascii=False,
        )

    @app.tool()
    def explain_risk_graph_user(user_id: str) -> str:
        copilot.runtime.prepare_graph_enriched_users()
        return json.dumps(
            copilot.runtime.artifacts["graph_analyzer"].explain_user(user_id),
            ensure_ascii=False,
            default=str,
        )

    @app.tool()
    def run_strategy_test(query: str, domain: str = "", event_code: str = "") -> str:
        request = StrategyRequest(
            request_id=f"MCP-{uuid4().hex[:10]}",
            query=query,
            domain=RiskDomain(domain) if domain else None,
            event_code=event_code or None,
        )
        state = asyncio.run(copilot.run_strategy(request))
        return state.context["strategy_package"].model_dump_json(indent=2)

    return app


if __name__ == "__main__":  # pragma: no cover
    create_server(Path(__file__).resolve().parents[2]).run(transport="stdio")
