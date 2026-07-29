from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from .agents.base import BaseAgent
from .schemas import AgentRunEnvelope
from .state import CopilotState


class CriticalAgentFailure(RuntimeError):
    def __init__(self, phase: str, failures: list[BaseException]) -> None:
        self.phase = phase
        self.failures = failures
        detail = "; ".join(f"{type(exc).__name__}: {exc}" for exc in failures)
        super().__init__(f"critical agent failure in phase {phase}: {detail}")


@dataclass(frozen=True)
class AgentTask:
    agent: BaseAgent
    critical: bool = True
    timeout_seconds: float = 300.0


async def run_agent_task(
    state: CopilotState,
    task: AgentTask,
    *,
    phase: str,
) -> None:
    """Execute an agent with a terminal trace record even when its tool call fails."""

    started_at = datetime.now(timezone.utc)
    started = time.perf_counter()
    result_count = len(state.agent_results)
    status = "succeeded"
    error_type: str | None = None
    error: str | None = None
    try:
        async with asyncio.timeout(task.timeout_seconds):
            await task.agent.run(state)
    except TimeoutError as exc:
        status = "timed_out"
        error_type = type(exc).__name__
        error = f"agent exceeded {task.timeout_seconds:.1f}s timeout"
        state.errors.append(f"{task.agent.name}: {error}")
        if len(state.agent_results) == result_count:
            state.add_result(
                task.agent.result(
                    f"{task.agent.name} timed out; downstream execution policy will decide whether to continue.",
                    {"status": status, "phase": phase},
                )
            )
        if task.critical:
            raise
    except Exception as exc:
        status = "failed" if task.critical else "degraded"
        error_type = type(exc).__name__
        error = str(exc)
        state.errors.append(
            f"{task.agent.name}: {error_type}: {error}"
        )
        if len(state.agent_results) == result_count:
            state.add_result(
                task.agent.result(
                    f"{task.agent.name} failed; trace retained for review.",
                    {
                        "status": status,
                        "phase": phase,
                        "error_type": error_type,
                    },
                )
            )
        if task.critical:
            raise
    finally:
        completed_at = datetime.now(timezone.utc)
        actions = task.agent.actions
        state.run_trace.append(
            AgentRunEnvelope(
                run_id=state.request.request_id,
                agent=task.agent.name,
                phase=phase,
                status=status,
                critical=task.critical,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=(time.perf_counter() - started) * 1000,
                action_count=len(actions),
                warning_count=len(task.agent.warnings),
                error_type=error_type,
                error=error,
            )
        )


async def run_parallel_phase(
    state: CopilotState,
    tasks: Iterable[AgentTask],
    *,
    phase: str,
) -> None:
    """Finish every sibling branch, then fail only if a critical branch failed."""

    task_list = list(tasks)
    results = await asyncio.gather(
        *[run_agent_task(state, task, phase=phase) for task in task_list],
        return_exceptions=True,
    )
    critical_failures = [
        result
        for task, result in zip(task_list, results)
        if task.critical and isinstance(result, BaseException)
    ]
    if critical_failures:
        raise CriticalAgentFailure(phase, critical_failures)
