from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ..config import load_yaml
from ..schemas import BacktestMetrics, CompanyTestStage, GovernanceDecision, StrategyCandidate, StrategyTestPlan


@dataclass
class CompanyStrategyTestPlanner:
    """Reconstruct the company-style Rule Engine/FEP strategy test environment.

    This is intentionally different from a generic software canary deployment flow.  The main
    controls are feature-contract validation, historical backtesting, simulation, an independent
    second review, a three-working-day post-launch observation template, and recurring
    effectiveness tickets.  The prototype never connects to production.
    """

    config_path: str | Path

    def __post_init__(self) -> None:
        self.config: dict[str, Any] = load_yaml(self.config_path)

    @staticmethod
    def stable_hash(value: Mapping[str, Any] | dict[str, Any]) -> str:
        canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def build_plan(
        self,
        *,
        strategy: StrategyCandidate,
        strategy_version: int,
        engine_payload: dict[str, Any],
        metrics: BacktestMetrics,
        governance: GovernanceDecision,
        data_snapshot_id: str,
        feature_catalog_version: str,
        stability_analysis: dict[str, Any] | None = None,
        conflict_analysis: dict[str, Any] | None = None,
        ai_advisory_board: dict[str, Any] | None = None,
    ) -> StrategyTestPlan:
        payload_hash = self.stable_hash(engine_payload)
        test_run_id = f"TESTRUN-{strategy.strategy_id}-{strategy_version:03d}-{payload_hash[:8]}"
        blockers: list[str] = []

        contract_ok = governance.audit_fields.get("event_contract_error_count", 1) == 0
        if not contract_ok:
            blockers.append("event_or_feature_contract_invalid")
        backtest_ok = metrics.sample_size >= 200 and metrics.alerts >= 1
        if not backtest_ok:
            blockers.append("historical_backtest_insufficient")
        simulation_ok = governance.decision == "approve" and governance.next_status.value == "PENDING_REVIEW"
        if not simulation_ok:
            blockers.append("simulation_gates_failed")

        stability_analysis = stability_analysis or {}
        conflict_analysis = conflict_analysis or {}
        ai_advisory_board = ai_advisory_board or {}
        stability_status = str(stability_analysis.get("status", "UNKNOWN"))
        conflict_recommendation = str(conflict_analysis.get("recommendation", "UNKNOWN"))
        action_conflict_count = int(conflict_analysis.get("action_conflict_count", 0) or 0)
        if stability_status == "UNSTABLE":
            blockers.append("cross_month_or_bootstrap_stability_failed")
        if conflict_recommendation == "REJECT_DUPLICATE":
            blockers.append("candidate_duplicates_existing_strategy_portfolio")

        second_review_ready = (
            contract_ok
            and backtest_ok
            and simulation_ok
            and stability_status != "UNSTABLE"
            and conflict_recommendation != "REJECT_DUPLICATE"
        )
        release_status = "PENDING_SECOND_REVIEW" if second_review_ready else "REVISION_REQUIRED"
        current_stage = "independent_second_review" if second_review_ready else "simulation_execution"

        stages = [
            CompanyTestStage(
                name="feature_contract_validation",
                status="completed" if contract_ok else "blocked",
                entry_gates=["registered event code", "registered decision-time features"],
                exit_gates=["event contract has zero blocking errors", "feature lineage is recorded"],
                evidence_refs=[governance.audit_fields.get("event_contract_hash", "")],
            ),
            CompanyTestStage(
                name="historical_backtest",
                status="completed" if backtest_ok else "blocked",
                entry_gates=["frozen Train/Development/OOT split", "mature point-in-time labels"],
                exit_gates=["OOT metrics generated", "alert volume and review capacity checked"],
                evidence_refs=[data_snapshot_id],
            ),
            CompanyTestStage(
                name="simulation_execution",
                status="completed" if simulation_ok else "blocked",
                entry_gates=["historical backtest completed", "engine payload confirmed"],
                exit_gates=["simulation metrics satisfy governance thresholds", "no production mutation"],
                evidence_refs=[test_run_id],
            ),
            CompanyTestStage(
                name="independent_second_review",
                status="ready" if second_review_ready else "blocked",
                entry_gates=["risk-strategy reviewer independent from creator", "exact version and payload hash bound"],
                exit_gates=["reviewer 1 approved", "reviewer 2 approved", "high-impact action compliance review if needed"],
                evidence_refs=[payload_hash],
            ),
            CompanyTestStage(
                name="release_readiness",
                status="pending" if second_review_ready else "blocked",
                entry_gates=["two-person review completed", "rollback and monitoring plan confirmed"],
                exit_gates=["release owner confirms execution window", "strategy ticket created"],
                evidence_refs=[],
            ),
            CompanyTestStage(
                name="post_launch_observation",
                status="not_started",
                entry_gates=["release completed outside this prototype", "first three working days observation enabled"],
                exit_gates=["false positives, user feedback, business metrics and feature PSI reviewed"],
                evidence_refs=[],
            ),
            CompanyTestStage(
                name="weekly_monthly_effectiveness_review",
                status="pending",
                entry_gates=["effectiveness ticket linked to strategy version"],
                exit_gates=["retain, tune, pause or retire decision recorded"],
                evidence_refs=[],
            ),
        ]
        thresholds = self.config.get("release_controls", {}).get("rollback_thresholds", {})
        required_approvals = list(dict.fromkeys(governance.required_approvals + ["independent_second_reviewer"]))
        if action_conflict_count:
            required_approvals.append("strategy_action_precedence_reviewer")
        if stability_status == "WATCH":
            required_approvals.append("model_stability_reviewer")
        if ai_advisory_board.get("decision") in {"REVISE", "REJECT_AS_DUPLICATE"}:
            required_approvals.append("ai_advisory_findings_owner")
        required_approvals = list(dict.fromkeys(required_approvals))

        # Action conflicts are conditions for second review rather than automatic blockers. The
        # human reviewer must resolve precedence before release readiness.
        for stage in stages:
            if stage.name == "independent_second_review" and action_conflict_count:
                stage.exit_gates.append("strategy action precedence conflict resolved")
                stage.evidence_refs.append("strategy_conflict_analysis")
            if stage.name == "independent_second_review" and ai_advisory_board:
                stage.evidence_refs.append("ai_advisory_board")
            if stage.name == "historical_backtest" and stability_analysis:
                stage.evidence_refs.append("strategy_stability_analysis")

        return StrategyTestPlan(
            test_run_id=test_run_id,
            strategy_id=strategy.strategy_id,
            strategy_version=strategy_version,
            data_snapshot_id=data_snapshot_id,
            event_contract_hash=governance.audit_fields.get("event_contract_hash", ""),
            feature_catalog_version=feature_catalog_version,
            payload_hash=payload_hash,
            current_stage=current_stage,
            release_status=release_status,
            stages=stages,
            required_approvals=required_approvals,
            monitoring_workdays=int(self.config.get("release_controls", {}).get("post_launch_initial_observation_workdays", 3)),
            monitoring_metrics=list(self.config.get("release_controls", {}).get("rollback_metrics", [])),
            rollback_thresholds={str(k): float(v) for k, v in thresholds.items()},
            blockers=blockers,
        )
