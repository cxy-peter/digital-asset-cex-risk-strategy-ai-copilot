from __future__ import annotations

from ..analysis import StrategyConflictAnalyzer
from ..state import CopilotState
from .base import BaseAgent


class StrategyConflictAgent(BaseAgent):
    name = "strategy_conflict_agent"
    description = "Measure overlap, containment, action conflicts, and incremental fraud contribution versus a synthetic existing portfolio."

    async def run(self, state: CopilotState):
        analyzer = StrategyConflictAnalyzer(target=state.request.target_label)
        portfolio = analyzer.load_portfolio(
            self.context.runtime.settings.config_dir / "existing_strategy_portfolio.yaml"
        )
        report = analyzer.analyze(
            state.context["evaluation_data"],
            state.context["selected_strategy"],
            portfolio,
        )
        state.merge_context({"conflict_analysis": report})
        result = self.result(
            f"完成与{report['compatible_portfolio_size']}条兼容策略的冲突分析；"
            f"建议={report['recommendation']}，增量召回={report['incremental']['recall_contribution']:.2%}。",
            report,
        )
        state.add_result(result)
        return result
