from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schemas import AgentResult, AgentRunEnvelope, StrategyCandidate, StrategyRequest


@dataclass
class CopilotState:
    request: StrategyRequest
    context: dict[str, Any] = field(default_factory=dict)
    agent_results: list[AgentResult] = field(default_factory=list)
    candidates: list[StrategyCandidate] = field(default_factory=list)
    candidate_metrics: dict[str, Any] = field(default_factory=dict)
    model_benchmarks: list[Any] = field(default_factory=list)
    feature_profiles: list[Any] = field(default_factory=list)
    selected_strategy_id: str | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    run_trace: list[AgentRunEnvelope] = field(default_factory=list)

    def add_result(self, result: AgentResult) -> None:
        self.agent_results.append(result)

    def merge_context(self, values: dict[str, Any]) -> None:
        self.context.update(values)
