from __future__ import annotations

import hashlib
import json

from ..state import CopilotState
from .base import BaseAgent


class StrategyTestEnvironmentAgent(BaseAgent):
    name = "strategy_test_environment_agent"
    description = (
        "Build the CoinTR-style feature-validation, historical-backtest, simulation, "
        "independent-review, post-launch-observation, and recurring-effectiveness test plan."
    )

    async def run(self, state: CopilotState):
        strategy = state.context["selected_strategy"]
        registry = state.context["strategy_registry"]
        data = state.context["evaluation_data"]
        snapshot_basis = {
            "rows": len(data),
            "columns": sorted(map(str, data.columns)),
            "max_event_date": str(data["event_date"].max()) if "event_date" in data else "unknown",
            "target_rate": float(data[state.request.target_label].mean()) if state.request.target_label in data else None,
        }
        data_snapshot_id = "SNAP-" + hashlib.sha256(
            json.dumps(snapshot_basis, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:16]
        result_value = await self.call_tool(
            "governance.evaluate_company_test_environment",
            strategy=strategy,
            strategy_version=int(registry["version"]),
            engine_payload=state.context["engine_payload"],
            metrics=state.context["selected_metrics"],
            governance=state.context["governance"],
            data_snapshot_id=data_snapshot_id,
            feature_catalog_version="FEP-SYNTHETIC-V1",
            stability_analysis=state.context.get("stability_analysis", {}),
            conflict_analysis=state.context.get("conflict_analysis", {}),
            ai_advisory_board=state.context.get("ai_advisory_board", {}),
        )
        plan = result_value["plan"]
        structured = {
            **plan.model_dump(mode="json"),
            "execution_mode": "DRY_RUN_ONLY",
            "production_connection": False,
            "dispatch_performed": False,
            "company_style_test_environment": True,
        }
        state.merge_context(
            {
                "strategy_test_environment": structured,
                "data_snapshot_id": data_snapshot_id,
            }
        )
        result = self.result(
            f"策略测试环境已生成：test_run_id={plan.test_run_id}，当前阶段={plan.current_stage}，"
            f"release_status={plan.release_status}；不包含生产连接或自动发布。",
            structured,
            citations=["TEST_ENV::RuleEngine_FEP_Backtest_SecondReview_3DayObservation"],
        )
        state.add_result(result)
        return result
