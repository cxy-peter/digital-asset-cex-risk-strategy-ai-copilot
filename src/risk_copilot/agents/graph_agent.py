from __future__ import annotations

import pandas as pd

from ..state import CopilotState
from .base import BaseAgent


class RiskGraphAgent(BaseAgent):
    name = "risk_graph_agent"
    description = "Build one-hop/two-hop risk graph features and auditable relationship paths."

    async def run(self, state: CopilotState):
        data: pd.DataFrame = await self.call_tool("graph.enrich_users", force=False)
        graph_columns = [
            "device_fraud_1hop_count",
            "withdraw_address_fraud_1hop_count",
            "email_fraud_1hop_count",
            "mobile_fraud_1hop_count",
            "kyc_id_fraud_1hop_count",
            "ip_fraud_1hop_count",
            "strong_relation_fraud_1hop_count",
            "fraud_2hop_count",
            "fraud_graph_score",
            "community_fraud_ratio",
        ]
        analyzer = self.context.runtime.artifacts["graph_analyzer"]
        top_graph_users = data.nlargest(5, "fraud_graph_score")[
            ["user_id", "fraud_graph_score"]
        ].to_dict("records")
        for record in top_graph_users:
            record["label_known_at_snapshot"] = (
                str(record["user_id"]) in analyzer.user_labels
            )
        stats = {
            "users": int(len(data)),
            "strong_relation_1hop_users": int((data["strong_relation_fraud_1hop_count"] > 0).sum()),
            "two_hop_fraud_users": int((data["fraud_2hop_count"] > 0).sum()),
            "ip_only_warning_users": int(
                ((data["ip_fraud_1hop_count"] > 0) & (data["strong_relation_fraud_1hop_count"] == 0)).sum()
            ),
            "top_graph_score_users": top_graph_users,
            "label_snapshot": self.context.runtime.artifacts.get(
                "graph_label_snapshot", {}
            ),
            "feature_columns": graph_columns,
            "relationship_policy": {
                "strong": ["device", "email", "mobile", "kyc_id", "withdraw_address"],
                "weak": ["ip"],
                "excluded_by_default": ["deposit_address"],
            },
        }
        state.merge_context({"analysis_data": data, "graph_analysis": stats})
        result = self.result(
            "完成Risk Graph一跳/二跳特征构建；IP仅作为弱关系，入金归集地址默认不作强关联。",
            stats,
            citations=["SOP::risk_graph"],
        )
        state.add_result(result)
        return result
