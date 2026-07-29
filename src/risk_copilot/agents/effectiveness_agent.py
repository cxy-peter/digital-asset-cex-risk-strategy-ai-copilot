from __future__ import annotations

from ..state import CopilotState
from .base import BaseAgent


class StrategyEffectivenessAgent(BaseAgent):
    name = "strategy_effectiveness_agent"
    description = "Create a Ticket-Module-style effectiveness label bound to strategy version, test run, and data snapshot."

    async def run(self, state: CopilotState):
        output = await self.call_tool(
            "governance.create_effectiveness_ticket",
            test_plan=state.context["strategy_test_environment"],
            metrics=state.context["selected_metrics"],
            conflict_analysis=state.context.get("conflict_analysis", {}),
            stability_analysis=state.context.get("stability_analysis", {}),
        )
        ticket = output["ticket"]
        observation_template = output.get("observation_template", [])
        test_environment = dict(state.context["strategy_test_environment"])
        test_environment["post_launch_observation_template"] = observation_template
        state.merge_context(
            {
                "strategy_effectiveness_ticket": ticket.model_dump(mode="json"),
                "strategy_test_environment": test_environment,
                "post_launch_observation_template": observation_template,
            }
        )
        result = self.result(
            f"已生成策略效果工单：{ticket.ticket_id}，simulation label={ticket.label}；"
            f"同时生成{len(observation_template)}个工作日的上线后观察模板，但未执行生产观察。",
            {
                "ticket": ticket.model_dump(mode="json"),
                "post_launch_observation_template": observation_template,
                "history": output.get("history", []),
            },
            citations=["TICKET_MODULE::strategy_launch_effectiveness_tagging"],
        )
        state.add_result(result)
        return result
