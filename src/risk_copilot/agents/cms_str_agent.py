from __future__ import annotations

from pathlib import Path
import json

from ..state import CopilotState
from .base import BaseAgent


class CMSSTRIntegrationAgent(BaseAgent):
    name = "cms_str_integration_agent"
    description = (
        "Prepare internal CMS/STR candidate-case previews for eligible L3 strategy tags; "
        "never submit to MASAK or another external system."
    )

    async def run(self, state: CopilotState):
        output = await self.call_tool(
            "integration.prepare_cms_str_candidates",
            strategy=state.context["selected_strategy"],
            strategy_version=int(state.context["strategy_registry"]["version"]),
            data=state.context["evaluation_data"],
            data_snapshot_id=state.context["data_snapshot_id"],
            top_k=10,
        )
        cases = [item.model_dump(mode="json") for item in output.get("cases", [])]
        structured = {**{k: v for k, v in output.items() if k != "cases"}, "cases": cases}
        target = Path(self.context.runtime.settings.output_dir) / "strategy_demo" / "cms_str_case_previews.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(structured, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        structured["artifact"] = str(target)
        state.merge_context({"cms_str_integration": structured})
        if structured.get("enabled"):
            summary = (
                f"根据三级标签{state.context['selected_strategy'].tag_level_3}生成"
                f"{structured.get('case_count', 0)}条内部CMS/STR候选案件预览；全部等待人工复核，未执行监管上报。"
            )
        else:
            summary = f"当前策略不触发CMS/STR候选案件：{structured.get('reason')}。"
        result = self.result(
            summary,
            structured,
            citations=["CMS_STR::one_click_internal_case_creation", "STR::MASAK_feedback_history"],
        )
        state.add_result(result)
        return result
