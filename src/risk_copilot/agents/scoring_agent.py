from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ..state import CopilotState
from .base import BaseAgent


class UserRiskScoringAgent(BaseAgent):
    name = "user_risk_scoring_agent"
    description = "Calculate onboarding + T+1 user risk tiers while preserving manual overrides and STR confidentiality."

    async def run(self, state: CopilotState):
        analysis = await self.call_tool(
            "scoring.assess_users",
            data=state.context["analysis_data"],
            top_k=50,
        )
        output = Path(self.context.runtime.settings.output_dir) / "user_risk_scoring"
        output.mkdir(parents=True, exist_ok=True)
        profile_path = output / "user_risk_profiles.csv"
        summary_path = output / "user_risk_scoring_summary.json"
        analysis["profiles"].to_csv(profile_path, index=False)
        serializable = {
            key: value
            for key, value in analysis.items()
            if key != "profiles"
        }
        serializable["artifacts"] = {
            "profiles_csv": str(profile_path),
            "summary_json": str(summary_path),
            "snapshots_sqlite": analysis["batch_manifest"]["database"],
        }
        summary_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        state.merge_context({"risk_scoring_analysis": serializable, "risk_profile_frame": analysis["profiles"]})
        result = self.result(
            f"完成Onboarding+T+1双层风险评分；输出{len(analysis['profiles'])}条用户画像，最高风险层级为{analysis['highest_tier']}。",
            serializable,
            citations=["SOP::user_risk_scoring", "SOP::str_confidentiality"],
        )
        state.add_result(result)
        return result
