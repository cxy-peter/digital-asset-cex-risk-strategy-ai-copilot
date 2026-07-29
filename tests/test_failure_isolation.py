from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from risk_copilot.execution import (
    AgentTask,
    CriticalAgentFailure,
    run_parallel_phase,
)
from risk_copilot.schemas import StrategyRequest
from risk_copilot.state import CopilotState


class _FakeAgent:
    def __init__(self, name: str, *, fail: bool = False):
        self.name = name
        self.fail = fail
        self.actions = []
        self.warnings = []

    async def run(self, state):
        await asyncio.sleep(0)
        if self.fail:
            raise ValueError(f"{self.name} injected failure")
        state.context[self.name] = {"completed": True}

    def result(self, summary, structured_output=None, citations=None):
        return SimpleNamespace(
            agent=self.name,
            summary=summary,
            structured_output=structured_output or {},
            citations=citations or [],
            actions=self.actions,
            warnings=self.warnings,
        )


def _state() -> CopilotState:
    return CopilotState(
        request=StrategyRequest(request_id="FAILURE-TEST", query="test")
    )


def test_noncritical_failure_is_degraded_and_sibling_completes():
    state = _state()
    asyncio.run(
        run_parallel_phase(
            state,
            [
                AgentTask(_FakeAgent("healthy"), critical=True),
                AgentTask(_FakeAgent("optional", fail=True), critical=False),
            ],
            phase="test_phase",
        )
    )

    assert state.context["healthy"]["completed"] is True
    statuses = {item.agent: item.status for item in state.run_trace}
    assert statuses == {"healthy": "succeeded", "optional": "degraded"}
    assert any("optional" in error for error in state.errors)


def test_critical_failure_waits_for_sibling_then_fails_phase():
    state = _state()
    with pytest.raises(CriticalAgentFailure):
        asyncio.run(
            run_parallel_phase(
                state,
                [
                    AgentTask(_FakeAgent("healthy"), critical=True),
                    AgentTask(_FakeAgent("critical", fail=True), critical=True),
                ],
                phase="test_phase",
            )
        )

    assert state.context["healthy"]["completed"] is True
    assert len(state.run_trace) == 2
    assert {item.status for item in state.run_trace} == {"succeeded", "failed"}
