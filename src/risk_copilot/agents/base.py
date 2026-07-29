from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..runtime import RuntimeContext
from ..schemas import AgentActionLog, AgentResult
from ..state import CopilotState
from ..tools.registry import ToolExecutionError, ToolRegistry


@dataclass
class AgentContext:
    runtime: RuntimeContext
    tools: ToolRegistry


class BaseAgent(ABC):
    name: str = "base_agent"
    description: str = ""

    def __init__(self, context: AgentContext) -> None:
        self.context = context
        self.actions: list[AgentActionLog] = []
        self.warnings: list[str] = []

    async def call_tool(self, name: str, **kwargs: Any) -> Any:
        try:
            result = await self.context.tools.execute(self.name, name, **kwargs)
            self.actions.append(result.log)
            return result.value
        except ToolExecutionError as exc:
            self.actions.append(exc.log)
            self.warnings.append(f"tool {name} failed: {exc}")
            raise

    def result(
        self,
        summary: str,
        structured_output: dict[str, Any] | None = None,
        citations: list[str] | None = None,
    ) -> AgentResult:
        return AgentResult(
            agent=self.name,
            summary=summary,
            structured_output=structured_output or {},
            citations=citations or [],
            actions=self.actions,
            warnings=self.warnings,
        )

    @abstractmethod
    async def run(self, state: CopilotState) -> AgentResult:
        raise NotImplementedError
