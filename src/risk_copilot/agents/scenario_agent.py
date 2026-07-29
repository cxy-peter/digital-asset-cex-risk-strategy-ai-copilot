from __future__ import annotations

from ..state import CopilotState
from .base import BaseAgent


class ScenarioKnowledgeAgent(BaseAgent):
    name = "scenario_knowledge_agent"
    description = "Retrieve black/grey industry patterns, event scenarios, SOPs, models, and dispositions."

    async def run(self, state: CopilotState):
        routing = state.context["routing"]
        scenario_query = (
            f"{state.request.query} 风险事件 黑灰产 作案工具 攻击偏好 特征表现 专家规则 模型 处置 "
            f"{routing['domain']} {routing['event_code']}"
        )
        sop_query = (
            f"{state.request.query} SOP 策略生命周期 审批 回测 RFI EDD 限额 冻结 "
            f"风险评分 STR 保密 {routing['domain']} {routing['event_code']}"
        )
        # Scenario metadata contains ``industry`` while SOP metadata deliberately does not.  The
        # two corpora must therefore be searched independently; applying the scenario filter to a
        # mixed result set silently removed every SOP in the previous implementation.
        scenario_hits = await self.call_tool(
            "knowledge.search",
            query=scenario_query,
            top_k=8,
            industry="digital_asset",
            document_type="scenario",
        )
        sop_hits = await self.call_tool(
            "knowledge.search",
            query=sop_query,
            top_k=5,
            document_type="sop",
        )

        def evidence(hit):
            return {
                "doc_id": hit["doc_id"],
                "document_type": hit["metadata"].get("type"),
                "score": round(hit["score"], 4),
                "title": hit["title"],
                "text_excerpt": hit["text"][:800],
                "metadata": hit["metadata"],
            }

        structured = {
            "top_scenarios": [
                {
                    "scenario_id": hit["doc_id"],
                    "score": round(hit["score"], 4),
                    "business_line": hit["metadata"].get("business_line"),
                    "event_stage": hit["metadata"].get("event_stage"),
                    "risk_types": hit["metadata"].get("risk_types", []),
                    "black_grey_tools": hit["metadata"].get("black_grey_tools", []),
                    "manifestations": hit["metadata"].get("manifestations", []),
                    "candidate_features": hit["metadata"].get("candidate_features", []),
                    "expert_rules": hit["metadata"].get("expert_rules", []),
                    "recommended_models": hit["metadata"].get("recommended_models", []),
                    "actions": hit["metadata"].get("actions", []),
                    "evidence": evidence(hit),
                }
                for hit in scenario_hits
            ],
            "sop_hits": [evidence(hit) for hit in sop_hits],
            "evidence": [evidence(hit) for hit in [*scenario_hits, *sop_hits]],
        }
        if not scenario_hits or scenario_hits[0]["score"] < 0.08:
            self.warnings.append("知识检索相关性较低，策略生成将主要依赖事件目录和离线数据。")
        if not sop_hits:
            self.warnings.append("未检索到相关SOP，治理结论需要人工补充证据。")
        state.merge_context({"knowledge_analysis": structured})
        all_hits = [*scenario_hits, *sop_hits]
        result = self.result(
            f"检索到{len(scenario_hits)}个数字资产风险场景和{len(sop_hits)}份相关SOP。",
            structured,
            citations=[hit["doc_id"] for hit in all_hits],
        )
        state.add_result(result)
        return result
