from __future__ import annotations

from dataclasses import dataclass

from ..runtime import RuntimeContext


@dataclass
class ToolContext:
    runtime: RuntimeContext
