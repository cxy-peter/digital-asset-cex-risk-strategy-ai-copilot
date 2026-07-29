from __future__ import annotations

import asyncio
import inspect
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from ..schemas import AgentActionLog


ToolCallable = Callable[..., Any] | Callable[..., Awaitable[Any]]


@dataclass
class ToolSpec:
    name: str
    description: str
    function: ToolCallable
    allowed_agents: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    read_only: bool = True

    @property
    def signature(self) -> str:
        return str(inspect.signature(self.function))


@dataclass
class ToolCallResult:
    value: Any
    log: AgentActionLog


class ToolRegistry:
    """In-process tool registry with discovery, permissions, timing, and audit logs."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(
        self,
        name: str,
        description: str,
        function: ToolCallable,
        allowed_agents: set[str] | None = None,
        tags: set[str] | None = None,
        read_only: bool = True,
    ) -> None:
        if name in self._tools:
            raise KeyError(f"tool already registered: {name}")
        self._tools[name] = ToolSpec(
            name=name,
            description=description,
            function=function,
            allowed_agents=allowed_agents or set(),
            tags=tags or set(),
            read_only=read_only,
        )

    def tool(
        self,
        name: str,
        description: str,
        allowed_agents: set[str] | None = None,
        tags: set[str] | None = None,
        read_only: bool = True,
    ) -> Callable[[ToolCallable], ToolCallable]:
        def decorator(function: ToolCallable) -> ToolCallable:
            self.register(name, description, function, allowed_agents, tags, read_only)
            return function
        return decorator

    def discover(self, agent: str | None = None, tags: set[str] | None = None) -> list[dict[str, Any]]:
        tag_filter = tags or set()
        result = []
        for tool in self._tools.values():
            if agent and tool.allowed_agents and agent not in tool.allowed_agents:
                continue
            if tag_filter and not tag_filter.intersection(tool.tags):
                continue
            result.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "signature": tool.signature,
                    "tags": sorted(tool.tags),
                    "read_only": tool.read_only,
                }
            )
        return sorted(result, key=lambda x: x["name"])

    @staticmethod
    def _summarize(value: Any) -> dict[str, Any]:
        try:
            import pandas as pd
            if isinstance(value, pd.DataFrame):
                return {"type": "DataFrame", "rows": len(value), "columns": list(value.columns)[:30]}
            if isinstance(value, pd.Series):
                return {"type": "Series", "rows": len(value), "name": value.name}
        except Exception:
            pass
        if hasattr(value, "model_dump"):
            dumped = value.model_dump(mode="json")
            return {"type": type(value).__name__, "keys": list(dumped)[:30]}
        if isinstance(value, dict):
            return {"type": "dict", "keys": list(value)[:30]}
        if isinstance(value, (list, tuple, set)):
            return {"type": type(value).__name__, "length": len(value)}
        return {"type": type(value).__name__, "preview": str(value)[:300]}

    async def execute(self, agent: str, name: str, **kwargs: Any) -> ToolCallResult:
        if name not in self._tools:
            raise KeyError(f"unknown tool: {name}")
        spec = self._tools[name]
        if spec.allowed_agents and agent not in spec.allowed_agents:
            raise PermissionError(f"agent {agent} is not allowed to call {name}")

        started_at = datetime.now(timezone.utc)
        start = time.perf_counter()
        try:
            if inspect.iscoroutinefunction(spec.function):
                value = await spec.function(**kwargs)
            else:
                value = await asyncio.to_thread(spec.function, **kwargs)
                if inspect.isawaitable(value):
                    value = await value
            duration = (time.perf_counter() - start) * 1000
            log = AgentActionLog(
                agent=agent,
                tool=name,
                status="success",
                started_at=started_at,
                duration_ms=duration,
                input_summary={key: self._summarize(val) for key, val in kwargs.items()},
                output_summary=self._summarize(value),
            )
            return ToolCallResult(value=value, log=log)
        except Exception as exc:
            duration = (time.perf_counter() - start) * 1000
            log = AgentActionLog(
                agent=agent,
                tool=name,
                status="failure",
                started_at=started_at,
                duration_ms=duration,
                input_summary={key: self._summarize(val) for key, val in kwargs.items()},
                output_summary={},
                error=f"{type(exc).__name__}: {exc}",
            )
            raise ToolExecutionError(str(exc), log) from exc


class ToolExecutionError(RuntimeError):
    def __init__(self, message: str, log: AgentActionLog) -> None:
        super().__init__(message)
        self.log = log
