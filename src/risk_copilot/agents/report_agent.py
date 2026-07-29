from __future__ import annotations

from pathlib import Path

from ..reporting.renderers import StrategyReportRenderer
from ..schemas import StrategyPackage
from ..state import CopilotState
from .base import BaseAgent


class StrategyReportAgent(BaseAgent):
    name = "strategy_report_agent"
    description = "Consolidate the multi-agent analysis into structured, Markdown, HTML, JSON, and CSV artifacts."

    async def run(self, state: CopilotState):
        ranked = state.context["ranked_candidates"]
        selected_id = state.selected_strategy_id
        alternatives = [(strategy, metrics) for strategy, metrics in ranked if strategy.strategy_id != selected_id][:9]
        package = StrategyPackage(
            request=state.request,
            selected_strategy=state.context["selected_strategy"],
            selected_metrics=state.context["selected_metrics"],
            alternatives=alternatives,
            model_benchmarks=state.model_benchmarks,
            feature_profiles=state.feature_profiles,
            agent_results=state.agent_results.copy(),
            governance=state.context["governance"],
            engine_payload=state.context["engine_payload"],
            product_context=state.context.get("product_analysis", {}),
            risk_scoring=state.context.get("risk_scoring_analysis", {}),
            disposition_plan=state.context.get("disposition_plan", {}),
            registry_record={
                key: value
                for key, value in state.context.get("strategy_registry", {}).items()
                if key != "history"
            },
            strategy_test_environment=state.context.get("strategy_test_environment", {}),
            effectiveness_ticket=state.context.get("strategy_effectiveness_ticket", {}),
            cms_str_integration=state.context.get("cms_str_integration", {}),
            stability_analysis=state.context.get("stability_analysis", {}),
            conflict_analysis=state.context.get("conflict_analysis", {}),
            ai_advisory_board=state.context.get("ai_advisory_board", {}),
            evaluation_context={
                "split": state.context.get("model_analysis", {}).get("split", {}),
                "threshold_selection_partition": state.context.get(
                    "model_analysis", {}
                ).get("threshold_selection_partition"),
                "final_evaluation_partition": state.context.get(
                    "model_analysis", {}
                ).get("final_evaluation_partition"),
                "development_model_benchmarks": state.context.get(
                    "model_analysis", {}
                ).get("development_benchmarks", []),
                "training_manifests": state.context.get(
                    "model_analysis", {}
                ).get("training_manifests", {}),
                "candidate_evaluations": state.context.get(
                    "backtest_analysis", {}
                ).get("candidate_evaluations", []),
                "selection_partition": state.context.get(
                    "backtest_analysis", {}
                ).get("selection_partition"),
                "selection_basis": state.context.get(
                    "backtest_analysis", {}
                ).get("selection_basis"),
                "frozen_strategy_id": state.selected_strategy_id,
                "suspected_mislabel_queue": state.context.get(
                    "model_analysis", {}
                ).get("suspected_mislabel_queue", []),
                "automatic_relabel_allowed": state.context.get(
                    "model_analysis", {}
                ).get("automatic_relabel_allowed", False),
            },
        )
        output_dir = Path(self.context.runtime.settings.output_dir) / "strategy_demo"
        renderer = StrategyReportRenderer(
            self.context.runtime.settings.project_root / "src/risk_copilot/reporting/templates"
        )
        paths = renderer.write(package, output_dir)
        state.merge_context({"strategy_package": package, "strategy_artifacts": paths})
        result = self.result(
            f"已生成AI专业顾问组结论、稳定性与冲突分析、策略报告、公司式测试环境、效果工单、CMS/STR内部候选预览、规则Payload和Agent执行轨迹，目录：{output_dir}。",
            {key: str(value) for key, value in paths.items()},
        )
        state.add_result(result)
        # Re-write package with the final report agent included in the trace.
        package = package.model_copy(update={"agent_results": state.agent_results.copy()})
        paths = renderer.write(package, output_dir)
        state.merge_context({"strategy_package": package, "strategy_artifacts": paths})
        return result
