from __future__ import annotations

import pandas as pd

from ..labeling import RiskLabelingService
from ..models.temporal import chronological_train_dev_oot_split
from ..state import CopilotState
from .base import BaseAgent


class ModelBenchmarkAgent(BaseAgent):
    name = "model_benchmark_agent"
    description = "Train interpretable and nonlinear fraud-model baselines using an out-of-time split."

    EXCLUDED = {
        "fraud_label",
        "estimated_loss_amount",
        "user_id",
        "event_date",
        "risk_level_change_30d",
        "strategy_hit_count_30d",
        "rfi_count_180d",
        "restriction_count_180d",
    }

    async def run(self, state: CopilotState):
        data: pd.DataFrame = state.context["analysis_data"]
        event_specs = await self.call_tool(
            "catalog.search_features",
            domain=state.request.domain.value,
            event_code=state.request.event_code,
        )
        core_cross_domain = [
            "fiat_in_crypto_out_ratio",
            "minutes_deposit_to_first_chain_out",
            "minutes_kyc_to_first_fiat_deposit",
            "chain_withdraw_count_24h",
            "single_fiat_deposit_over_10000_cnt_30d",
            "small_fiat_deposit_count_24h",
            "fund_stay_minutes_median",
            "bank_fraud_ratio_max",
            "device_user_count_24h",
            "proxy_flag",
            "new_device_flag",
            "failed_login_count_1h",
            "new_withdraw_address_flag",
            "high_risk_chain_exposure",
            "mixer_exposure",
            "gambling_exposure",
            "counterparty_fraud_ratio",
            "fan_in_degree_24h",
            "fan_out_degree_24h",
            "campaign_task_similarity",
            "strong_relation_fraud_1hop_count",
            "fraud_2hop_count",
            "fraud_graph_score",
            "community_fraud_ratio",
            "registration_channel",
            "kyc_level",
            "occupation_risk_score",
            "behavior_event_count_30d",
            "behavior_event_diversity_30d",
            "behavior_success_ratio_30d",
            "api_activity_ratio_30d",
            "night_activity_ratio_30d",
            "strategy_avoidance_ratio_30d",
            "chain_out_5min_count_30d",
        ]
        features: list[str] = []
        allowed = {spec["name"] for spec in event_specs}
        for name in [spec["name"] for spec in event_specs] + core_cross_domain:
            if name in allowed and name in data.columns and name not in self.EXCLUDED and name not in features:
                features.append(name)
        features = features[:36]
        models = await self.call_tool(
            "models.train_benchmarks",
            data=data,
            features=features,
            request=state.request,
        )
        development = await self.call_tool(
            "rules.prepare_holdout",
            data=data,
            trained_models=models,
            partition="dev",
        )
        holdout = await self.call_tool(
            "rules.prepare_holdout",
            data=data,
            trained_models=models,
            partition="oot",
        )
        importance = {}
        for model in models:
            importance[model.name] = await self.call_tool(
                "models.global_importance", trained_model=model, top_k=15
            )
        oot_metrics = [model.metrics for model in models]
        dev_metrics = [
            model.dev_metrics for model in models if model.dev_metrics is not None
        ]
        if len(dev_metrics) != len(models):
            raise RuntimeError("one or more trained models are missing development metrics")
        split_summary = chronological_train_dev_oot_split(
            data,
            time_column=self.context.runtime.artifacts["project_config"].get(
                "time_column", "event_date"
            ),
        ).summary()
        state.model_benchmarks = oot_metrics
        state.merge_context(
            {
                "trained_models": models,
                "model_features": features,
                "candidate_data": development,
                "evaluation_data": holdout,
                "model_analysis": {
                    "features": features,
                    "development_benchmarks": [
                        metric.model_dump(mode="json") for metric in dev_metrics
                    ],
                    "benchmarks": [
                        metric.model_dump(mode="json") for metric in oot_metrics
                    ],
                    "global_importance": importance,
                    "training_manifests": {
                        model.name: model.training_manifest for model in models
                    },
                    "split": split_summary,
                    "threshold_selection_partition": "development",
                    "final_evaluation_partition": "out_of_time",
                    "leakage_controls": sorted(self.EXCLUDED),
                },
            }
        )
        best = models[0]
        label_review_queue = RiskLabelingService(
            self.context.runtime.settings.config_dir / "labeling.yaml"
        ).suspected_mislabel_queue(
            data,
            scores=best.oot_scores,
            row_indices=best.oot_index,
            target=state.request.target_label,
            model_name=best.name,
            evidence_columns=[
                "fiat_in_crypto_out_ratio",
                "chain_out_5min_count_30d",
                "strategy_avoidance_ratio_30d",
                "high_risk_chain_exposure",
                "fraud_graph_score",
                "strong_relation_fraud_1hop_count",
            ],
            top_n=70,
        )
        state.context["model_analysis"]["suspected_mislabel_queue"] = label_review_queue
        state.context["model_analysis"]["automatic_relabel_allowed"] = False
        result = self.result(
            f"完成Logistic、深度4决策树和XGBoost；开发集选择阈值后在OOT集最终评估。"
            f"开发集首选{best.name}，OOT ROC-AUC={best.metrics.roc_auc:.3f}，KS={best.metrics.ks:.3f}；"
            f"另生成{len(label_review_queue)}条高分负样本人工复核队列，不自动改标。",
            state.context["model_analysis"],
        )
        state.add_result(result)
        return result
