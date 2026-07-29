from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from .agents import (
    AgentContext,
    BacktestRankingAgent,
    AIStrategyProposalAgent,
    StrategyStabilityAgent,
    StrategyConflictAgent,
    AIAdvisoryBoardAgent,
    CMSSTRIntegrationAgent,
    FeatureIntelligenceAgent,
    DispositionPlanningAgent,
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
from .execution import AgentTask, run_agent_task, run_parallel_phase
from .runtime import RuntimeContext
from .reporting import write_project_manifest
from .schemas import StrategyRequest
from .state import CopilotState
from .tools import build_tool_registry


@dataclass
class RiskStrategyCopilot:
    """Focused internship-derived risk-strategy test-platform prototype.

    Scope is deliberately limited to Rule Engine/FEP/strategy backtracking, user risk scoring,
    Risk Graph, penalty/verification controls, strategy-effectiveness tickets, and internal
    CMS/STR candidate-case preparation.  KEP and the Anti-Fraud operations dashboard live in
    separate projects.
    """

    runtime: RuntimeContext

    @classmethod
    def create(cls, project_root: str | Path | None = None) -> "RiskStrategyCopilot":
        runtime = RuntimeContext.create(project_root)
        runtime.ensure_demo_data()
        return cls(runtime=runtime)

    def _agent_context(self) -> AgentContext:
        tools = self.runtime.artifacts.get("tool_registry")
        if tools is None:
            tools = build_tool_registry(self.runtime)
            self.runtime.artifacts["tool_registry"] = tools
        return AgentContext(runtime=self.runtime, tools=tools)

    async def run_strategy(self, request: StrategyRequest) -> CopilotState:
        state = CopilotState(request=request)
        ctx = self._agent_context()

        await run_agent_task(state, AgentTask(IntentRouterAgent(ctx)), phase="routing")
        await run_parallel_phase(
            state,
            [
                AgentTask(RiskGraphAgent(ctx), critical=True),
                AgentTask(ScenarioKnowledgeAgent(ctx), critical=False),
                AgentTask(ProductCapabilityAgent(ctx), critical=False),
            ],
            phase="preparation",
        )
        await run_parallel_phase(
            state,
            [
                AgentTask(FeatureIntelligenceAgent(ctx), critical=True),
                AgentTask(FraudBehaviorAgent(ctx), critical=False),
                AgentTask(ModelBenchmarkAgent(ctx), critical=True),
                AgentTask(UserRiskScoringAgent(ctx), critical=False),
            ],
            phase="specialist_analysis",
        )
        for agent, phase in [
            (AIStrategyProposalAgent(ctx), "ai_strategy_planning"),
            (StrategyGenerationAgent(ctx), "strategy_generation"),
            (BacktestRankingAgent(ctx), "backtest_and_ranking"),
            (StrategyStabilityAgent(ctx), "cross_month_bootstrap_stability"),
            (StrategyConflictAgent(ctx), "portfolio_conflict_and_incremental_value"),
            (AIAdvisoryBoardAgent(ctx), "ai_specialist_board"),
            (DispositionPlanningAgent(ctx), "disposition"),
            (GovernanceAgent(ctx), "governance_and_registry"),
            (StrategyTestEnvironmentAgent(ctx), "company_test_environment"),
            (StrategyEffectivenessAgent(ctx), "effectiveness_ticket"),
            (CMSSTRIntegrationAgent(ctx), "cms_str_internal_case_preview"),
            (StrategyReportAgent(ctx), "reporting"),
        ]:
            await run_agent_task(state, AgentTask(agent), phase=phase)

        trace_path = self._write_run_trace(state)
        state.context.get("strategy_artifacts", {})["run_trace"] = trace_path
        manifest_paths = write_project_manifest(self.runtime, state)
        state.context.get("strategy_artifacts", {}).update(manifest_paths)
        self._write_index(state)
        return state

    async def run_full_suite(self, request: StrategyRequest) -> CopilotState:
        """Compatibility alias: the focused project has one strategy test-platform suite."""
        return await self.run_strategy(request)

    def _write_run_trace(self, state: CopilotState) -> Path:
        path = self.runtime.settings.output_dir / "agent_run_trace.json"
        path.write_text(
            json.dumps(
                [item.model_dump(mode="json") for item in state.run_trace],
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        return path

    def _write_index(self, state: CopilotState) -> Path:
        output = self.runtime.settings.output_dir
        strategy = {key: str(value) for key, value in state.context.get("strategy_artifacts", {}).items()}
        cms = state.context.get("cms_str_integration", {})
        effectiveness = state.context.get("strategy_effectiveness_ticket", {})
        test_plan = state.context.get("strategy_test_environment", {})
        ai_board = state.context.get("ai_advisory_board", {})
        stability = state.context.get("stability_analysis", {})
        conflict = state.context.get("conflict_analysis", {})
        artifact_items = list(strategy.items())
        cms_trigger_demo = output / "cms_str_trigger_demo" / "README.md"
        if cms_trigger_demo.exists():
            artifact_items.append(("cms_str_trigger_demo", str(cms_trigger_demo)))
        rows = "\n".join(
            f'<tr><td>{label}</td><td><a href="{Path(path).resolve().relative_to(output.resolve()).as_posix() if Path(path).exists() else path}">{path}</a></td></tr>'
            for label, path in artifact_items
            if isinstance(path, (str, Path))
        )
        html = f"""<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'>
<title>Digital Asset Risk Strategy AI Copilot</title>
<style>body{{font-family:system-ui;margin:0;background:#f4f7fb;color:#172033}}header{{background:#17324d;color:white;padding:30px}}main{{max-width:1200px;margin:auto;padding:28px}}section{{background:white;border:1px solid #dbe3ee;border-radius:12px;padding:20px;margin-bottom:18px}}table{{border-collapse:collapse;width:100%}}td,th{{padding:10px;border-bottom:1px solid #e5eaf0;text-align:left}}code,pre{{white-space:pre-wrap;word-break:break-word}}</style></head>
<body><header><h1>Digital Asset Risk Strategy AI Copilot</h1><p>Internship-derived, synthetic-data prototype aligned to Rule Engine, FEP, Strategy Backtracking, Ticket Module, CMS/STR, Penalty/Verification Center and User Risk Profile.</p></header><main>
<section><h2>Boundary</h2><p>KEP is excluded. Anti-Fraud operations metrics are maintained as a separate project. No production connection, automatic enforcement or external regulatory filing exists.</p></section>
<section><h2>AI Strategy Advisory Board</h2><p><strong>Lead Agent Decision:</strong> {ai_board.get('decision', 'NOT_RUN')}</p><pre>{json.dumps(ai_board, ensure_ascii=False, indent=2, default=str)}</pre><p><a href="/console">Interactive FastAPI Console (when served locally)</a></p></section>
<section><h2>Selected Strategy</h2><pre>{json.dumps(state.context['selected_strategy'].model_dump(mode='json'), ensure_ascii=False, indent=2)}</pre></section>
<section><h2>P0 Stability & Portfolio Conflict</h2><pre>{json.dumps({'stability': stability, 'conflict': conflict}, ensure_ascii=False, indent=2, default=str)}</pre></section>
<section><h2>Company-style Test Environment</h2><pre>{json.dumps(test_plan, ensure_ascii=False, indent=2, default=str)}</pre></section>
<section><h2>Strategy Effectiveness Ticket</h2><pre>{json.dumps(effectiveness, ensure_ascii=False, indent=2, default=str)}</pre></section>
<section><h2>CMS/STR Internal Case Preview</h2><pre>{json.dumps(cms, ensure_ascii=False, indent=2, default=str)}</pre></section>
<section><h2>Artifacts</h2><table><thead><tr><th>Artifact</th><th>Path</th></tr></thead><tbody>{rows}</tbody></table></section>
</main></body></html>"""
        index = output / "index.html"
        index.write_text(html, encoding="utf-8")
        return index


def run(coro):
    return asyncio.run(coro)
