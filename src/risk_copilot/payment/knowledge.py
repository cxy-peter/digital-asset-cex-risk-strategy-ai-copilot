from __future__ import annotations

from typing import Any

from .models import PaymentControl, PaymentScenarioId
from .state_machines import build_default_state_machines


PAYMENT_ACTOR_CATALOG: list[dict[str, Any]] = [
    {
        "actor": "customer",
        "sees": ["checkout", "authentication challenge", "order and refund communication"],
        "can_control": ["consent", "credential use", "challenge completion", "dispute initiation"],
        "risk_focus": ["account takeover", "authorized-push-payment scams", "subscription consent"],
    },
    {
        "actor": "merchant",
        "sees": ["order", "customer account", "fulfillment", "support and cancellation"],
        "can_control": ["checkout design", "3DS request", "capture timing", "refund", "evidence retention"],
        "risk_focus": ["CNP fraud", "friendly fraud", "refund abuse", "false declines"],
    },
    {
        "actor": "gateway_or_orchestrator",
        "sees": ["payment method", "PSP/acquirer responses", "routing and retry history"],
        "can_control": ["tokenization", "route selection", "guarded retries", "webhook normalization"],
        "risk_focus": ["duplicate payment", "decline recovery", "channel concentration"],
    },
    {
        "actor": "payfac_or_mor",
        "sees": ["sub-merchant", "transaction portfolio", "settlement and chargeback exposure"],
        "can_control": ["merchant underwriting", "reserve", "settlement delay", "ongoing monitoring"],
        "risk_focus": ["merchant fraud", "transaction laundering", "merchant credit risk"],
    },
    {
        "actor": "acquirer",
        "sees": ["merchant portfolio", "authorization/capture/clearing data", "network monitoring"],
        "can_control": ["merchant acceptance", "network routing", "funding and reserve terms"],
        "risk_focus": ["scheme monitoring", "merchant exposure", "chargebacks"],
    },
    {
        "actor": "card_network",
        "sees": ["network-wide authorization and dispute signals"],
        "can_control": ["message standards", "3DS programs", "token programs", "reason codes"],
        "risk_focus": ["ecosystem integrity", "liability allocation", "network fraud"],
    },
    {
        "actor": "issuer",
        "sees": ["cardholder account", "credential lifecycle", "cross-merchant behavior", "balance and limits"],
        "can_control": ["authorization", "step-up", "credential suspension", "cardholder dispute review"],
        "risk_focus": ["stolen credential", "ATO", "cardholder protection", "credit exposure"],
    },
]


