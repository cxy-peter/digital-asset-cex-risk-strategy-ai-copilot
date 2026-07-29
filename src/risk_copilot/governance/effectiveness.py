from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ..schemas import BacktestMetrics, StrategyEffectivenessTicket, StrategyTestPlan


@dataclass
class StrategyEffectivenessService:
    database_path: str | Path

    def __post_init__(self) -> None:
        self.database_path = Path(self.database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS effectiveness_tickets (
                    ticket_id TEXT PRIMARY KEY,
                    strategy_id TEXT NOT NULL,
                    strategy_version INTEGER NOT NULL,
                    test_run_id TEXT NOT NULL,
                    evaluation_phase TEXT NOT NULL,
                    label TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS strategy_observation_records (
                    observation_id TEXT PRIMARY KEY,
                    strategy_id TEXT NOT NULL,
                    strategy_version INTEGER NOT NULL,
                    test_run_id TEXT NOT NULL,
                    observation_date TEXT NOT NULL,
                    workday_index INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    record_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def classify(metrics: BacktestMetrics) -> tuple[str, str]:
        if metrics.sample_size < 200 or metrics.alerts < 5:
            return "INSUFFICIENT_SAMPLE", "扩大观察样本后再决定上线或阈值调整。"
        if metrics.false_positive_rate > 0.05 or (metrics.alerts and metrics.precision < 0.35):
            return "FALSE_POSITIVE_HEAVY", "收紧阈值、增加强关系或资金闭环条件，降低误伤。"
        if metrics.precision >= 0.65 and metrics.recall >= 0.25 and metrics.stability_score >= 0.70:
            return "EFFECTIVE", "保留候选方案并进入独立复核；上线后连续观察三个工作日。"
        if metrics.precision >= 0.50 and metrics.recall >= 0.10:
            return "PARTIALLY_EFFECTIVE", "策略方向有效，建议对阈值、标签和处置进行小步调整。"
        if metrics.recall < 0.10 and metrics.precision >= 0.50:
            return "NEEDS_THRESHOLD_ADJUSTMENT", "精度尚可但覆盖不足，建议放宽阈值并控制审核容量。"
        return "INEFFECTIVE", "不建议进入上线审批；返回特征和策略设计阶段。"

    def create_simulation_ticket(
        self,
        *,
        plan: StrategyTestPlan,
        metrics: BacktestMetrics,
        labeler: str = "strategy_operations_demo",
        conflict_analysis: dict[str, Any] | None = None,
        stability_analysis: dict[str, Any] | None = None,
    ) -> StrategyEffectivenessTicket:
        label, recommendation = self.classify(metrics)
        conflict_analysis = conflict_analysis or {}
        stability_analysis = stability_analysis or {}
        if conflict_analysis.get("recommendation") == "REJECT_DUPLICATE" or int(
            conflict_analysis.get("action_conflict_count", 0) or 0
        ) > 0:
            label = "STRATEGY_CONFLICT"
            recommendation = (
                "候选与现有策略存在高重叠或处置动作优先级冲突；先完成策略合并、增量贡献和动作优先级复核。"
            )
        elif stability_analysis.get("status") == "UNSTABLE":
            label = "NEEDS_THRESHOLD_ADJUSTMENT"
            recommendation = "跨月份或Bootstrap稳定性未通过，返回阈值、特征与窗口设计阶段。"
        now = datetime.now(timezone.utc)
        ticket = StrategyEffectivenessTicket(
            ticket_id=f"EFF-{plan.strategy_id}-{plan.strategy_version:03d}-{plan.payload_hash[:8]}",
            strategy_id=plan.strategy_id,
            strategy_version=plan.strategy_version,
            test_run_id=plan.test_run_id,
            data_snapshot_id=plan.data_snapshot_id,
            evaluation_phase="SIMULATION",
            label=label,
            metrics={
                "sample_size": metrics.sample_size,
                "hit_count": metrics.alerts,
                "confirmed_risk_count": metrics.true_positives,
                "false_positive_count": metrics.false_positives,
                "confirmation_rate": metrics.precision,
                "false_positive_rate": metrics.false_positive_rate,
                "recall": metrics.recall,
                "f1": metrics.f1,
                "alert_rate": metrics.alert_rate,
                "captured_loss_rate": metrics.captured_loss_rate,
                "stability_score": metrics.stability_score,
                "user_feedback_count": None,
                "business_metric_delta": None,
                "feature_psi": None,
            },
            labeler=labeler,
            observation_start=now.date().isoformat(),
            observation_end=now.date().isoformat(),
            evidence_refs=[plan.test_run_id, plan.payload_hash, plan.data_snapshot_id],
            recommendation=recommendation,
            status="PENDING_REVIEW",
            synthetic_demo=True,
        )
        with sqlite3.connect(self.database_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO effectiveness_tickets(
                    ticket_id,strategy_id,strategy_version,test_run_id,evaluation_phase,label,
                    metrics_json,recommendation,status,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    ticket.ticket_id,
                    ticket.strategy_id,
                    ticket.strategy_version,
                    ticket.test_run_id,
                    ticket.evaluation_phase,
                    ticket.label,
                    json.dumps(ticket.metrics, ensure_ascii=False),
                    ticket.recommendation,
                    ticket.status,
                    now.isoformat(),
                ),
            )
        return ticket

    def create_three_workday_observation_template(
        self,
        *,
        plan: StrategyTestPlan,
        baseline_metrics: BacktestMetrics,
    ) -> list[dict[str, Any]]:
        """Create blank post-launch observation records without claiming a production launch.

        The template is bound to an exact strategy version/test run. All post-launch fields remain
        null until a production owner supplies evidence. This prevents simulation metrics from
        being silently reused as production effectiveness.
        """
        start = datetime.now(timezone.utc).date()
        rows: list[dict[str, Any]] = []
        cursor = start
        workday = 0
        while workday < int(plan.monitoring_workdays):
            if cursor.weekday() < 5:
                workday += 1
                record = {
                    "observation_id": f"OBS-{plan.strategy_id}-{plan.strategy_version:03d}-D{workday}",
                    "strategy_id": plan.strategy_id,
                    "strategy_version": plan.strategy_version,
                    "test_run_id": plan.test_run_id,
                    "data_snapshot_id": plan.data_snapshot_id,
                    "payload_hash": plan.payload_hash,
                    "observation_date": cursor.isoformat(),
                    "workday_index": workday,
                    "status": "PLANNED_NOT_EXECUTED",
                    "hit_count": None,
                    "confirmed_risk_count": None,
                    "false_positive_count": None,
                    "confirmation_rate": None,
                    "false_positive_rate": None,
                    "user_feedback_count": None,
                    "appeal_count": None,
                    "business_metric_delta": None,
                    "feature_psi": None,
                    "alert_volume_delta": None,
                    "action_success_rate": None,
                    "error_rate": None,
                    "p95_latency_ms": None,
                    "baseline_simulation": {
                        "alerts": baseline_metrics.alerts,
                        "precision": baseline_metrics.precision,
                        "recall": baseline_metrics.recall,
                        "false_positive_rate": baseline_metrics.false_positive_rate,
                        "alert_rate": baseline_metrics.alert_rate,
                    },
                    "operator_comment": "",
                    "evidence_refs": [],
                    "synthetic_template": True,
                    "production_observation_performed": False,
                }
                rows.append(record)
                with sqlite3.connect(self.database_path) as conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO strategy_observation_records(
                            observation_id,strategy_id,strategy_version,test_run_id,observation_date,
                            workday_index,status,record_json,created_at
                        ) VALUES(?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            record["observation_id"],
                            plan.strategy_id,
                            plan.strategy_version,
                            plan.test_run_id,
                            record["observation_date"],
                            workday,
                            record["status"],
                            json.dumps(record, ensure_ascii=False),
                            datetime.now(timezone.utc).isoformat(),
                        ),
                    )
            cursor += timedelta(days=1)
        return rows

    def history(self, strategy_id: str) -> list[dict[str, Any]]:
        with sqlite3.connect(self.database_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM effectiveness_tickets WHERE strategy_id=? ORDER BY created_at",
                (strategy_id,),
            ).fetchall()
        return [dict(row) for row in rows]
