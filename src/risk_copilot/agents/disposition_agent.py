from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ..state import CopilotState
from .base import BaseAgent


class DispositionPlanningAgent(BaseAgent):
    name = "disposition_planning_agent"
    description = "Design the tier-to-action ladder and penalty/verification-center approval controls."

    async def run(self, state: CopilotState):
        plan = await self.call_tool(
            "governance.plan_disposition",
            strategy=state.context["selected_strategy"],
        )
        output = Path(self.context.runtime.settings.output_dir) / "disposition_center"
        output.mkdir(parents=True, exist_ok=True)
        matrix_path = output / "risk_tier_disposition_matrix.csv"
        payload_path = output / "penalty_center_proposal.json"
        pd.DataFrame(plan["tier_matrix"]).to_csv(matrix_path, index=False)
        payload_path.write_text(
            json.dumps(plan["selected_strategy_plan"], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        structured = {
            **plan,
            "artifacts": {
                "tier_matrix_csv": str(matrix_path),
                "penalty_center_payload": str(payload_path),
            },
        }
        state.merge_context({"disposition_plan": structured})
        result = self.result(
            "完成L1-L4分层处置矩阵和处罚/验证中心审批方案；所有动作仅为提议，不允许Agent直接处罚。",
            structured,
            citations=["SOP::rfi_edd_restriction", "SOP::strategy_lifecycle"],
        )
        state.add_result(result)
        return result
