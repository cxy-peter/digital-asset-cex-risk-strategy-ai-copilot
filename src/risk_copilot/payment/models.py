from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PaymentActor(str, Enum):
    CUSTOMER = "customer"
    MERCHANT = "merchant"
    GATEWAY = "gateway"
    ORCHESTRATOR = "orchestrator"
    PAYMENT_FACILITATOR = "payment_facilitator"
    MERCHANT_OF_RECORD = "merchant_of_record"
    ACQUIRER = "acquirer"
    CARD_NETWORK = "card_network"
    ISSUER = "issuer"
    SPONSOR_BANK = "sponsor_bank"


class PaymentScenarioId(str, Enum):
    CARD_TESTING = "PAY-CARD-TESTING"
    CNP_STOLEN_CREDENTIAL = "PAY-CNP-STOLEN"
    ACCOUNT_TAKEOVER = "PAY-ATO"
    APP_BEC_SCAM = "PAY-APP-BEC"
    FRIENDLY_FRAUD = "PAY-FRIENDLY-FRAUD"
    REFUND_ABUSE = "PAY-REFUND-ABUSE"
    SUBSCRIPTION_DISPUTE = "PAY-SUBSCRIPTION"
    MERCHANT_FRAUD = "PAY-MERCHANT-FRAUD"
    MERCHANT_CREDIT_RISK = "PAY-MERCHANT-CREDIT"
    TRANSACTION_LAUNDERING = "PAY-TRANSACTION-LAUNDERING"
    PAYOUT_MULE = "PAY-PAYOUT-MULE"
    DUPLICATE_PAYMENT_API = "PAY-DUPLICATE-API"
    DCC_CONSENT = "PAY-DCC-CONSENT"
    AGENTIC_AUTHORIZATION = "PAY-AGENTIC-AUTH"


class PaymentControl(str, Enum):
    PASS = "PASS"
    MONITOR = "MONITOR"
    REQUEST_3DS = "REQUEST_3DS"
    STEP_UP_AUTHENTICATION = "STEP_UP_AUTHENTICATION"
    REQUEST_NETWORK_TOKEN = "REQUEST_NETWORK_TOKEN"
    ROUTE_TO_ALTERNATIVE_ACQUIRER = "ROUTE_TO_ALTERNATIVE_ACQUIRER"
    GUARDED_RETRY = "GUARDED_RETRY"
    MANUAL_CAPTURE = "MANUAL_CAPTURE"
    DELAY = "DELAY"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    BENEFICIARY_WARNING = "BENEFICIARY_WARNING"
    REFUND_LIMIT = "REFUND_LIMIT"
    RESERVE_HOLD = "RESERVE_HOLD"
    SETTLEMENT_DELAY = "SETTLEMENT_DELAY"
    PAYOUT_RESTRICTION = "PAYOUT_RESTRICTION"
    BLOCK = "BLOCK"
    REJECT = "REJECT"
    ESCALATE_COMPLIANCE = "ESCALATE_COMPLIANCE"


class PaymentDecision(str, Enum):
    PASS = "PASS"
    MONITOR = "MONITOR"
    CHALLENGE = "CHALLENGE"
    REVIEW = "REVIEW"
    BLOCK_CANDIDATE = "BLOCK_CANDIDATE"


class ThreeDSResult(str, Enum):
    NOT_REQUESTED = "NOT_REQUESTED"
    FRICTIONLESS = "FRICTIONLESS"
    CHALLENGE_SUCCEEDED = "CHALLENGE_SUCCEEDED"
    CHALLENGE_FAILED = "CHALLENGE_FAILED"
    UNAVAILABLE = "UNAVAILABLE"
    ATTEMPT_ACKNOWLEDGED = "ATTEMPT_ACKNOWLEDGED"


class TokenType(str, Enum):
    NONE = "NONE"
    VAULT_TOKEN = "VAULT_TOKEN"
    NETWORK_TOKEN = "NETWORK_TOKEN"
    WALLET_TOKEN = "WALLET_TOKEN"


class LiabilityOwner(str, Enum):
    MERCHANT = "MERCHANT"
    ISSUER = "ISSUER"
    ACQUIRER_OR_PAYFAC = "ACQUIRER_OR_PAYFAC"
    SHARED = "SHARED"
    UNDETERMINED = "UNDETERMINED"


