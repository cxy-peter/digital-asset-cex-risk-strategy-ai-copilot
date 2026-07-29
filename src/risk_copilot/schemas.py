from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RiskDomain(str, Enum):
    ACCOUNT_SECURITY = "account_security"
    TRANSACTION_SECURITY = "transaction_security"
    FUND_SECURITY = "fund_security"
    AML_COMPLIANCE = "aml_compliance"
    MARKETING_ABUSE = "marketing_abuse"
    MERCHANT_KYB = "merchant_kyb"
    REGULATORY_OPERATIONS = "regulatory_operations"
    CREDIT_RISK = "credit_risk"
    PAYMENT_FRAUD = "payment_fraud"


class StrategyStatus(str, Enum):
    DRAFT = "DRAFT"
    SIMULATION = "SIMULATION"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    ONLINE = "ONLINE"
    PAUSED = "PAUSED"
    RETIRED = "RETIRED"


class ActionType(str, Enum):
    PASS = "PASS"
    MONITOR = "MONITOR"
    ALERT = "ALERT"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    RFI = "RFI"
    EDD = "EDD"
    VIDEO_KYC = "VIDEO_KYC"
    DELAY = "DELAY"
    DAILY_LIMIT = "DAILY_LIMIT"
    WITHDRAWAL_RESTRICTION = "WITHDRAWAL_RESTRICTION"
    TRANSACTION_RESTRICTION = "TRANSACTION_RESTRICTION"
    FREEZE = "FREEZE"
    REJECT = "REJECT"
    ESCALATE_COMPLIANCE = "ESCALATE_COMPLIANCE"


