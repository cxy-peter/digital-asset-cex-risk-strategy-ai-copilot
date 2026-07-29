from __future__ import annotations

from ..state import CopilotState
from .base import BaseAgent


class StrategyGenerationAgent(BaseAgent):
    name = "strategy_generation_agent"
    description = "Generate expert, quantile, graph, decision-tree, and model-score strategy candidates."

    async def run(self, state: CopilotState):
        models = state.context["trained_models"]
        tree_candidates = await self.call_tool(
            "models.extract_tree_rules",
            trained_models=models,
            domain=state.request.domain.value,
            event_code=state.request.event_code,
            action=state.request.preferred_actions[0].value,
        )
        candidates = await self.call_tool(
            "rules.generate_candidates",
            # Candidate thresholds are selected on development rows only. OOT data is reserved
            # for the final, frozen evaluation in BacktestRankingAgent.
            data=state.context["candidate_data"],
            profiles=state.feature_profiles,
            request=state.request,
            tree_candidates=tree_candidates,
            trained_models=models,
        )
        ai_candidates = state.context.get("ai_strategy_proposal", {}).get("candidates", [])
        candidates.extend(ai_candidates)
        state.candidates = candidates
        by_source = {}
        for candidate in candidates:
            by_source[candidate.source] = by_source.get(candidate.source, 0) + 1
        structured = {
            "candidate_count": len(candidates),
            "by_source": by_source,
            "tree_candidate_count": len(tree_candidates),
            "ai_candidate_count": len(ai_candidates),
            "ai_proposal_mode": state.context.get("ai_strategy_proposal", {}).get("mode"),
            "candidate_preview": [
                {
                    "strategy_id": c.strategy_id,
                    "name": c.name,
                    "source": c.source,
                    "action": c.action.value,
                    "required_features": c.required_features,
                    "rationale": c.rationale,
                }
                for c in candidates[:20]
            ],
        }
        state.merge_context({"strategy_generation": structured})
        result = self.result(
            f"生成{len(candidates)}条候选策略，覆盖AI规划、专家模板、分位阈值、Risk Graph、决策树路径和模型分层。",
            structured,
        )
        state.add_result(result)
        return result