class PaymentRiskContext(BaseModel):
    """Synthetic decision-time context for a payment-risk assessment.

    The schema is intentionally provider-neutral. It models evidence that can be
    available at checkout, authentication, authorization, capture, payout,
    settlement, refund, and dispute stages without assuming a production PSP API.
    """

    model_config = ConfigDict(extra="forbid")

    transaction_id: str = "DEMO-TXN"
    customer_id: str = "DEMO-CUSTOMER"
    merchant_id: str = "DEMO-MERCHANT"
    amount: float = Field(default=100.0, ge=0)
    currency: str = "USD"
    channel: Literal["ecommerce", "mobile", "pos", "a2a", "wallet", "stablecoin"] = "ecommerce"
    cross_border: bool = False
    digital_goods: bool = False

    # Credential, device, and card-testing evidence.
    new_device: bool = False
    proxy_or_datacenter_ip: bool = False
    ip_country_bin_mismatch: bool = False
    shipping_billing_mismatch: bool = False
    card_count_per_device_10m: int = Field(default=1, ge=0)
    authorization_attempts_10m: int = Field(default=1, ge=0)
    small_authorization_count_10m: int = Field(default=0, ge=0)
    decline_ratio_10m: float = Field(default=0.0, ge=0, le=1)
    amount_step_up_ratio: float = Field(default=1.0, ge=0)
    token_type: TokenType = TokenType.NONE
    cryptogram_valid: bool | None = None
    credential_age_days: int | None = Field(default=None, ge=0)

    # Authentication and issuer authorization are deliberately separate.
    three_ds_result: ThreeDSResult = ThreeDSResult.NOT_REQUESTED
    liability_shift: bool = False
    issuer_authorized: bool | None = None
    issuer_response_code: str | None = None
    soft_decline: bool = False
    hard_decline: bool = False
    retry_count: int = Field(default=0, ge=0)
    retry_interval_seconds: int | None = Field(default=None, ge=0)

    # Account-takeover and scam indicators.
    recent_password_or_2fa_change: bool = False
    first_beneficiary: bool = False
    beneficiary_risk_score: float = Field(default=0.0, ge=0, le=1)
    customer_confirmed_social_engineering: bool = False
    trusted_device_history_days: int = Field(default=180, ge=0)

    # Merchant, fulfillment, refund, and dispute evidence.
    merchant_risk_score: float = Field(default=0.0, ge=0, le=1)
    merchant_age_days: int = Field(default=365, ge=0)
    expected_volume_gap: float = Field(default=1.0, ge=0)
    product_mcc_mismatch: bool = False
    descriptor_website_mismatch: bool = False
    refund_ratio_30d: float = Field(default=0.0, ge=0, le=1)
    chargeback_ratio_90d: float = Field(default=0.0, ge=0, le=1)
    reserve_coverage_ratio: float = Field(default=1.0, ge=0)
    settlement_exposure: float = Field(default=0.0, ge=0)
    prior_dispute_count_180d: int = Field(default=0, ge=0)
    refund_to_alternative_instrument: bool = False
    delivery_evidence: bool = False
    digital_usage_evidence: bool = False
    consent_evidence: bool = False
    cancellation_evidence: bool = False
    communication_evidence: bool = False
    recurring_notice_sent: bool = False
    easy_cancellation_available: bool = True
    merchant_initiated_transaction: bool = False
    credential_on_file: bool = False

    # Payout, API, DCC, agentic-commerce, and stablecoin overlays.
    payout_fan_in_24h: int = Field(default=0, ge=0)
    payout_fan_out_24h: int = Field(default=0, ge=0)
    fund_stay_minutes_median: float = Field(default=1440.0, ge=0)
    new_payout_account: bool = False
    idempotency_key_reused_with_different_payload: bool = False
    duplicate_webhook_count: int = Field(default=0, ge=0)
    dcc_applied: bool = False
    dcc_explicit_consent: bool = False
    fx_disclosure_present: bool = True
    agentic_payment: bool = False
    delegated_spend_limit: float | None = Field(default=None, ge=0)
    human_approval_present: bool = False
    token_scope_risk: float = Field(default=0.0, ge=0, le=1)
    agent_identity_assurance: float = Field(default=1.0, ge=0, le=1)
    stablecoin_payment: bool = False
    stablecoin_issuer_risk: float = Field(default=0.0, ge=0, le=1)
    wallet_address_risk: float = Field(default=0.0, ge=0, le=1)
    sanctioned_address_hit: bool = False
    smart_contract_risk: float = Field(default=0.0, ge=0, le=1)
    liquidity_fx_exposure: float = Field(default=0.0, ge=0, le=1)
    reconciliation_break_count: int = Field(default=0, ge=0)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("currency must not be empty")
        return value


class ScenarioFinding(BaseModel):
    scenario_id: PaymentScenarioId
    score: float = Field(ge=0, le=100)
    evidence: list[str] = Field(default_factory=list)
    controls: list[PaymentControl] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    explanation: str


class LiabilityAssessment(BaseModel):
    likely_owner: LiabilityOwner
    liability_shift_recognized: bool
    rationale: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Prototype responsibility analysis only; network rules, local law, contract terms, "
        "reason code, and evidence timing must be checked before a real dispute decision."
    )


class PaymentRiskAssessment(BaseModel):
    transaction_id: str
    score: float = Field(ge=0, le=100)
    decision: PaymentDecision
    findings: list[ScenarioFinding] = Field(default_factory=list)
    recommended_controls: list[PaymentControl] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    liability: LiabilityAssessment
    stablecoin_overlay: dict[str, Any] = Field(default_factory=dict)
    human_review_required: bool = True
    automatic_enforcement_performed: bool = False
    production_connection: bool = False
    synthetic_demo: bool = True


class DisputeEvidenceResult(BaseModel):
    reason_code_family: str
    required_items: list[str]
    present_items: list[str]
    missing_items: list[str]
    completeness_score: float = Field(ge=0, le=1)
    expected_recovery: float = Field(ge=0)
    operating_cost: float = Field(ge=0)
    expected_net_value: float
    recommendation: Literal[
        "REPRESENTMENT_CANDIDATE",
        "COLLECT_MORE_EVIDENCE",
        "ACCEPT_OR_REFUND",
        "MANUAL_REVIEW_REQUIRED",
    ]
    human_review_required: bool = True
    rationale: list[str] = Field(default_factory=list)


class StateTransitionResult(BaseModel):
    machine: str
    from_state: str
    to_state: str
    accepted: bool
    terminal_before: bool
    reason: str


class PaymentReadySuiteResult(BaseModel):
    schema_version: str = "payment_ready_suite.v1"
    assessments: list[PaymentRiskAssessment]
    dispute_evidence: list[DisputeEvidenceResult]
    state_machine_checks: dict[str, list[StateTransitionResult]]
    artifacts: dict[str, str] = Field(default_factory=dict)
    boundary: dict[str, Any] = Field(
        default_factory=lambda: {
            "synthetic_data_only": True,
            "production_connection": False,
            "automatic_enforcement": False,
            "automatic_regulatory_submission": False,
            "payment_extension_is_post_internship_research": True,
        }
    )