PAYMENT_SCENARIO_CATALOG: list[dict[str, Any]] = [
    {
        "scenario_id": PaymentScenarioId.CARD_TESTING.value,
        "name": "Card testing / credential validation",
        "stage": "authorization",
        "signals": ["small repeated authorizations", "high decline ratio", "many cards per device"],
        "controls": [PaymentControl.BLOCK.value, PaymentControl.REQUEST_3DS.value, PaymentControl.MANUAL_REVIEW.value],
    },
    {
        "scenario_id": PaymentScenarioId.CNP_STOLEN_CREDENTIAL.value,
        "name": "CNP stolen-card fraud",
        "stage": "authentication_and_authorization",
        "signals": ["new device", "cross-border mismatch", "no successful authentication", "step-up amount"],
        "controls": [PaymentControl.REQUEST_3DS.value, PaymentControl.REQUEST_NETWORK_TOKEN.value, PaymentControl.MANUAL_REVIEW.value],
    },
    {
        "scenario_id": PaymentScenarioId.ACCOUNT_TAKEOVER.value,
        "name": "Account takeover followed by payment",
        "stage": "login_to_payment",
        "signals": ["recent security change", "new device", "new beneficiary", "abnormal amount"],
        "controls": [PaymentControl.STEP_UP_AUTHENTICATION.value, PaymentControl.DELAY.value, PaymentControl.MANUAL_REVIEW.value],
    },
    {
        "scenario_id": PaymentScenarioId.APP_BEC_SCAM.value,
        "name": "Authorized push-payment / BEC scam",
        "stage": "beneficiary_confirmation",
        "signals": ["first beneficiary", "beneficiary risk", "social-engineering confirmation", "large transfer"],
        "controls": [PaymentControl.BENEFICIARY_WARNING.value, PaymentControl.DELAY.value, PaymentControl.MANUAL_REVIEW.value],
    },
    {
        "scenario_id": PaymentScenarioId.FRIENDLY_FRAUD.value,
        "name": "First-party / friendly fraud",
        "stage": "post_purchase_dispute",
        "signals": ["prior disputes", "fulfilled order", "authenticated use", "cardholder denial"],
        "controls": [PaymentControl.MONITOR.value, PaymentControl.MANUAL_REVIEW.value],
    },
    {
        "scenario_id": PaymentScenarioId.REFUND_ABUSE.value,
        "name": "Refund and return abuse",
        "stage": "refund",
        "signals": ["high refund velocity", "refund to alternative instrument", "repeat return behavior"],
        "controls": [PaymentControl.REFUND_LIMIT.value, PaymentControl.MANUAL_REVIEW.value],
    },
    {
        "scenario_id": PaymentScenarioId.SUBSCRIPTION_DISPUTE.value,
        "name": "Subscription and MIT dispute",
        "stage": "recurring_payment",
        "signals": ["missing recurring notice", "weak consent evidence", "cancellation friction", "MIT flag"],
        "controls": [PaymentControl.MONITOR.value, PaymentControl.MANUAL_REVIEW.value, PaymentControl.REFUND_LIMIT.value],
    },
    {
        "scenario_id": PaymentScenarioId.MERCHANT_FRAUD.value,
        "name": "Merchant fraud / non-fulfillment",
        "stage": "merchant_monitoring",
        "signals": ["volume spike", "weak fulfillment", "refund/chargeback spike", "website mismatch"],
        "controls": [PaymentControl.RESERVE_HOLD.value, PaymentControl.SETTLEMENT_DELAY.value, PaymentControl.MANUAL_REVIEW.value],
    },
    {
        "scenario_id": PaymentScenarioId.MERCHANT_CREDIT_RISK.value,
        "name": "Merchant credit and settlement exposure",
        "stage": "settlement",
        "signals": ["chargeback exposure exceeds reserve", "negative balance risk", "rapid volume growth"],
        "controls": [PaymentControl.RESERVE_HOLD.value, PaymentControl.SETTLEMENT_DELAY.value, PaymentControl.PAYOUT_RESTRICTION.value],
    },
    {
        "scenario_id": PaymentScenarioId.TRANSACTION_LAUNDERING.value,
        "name": "Transaction laundering / undeclared processing",
        "stage": "merchant_transaction",
        "signals": ["MCC-product mismatch", "descriptor/website mismatch", "unexplained traffic mix"],
        "controls": [PaymentControl.MANUAL_REVIEW.value, PaymentControl.RESERVE_HOLD.value, PaymentControl.ESCALATE_COMPLIANCE.value],
    },
    {
        "scenario_id": PaymentScenarioId.PAYOUT_MULE.value,
        "name": "Payout mule / rapid fund dispersion",
        "stage": "payout",
        "signals": ["fan-in and fan-out", "short fund stay", "new payout account"],
        "controls": [PaymentControl.DELAY.value, PaymentControl.PAYOUT_RESTRICTION.value, PaymentControl.MANUAL_REVIEW.value],
    },
    {
        "scenario_id": PaymentScenarioId.DUPLICATE_PAYMENT_API.value,
        "name": "Duplicate payment and API idempotency failure",
        "stage": "api_and_webhook",
        "signals": ["same idempotency key with different payload", "duplicate webhook", "repeat capture"],
        "controls": [PaymentControl.BLOCK.value, PaymentControl.MANUAL_CAPTURE.value, PaymentControl.MANUAL_REVIEW.value],
    },
    {
        "scenario_id": PaymentScenarioId.DCC_CONSENT.value,
        "name": "DCC consent and disclosure failure",
        "stage": "checkout",
        "signals": ["DCC applied", "no explicit consent", "missing FX disclosure"],
        "controls": [PaymentControl.BLOCK.value, PaymentControl.MANUAL_REVIEW.value],
    },
    {
        "scenario_id": PaymentScenarioId.AGENTIC_AUTHORIZATION.value,
        "name": "Agentic-commerce delegated authority",
        "stage": "agent_authorization",
        "signals": ["spend exceeds delegated limit", "broad token scope", "weak agent identity", "missing human approval"],
        "controls": [PaymentControl.BLOCK.value, PaymentControl.STEP_UP_AUTHENTICATION.value, PaymentControl.MANUAL_REVIEW.value],
    },
]


