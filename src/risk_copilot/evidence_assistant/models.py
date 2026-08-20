from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class EvidenceLevel(str, Enum):
    INTERNSHIP_DIRECT = "A_direct_internship"
    TEAM_SYSTEM = "B_team_system"
    PERSONAL_PROTOTYPE = "C_personal_prototype"
    EXTERNAL_RESEARCH = "D_external_research"


class GateStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class LifecycleStatus(str, Enum):
    DRAFT = "DRAFT"
    DATA_READY = "DATA_READY"
    OFFLINE_BACKTEST = "OFFLINE_BACKTEST"
    SHADOW = "SHADOW"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    PAUSED = "PAUSED"
    RETIRED = "RETIRED"


class AssistantDecision(str, Enum):
    PROCEED_TO_DATA_AUDIT = "PROCEED_TO_DATA_AUDIT"
    PROCEED_TO_OFFLINE_BACKTEST = "PROCEED_TO_OFFLINE_BACKTEST"
    REVISE_PROBLEM_DEFINITION = "REVISE_PROBLEM_DEFINITION"
    REVISE_DATA_OR_LABELS = "REVISE_DATA_OR_LABELS"
    HOLD_FOR_OWNER_DECISION = "HOLD_FOR_OWNER_DECISION"


class SourceEvidence(BaseModel):
    evidence_id: str
    title: str
    evidence_level: EvidenceLevel
    source_type: Literal["ocr", "txt", "github", "external"]
    scope: str
    supports: list[str] = Field(default_factory=list)
    public_boundary: str


class ProblemLayer(BaseModel):
    order: int = Field(ge=1)
    layer: str
    core_question: str
    answer_template: str
    required_evidence: list[str] = Field(default_factory=list)
    output_object: str


class ModelAnalysisStep(BaseModel):
    order: int = Field(ge=1)
    step: str
    objective: str
    required_checks: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    decision_standard: list[str] = Field(default_factory=list)
    output: str
    failure_action: str


class DeliveryStage(BaseModel):
    order: int = Field(ge=1)
    stage: str
    owner: str
    collaborators: list[str] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    required_outputs: list[str] = Field(default_factory=list)
    exit_gate: list[str] = Field(default_factory=list)
    rollback_to: str | None = None


class FeatureFamilyRecommendation(BaseModel):
    family: str
    business_hypothesis: str
    candidate_features: list[str] = Field(default_factory=list)
    aggregation_or_transformation: list[str] = Field(default_factory=list)
    decision_time_requirement: str = "available_at_or_before_event"
    model_role: str
    false_positive_controls: list[str] = Field(default_factory=list)


class DistributionCheck(BaseModel):
    dataset: str
    check_id: str
    description: str
    status: GateStatus
    observed: Any = None
    expected: Any = None
    critical: bool = False
    notes: list[str] = Field(default_factory=list)


class DistributionAudit(BaseModel):
    profile_version: str
    overall_status: GateStatus
    checks: list[DistributionCheck] = Field(default_factory=list)
    passed: int = 0
    watched: int = 0
    failed: int = 0
    disclaimer: str

    @model_validator(mode="after")
    def derive_counts(self) -> "DistributionAudit":
        self.passed = sum(item.status == GateStatus.PASS for item in self.checks)
        self.watched = sum(item.status == GateStatus.WATCH for item in self.checks)
        self.failed = sum(item.status == GateStatus.FAIL for item in self.checks)
        if any(item.status == GateStatus.FAIL and item.critical for item in self.checks):
            self.overall_status = GateStatus.FAIL
        elif any(item.status in {GateStatus.FAIL, GateStatus.WATCH} for item in self.checks):
            self.overall_status = GateStatus.WATCH
        else:
            self.overall_status = GateStatus.PASS
        return self


class LabelMaturitySummary(BaseModel):
    cutoff_date: str
    total_rows: int
    ground_truth_positive_rate: float
    investigation_selected_rate: float
    mature_label_rate: float
    observed_positive_rate_among_mature: float | None = None
    pending_label_rate: float
    inconclusive_rate: float
    notes: list[str] = Field(default_factory=list)


class StrategyDesignObject(BaseModel):
    strategy_id: str
    name: str
    event_code: str
    risk_domain: str
    population: str
    hypothesis: str
    feature_families: list[str]
    window_policy: str
    threshold_policy: str
    exclusions: list[str]
    recommended_action: str
    action_precedence: list[str]
    evaluation_metrics: list[str]
    monitoring_metrics: list[str]
    rollback_conditions: list[str]
    lifecycle_status: LifecycleStatus = LifecycleStatus.DRAFT
    human_review_required: bool = True


class AssistantRequest(BaseModel):
    request_id: str
    query: str
    business_objective: str
    risk_domain: str = "fund_security"
    event_code: str = "ChainWithdraw"
    target_label: str = "fraud_label"
    maximum_alert_rate: float = Field(default=0.05, gt=0, le=1)
    minimum_precision: float = Field(default=0.50, ge=0, le=1)
    minimum_recall: float = Field(default=0.05, ge=0, le=1)
    review_capacity: int = Field(default=300, gt=0)
    preferred_actions: list[str] = Field(default_factory=lambda: ["MANUAL_REVIEW", "RFI"])
    notes: list[str] = Field(default_factory=list)


class EvidenceGroundedPlan(BaseModel):
    schema_version: str = "evidence_grounded_strategy_plan.v1"
    request: AssistantRequest
    inferred_scenario: str
    decision: AssistantDecision
    problem_decomposition: list[ProblemLayer]
    evidence_map: list[SourceEvidence]
    feature_families: list[FeatureFamilyRecommendation]
    model_analysis_playbook: list[ModelAnalysisStep]
    strategy_design: StrategyDesignObject
    strategy_lifecycle: list[LifecycleStatus]
    delivery_workflow: list[DeliveryStage]
    distribution_audit: DistributionAudit | None = None
    label_maturity: LabelMaturitySummary | None = None
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    truthfulness_boundary: list[str] = Field(default_factory=list)
