from __future__ import annotations

import asyncio
import json
from pathlib import Path
from uuid import uuid4

import typer
from rich.console import Console
from rich.table import Table

from .orchestrator import RiskStrategyCopilot
from .schemas import RiskDomain, StrategyRequest

app = typer.Typer(help="Digital Asset Risk Strategy AI Copilot")
console = Console()


def _request(query: str, domain: str | None, event: str | None) -> StrategyRequest:
    return StrategyRequest(
        request_id=f"REQ-{uuid4().hex[:10]}",
        query=query,
        domain=RiskDomain(domain) if domain else None,
        event_code=event,
        max_alert_rate=0.05,
        minimum_precision=0.50,
        minimum_recall=0.05,
        review_capacity=300,
    )


@app.command("generate-data")
def generate_data(
    project_root: Path = typer.Option(Path(__file__).resolve().parents[2], exists=True),
    users: int = typer.Option(10000, min=1000),
    cases: int = typer.Option(2600, min=500),
    force: bool = typer.Option(False),
) -> None:
    copilot = RiskStrategyCopilot.create(project_root)
    for key, path in copilot.runtime.ensure_demo_data(users=users, cases=cases, force=force).items():
        console.print(f"[green]{key}[/green]: {path}")


@app.command("strategy")
def strategy(
    query: str = typer.Option("识别KYC后快速法币入金、换币并链上提币，叠加高风险银行和Risk Graph强关系的可疑用户"),
    domain: str | None = typer.Option(None),
    event: str | None = typer.Option(None),
    project_root: Path = typer.Option(Path(__file__).resolve().parents[2], exists=True),
) -> None:
    copilot = RiskStrategyCopilot.create(project_root)
    state = asyncio.run(copilot.run_strategy(_request(query, domain, event)))
    package = state.context["strategy_package"]
    table = Table(title="Selected Risk Strategy")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Strategy", package.selected_strategy.name)
    table.add_row("L1/L2/L3", f"{package.selected_strategy.tag_level_1} / {package.selected_strategy.tag_level_2} / {package.selected_strategy.tag_level_3}")
    table.add_row("Precision", f"{package.selected_metrics.precision:.2%}")
    table.add_row("Recall", f"{package.selected_metrics.recall:.2%}")
    table.add_row("Test Stage", package.strategy_test_environment.get("current_stage", "unknown"))
    table.add_row("Effectiveness", package.effectiveness_ticket.get("label", "unknown"))
    table.add_row("CMS/STR Cases", str(package.cms_str_integration.get("case_count", 0)))
    table.add_row("AI Lead Decision", package.ai_advisory_board.get("decision", "NOT_RUN"))
    table.add_row("Stability", package.stability_analysis.get("status", "NOT_RUN"))
    table.add_row("Conflict", package.conflict_analysis.get("recommendation", "NOT_RUN"))
    console.print(table)
    console.print_json(json.dumps({k: str(v) for k, v in state.context["strategy_artifacts"].items()}))


@app.command("ai-agent")
def ai_agent(
    query: str = typer.Option("识别KYC后快速法币入金、换币并链上提币，叠加高风险银行和Risk Graph强关系的可疑用户"),
    live_react: bool = typer.Option(False, help="Use external LLM-backed ReAct reviewers after the deterministic pipeline."),
    project_root: Path = typer.Option(Path(__file__).resolve().parents[2], exists=True),
) -> None:
    request = _request(query, None, None)
    if live_react:
        from .react_app import run_react_review
        result = asyncio.run(run_react_review(request, project_root))
        console.print(f"[green]Live ReAct review complete[/green]: {result['artifacts']['summary']}")
        return
    copilot = RiskStrategyCopilot.create(project_root)
    state = asyncio.run(copilot.run_strategy(request))
    board = state.context.get("ai_advisory_board", {})
    console.print(f"[bold cyan]Lead Risk Strategy Agent[/bold cyan]: {board.get('decision', 'NOT_RUN')}")
    console.print(board.get("executive_summary", ""))
    for name, review in board.get("specialist_reviews", {}).items():
        console.print(f"- [bold]{name}[/bold]: {review.get('summary', '')}")
    console.print(f"Open console after running: http://127.0.0.1:8000/console")


@app.command("products")
def products(
    query: str = typer.Option("rule engine fep strategy backtracking ticket cms str"),
    domain: str | None = typer.Option(None),
    event: str | None = typer.Option(None),
    project_root: Path = typer.Option(Path(__file__).resolve().parents[2], exists=True),
) -> None:
    copilot = RiskStrategyCopilot.create(project_root)
    mapped = copilot.runtime.product_catalog.map_stack(domain=domain, event_code=event, query=query)
    table = Table(title="Internship-derived Risk Product Stack")
    table.add_column("Product")
    table.add_column("Layer")
    table.add_column("Prototype")
    table.add_column("Purpose")
    for item in mapped["products"]:
        table.add_row(item["name"], item["layer"], item["prototype_status"], item["purpose"])
    console.print(table)


@app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(8000),
    project_root: Path = typer.Option(Path(__file__).resolve().parents[2], exists=True),
) -> None:
    import os
    import uvicorn
    os.environ["RISK_COPILOT_PROJECT_ROOT"] = str(project_root)
    uvicorn.run("risk_copilot.api:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
