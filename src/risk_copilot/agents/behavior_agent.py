from __future__ import annotations

import pandas as pd

from ..models.temporal import chronological_train_dev_oot_split
from ..state import CopilotState
from .base import BaseAgent


class FraudBehaviorAgent(BaseAgent):
    name = "fraud_behavior_agent"
    description = "Contrast black/white samples and summarize fraud manifestations in business language."

    CORE_FEATURES = [
        "fiat_in_crypto_out_ratio",
        "minutes_deposit_to_first_chain_out",
        "minutes_kyc_to_first_fiat_deposit",
        "single_fiat_deposit_over_10000_cnt_30d",
        "small_fiat_deposit_count_24h",
        "chain_withdraw_count_24h",
        "fund_stay_minutes_median",
        "trade_pair_count_30d",
        "bank_fraud_ratio_max",
        "device_user_count_24h",
        "proxy_flag",
        "failed_login_count_1h",
        "high_risk_chain_exposure",
        "counterparty_fraud_ratio",
        "fan_in_degree_24h",
        "campaign_task_similarity",
        "fraud_graph_score",
    ]

    async def run(self, state: CopilotState):
        source: pd.DataFrame = state.context["analysis_data"]
        # Behavioral findings can inform candidate rationale, so they must not inspect OOT labels.
        data = chronological_train_dev_oot_split(
            source,
            time_column=self.context.runtime.artifacts["project_config"].get(
                "time_column", "event_date"
            ),
        ).dev
        features = [name for name in self.CORE_FEATURES if name in data]
        contrast = await self.call_tool(
            "features.behavior_contrast",
            data=data,
            features=features,
            target=state.request.target_label,
        )
        manifestations = []
        for row in contrast[:12]:
            direction = "更高" if row["direction"] == "higher_in_fraud" else "更低"
            manifestations.append(
                f"{row['feature']}在Fraud样本中均值{direction}（Fraud={row['fraud_mean']:.3g}, Normal={row['normal_mean']:.3g}）"
            )
        structured = {
            "sample_size": len(data),
            "positive_rate": float(data[state.request.target_label].mean()),
            "selection_partition": "development",
            "contrasts": contrast[:20],
            "manifestations": manifestations,
            "business_findings": [
                "比例类闭环特征通常比单纯金额更稳定。",
                "资金转移时间越短，风险信号通常越强。",
                "小额本身不一定显著，但小额高频与多账户/设备聚集组合后更有意义。",
                "单笔大额入金需结合资金去向、账户历史和外部银行风险，避免单条件粗暴拦截。",
            ],
        }
        state.merge_context({"behavior_analysis": structured})
        result = self.result(
            "完成黑白样本行为对比，将资金闭环、速度、次数、银行、设备、链上和图谱信号转为可解释业务结论。",
            structured,
        )
        state.add_result(result)
        return result