CONTROL_CATALOG: list[dict[str, Any]] = [
    {"control": "REQUEST_3DS", "objective": "obtain stronger cardholder authentication", "reversible": True},
    {"control": "REQUEST_NETWORK_TOKEN", "objective": "reduce credential exposure and improve lifecycle continuity", "reversible": True},
    {"control": "ROUTE_TO_ALTERNATIVE_ACQUIRER", "objective": "recover valid soft declines without changing risk truth", "reversible": True},
    {"control": "GUARDED_RETRY", "objective": "retry only eligible soft declines under velocity and idempotency limits", "reversible": True},
    {"control": "MANUAL_CAPTURE", "objective": "delay capture until fulfillment or evidence conditions are met", "reversible": True},
    {"control": "DELAY", "objective": "create an investigation window before irreversible movement", "reversible": True},
    {"control": "MANUAL_REVIEW", "objective": "resolve complex identity, merchant, fulfillment, or dispute facts", "reversible": True},
    {"control": "REFUND_LIMIT", "objective": "contain refund-abuse exposure while preserving legitimate service", "reversible": True},
    {"control": "RESERVE_HOLD", "objective": "cover merchant chargeback and settlement credit exposure", "reversible": True},
    {"control": "SETTLEMENT_DELAY", "objective": "defer merchant funding while evidence matures", "reversible": True},
    {"control": "BLOCK", "objective": "stop high-confidence transaction or protocol abuse", "reversible": False},
]


JOINT_METRICS = [
    "checkout_conversion_rate",
    "authentication_success_rate",
    "three_ds_challenge_rate",
    "authorization_approval_rate",
    "soft_decline_recovery_rate",
    "false_decline_rate",
    "fraud_rate",
    "chargeback_rate",
    "refund_rate",
    "alert_rate",
    "manual_review_capacity",
    "captured_loss_rate",
    "dispute_win_rate",
    "evidence_completeness_rate",
    "operational_cost",
    "merchant_settlement_exposure",
    "net_loss_after_recovery",
]


PAYMENT_FEATURE_GROUPS: dict[str, list[str]] = {
    "actor_and_merchant": [
        "merchant_risk_score", "merchant_age_days", "mcc_risk_score", "merchant_country_risk",
        "expected_volume_gap", "volume_growth_ratio_7d", "avg_ticket_gap", "chargeback_ratio_90d",
        "refund_ratio_30d", "reserve_coverage_ratio", "settlement_exposure", "fulfillment_rate",
        "website_descriptor_match", "product_mcc_match", "ubo_risk_score", "sanction_match",
    ],
    "credential_device_card": [
        "card_count_per_device_10m", "card_count_per_account_24h", "device_card_cluster_size",
        "new_device_flag", "proxy_flag", "ip_country_bin_mismatch", "shipping_billing_mismatch",
        "cardholder_name_mismatch", "network_token_flag", "wallet_token_flag", "vault_token_flag",
        "cryptogram_valid", "account_updater_status", "credential_age_days", "cit_mit_flag",
        "recurring_consent_flag",
    ],
    "transaction_velocity": [
        "small_auth_count_10m", "auth_attempt_count_10m", "decline_ratio_10m", "amount_step_up_ratio",
        "txn_count_1h", "txn_amount_1h", "cross_border_flag", "amount_vs_customer_p95",
        "first_merchant_flag", "first_beneficiary_flag", "transaction_time_anomaly",
        "order_to_auth_latency_ms",
    ],
    "authentication_3ds": [
        "three_ds_requested", "three_ds_version", "three_ds_flow", "three_ds_result",
        "challenge_rate_30d", "frictionless_rate_30d", "liability_shift_flag", "sca_exemption_type",
        "authentication_to_authorization_gap_ms", "issuer_authentication_required_flag",
    ],
    "authorization_and_api": [
        "soft_decline_flag", "hard_decline_flag", "issuer_response_code", "retry_count",
        "retry_interval_seconds", "route_count", "acquirer_country", "issuer_country",
        "authorization_approval_rate_30d", "capture_delay_minutes", "partial_capture_flag",
        "reversal_flag", "idempotency_conflict_flag", "duplicate_webhook_count",
    ],
    "dispute_and_evidence": [
        "prior_dispute_count_180d", "friendly_fraud_score", "reason_code_family",
        "delivery_evidence_flag", "digital_usage_evidence_flag", "consent_evidence_flag",
        "cancellation_evidence_flag", "communication_evidence_flag", "evidence_completeness_score",
        "representment_expected_value",
    ],
    "refund_subscription_payout": [
        "refund_count_30d", "refund_to_alt_instrument_flag", "return_velocity",
        "mit_without_notice_flag", "cancellation_friction_score", "payout_fan_in_24h",
        "payout_fan_out_24h", "payout_account_age_days", "fund_stay_minutes_median",
        "beneficiary_risk_score",
    ],
    "agentic_and_stablecoin": [
        "agentic_payment_flag", "delegated_limit_utilization", "human_approval_required",
        "token_scope_risk", "agent_identity_assurance", "stablecoin_flag", "stablecoin_issuer_risk",
        "reserve_transparency_score", "redemption_risk", "wallet_address_risk",
        "sanction_address_flag", "smart_contract_risk", "liquidity_fx_exposure",
        "reconciliation_break_count",
    ],
}


