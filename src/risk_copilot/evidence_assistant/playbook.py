from __future__ import annotations

from copy import deepcopy
from typing import Any

from .catalog import DEFAULT_FEATURE_FAMILIES, DELIVERY_WORKFLOW, FEATURE_FAMILY_CATALOG, MODEL_ANALYSIS_PLAYBOOK, SOURCE_EVIDENCE
from .models import AssistantDecision, AssistantRequest, FeatureFamilyRecommendation, LifecycleStatus, ProblemLayer, StrategyDesignObject


SCENARIO_HINTS: dict[str, list[str]] = {
    "account_takeover": ["ato", "account takeover", "credential", "login", "new device", "password", "盗号", "盗账户", "新设备", "改密"],
    "rapid_cashout": ["rapid cashout", "cashout", "fiat", "chain out", "withdraw", "convert", "快进快出", "入金", "出金", "提币", "法币"],
    "aml_layering": ["aml", "launder", "layering", "internal transfer", "fan in", "fan out", "洗钱", "分层", "内部转账", "资金归集"],
    "campaign_abuse": ["campaign", "reward", "bonus", "inviter", "campaign abuse", "羊毛", "活动", "奖励", "邀请"],
    "market_abuse": ["market abuse", "wash trading", "spoofing", "insider", "front running", "api trading", "对敲", "交易操纵", "老鼠仓", "内幕", "秒单"],
}

SCENARIO_DEFAULTS: dict[str, dict[str, str]] = {
    "account_takeover": {"event_code": "ChainWithdraw", "risk_domain": "account_security", "population": "users requesting a withdrawal after authentication or sensitive-security changes", "action": "VIDEO_KYC_OR_MANUAL_REVIEW"},
    "rapid_cashout": {"event_code": "ChainWithdraw", "risk_domain": "fund_security", "population": "users with recent fiat funding, conversion or chain-withdrawal activity", "action": "MANUAL_REVIEW_OR_RFI"},
    "aml_layering": {"event_code": "InternalTransfer", "risk_domain": "aml_compliance", "population": "users or connected accounts participating in internal layering and external exit paths", "action": "RFI_OR_EDD"},
    "campaign_abuse": {"event_code": "CampaignReward", "risk_domain": "marketing_abuse", "population": "campaign participants with identity, device, inviter or reward-destination clustering", "action": "MANUAL_REVIEW_OR_REWARD_RESTRICTION"},
    "market_abuse": {"event_code": "SpotTrade", "risk_domain": "transaction_security", "population": "accounts with suspicious order, execution, PnL or related-party patterns", "action": "MONITOR_OR_MANUAL_REVIEW"},
}


def infer_scenario(query: str) -> str:
    normalized = query.lower()
    scored = {scenario: sum(keyword in normalized for keyword in keywords) for scenario, keywords in SCENARIO_HINTS.items()}
    winner = max(scored, key=scored.get)
    return winner if scored[winner] > 0 else "rapid_cashout"


def build_problem_decomposition(request: AssistantRequest, scenario: str) -> list[ProblemLayer]:
    defaults = SCENARIO_DEFAULTS[scenario]
    event_code = request.event_code or defaults["event_code"]
    domain = request.risk_domain or defaults["risk_domain"]
    objective = request.business_objective
    return [
        ProblemLayer(order=1, layer="Macro objective", core_question="Why must the platform solve this problem at all?", answer_template=f"The macro goal is {objective}. The risk capability is not an isolated model: it protects the platform's ability to operate, satisfy regulatory/business obligations, control loss and preserve legitimate user conversion.", required_evidence=["business objective", "regulatory or loss context", "affected owner"], output_object="one-sentence north-star objective"),
        ProblemLayer(order=2, layer="Regulatory or business requirement", core_question="Which concrete finding, loss, SLA, complaint or coverage gap is being addressed?", answer_template="Translate the broad goal into a measurable requirement: which risk must be detected, which users/transactions are in scope, how quickly a decision is needed, and what constitutes success.", required_evidence=["finding or risk statement", "scope", "SLA", "capacity and cost boundary"], output_object="measurable problem charter"),
        ProblemLayer(order=3, layer="Business flow and state", core_question="Where in the end-to-end flow does the risk arise and where is intervention still reversible?", answer_template=f"Map the {scenario} path before designing features: registration/KYC -> login/security -> funding -> trade/convert/internal transfer -> {event_code} -> investigation/case. Mark the decision point, terminal states and normal-business alternatives.", required_evidence=["state machine", "event sequence", "actor/owner", "reversible and irreversible nodes"], output_object="business flow and control-point map"),
        ProblemLayer(order=4, layer="System, event and data", core_question="Which system is the source of truth, what is available at decision time and who owns each field?", answer_template=f"For event {event_code}, define the event payload, feature source, freshness, window, available_at, PII level, owner and failure behaviour. A field created after the event cannot be used in a real-time decision.", required_evidence=["event contract", "feature lineage", "available_at", "owner", "data-quality checks"], output_object="event/feature contract and PIT audit"),
        ProblemLayer(order=5, layer="Risk intelligence", core_question="How will data be converted into risk evidence: rule, model, sequence or graph?", answer_template=f"Start with the {scenario} mechanism and feature families, then evaluate single features, a linear baseline, a shallow tree, XGBoost and Risk Graph evidence. The algorithm is selected only after label and data contracts are sound.", required_evidence=["feature evidence cards", "model comparison", "graph paths", "stability results"], output_object="model/feature analysis package"),
        ProblemLayer(order=6, layer="Strategy, action and governance", core_question="How does the signal become a controlled strategy instead of an ungoverned score?", answer_template=f"Build a strategy object for domain {domain}: Event + Population + Feature/Window + Threshold + Exclusion + Action + Version + Evidence + Monitoring + Rollback. The action must match confidence and harm.", required_evidence=["Rule DSL or model threshold", "exclusions", "action precedence", "approval roles"], output_object="versioned strategy candidate"),
        ProblemLayer(order=7, layer="Validation, outcome and ownership", core_question="What proves the solution works, and who owns release, monitoring and retirement?", answer_template="Use chronological OOT, simulation, independent review, test/production acceptance, an initial observation window and recurring effectiveness tickets. Report both risk value and operational/user impact; retain, tune, pause or retire.", required_evidence=["frozen snapshot", "simulation metrics", "acceptance record", "effectiveness labels", "RCA"], output_object="release-readiness and lifecycle decision"),
    ]


