from __future__ import annotations

import pandas as pd

from ..analysis import StrategyStabilityAnalyzer
from ..state import CopilotState
from .base import BaseAgent


class StrategyStabilityAgent(BaseAgent):
    name = "strategy_stability_agent"
    description = "Run cross-month, bootstrap, and feature-direction stability analysis for the frozen strategy."

    async def run(self, state: CopilotState):
        combined = pd.concat(
            [state.context["candidate_data"], state.context["evaluation_data"]],
            ignore_index=True,
        ).sort_values("event_date")
        analyzer = StrategyStabilityAnalyzer(
            target=state.request.target_label,
            time_column="event_date",
            bootstrap_rounds=200,
            random_seed=self.context.runtime.settings.random_seed,
        )
        report = analyzer.analyze(combined, state.context["selected_strategy"], state.request)
        state.merge_context({"stability_analysis": report})
        result = self.result(
            f"跨月与Bootstrap稳定性结论={report['status']}；"
            f"通过{report['summary']['gates_passed']}/{report['summary']['gates_total']}项门槛。",
            report,
        )
        state.add_result(result)
        return result
