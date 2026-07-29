from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import load_yaml
from ..schemas import ActionType, Condition, RiskDomain, RuleGroup, StrategyCandidate, StrategyRequest
from .dsl import required_features


class CandidateRuleGenerator:
    def __init__(self, templates_path: str | Path) -> None:
        self.templates = load_yaml(templates_path)

    def from_templates(self, request: StrategyRequest) -> list[StrategyCandidate]:
        result = []
        for item in self.templates:
            if request.domain and item["domain"] != request.domain.value:
                continue
            if request.event_code and item["event_code"] != request.event_code:
                continue
            rule = RuleGroup.model_validate(item["rule"])
            strategy = StrategyCandidate(
                strategy_id=f"TPL-{item['template_id']}",
                name=item["name"], domain=RiskDomain(item["domain"]), event_code=item["event_code"],
                description=item["description"], rule=rule, action=ActionType(item["action"]), source="expert",
                rationale=["来自知识库专家规则模板", "需以当前标签口径重新回测"],
                required_features=required_features(rule), tags=item.get("tags", []),
                tag_level_1=item.get("tag_level_1", item["domain"]),
                tag_level_2=item.get("tag_level_2", "unclassified"),
                tag_level_3=item.get("tag_level_3", "MANUAL_REVIEW"),
            )
            result.append(strategy)
        return result

    def quantile_candidates(
        self,
        data: pd.DataFrame,
        profiles: list,
        request: StrategyRequest,
        top_features: int = 6,
    ) -> list[StrategyCandidate]:
        result = []
        candidates = [p for p in profiles if p.recommended and p.feature in data][:top_features]
        for profile in candidates:
            series = pd.to_numeric(data[profile.feature], errors="coerce").dropna()
            if len(series) < 50:
                continue
            if profile.direction == "lower_risk":
                thresholds = series.quantile([0.10, 0.20]).unique()
                operator = "<="
            else:
                thresholds = series.quantile([0.80, 0.90]).unique()
                operator = ">="
            for threshold in thresholds:
                rule = RuleGroup(conditions=[Condition(feature=profile.feature, operator=operator, value=float(threshold))])
                result.append(
                    StrategyCandidate(
                        strategy_id=f"QTL-{profile.feature}-{len(result)+1:02d}",
                        name=f"{profile.feature}分位阈值规则",
                        domain=request.domain or RiskDomain.FUND_SECURITY,
                        event_code=request.event_code or "RiskScoreDaily",
                        description=f"基于历史分位和单变量区分度自动生成；{profile.feature} {operator} {float(threshold):.4g}。",
                        rule=rule,
                        action=request.preferred_actions[0] if request.preferred_actions else ActionType.MANUAL_REVIEW,
                        source="quantile",
                        rationale=[f"AUC={profile.auc_1d}", f"KS={profile.ks_1d}", f"Lift@10={profile.lift_top_10}"],
                        required_features=[profile.feature], tags=["quantile", "single_feature"],
                        tag_level_1=(request.domain or RiskDomain.FUND_SECURITY).value,
                        tag_level_2="data_driven_threshold",
                        tag_level_3="MANUAL_REVIEW",
                    )
                )
        return result

    @staticmethod
    def graph_candidates(request: StrategyRequest) -> list[StrategyCandidate]:
        domain = request.domain or RiskDomain.FUND_SECURITY
        event = request.event_code or "RiskScoreDaily"
        groups = [
            ("强关系一跳Fraud", RuleGroup(logic="OR", conditions=[
                Condition(feature="device_fraud_1hop_count", operator=">=", value=1),
                Condition(feature="withdraw_address_fraud_1hop_count", operator=">=", value=1),
                Condition(feature="kyc_id_fraud_1hop_count", operator=">=", value=1),
            ])),
            ("二跳关联叠加快进快出", RuleGroup(logic="AND", conditions=[
                Condition(feature="fraud_2hop_count", operator=">=", value=2),
                Condition(feature="fiat_in_crypto_out_ratio", operator=">=", value=0.75),
                Condition(feature="minutes_deposit_to_first_chain_out", operator="<", value=720),
            ])),
            ("图社区风险叠加资金归集", RuleGroup(logic="AND", conditions=[
                Condition(feature="community_fraud_ratio", operator=">=", value=0.20),
                Condition(feature="fan_in_degree_24h", operator=">=", value=5),
            ])),
        ]
        result = []
        for idx, (name, rule) in enumerate(groups, 1):
            result.append(
                StrategyCandidate(
                    strategy_id=f"GRF-{idx:02d}", name=name, domain=domain, event_code=event,
                    description="Risk Graph候选规则：强关系用于精度，二跳和社区信号必须叠加行为特征控制误伤。",
                    rule=rule, action=ActionType.MANUAL_REVIEW, source="graph",
                    rationale=["IP不是单独强拦截条件", "充值归集地址需过滤"],
                    required_features=required_features(rule), tags=["graph"],
                    tag_level_1=domain.value,
                    tag_level_2="shared_identifier_fraud_ring",
                    tag_level_3="CMS_CASE_ONLY",
                )
            )
        return result
