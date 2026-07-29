from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import pandas as pd

from ..llm.client import OpenAICompatibleClient
from ..rules.dsl import required_features
from ..schemas import ActionType, Condition, RiskDomain, RuleGroup, StrategyCandidate, StrategyRequest


def _safe_quantile(data: pd.DataFrame, feature: str, q: float, default: float) -> float:
    if feature not in data:
        return default
    values = pd.to_numeric(data[feature], errors="coerce").dropna()
    return float(values.quantile(q)) if len(values) >= 30 else default


@dataclass
class AIStrategyProposalService:
    """AI-assisted strategy proposal layer with a deterministic offline fallback.

    The LLM is never allowed to persist a strategy, change a lifecycle status, or execute a user
    action.  Its output is parsed into the same strict StrategyCandidate schema and then enters the
    deterministic backtest and governance path.
    """

    max_candidates: int = 3

    def _client(self) -> OpenAICompatibleClient | None:
        key = os.getenv("OPENAI_COMPATIBLE_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not key:
            return None
        return OpenAICompatibleClient(
            api_key=key,
            base_url=os.getenv("OPENAI_COMPATIBLE_BASE_URL", "https://api.openai.com/v1"),
            model=os.getenv("OPENAI_COMPATIBLE_MODEL", "gpt-4o-mini"),
            timeout_seconds=int(os.getenv("RISK_COPILOT_LLM_TIMEOUT", "90")),
        )

    def propose(
        self,
        *,
        request: StrategyRequest,
        data: pd.DataFrame,
        feature_profiles: list[Any],
        knowledge_context: dict[str, Any],
        behavior_context: dict[str, Any],
        graph_context: dict[str, Any],
        model_context: dict[str, Any],
        allowed_features: set[str],
    ) -> dict[str, Any]:
        client = self._client()
        if client is not None:
            try:
                candidates = self._propose_with_llm(
                    client=client,
                    request=request,
                    data=data,
                    feature_profiles=feature_profiles,
                    knowledge_context=knowledge_context,
                    behavior_context=behavior_context,
                    graph_context=graph_context,
                    model_context=model_context,
                    allowed_features=allowed_features,
                )
                if candidates:
                    return {
                        "mode": "llm",
                        "candidates": candidates[: self.max_candidates],
                        "guardrails": self.guardrails(),
                    }
            except Exception as exc:
                fallback = self._offline_fallback(request, data, feature_profiles, allowed_features)
                return {
                    "mode": "deterministic_fallback_after_llm_error",
                    "error": f"{type(exc).__name__}: {exc}",
                    "candidates": fallback,
                    "guardrails": self.guardrails(),
                }
        return {
            "mode": "deterministic_offline_fallback",
            "candidates": self._offline_fallback(request, data, feature_profiles, allowed_features),
            "guardrails": self.guardrails(),
        }

    @staticmethod
    def guardrails() -> list[str]:
        return [
            "Only registered decision-time features may be proposed.",
            "Thresholds must be grounded in development data or an approved SOP template.",
            "AI output is a DRAFT candidate and cannot change strategy status.",
            "All candidates require deterministic backtest, conflict analysis, stability analysis, and independent human review.",
            "AI cannot execute restrictions, freeze accounts, or submit STR externally.",
        ]

    def _offline_fallback(
        self,
        request: StrategyRequest,
        data: pd.DataFrame,
        profiles: list[Any],
        allowed_features: set[str],
    ) -> list[StrategyCandidate]:
        domain = request.domain or RiskDomain.FUND_SECURITY
        event = request.event_code or "ChainWithdraw"
        action = request.preferred_actions[0] if request.preferred_actions else ActionType.MANUAL_REVIEW
        ranked = [
            p.feature
            for p in profiles
            if getattr(p, "recommended", False) and p.feature in allowed_features and p.feature in data
        ]
        known = [
            "fiat_in_crypto_out_ratio",
            "minutes_deposit_to_first_chain_out",
            "bank_fraud_ratio_max",
            "strong_relation_fraud_1hop_count",
            "fraud_graph_score",
            "small_fiat_deposit_count_24h",
            "chain_out_5min_count_30d",
            "high_risk_chain_exposure",
            "new_device_flag",
            "proxy_flag",
        ]
        ordered = []
        for name in [*known, *ranked]:
            if name in allowed_features and name in data and name not in ordered:
                ordered.append(name)

        result: list[StrategyCandidate] = []
        if all(name in ordered for name in ["fiat_in_crypto_out_ratio", "minutes_deposit_to_first_chain_out"]):
            ratio = _safe_quantile(data, "fiat_in_crypto_out_ratio", 0.82, 0.82)
            minutes = _safe_quantile(data, "minutes_deposit_to_first_chain_out", 0.25, 360.0)
            conditions = [
                Condition(feature="fiat_in_crypto_out_ratio", operator=">=", value=ratio),
                Condition(feature="minutes_deposit_to_first_chain_out", operator="<=", value=minutes),
            ]
            if "bank_fraud_ratio_max" in ordered:
                conditions.append(
                    Condition(
                        feature="bank_fraud_ratio_max",
                        operator=">=",
                        value=_safe_quantile(data, "bank_fraud_ratio_max", 0.80, 0.30),
                    )
                )
            result.append(
                self._candidate(
                    idx=1,
                    name="AI建议：快进快出与高风险银行组合",
                    domain=domain,
                    event=event,
                    action=action,
                    rule=RuleGroup(logic="AND", conditions=conditions),
                    rationale=[
                        "基于风险需求、Fraud行为对比和Development分位生成",
                        "比例和速度联合使用，避免单一金额条件粗暴拦截",
                        "当前为离线fallback；接入LLM时由ReAct工具链生成同一Schema",
                    ],
                )
            )
        if "strong_relation_fraud_1hop_count" in ordered and "fiat_in_crypto_out_ratio" in ordered:
            result.append(
                self._candidate(
                    idx=2,
                    name="AI建议：Risk Graph强关系叠加资金闭环",
                    domain=domain,
                    event=event,
                    action=ActionType.MANUAL_REVIEW,
                    rule=RuleGroup(
                        logic="AND",
                        conditions=[
                            Condition(feature="strong_relation_fraud_1hop_count", operator=">=", value=1),
                            Condition(
                                feature="fiat_in_crypto_out_ratio",
                                operator=">=",
                                value=_safe_quantile(data, "fiat_in_crypto_out_ratio", 0.75, 0.75),
                            ),
                        ],
                    ),
                    rationale=[
                        "强关系用于提高Precision，资金闭环用于提供行为证据",
                        "IP和平台归集地址不作为单独强拦截条件",
                    ],
                )
            )
        if "high_risk_chain_exposure" in ordered:
            conditions = [
                Condition(
                    feature="high_risk_chain_exposure",
                    operator=">=",
                    value=_safe_quantile(data, "high_risk_chain_exposure", 0.85, 0.70),
                )
            ]
            if "chain_out_5min_count_30d" in ordered:
                conditions.append(
                    Condition(
                        feature="chain_out_5min_count_30d",
                        operator=">=",
                        value=max(1.0, _safe_quantile(data, "chain_out_5min_count_30d", 0.80, 2.0)),
                    )
                )
            result.append(
                self._candidate(
                    idx=3,
                    name="AI建议：高风险链上暴露与极速提币",
                    domain=domain,
                    event=event,
                    action=ActionType.RFI,
                    rule=RuleGroup(logic="AND", conditions=conditions),
                    rationale=[
                        "链上风险标签必须与用户行为和资金速度联合判断",
                        "建议先RFI/人工审核，不允许AI直接冻结或外部上报",
                    ],
                )
            )
        return result[: self.max_candidates]

    def _candidate(
        self,
        *,
        idx: int,
        name: str,
        domain: RiskDomain,
        event: str,
        action: ActionType,
        rule: RuleGroup,
        rationale: list[str],
    ) -> StrategyCandidate:
        return StrategyCandidate(
            strategy_id=f"AIP-{idx:02d}",
            name=name,
            domain=domain,
            event_code=event,
            description="AI策略规划层提出的候选，必须进入确定性测试环境后才能提交人工复核。",
            rule=rule,
            action=action,
            source="ai_planner",
            rationale=rationale,
            required_features=required_features(rule),
            tags=["ai_assisted", "human_in_the_loop", "simulation_only"],
            tag_level_1=domain.value,
            tag_level_2="ai_assisted_candidate",
            tag_level_3=action.value,
        )

    def _propose_with_llm(
        self,
        *,
        client: OpenAICompatibleClient,
        request: StrategyRequest,
        data: pd.DataFrame,
        feature_profiles: list[Any],
        knowledge_context: dict[str, Any],
        behavior_context: dict[str, Any],
        graph_context: dict[str, Any],
        model_context: dict[str, Any],
        allowed_features: set[str],
    ) -> list[StrategyCandidate]:
        profile_rows = []
        for profile in feature_profiles[:25]:
            if profile.feature not in allowed_features:
                continue
            profile_rows.append(
                {
                    "feature": profile.feature,
                    "auc": profile.auc_1d,
                    "ks": profile.ks_1d,
                    "iv": profile.iv,
                    "lift10": profile.lift_top_10,
                    "psi": profile.psi,
                    "direction": profile.direction,
                    "recommended": profile.recommended,
                    "q20": _safe_quantile(data, profile.feature, 0.20, 0.0),
                    "q50": _safe_quantile(data, profile.feature, 0.50, 0.0),
                    "q80": _safe_quantile(data, profile.feature, 0.80, 0.0),
                    "q90": _safe_quantile(data, profile.feature, 0.90, 0.0),
                }
            )
        context = {
            "request": request.model_dump(mode="json"),
            "allowed_features": sorted(allowed_features),
            "feature_profiles": profile_rows,
            "top_scenarios": knowledge_context.get("top_scenarios", [])[:4],
            "behavior_manifestations": behavior_context.get("manifestations", [])[:12],
            "graph_policy": graph_context.get("relationship_policy", {}),
            "model_importance": model_context.get("global_importance", {}),
        }
        system = (
            "You are an internal risk strategy planning agent. Propose at most three auditable DRAFT strategies. "
            "Use only allowed features and the supplied quantiles. Never claim production deployment. Never choose "
            "automatic freeze or regulatory submission. Return one JSON object with key candidates. Each candidate "
            "must contain name, action, rationale, and a rule object using logic/conditions with feature/operator/value."
        )
        raw = client.chat(system, json.dumps(context, ensure_ascii=False), temperature=0.1, max_tokens=2600)
        start, end = raw.find("{"), raw.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("LLM proposal does not contain JSON")
        payload = json.loads(raw[start : end + 1])
        result: list[StrategyCandidate] = []
        for idx, item in enumerate(payload.get("candidates", []), 1):
            rule = RuleGroup.model_validate(item["rule"])
            features = required_features(rule)
            if not features or any(feature not in allowed_features for feature in features):
                continue
            action = ActionType(item.get("action", "MANUAL_REVIEW"))
            if action in {ActionType.FREEZE, ActionType.REJECT}:
                action = ActionType.MANUAL_REVIEW
            result.append(
                StrategyCandidate(
                    strategy_id=f"LLM-{idx:02d}",
                    name=str(item.get("name", f"LLM Candidate {idx}")),
                    domain=request.domain or RiskDomain.FUND_SECURITY,
                    event_code=request.event_code or "ChainWithdraw",
                    description="由LLM策略规划Agent生成，经Schema与特征白名单校验后进入回测。",
                    rule=rule,
                    action=action,
                    source="llm",
                    rationale=[str(x) for x in item.get("rationale", [])],
                    required_features=features,
                    tags=["llm_proposed", "human_in_the_loop", "simulation_only"],
                    tag_level_1=(request.domain or RiskDomain.FUND_SECURITY).value,
                    tag_level_2="llm_assisted_candidate",
                    tag_level_3=action.value,
                )
            )
        return result
