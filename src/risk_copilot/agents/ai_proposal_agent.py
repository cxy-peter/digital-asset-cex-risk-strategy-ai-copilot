from __future__ import annotations

from ..ai import AIStrategyProposalService
from ..state import CopilotState
from .base import BaseAgent


class AIStrategyProposalAgent(BaseAgent):
    name = "ai_strategy_proposal_agent"
    description = "Use an optional LLM planning layer, with a deterministic fallback, to propose schema-valid strategy candidates."

    async def run(self, state: CopilotState):
        data = state.context["candidate_data"]
        allowed = {
            spec.name
            for spec in self.context.runtime.feature_registry.search(
                domain=state.request.domain.value,
                event_code=state.request.event_code,
            )
        }
        service = AIStrategyProposalService(max_candidates=3)
        proposal = service.propose(
            request=state.request,
            data=data,
            feature_profiles=state.feature_profiles,
            knowledge_context=state.context.get("knowledge_analysis", {}),
            behavior_context=state.context.get("behavior_analysis", {}),
            graph_context=state.context.get("graph_analysis", {}),
            model_context=state.context.get("model_analysis", {}),
            allowed_features=allowed,
        )
        state.merge_context({"ai_strategy_proposal": proposal})
        result = self.result(
            f"AI策略规划层以{proposal['mode']}模式生成{len(proposal['candidates'])}条候选；"
            "候选只进入确定性回测，不具备上线或处罚权限。",
            {
                "mode": proposal["mode"],
                "candidate_count": len(proposal["candidates"]),
                "candidate_preview": [
                    {
                        "strategy_id": item.strategy_id,
                        "name": item.name,
                        "source": item.source,
                        "features": item.required_features,
                        "action": item.action.value,
                    }
                    for item in proposal["candidates"]
                ],
                "guardrails": proposal["guardrails"],
                "error": proposal.get("error"),
            },
        )
        state.add_result(result)
        return result