STABLECOIN_OVERLAY = {
    "risk_dimensions": [
        "customer and counterparty KYC",
        "sanctions and address screening",
        "Travel Rule or transfer data completeness",
        "issuer and reserve transparency",
        "custody and private-key control",
        "redemption and liquidity",
        "smart-contract and bridge exposure",
        "FX, treasury, reconciliation, and settlement finality",
    ],
    "principle": "Stablecoins change settlement and liquidity architecture; they do not remove identity, fraud, AML, credit, custody, or operational risk.",
}


AGENTIC_GOVERNANCE = {
    "required_controls": [
        "explicit delegated authority",
        "per-agent and per-merchant spend limits",
        "scoped and revocable credentials",
        "strong agent identity and device/workload attestation",
        "human approval for high-impact or out-of-policy transactions",
        "idempotency, purpose binding, and full audit trail",
        "clear dispute attribution between user, agent, merchant, and payment provider",
    ],
    "boundary": "An LLM may plan or explain a payment, but deterministic policy must own limits, credential scope, execution, and state transitions.",
}


def detect_payment_topics(query: str, event_code: str | None = None) -> list[str]:
    text = f"{query} {event_code or ''}".lower()
    topic_keywords = {
        "card_testing": ["card testing", "测试卡", "小额多笔", "多卡", "decline"],
        "3ds_authentication": ["3ds", "3d secure", "sca", "认证", "challenge", "frictionless"],
        "authorization_capture": ["authorization", "授权", "capture", "请款", "settlement", "结算"],
        "tokenization": ["token", "tokenization", "network token", "cryptogram", "代币化"],
        "merchant_risk": ["merchant", "商户", "underwriting", "收单", "reserve"],
        "dispute": ["chargeback", "dispute", "拒付", "争议", "friendly fraud", "subscription", "退款"],
        "payment_optimization": ["成功率", "approval", "routing", "路由", "retry", "重试", "soft decline"],
        "payout": ["payout", "出款", "归集", "跑分", "mule"],
        "stablecoin": ["stablecoin", "稳定币", "usdt", "usdc", "链上支付"],
        "agentic_commerce": ["agentic", "agent payment", "智能体支付", "代理支付", "delegated"],
        "api_integrity": ["idempotency", "幂等", "webhook", "重复支付", "duplicate"],
    }
    return [topic for topic, keywords in topic_keywords.items() if any(keyword in text for keyword in keywords)]


def build_payment_brief(query: str, event_code: str | None = None) -> dict[str, Any]:
    topics = detect_payment_topics(query, event_code)
    scenario_hits = []
    for scenario in PAYMENT_SCENARIO_CATALOG:
        haystack = " ".join(
            [scenario["scenario_id"], scenario["name"], scenario["stage"], *scenario["signals"]]
        ).lower()
        if any(token.replace("_", " ") in haystack for token in topics):
            scenario_hits.append(scenario)
    if not scenario_hits and topics:
        scenario_hits = PAYMENT_SCENARIO_CATALOG[:4]

    machines = build_default_state_machines()
    return {
        "activated": bool(topics),
        "topics": topics,
        "scenario_candidates": scenario_hits,
        "actor_responsibility_map": PAYMENT_ACTOR_CATALOG,
        "recommended_controls": CONTROL_CATALOG,
        "joint_metrics": JOINT_METRICS,
        "state_machines": {
            name: {
                "initial_state": machine.spec.initial_state,
                "terminal_states": sorted(machine.spec.terminal_states),
            }
            for name, machine in machines.items()
        },
        "stablecoin_overlay": STABLECOIN_OVERLAY if "stablecoin" in topics else {},
        "agentic_governance": AGENTIC_GOVERNANCE if "agentic_commerce" in topics else {},
        "reasoning_principles": [
            "authentication and issuer authorization are separate decisions",
            "payment, risk, merchant, and dispute states must remain separate",
            "controls should be the minimum necessary and reversible when evidence is incomplete",
            "approval-rate uplift must be evaluated together with fraud, chargeback, operational cost, and net loss",
            "dispute evidence must be designed during checkout and fulfillment rather than after a chargeback arrives",
        ],
        "boundary": {
            "source": "post-internship payment and anti-fraud research corpus",
            "cointr_production_capability_claimed": False,
            "automatic_enforcement": False,
            "human_review_required_for_high_impact_actions": True,
        },
    }
