from __future__ import annotations

import pandas as pd

from ..state import CopilotState
from .base import BaseAgent


class FeatureIntelligenceAgent(BaseAgent):
    name = "feature_intelligence_agent"
    description = "Profile feature quality, decision-time availability, drift, and single-variable separation."

    async def run(self, state: CopilotState):
        data: pd.DataFrame = state.context["analysis_data"]
        request = state.request
        event_specs = await self.call_tool(
            "catalog.search_features",
            domain=request.domain.value,
            event_code=request.event_code,
        )
        scenario_features = []
        for scenario in state.context.get("knowledge_analysis", {}).get("top_scenarios", []):
            scenario_features.extend(scenario.get("candidate_features", []))
        names = []
        allowed = {spec["name"] for spec in event_specs}
        for name in [spec["name"] for spec in event_specs] + scenario_features:
            if name in allowed and name in data.columns and name not in names:
                names.append(name)
        # Include cross-domain signals that repeatedly appear in CoinTR materials.
        for name in [
            "fiat_in_crypto_out_ratio",
            "minutes_deposit_to_first_chain_out",
            "single_fiat_deposit_over_10000_cnt_30d",
            "small_fiat_deposit_count_24h",
            "bank_fraud_ratio_max",
            "strong_relation_fraud_1hop_count",
            "fraud_2hop_count",
            "fraud_graph_score",
            "counterparty_fraud_ratio",
            "risk_score_t1",
            "behavior_event_count_30d",
            "behavior_event_diversity_30d",
            "behavior_success_ratio_30d",
            "api_activity_ratio_30d",
            "night_activity_ratio_30d",
            "strategy_avoidance_ratio_30d",
            "chain_out_5min_count_30d",
        ]:
            if name in allowed and name in data and name not in names:
                names.append(name)
        profiles = await self.call_tool(
            "features.profile",
            data=data,
            feature_names=names[:60],
            target=request.target_label,
            time_column="event_date",
        )
        top = [p.model_dump(mode="json") for p in profiles[:20]]
        summary = {
            "profiled_features": len(profiles),
            "recommended_features": int(sum(p.recommended for p in profiles)),
            "event_features": [spec["name"] for spec in event_specs],
            "top_profiles": top,
            "decision_time_errors": await self.call_tool(
                "catalog.validate_decision_time",
                feature_names=[spec["name"] for spec in event_specs],
                event_code=request.event_code,
            ),
        }
        state.feature_profiles = profiles
        state.merge_context({"feature_analysis": summary})
        result = self.result(
            f"完成{len(profiles)}个候选特征的AUC/KS/IV/Lift/PSI分析，其中{summary['recommended_features']}个达到演示推荐标准。",
            summary,
        )
        state.add_result(result)
        return result