class FeatureType(str, Enum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    GRAPH = "graph"
    TEXT = "text"


class FeatureFreshness(str, Enum):
    REALTIME = "realtime"
    H1 = "h+1"
    T1 = "t+1"
    OFFLINE = "offline"


class FeatureSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    display_name: str
    description: str
    domain: RiskDomain
    dtype: FeatureType
    freshness: FeatureFreshness
    source: str
    event_codes: list[str] = Field(default_factory=list)
    available_at: str = "decision_time"
    pii_level: Literal["none", "low", "restricted"] = "none"
    default_operator: str | None = None
    expected_direction: Literal["higher_risk", "lower_risk", "non_monotonic", "unknown"] = "unknown"
    tags: list[str] = Field(default_factory=list)


class EventSpec(BaseModel):
    code: str
    display_name: str
    stage: str
    domain: RiskDomain
    description: str
    available_features: list[str]
    allowed_actions: list[ActionType]
    latency_requirement: FeatureFreshness


class ContractIssue(BaseModel):
    severity: Literal["error", "warning", "info"]
    code: str
    message: str
    event_code: str | None = None
    feature_name: str | None = None


class EventContract(BaseModel):
    contract_version: str
    contract_hash: str
    event: EventSpec
    features: list[FeatureSpec]
    validation_issues: list[ContractIssue] = Field(default_factory=list)


class ContractValidationReport(BaseModel):
    valid: bool
    event_count: int
    feature_count: int
    error_count: int
    warning_count: int
    issues: list[ContractIssue] = Field(default_factory=list)
    event_contract_hashes: dict[str, str] = Field(default_factory=dict)


class Condition(BaseModel):
    feature: str
    operator: Literal[
        ">", ">=", "<", "<=", "==", "!=", "in", "not_in", "between", "is_true", "is_false"
    ]
    value: Any = None

    @model_validator(mode="after")
    def validate_value(self) -> "Condition":
        if self.operator in {"is_true", "is_false"}:
            return self
        if self.value is None:
            raise ValueError(f"operator {self.operator} requires a value")
        if self.operator == "between" and (not isinstance(self.value, list) or len(self.value) != 2):
            raise ValueError("between requires a two-element list")
        if self.operator in {"in", "not_in"} and not isinstance(self.value, list):
            raise ValueError(f"{self.operator} requires a list")
        return self


class RuleGroup(BaseModel):
    logic: Literal["AND", "OR"] = "AND"
    conditions: list[Condition] = Field(default_factory=list)
    groups: list["RuleGroup"] = Field(default_factory=list)

    @model_validator(mode="after")
    def not_empty(self) -> "RuleGroup":
        if not self.conditions and not self.groups:
            raise ValueError("a rule group must include at least one condition or nested group")
        return self


class StrategyCandidate(BaseModel):
    strategy_id: str
    name: str
    domain: RiskDomain
    event_code: str
    description: str
    rule: RuleGroup
    action: ActionType
    action_params: dict[str, Any] = Field(default_factory=dict)
    source: Literal["expert", "tree", "quantile", "graph", "model_score", "ai_planner", "llm"] = "expert"
    rationale: list[str] = Field(default_factory=list)
    required_features: list[str] = Field(default_factory=list)
    status: StrategyStatus = StrategyStatus.DRAFT
    tags: list[str] = Field(default_factory=list)
    tag_level_1: str = "unclassified"
    tag_level_2: str = "unclassified"
    tag_level_3: str = "MANUAL_REVIEW"


class BacktestMetrics(BaseModel):
    sample_size: int
    positives: int
    alerts: int
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int
    precision: float
    recall: float
    f1: float
    false_positive_rate: float
    alert_rate: float
    lift: float
    captured_loss_rate: float
    alert_amount: float
    captured_loss_amount: float
    monthly_precision_std: float
    monthly_alert_rate_std: float
    stability_score: float
    explainability_score: float
    operational_score: float
    reward: float = 0.0
    relative_advantage: float = 0.0


class ModelMetrics(BaseModel):
    model_name: str
    roc_auc: float
    ks: float
    average_precision: float
    precision: float
    recall: float
    f1: float
    false_positive_rate: float
    threshold: float
    lift_top_10: float
    train_size: int
    test_size: int


class FeatureProfile(BaseModel):
    feature: str
    dtype: str
    missing_rate: float
    unique_count: int
    auc_1d: float | None = None
    ks_1d: float | None = None
    iv: float | None = None
    lift_top_10: float | None = None
    cramer_v: float | None = None
    psi: float | None = None
    direction: str = "unknown"
    recommended: bool = False
    notes: list[str] = Field(default_factory=list)


class AgentActionLog(BaseModel):
    agent: str
    tool: str
    status: Literal["success", "failure", "skipped"]
    started_at: datetime
    duration_ms: float
    input_summary: dict[str, Any] = Field(default_factory=dict)
    output_summary: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class AgentResult(BaseModel):
    agent: str
    summary: str
    structured_output: dict[str, Any] = Field(default_factory=dict)
    citations: list[str] = Field(default_factory=list)
    actions: list[AgentActionLog] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AgentRunEnvelope(BaseModel):
    run_id: str
    agent: str
    phase: str
    status: Literal["succeeded", "failed", "degraded", "timed_out", "skipped"]
    critical: bool
    started_at: datetime
    completed_at: datetime
    duration_ms: float
    action_count: int = 0
    warning_count: int = 0
    error_type: str | None = None
    error: str | None = None


class ReviewerFinding(BaseModel):
    category: str
    severity: Literal["low", "medium", "high", "critical"]
    statement: str
    evidence_refs: list[str] = Field(default_factory=list)


class ReviewerBundle(BaseModel):
    reviewer: str
    status: Literal["succeeded", "degraded", "failed", "timed_out"]
    summary: str
    findings: list[ReviewerFinding] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    revisions: list[str] = Field(default_factory=list)
    acceptance_tests: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    attempts: int = 1
    latency_ms: float = 0.0
    error: str | None = None
    raw_text: str | None = None


class StrategyRequest(BaseModel):
    request_id: str
    query: str
    domain: RiskDomain | None = None
    event_code: str | None = None
    target_label: str = "fraud_label"
    max_alert_rate: float = Field(default=0.05, gt=0, le=1)
    minimum_precision: float = Field(default=0.50, ge=0, le=1)
    minimum_recall: float = Field(default=0.05, ge=0, le=1)
    review_capacity: int = Field(default=300, gt=0)
    preferred_actions: list[ActionType] = Field(default_factory=lambda: [ActionType.MANUAL_REVIEW, ActionType.RFI])
    require_human_review: bool = True


class GovernanceDecision(BaseModel):
    strategy_id: str
    current_status: StrategyStatus
    next_status: StrategyStatus
    decision: Literal["approve", "reject", "revise", "hold"]
    reasons: list[str]
    required_approvals: list[str]
    blocked_actions: list[ActionType] = Field(default_factory=list)
    audit_fields: dict[str, Any] = Field(default_factory=dict)


class StrategyPackage(BaseModel):
    request: StrategyRequest
    selected_strategy: StrategyCandidate
    selected_metrics: BacktestMetrics
    alternatives: list[tuple[StrategyCandidate, BacktestMetrics]]
    model_benchmarks: list[ModelMetrics]
    feature_profiles: list[FeatureProfile]
    agent_results: list[AgentResult]
    governance: GovernanceDecision
    engine_payload: dict[str, Any]
    product_context: dict[str, Any] = Field(default_factory=dict)
    risk_scoring: dict[str, Any] = Field(default_factory=dict)
    disposition_plan: dict[str, Any] = Field(default_factory=dict)
    registry_record: dict[str, Any] = Field(default_factory=dict)
    strategy_test_environment: dict[str, Any] = Field(default_factory=dict)
    effectiveness_ticket: dict[str, Any] = Field(default_factory=dict)
    cms_str_integration: dict[str, Any] = Field(default_factory=dict)
    stability_analysis: dict[str, Any] = Field(default_factory=dict)
    conflict_analysis: dict[str, Any] = Field(default_factory=dict)
    ai_advisory_board: dict[str, Any] = Field(default_factory=dict)
    evaluation_context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data_disclaimer: str = "All included records and metrics are synthetic or aggregated demo data."



class RiskProductSpec(BaseModel):
    product_id: str
    name: str
    layer: str
    purpose: str
    capabilities: list[str] = Field(default_factory=list)
    data_objects: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    event_codes: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    source_evidence: list[str] = Field(default_factory=list)
    prototype_status: Literal["implemented", "modeled", "catalog_only"] = "catalog_only"


class KnowledgeScenario(BaseModel):
    scenario_id: str
    industry: Literal["banking", "digital_asset"]
    business_line: str
    event_stage: str
    risk_domain: RiskDomain
    risk_types: list[str]
    definition: str
    attacker_profiles: list[str]
    black_grey_tools: list[str]
    attack_preferences: list[str]
    manifestations: list[str]
    data_sources: list[str]
    candidate_features: list[str]
    expert_rules: list[str]
    recommended_models: list[str]
    model_tradeoffs: dict[str, str]
    actions: list[ActionType]
    monitoring_metrics: list[str]



class ComplianceAnswer(BaseModel):
    schema_version: str = "compliance_answer.v1"
    question: str
    answer: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    retrieval_scores: list[float] = Field(default_factory=list)
    groundedness_score: float = Field(ge=0, le=1)
    abstained: bool = False
    uncertainty: str | None = None
    access_scope: str = "compliance_internal"



class CompanyTestStage(BaseModel):
    name: Literal[
        "feature_contract_validation",
        "historical_backtest",
        "simulation_execution",
        "independent_second_review",
        "release_readiness",
        "post_launch_observation",
        "weekly_monthly_effectiveness_review",
    ]
    status: Literal["completed", "blocked", "pending", "ready", "not_started"]
    entry_gates: list[str] = Field(default_factory=list)
    exit_gates: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class StrategyTestPlan(BaseModel):
    schema_version: str = "cointr_strategy_test_plan.v1"
    test_run_id: str
    strategy_id: str
    strategy_version: int
    data_snapshot_id: str
    event_contract_hash: str
    feature_catalog_version: str
    payload_hash: str
    current_stage: str
    release_status: Literal[
        "REVISION_REQUIRED",
        "PENDING_SECOND_REVIEW",
        "READY_FOR_RELEASE_REVIEW",
        "POST_LAUNCH_OBSERVATION",
        "ACTIVE",
        "ROLLBACK_REQUIRED",
    ]
    stages: list[CompanyTestStage]
    required_approvals: list[str]
    monitoring_workdays: int = 3
    monitoring_metrics: list[str] = Field(default_factory=list)
    rollback_thresholds: dict[str, float] = Field(default_factory=dict)
    blockers: list[str] = Field(default_factory=list)
    production_connection: bool = False
    dispatch_performed: bool = False
    direct_production_release: bool = False


class StrategyEffectivenessTicket(BaseModel):
    schema_version: str = "strategy_effectiveness_ticket.v1"
    ticket_id: str
    strategy_id: str
    strategy_version: int
    test_run_id: str
    data_snapshot_id: str
    evaluation_phase: Literal["SIMULATION", "POST_LAUNCH_3D", "WEEKLY", "MONTHLY"]
    environment: Literal["synthetic_test", "production"] = "synthetic_test"
    label: Literal[
        "EFFECTIVE",
        "PARTIALLY_EFFECTIVE",
        "INEFFECTIVE",
        "FALSE_POSITIVE_HEAVY",
        "INSUFFICIENT_SAMPLE",
        "NEEDS_THRESHOLD_ADJUSTMENT",
        "DATA_QUALITY_ISSUE",
        "STRATEGY_CONFLICT",
    ]
    metrics: dict[str, float | int | None]
    labeler: str
    observation_start: str
    observation_end: str
    evidence_refs: list[str] = Field(default_factory=list)
    recommendation: str
    status: Literal["OPEN", "PENDING_REVIEW", "CONFIRMED", "CLOSED"] = "OPEN"
    synthetic_demo: bool = True


class CMSSTRCasePreview(BaseModel):
    schema_version: str = "cms_str_case_preview.v1"
    case_id: str
    dedup_key: str
    user_id: str
    strategy_id: str
    strategy_version: int
    event_code: str
    strategy_tag_level_3: str
    status: Literal[
        "DRAFT_CASE",
        "PENDING_COMPLIANCE_REVIEW",
        "NEEDS_INFORMATION",
        "READY_FOR_STR_DECISION",
        "CLOSED_NO_STR",
        "STR_APPROVED_INTERNAL",
    ] = "DRAFT_CASE"
    masak_feedback_status: Literal[
        "NOT_SUBMITTED",
        "SUBMITTED_PENDING",
        "ACCEPTED",
        "REJECTED",
        "NEEDS_CORRECTION",
    ] = "NOT_SUBMITTED"
    feature_snapshot: dict[str, Any] = Field(default_factory=dict)
    strategy_expression: str
    risk_history_summary: dict[str, Any] = Field(default_factory=dict)
    graph_path_summary: dict[str, Any] = Field(default_factory=dict)
    evidence_hash: str
    human_review_required: bool = True
    external_submission_allowed: bool = False
    automatic_filing_performed: bool = False


RuleGroup.model_rebuild()
