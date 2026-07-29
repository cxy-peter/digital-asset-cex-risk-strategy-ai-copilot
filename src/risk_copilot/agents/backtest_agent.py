from __future__ import annotations

from ..rules.dsl import rule_to_expression
from ..state import CopilotState
from .base import BaseAgent


class BacktestRankingAgent(BaseAgent):
    name = "backtest_ranking_agent"
    description = "Rank on development data, freeze the strategy, and report final OOT metrics."

    async def run(self, state: CopilotState):
        development_ranked = await self.call_tool(
            "rules.backtest_rank",
            data=state.context["candidate_data"],
            candidates=state.candidates,
            request=state.request,
        )
        development_failures = list(
            self.context.runtime.artifacts.get("candidate_failures", [])
        )
        if not development_ranked:
            raise RuntimeError("no strategy candidate could be evaluated on the development split")

        valid_ranked = []
        validation_failures = []
        for strategy, metrics in development_ranked:
            errors = self.context.runtime.feature_registry.validate_decision_time(
                [f for f in strategy.required_features if not f.startswith("model_score__")],
                strategy.event_code,
            )
            if errors:
                validation_failures.append({"strategy_id": strategy.strategy_id, "errors": errors})
            else:
                valid_ranked.append((strategy, metrics))

        feasible = [
            item
            for item in valid_ranked
            if item[1].precision >= state.request.minimum_precision
            and item[1].recall >= state.request.minimum_recall
            and item[1].alert_rate <= state.request.max_alert_rate
        ]
        interpretable_feasible = [item for item in feasible if item[0].source != "model_score"]
        if interpretable_feasible:
            selected_pool = interpretable_feasible
            selection_basis = "interpretable_feasible_preferred"
        elif feasible:
            selected_pool = feasible
            selection_basis = "feasible_candidate"
        elif valid_ranked:
            selected_pool = valid_ranked
            selection_basis = "best_valid_fallback"
        else:
            selected_pool = development_ranked
            selection_basis = "execution_only_fallback"
        selected_strategy, selected_development_metrics = selected_pool[0]

        # OOT is evaluated only after the development-set decision is frozen. Its metrics never
        # affect candidate order, feasibility filtering, or selected_strategy_id.
        oot_evaluated = await self.call_tool(
            "rules.backtest_rank",
            data=state.context["evaluation_data"],
            candidates=state.candidates,
            request=state.request,
        )
        oot_failures = list(self.context.runtime.artifacts.get("candidate_failures", []))
        oot_metrics_by_id = {
            strategy.strategy_id: metrics for strategy, metrics in oot_evaluated
        }
        if selected_strategy.strategy_id not in oot_metrics_by_id:
            selected_available = next(
                (
                    item
                    for item in selected_pool
                    if item[0].strategy_id in oot_metrics_by_id
                ),
                None,
            )
            if selected_available is None:
                raise RuntimeError("development-selected candidates could not be evaluated on OOT")
            selected_strategy, selected_development_metrics = selected_available

        # Preserve development order while pairing candidates with reporting-only OOT metrics.
        ranked = [
            (strategy, oot_metrics_by_id[strategy.strategy_id])
            for strategy, _ in development_ranked
            if strategy.strategy_id in oot_metrics_by_id
        ]
        selected_metrics = oot_metrics_by_id[selected_strategy.strategy_id]
        candidate_evaluations = [
            {
                "strategy_id": strategy.strategy_id,
                "name": strategy.name,
                "source": strategy.source,
                "action": strategy.action.value,
                "expression": rule_to_expression(strategy.rule),
                "selected": strategy.strategy_id == selected_strategy.strategy_id,
                "development": development_metrics.model_dump(mode="json"),
                "out_of_time": oot_metrics_by_id[
                    strategy.strategy_id
                ].model_dump(mode="json"),
            }
            for strategy, development_metrics in development_ranked
            if strategy.strategy_id in oot_metrics_by_id
        ]
        state.selected_strategy_id = selected_strategy.strategy_id
        state.candidate_metrics = {strategy.strategy_id: metrics for strategy, metrics in ranked}
        state.merge_context(
            {
                "ranked_candidates": ranked,
                "development_ranked_candidates": development_ranked,
                "selected_strategy": selected_strategy,
                "selected_metrics": selected_metrics,
                "backtest_analysis": {
                    "backtested": len(ranked),
                    "feasible": len(feasible),
                    "interpretable_feasible": len(interpretable_feasible),
                    "selection_partition": "development",
                    "selection_basis": selection_basis,
                    "final_evaluation_partition": "out_of_time",
                    "selected": {
                        "strategy_id": selected_strategy.strategy_id,
                        "name": selected_strategy.name,
                        "source": selected_strategy.source,
                        "expression": rule_to_expression(selected_strategy.rule),
                        "development_metrics": selected_development_metrics.model_dump(
                            mode="json"
                        ),
                        "metrics": selected_metrics.model_dump(mode="json"),
                    },
                    "top_candidates": [
                        {
                            "strategy_id": strategy.strategy_id,
                            "name": strategy.name,
                            "source": strategy.source,
                            "expression": rule_to_expression(strategy.rule),
                            "development_metrics": development_metrics.model_dump(
                                mode="json"
                            ),
                            "metrics": oot_metrics_by_id[
                                strategy.strategy_id
                            ].model_dump(mode="json"),
                        }
                        for strategy, development_metrics in development_ranked[:12]
                        if strategy.strategy_id in oot_metrics_by_id
                    ],
                    "validation_failures": validation_failures,
                    "development_execution_failures": development_failures,
                    "execution_failures": oot_failures,
                    "candidate_evaluations": candidate_evaluations,
                    "ranking_method": (
                        "development-set multi-objective reward + group-relative standardized "
                        "advantage; frozen selection followed by OOT final evaluation"
                    ),
                },
            }
        )
        result = self.result(
            f"开发集完成{len(development_ranked)}条候选排序并冻结{selected_strategy.name}；"
            f"OOT最终Precision={selected_metrics.precision:.2%}，Recall={selected_metrics.recall:.2%}。",
            state.context["backtest_analysis"],
        )
        state.add_result(result)
        return result
