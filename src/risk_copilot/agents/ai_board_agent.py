from __future__ import annotations

from ..ai import AIAdvisoryBoard
from ..state import CopilotState
from .base import BaseAgent


class AIAdvisoryBoardAgent(BaseAgent):
    name = "ai_advisory_board_agent"
    description = "Run four specialist AI roles and a lead strategy synthesizer over validated deterministic evidence."

    async def run(self, state: CopilotState):
        board = AIAdvisoryBoard().run(state)
        state.merge_context({"ai_advisory_board": board})
        result = self.result(
            f"AI专业顾问组完成场景、特征模型、图谱行为和治理复核；Lead Agent建议={board['decision']}。",
            board,
        )
        state.add_result(result)
        return result
