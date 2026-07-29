from __future__ import annotations

import json
from pathlib import Path

from ..state import CopilotState
from .base import BaseAgent


class GovernanceAgent(BaseAgent):
    name = "governance_agent"
    description = "Enforce simulation gates, approvals, STR confidentiality, manual-override preservation, and versioned audit records."

    async def run(self, state: CopilotState):
        output = await self.call_tool(
            "governance.review_strategy",
            strategy=state.context["selected_strategy"],
            metrics=state.context["selected_metrics"],
            request=state.request,
        )
        decision = output["decision"]
        payload = output["payload"]
        if state.context.get("disposition_plan"):
            payload["dispositionProposal"] = state.context["disposition_plan"]["selected_strategy_plan"]

        registry = await self.call_tool(
            "governance.persist_strategy",
            strategy=state.context["selected_strategy"],
            metrics=state.context["selected_metrics"],
            governance=decision,
        )
        history_path = Path(self.context.runtime.settings.output_dir) / "strategy_registry_history.json"
        history_path.write_text(
            json.dumps(registry["history"], ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        registry["history_path"] = str(history_path)
        state.merge_context(
            {
                "governance": decision,
                "engine_payload": payload,
                "strategy_registry": registry,
            }
        )
        result = self.result(
            f"治理结论：{decision.current_status.value}->{decision.next_status.value}，decision={decision.decision}；候选策略已写入SQLite版本库，但系统不允许Agent直接上线或执行处罚。",
            {
                "decision": decision.model_dump(mode="json"),
                "payload_summary": {
                    "status": payload["status"],
                    "executionMode": payload["executionMode"],
                    "eventContractVersion": payload["eventContract"]["version"],
                    "requiredApprovals": payload["guardrails"]["requiredApprovals"],
                },
                "registry": {
                    "strategy_id": registry["strategy_id"],
                    "version": registry["version"],
                    "status": registry["status"],
                    "database": registry["database"],
                    "history_path": registry["history_path"],
                },
            },
            citations=["SOP::strategy_lifecycle", "SOP::str_confidentiality", "SOP::user_risk_scoring"],
        )
        state.add_result(result)
        return result
