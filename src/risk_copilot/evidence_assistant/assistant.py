from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .distribution import LabelMaturitySimulator, SyntheticDistributionAuditor
from .models import AssistantRequest, EvidenceGroundedPlan, GateStatus
from .playbook import (
    build_existing_strategy_request_payload,
    build_problem_decomposition,
    build_strategy_design,
    choose_initial_decision,
    delivery_workflow,
    feature_families_for,
    infer_scenario,
    lifecycle,
    model_analysis_playbook,
    source_evidence,
)


@dataclass
class EvidenceGroundedStrategyAssistant:
    """Upstream planning layer for the existing deterministic Risk Strategy Copilot.

    It adds source-grounded problem decomposition, label realism, distribution checks, model-analysis
    standards and the complete product-delivery workflow. It never publishes raw OCR/TXT materials,
    trains on future labels, changes a strategy status or executes a user action.
    """

    project_root: Path
    assistant_config: dict[str, Any]
    distribution_auditor: SyntheticDistributionAuditor

    @classmethod
    def create(cls, project_root: str | Path | None = None) -> "EvidenceGroundedStrategyAssistant":
        root = Path(project_root or Path(__file__).resolve().parents[3]).resolve()
        with (root / "configs" / "evidence_strategy_assistant.yaml").open("r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle)
        return cls(project_root=root, assistant_config=config, distribution_auditor=SyntheticDistributionAuditor.from_yaml(root / "configs" / "synthetic_distribution_profile.yaml"))

    def run(self, request: AssistantRequest, *, audit_demo_data: bool = True, simulate_label_maturity: bool = True, output_dir: str | Path | None = None) -> tuple[EvidenceGroundedPlan, dict[str, Path]]:
        audit = None
        maturity = None
        maturity_frame: pd.DataFrame | None = None
        data_dir = self.project_root / "data" / "demo"
        if audit_demo_data:
            audit = self.distribution_auditor.audit_directory(data_dir)
        if simulate_label_maturity and (data_dir / "users.csv").exists():
            users = pd.read_csv(data_dir / "users.csv", parse_dates=["event_date"], low_memory=False)
            maturity_frame, maturity = LabelMaturitySimulator().transform(users)
        plan = self.build_plan(request, distribution_audit=audit, label_maturity=maturity)
        return plan, self.write_outputs(plan, output_dir=output_dir, maturity_frame=maturity_frame)

    def build_plan(self, request: AssistantRequest, *, distribution_audit=None, label_maturity=None) -> EvidenceGroundedPlan:
        scenario = infer_scenario(request.query)
        families = feature_families_for(scenario)
        audit_failed = bool(distribution_audit is not None and distribution_audit.overall_status == GateStatus.FAIL)
        decision = choose_initial_decision(has_distribution_audit=distribution_audit is not None, audit_failed=audit_failed, missing_business_objective=not bool(request.business_objective.strip()))
        strengths = [
            "AI proposal/explanation is already separated from deterministic metrics and lifecycle control.",
            "The generator contains class imbalance, overlapping ATO/cashout/AML/campaign/graph mechanisms, long-tailed amounts and rare screening hits.",
            "Feature profiling calculates Development-only AUC, KS, IV, Lift and train-to-development PSI before OOT reporting.",
            "The strategy pipeline includes LR, shallow Tree, XGBoost, graph evidence, chronological OOT, stability, portfolio overlap and independent review.",
            "CMS/STR remains an internal candidate preview with human confirmation and no external filing.",
        ]
        gaps = [
            "The 5716 macro-to-micro reasoning was not previously a first-class output.",
            "The full demand-to-RCA delivery sequence was documented but not structured in the assistant.",
            "Synthetic distributions were intentional but not audited against a transparent profile contract.",
            "Hidden synthetic truth is cleaner than investigation-selected, delayed and sometimes inconclusive observed labels.",
            "Many snapshot counters are generated directly rather than recomputed from the event stream.",
        ]
        next_actions = [
            "Resolve critical synthetic-distribution mismatches before presenting demo metrics.",
            "Use the observed-label view for discovery and keep fraud_label as hidden evaluation truth.",
            "Feed strategy_request.json into the current RiskStrategyCopilot workflow.",
            "Freeze the candidate before OOT and review increment, action precedence and operations capacity.",
            "Recompute selected velocity, sequence and graph features from transactions.csv and reconcile them with snapshot counters.",
        ]
        return EvidenceGroundedPlan(
            request=request,
            inferred_scenario=scenario,
            decision=decision,
            problem_decomposition=build_problem_decomposition(request, scenario),
            evidence_map=source_evidence(),
            feature_families=families,
            model_analysis_playbook=model_analysis_playbook(),
            strategy_design=build_strategy_design(request, scenario, families),
            strategy_lifecycle=lifecycle(),
            delivery_workflow=delivery_workflow(),
            distribution_audit=distribution_audit,
            label_maturity=label_maturity,
            strengths=strengths,
            gaps=gaps,
            next_actions=next_actions,
            truthfulness_boundary=[str(item) for item in self.assistant_config.get("public_boundary", [])],
        )

    def write_outputs(self, plan: EvidenceGroundedPlan, *, output_dir: str | Path | None = None, maturity_frame: pd.DataFrame | None = None) -> dict[str, Path]:
        target = Path(output_dir or self.project_root / "outputs" / "evidence_strategy_assistant")
        target.mkdir(parents=True, exist_ok=True)
        paths = {
            "plan_json": target / "evidence_grounded_strategy_plan.json",
            "plan_markdown": target / "EVIDENCE_GROUNDED_STRATEGY_PLAN.md",
            "strategy_request": target / "strategy_request.json",
            "proposal_context": target / "proposal_context.json",
        }
        paths["plan_json"].write_text(plan.model_dump_json(indent=2), encoding="utf-8")
        paths["plan_markdown"].write_text(self.to_markdown(plan), encoding="utf-8")
        paths["strategy_request"].write_text(json.dumps(build_existing_strategy_request_payload(plan.request), ensure_ascii=False, indent=2), encoding="utf-8")
        context = {
            "schema_version": "evidence_strategy_context.v1",
            "scenario": plan.inferred_scenario,
            "problem_layers": [item.model_dump(mode="json") for item in plan.problem_decomposition],
            "feature_families": [item.model_dump(mode="json") for item in plan.feature_families],
            "strategy_design": plan.strategy_design.model_dump(mode="json"),
            "model_analysis_standards": [{"step": item.step, "decision_standard": item.decision_standard, "failure_action": item.failure_action} for item in plan.model_analysis_playbook],
            "evidence_ids": [item.evidence_id for item in plan.evidence_map],
            "guardrails": plan.truthfulness_boundary,
        }
        paths["proposal_context"].write_text(json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8")
        if plan.distribution_audit is not None:
            paths["distribution_audit"] = target / "synthetic_distribution_audit.json"
            paths["distribution_audit"].write_text(plan.distribution_audit.model_dump_json(indent=2), encoding="utf-8")
        if maturity_frame is not None:
            paths["label_maturity_preview"] = target / "label_maturity_preview.csv"
            columns = [col for col in ["user_id", "event_date", "risk_score_t1", "strategy_hit_count_30d", "investigation_selected_flag", "label_observed_at_simulated", "observed_label_status", "observed_fraud_label", "label_maturity_lag_days"] if col in maturity_frame]
            maturity_frame[columns].head(250).to_csv(paths["label_maturity_preview"], index=False)
        return paths

    @staticmethod
    def to_markdown(plan: EvidenceGroundedPlan) -> str:
        lines = [
            "# Evidence-Grounded CEX Risk Strategy Assistant",
            "",
            "> Public synthetic prototype. Raw OCR/TXT evidence is not included; evidence IDs are traceability references only.",
            "",
            "## 1. Request and decision",
            "",
            f"- Request ID: `{plan.request.request_id}`",
            f"- Inferred scenario: `{plan.inferred_scenario}`",
            f"- Event: `{plan.request.event_code}`",
            f"- Risk domain: `{plan.request.risk_domain}`",
            f"- Current assistant decision: `{plan.decision.value}`",
            f"- Business objective: {plan.request.business_objective}",
            "",
            "## 2. 5716 macro-to-micro decomposition",
            "",
        ]
        for item in plan.problem_decomposition:
            lines += [f"### {item.order}. {item.layer}", "", f"**Question:** {item.core_question}", "", f"**Interview-ready answer:** {item.answer_template}", "", f"**Required evidence:** {', '.join(item.required_evidence)}", "", f"**Output:** `{item.output_object}`", ""]
        lines += ["## 3. Recommended feature families", ""]
        for family in plan.feature_families:
            lines += [f"### {family.family}", "", family.business_hypothesis, "", f"- Candidate features: {', '.join(family.candidate_features)}", f"- Transformations: {', '.join(family.aggregation_or_transformation)}", f"- Model role: {family.model_role}", f"- False-positive controls: {', '.join(family.false_positive_controls)}", ""]
        lines += ["## 4. Model-analysis steps and standards", ""]
        for item in plan.model_analysis_playbook:
            lines += [f"### {item.order}. {item.step}", "", f"**Objective:** {item.objective}", "", f"- Checks: {'; '.join(item.required_checks)}", f"- Metrics: {', '.join(item.metrics)}", f"- Standards: {'; '.join(item.decision_standard)}", f"- Output: {item.output}", f"- Failure action: {item.failure_action}", ""]
        lines += ["## 5. Strategy object", "", "```json", json.dumps(plan.strategy_design.model_dump(mode="json"), ensure_ascii=False, indent=2), "```", "", "## 6. Full delivery workflow", ""]
        for stage in plan.delivery_workflow:
            lines += [f"### {stage.order}. {stage.stage}", "", f"- Owner: `{stage.owner}`", f"- Collaborators: {', '.join(stage.collaborators)}", f"- Inputs: {', '.join(stage.required_inputs)}", f"- Outputs: {', '.join(stage.required_outputs)}", f"- Exit gate: {'; '.join(stage.exit_gate)}", f"- Rollback: {stage.rollback_to or 'N/A'}", ""]
        if plan.distribution_audit is not None:
            audit = plan.distribution_audit
            lines += ["## 7. Synthetic-distribution audit", "", f"Overall status: `{audit.overall_status.value}`; PASS={audit.passed}, WATCH={audit.watched}, FAIL={audit.failed}", "", "| Dataset | Check | Status | Observed |", "|---|---|---:|---:|"]
            lines += [f"| {check.dataset} | {check.description} | {check.status.value} | {check.observed} |" for check in audit.checks]
            lines += ["", audit.disclaimer, ""]
        if plan.label_maturity is not None:
            maturity = plan.label_maturity
            lines += ["## 8. Simulated label maturity", "", f"- Cutoff: `{maturity.cutoff_date}`", f"- Hidden truth positive rate: {maturity.ground_truth_positive_rate:.4f}", f"- Investigation selected rate: {maturity.investigation_selected_rate:.4f}", f"- Mature observed-label rate: {maturity.mature_label_rate:.4f}", f"- Pending rate: {maturity.pending_label_rate:.4f}", f"- Inconclusive rate: {maturity.inconclusive_rate:.4f}", ""]
        lines += ["## 9. Current strengths", ""] + [f"- {item}" for item in plan.strengths]
        lines += ["", "## 10. Gaps", ""] + [f"- {item}" for item in plan.gaps]
        lines += ["", "## 11. Next actions", ""] + [f"- {item}" for item in plan.next_actions]
        lines += ["", "## 12. Truthfulness boundary", ""] + [f"- {item}" for item in plan.truthfulness_boundary] + [""]
        return "\n".join(lines)
