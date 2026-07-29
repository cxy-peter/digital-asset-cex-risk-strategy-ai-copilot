from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..rules.dsl import rule_to_expression
from ..schemas import BacktestMetrics, GovernanceDecision, StrategyCandidate


@dataclass
class StrategyRegistryRepository:
    database_path: str | Path

    def __post_init__(self) -> None:
        self.database_path = Path(self.database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 30000")
        try:
            connection.execute("PRAGMA journal_mode = WAL")
        except sqlite3.OperationalError:
            # Another process may be enabling WAL at the same time. The busy timeout still
            # protects subsequent schema/version transactions.
            pass
        return connection

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS strategies (
                    strategy_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    event_code TEXT NOT NULL,
                    current_status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS strategy_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    rule_expression TEXT NOT NULL,
                    strategy_json TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    governance_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(strategy_id, version)
                );
                CREATE TABLE IF NOT EXISTS approvals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    actor TEXT,
                    decision TEXT NOT NULL,
                    comment TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    from_status TEXT,
                    to_status TEXT,
                    payload_json TEXT,
                    actor TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )

    def persist_candidate(
        self,
        strategy: StrategyCandidate,
        metrics: BacktestMetrics,
        governance: GovernanceDecision,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            # Serialize version allocation and insertion so concurrent runs cannot select the
            # same MAX(version)+1 value.
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                "SELECT current_status FROM strategies WHERE strategy_id=?", (strategy.strategy_id,)
            ).fetchone()
            if existing is None:
                conn.execute(
                    "INSERT INTO strategies(strategy_id,name,domain,event_code,current_status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                    (
                        strategy.strategy_id,
                        strategy.name,
                        strategy.domain.value,
                        strategy.event_code,
                        governance.next_status.value,
                        now,
                        now,
                    ),
                )
            else:
                conn.execute(
                    "UPDATE strategies SET current_status=?, updated_at=? WHERE strategy_id=?",
                    (governance.next_status.value, now, strategy.strategy_id),
                )
            version = conn.execute(
                "SELECT COALESCE(MAX(version),0)+1 AS next_version FROM strategy_versions WHERE strategy_id=?",
                (strategy.strategy_id,),
            ).fetchone()["next_version"]
            conn.execute(
                "INSERT INTO strategy_versions(strategy_id,version,rule_expression,strategy_json,metrics_json,governance_json,created_at) VALUES(?,?,?,?,?,?,?)",
                (
                    strategy.strategy_id,
                    version,
                    rule_to_expression(strategy.rule),
                    strategy.model_dump_json(),
                    metrics.model_dump_json(),
                    governance.model_dump_json(),
                    now,
                ),
            )
            conn.execute(
                "INSERT INTO audit_events(strategy_id,event_type,from_status,to_status,payload_json,actor,created_at) VALUES(?,?,?,?,?,?,?)",
                (
                    strategy.strategy_id,
                    "AI_CANDIDATE_REVIEWED",
                    governance.current_status.value,
                    governance.next_status.value,
                    json.dumps(governance.audit_fields, ensure_ascii=False),
                    "risk_strategy_copilot",
                    now,
                ),
            )
        return {"strategy_id": strategy.strategy_id, "version": int(version), "status": governance.next_status.value, "database": str(self.database_path)}

    def record_approval(
        self,
        strategy_id: str,
        version: int,
        role: str,
        decision: str,
        actor: str,
        comment: str = "",
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO approvals(strategy_id,version,role,actor,decision,comment,created_at) VALUES(?,?,?,?,?,?,?)",
                (strategy_id, version, role, actor, decision, comment, datetime.now(timezone.utc).isoformat()),
            )

    def history(self, strategy_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            strategy = conn.execute("SELECT * FROM strategies WHERE strategy_id=?", (strategy_id,)).fetchone()
            versions = conn.execute(
                "SELECT version,rule_expression,metrics_json,governance_json,created_at FROM strategy_versions WHERE strategy_id=? ORDER BY version",
                (strategy_id,),
            ).fetchall()
            approvals = conn.execute(
                "SELECT version,role,actor,decision,comment,created_at FROM approvals WHERE strategy_id=? ORDER BY id",
                (strategy_id,),
            ).fetchall()
            audits = conn.execute(
                "SELECT event_type,from_status,to_status,actor,created_at FROM audit_events WHERE strategy_id=? ORDER BY id",
                (strategy_id,),
            ).fetchall()
        return {
            "strategy": dict(strategy) if strategy else None,
            "versions": [dict(row) for row in versions],
            "approvals": [dict(row) for row in approvals],
            "audit_events": [dict(row) for row in audits],
        }