def feature_families_for(scenario: str) -> list[FeatureFamilyRecommendation]:
    return deepcopy(FEATURE_FAMILY_CATALOG.get(scenario, DEFAULT_FEATURE_FAMILIES))


def build_strategy_design(request: AssistantRequest, scenario: str, feature_families: list[FeatureFamilyRecommendation]) -> StrategyDesignObject:
    defaults = SCENARIO_DEFAULTS[scenario]
    event_code = request.event_code or defaults["event_code"]
    domain = request.risk_domain or defaults["risk_domain"]
    preferred = request.preferred_actions[0] if request.preferred_actions else defaults["action"]
    return StrategyDesignObject(
        strategy_id=f"EVID-{request.request_id}",
        name=f"Evidence-grounded {scenario.replace('_', ' ')} candidate",
        event_code=event_code,
        risk_domain=domain,
        population=defaults["population"],
        hypothesis=f"The selected population exhibits a time-ordered {scenario} mechanism supported by at least two independent feature families or a strong graph path plus behavioural evidence.",
        feature_families=[item.family for item in feature_families],
        window_policy="Use event-specific 1h/24h windows plus 7d/30d context; longer windows are supporting evidence, not a replacement for decision-time signals.",
        threshold_policy="Discover thresholds on Development only using quantiles/tree paths and freeze them before OOT; evaluate Lift and precision at the actual review capacity rather than choosing a global-score maximum.",
        exclusions=["approved test/internal/treasury accounts", "documented market-making or corporate operating patterns", "public IP, exchange wallet and other graph super-nodes", "trusted recurring behaviour when evidence supports it"],
        recommended_action=preferred,
        action_precedence=["PASS/MONITOR < ALERT < MANUAL_REVIEW < RFI/EDD/VIDEO_KYC < DELAY/LIMIT/RESTRICTION < FREEZE/REJECT", "a lower-confidence AI proposal cannot override a stronger existing action without an action-precedence review"],
        evaluation_metrics=["precision", "recall", "false_positive_rate", "alert_rate", "Lift@review_capacity", "captured_loss_rate", "incremental_recall", "duplicate_workload_rate", "monthly_stability"],
        monitoring_metrics=["confirmed-positive rate", "case SLA and backlog", "complaint/appeal rate", "feature PSI and missingness", "action outcome and re-review rate"],
        rollback_conditions=["point-in-time or data-quality breach", "material precision/recall or feature-direction decay", "alert volume exceeds operations capacity", "duplicate or action conflict with the active portfolio", "business process or regulatory requirement changes"],
        lifecycle_status=LifecycleStatus.DRAFT,
        human_review_required=True,
    )


def choose_initial_decision(*, has_distribution_audit: bool, audit_failed: bool, missing_business_objective: bool) -> AssistantDecision:
    if missing_business_objective:
        return AssistantDecision.REVISE_PROBLEM_DEFINITION
    if audit_failed:
        return AssistantDecision.REVISE_DATA_OR_LABELS
    if has_distribution_audit:
        return AssistantDecision.PROCEED_TO_OFFLINE_BACKTEST
    return AssistantDecision.PROCEED_TO_DATA_AUDIT


def model_analysis_playbook() -> list:
    return deepcopy(MODEL_ANALYSIS_PLAYBOOK)


def delivery_workflow() -> list:
    return deepcopy(DELIVERY_WORKFLOW)


def source_evidence() -> list:
    return deepcopy(SOURCE_EVIDENCE)


def lifecycle() -> list[LifecycleStatus]:
    return list(LifecycleStatus)


def build_existing_strategy_request_payload(request: AssistantRequest) -> dict[str, Any]:
    return {"request_id": request.request_id, "query": request.query, "domain": request.risk_domain, "event_code": request.event_code, "target_label": request.target_label, "max_alert_rate": request.maximum_alert_rate, "minimum_precision": request.minimum_precision, "minimum_recall": request.minimum_recall, "review_capacity": request.review_capacity, "preferred_actions": request.preferred_actions, "require_human_review": True}
