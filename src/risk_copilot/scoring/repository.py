from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

import pandas as pd

from .service import RiskTier, UserRiskScoringService


@dataclass(frozen=True)
class ManualRiskOverride:
    override_id: int
    user_id: str
    tier: str
    reason: str
    actor: str
    created_at: str


@dataclass
class RiskSnapshotRepository:
    """SQLite store for idempotent T+1 snapshots and durable manual overrides."""

    database_path: str | Path

    def __post_init__(self) -> None:
        self.database_path = Path(self.database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS manual_risk_overrides (
                    override_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    revoked_at TEXT
                );
                CREATE UNIQUE INDEX IF NOT EXISTS uq_active_manual_override
                    ON manual_risk_overrides(user_id)
                    WHERE active = 1;

                CREATE TABLE IF NOT EXISTS risk_batch_runs (
                    batch_id TEXT PRIMARY KEY,
                    as_of_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_rows INTEGER NOT NULL,
                    persisted_rows INTEGER NOT NULL DEFAULT 0,
                    started_at TEXT NOT NULL,
                    completed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS risk_snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT NOT NULL,
                    as_of_date TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    onboarding_score REAL NOT NULL,
                    dynamic_t1_score REAL NOT NULL,
                    combined_score REAL NOT NULL,
                    automatic_tier TEXT NOT NULL,
                    final_tier TEXT NOT NULL,
                    risk_source TEXT NOT NULL,
                    recommended_actions_json TEXT NOT NULL,
                    profile_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(batch_id, user_id),
                    FOREIGN KEY(batch_id) REFERENCES risk_batch_runs(batch_id)
                );

                CREATE TABLE IF NOT EXISTS current_risk_profiles (
                    user_id TEXT PRIMARY KEY,
                    latest_batch_id TEXT NOT NULL,
                    as_of_date TEXT NOT NULL,
                    combined_score REAL NOT NULL,
                    automatic_tier TEXT NOT NULL,
                    final_tier TEXT NOT NULL,
                    risk_source TEXT NOT NULL,
                    profile_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS risk_audit_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def set_manual_override(
        self,
        user_id: str,
        tier: RiskTier | str,
        reason: str,
        actor: str,
    ) -> ManualRiskOverride:
        tier_value = RiskTier(tier).value
        user_id = str(user_id)
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            existing = conn.execute(
                """
                SELECT * FROM manual_risk_overrides
                WHERE user_id=? AND active=1
                """,
                (user_id,),
            ).fetchone()
            if (
                existing is not None
                and existing["tier"] == tier_value
                and existing["reason"] == reason
                and existing["actor"] == actor
            ):
                return ManualRiskOverride(
                    override_id=int(existing["override_id"]),
                    user_id=user_id,
                    tier=tier_value,
                    reason=reason,
                    actor=actor,
                    created_at=str(existing["created_at"]),
                )
            conn.execute(
                """
                UPDATE manual_risk_overrides
                SET active=0, revoked_at=?
                WHERE user_id=? AND active=1
                """,
                (now, user_id),
            )
            cursor = conn.execute(
                """
                INSERT INTO manual_risk_overrides(
                    user_id,tier,reason,actor,active,created_at
                ) VALUES(?,?,?,?,1,?)
                """,
                (user_id, tier_value, reason, actor, now),
            )
            override_id = int(cursor.lastrowid)
            conn.execute(
                """
                INSERT INTO risk_audit_events(
                    user_id,event_type,actor,payload_json,created_at
                ) VALUES(?,?,?,?,?)
                """,
                (
                    user_id,
                    "MANUAL_OVERRIDE_SET",
                    actor,
                    json.dumps(
                        {
                            "override_id": override_id,
                            "tier": tier_value,
                            "reason": reason,
                        },
                        ensure_ascii=False,
                    ),
                    now,
                ),
            )
        return ManualRiskOverride(
            override_id=override_id,
            user_id=user_id,
            tier=tier_value,
            reason=reason,
            actor=actor,
            created_at=now,
        )

    def revoke_manual_override(self, user_id: str, actor: str, reason: str) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        user_id = str(user_id)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE manual_risk_overrides
                SET active=0, revoked_at=?
                WHERE user_id=? AND active=1
                """,
                (now, user_id),
            )
            changed = cursor.rowcount > 0
            if changed:
                conn.execute(
                    """
                    INSERT INTO risk_audit_events(
                        user_id,event_type,actor,payload_json,created_at
                    ) VALUES(?,?,?,?,?)
                    """,
                    (
                        user_id,
                        "MANUAL_OVERRIDE_REVOKED",
                        actor,
                        json.dumps({"reason": reason}, ensure_ascii=False),
                        now,
                    ),
                )
        return changed

    def active_overrides(self, user_ids: Iterable[str] | None = None) -> dict[str, ManualRiskOverride]:
        params: list[str] = []
        where = "WHERE active=1"
        if user_ids is not None:
            ids = sorted({str(value) for value in user_ids})
            if not ids:
                return {}
            placeholders = ",".join("?" for _ in ids)
            where += f" AND user_id IN ({placeholders})"
            params.extend(ids)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT override_id,user_id,tier,reason,actor,created_at
                FROM manual_risk_overrides
                {where}
                """,
                params,
            ).fetchall()
        return {
            str(row["user_id"]): ManualRiskOverride(
                override_id=int(row["override_id"]),
                user_id=str(row["user_id"]),
                tier=str(row["tier"]),
                reason=str(row["reason"]),
                actor=str(row["actor"]),
                created_at=str(row["created_at"]),
            )
            for row in rows
        }

    def persist_batch(
        self,
        batch_id: str,
        as_of_date: str,
        profiles: list[dict[str, Any]],
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                INSERT INTO risk_batch_runs(
                    batch_id,as_of_date,status,input_rows,persisted_rows,started_at
                ) VALUES(?,?,'RUNNING',?,0,?)
                ON CONFLICT(batch_id) DO UPDATE SET
                    as_of_date=excluded.as_of_date,
                    status='RUNNING',
                    input_rows=excluded.input_rows,
                    persisted_rows=0,
                    started_at=excluded.started_at,
                    completed_at=NULL
                """,
                (batch_id, as_of_date, len(profiles), now),
            )
            for profile in profiles:
                payload = json.dumps(profile, ensure_ascii=False)
                actions = json.dumps(profile["recommended_actions"], ensure_ascii=False)
                values = (
                    batch_id,
                    as_of_date,
                    str(profile["user_id"]),
                    float(profile["onboarding_score"]),
                    float(profile["dynamic_t1_score"]),
                    float(profile["combined_score"]),
                    str(profile["automatic_tier"]),
                    str(profile["final_tier"]),
                    str(profile["risk_source"]),
                    actions,
                    payload,
                    now,
                )
                conn.execute(
                    """
                    INSERT INTO risk_snapshots(
                        batch_id,as_of_date,user_id,onboarding_score,
                        dynamic_t1_score,combined_score,automatic_tier,final_tier,
                        risk_source,recommended_actions_json,profile_json,created_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(batch_id,user_id) DO UPDATE SET
                        as_of_date=excluded.as_of_date,
                        onboarding_score=excluded.onboarding_score,
                        dynamic_t1_score=excluded.dynamic_t1_score,
                        combined_score=excluded.combined_score,
                        automatic_tier=excluded.automatic_tier,
                        final_tier=excluded.final_tier,
                        risk_source=excluded.risk_source,
                        recommended_actions_json=excluded.recommended_actions_json,
                        profile_json=excluded.profile_json,
                        created_at=excluded.created_at
                    """,
                    values,
                )
                conn.execute(
                    """
                    INSERT INTO current_risk_profiles(
                        user_id,latest_batch_id,as_of_date,combined_score,
                        automatic_tier,final_tier,risk_source,profile_json,updated_at
                    ) VALUES(?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        latest_batch_id=excluded.latest_batch_id,
                        as_of_date=excluded.as_of_date,
                        combined_score=excluded.combined_score,
                        automatic_tier=excluded.automatic_tier,
                        final_tier=excluded.final_tier,
                        risk_source=excluded.risk_source,
                        profile_json=excluded.profile_json,
                        updated_at=excluded.updated_at
                    """,
                    (
                        str(profile["user_id"]),
                        batch_id,
                        as_of_date,
                        float(profile["combined_score"]),
                        str(profile["automatic_tier"]),
                        str(profile["final_tier"]),
                        str(profile["risk_source"]),
                        payload,
                        now,
                    ),
                )
            conn.execute(
                """
                UPDATE risk_batch_runs
                SET status='SUCCEEDED', persisted_rows=?, completed_at=?
                WHERE batch_id=?
                """,
                (len(profiles), now, batch_id),
            )
        return {
            "batch_id": batch_id,
            "as_of_date": as_of_date,
            "status": "SUCCEEDED",
            "input_rows": len(profiles),
            "persisted_rows": len(profiles),
            "database": str(self.database_path),
        }

    def current_profile(self, user_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT profile_json FROM current_risk_profiles WHERE user_id=?",
                (str(user_id),),
            ).fetchone()
        return json.loads(row["profile_json"]) if row else None

    def history(self, user_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            snapshots = conn.execute(
                """
                SELECT batch_id,as_of_date,automatic_tier,final_tier,risk_source,
                       combined_score,created_at
                FROM risk_snapshots
                WHERE user_id=?
                ORDER BY snapshot_id
                """,
                (str(user_id),),
            ).fetchall()
            overrides = conn.execute(
                """
                SELECT override_id,tier,reason,actor,active,created_at,revoked_at
                FROM manual_risk_overrides
                WHERE user_id=?
                ORDER BY override_id
                """,
                (str(user_id),),
            ).fetchall()
            audit = conn.execute(
                """
                SELECT event_type,actor,payload_json,created_at
                FROM risk_audit_events
                WHERE user_id=?
                ORDER BY event_id
                """,
                (str(user_id),),
            ).fetchall()
        return {
            "user_id": str(user_id),
            "snapshots": [dict(row) for row in snapshots],
            "manual_overrides": [dict(row) for row in overrides],
            "audit_events": [
                {
                    **dict(row),
                    "payload": json.loads(row["payload_json"]),
                }
                for row in audit
            ],
        }


@dataclass
class T1RiskBatchRunner:
    repository: RiskSnapshotRepository
    scoring_service: UserRiskScoringService

    def run(
        self,
        data: pd.DataFrame,
        *,
        batch_id: str | None = None,
        as_of_date: str | date | None = None,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        if "user_id" not in data:
            raise ValueError("T+1 batch requires a user_id column")
        resolved_batch_id = batch_id or f"T1-{uuid4().hex[:12]}"
        resolved_as_of = (
            as_of_date.isoformat()
            if isinstance(as_of_date, date)
            else str(as_of_date or datetime.now(timezone.utc).date().isoformat())
        )
        overrides = self.repository.active_overrides(data["user_id"].astype(str))
        profiles: list[dict[str, Any]] = []
        for _, row in data.iterrows():
            override = overrides.get(str(row["user_id"]))
            profiles.append(
                self.scoring_service.assess(
                    row,
                    manual_tier=override.tier if override else None,
                    manual_reason=override.reason if override else None,
                    actor=override.actor if override else None,
                )
            )
        manifest = self.repository.persist_batch(
            resolved_batch_id,
            resolved_as_of,
            profiles,
        )
        flat = pd.DataFrame(
            [
                {
                    "user_id": profile["user_id"],
                    "onboarding_score": profile["onboarding_score"],
                    "dynamic_t1_score": profile["dynamic_t1_score"],
                    "combined_score": profile["combined_score"],
                    "automatic_tier": profile["automatic_tier"],
                    "final_tier": profile["final_tier"],
                    "risk_source": profile["risk_source"],
                    "recommended_actions": "|".join(profile["recommended_actions"]),
                    "str_details_visible": profile["str_details"] is not None,
                }
                for profile in profiles
            ]
        )
        manifest["manual_override_count"] = int(
            (flat["risk_source"] == "manual_override").sum()
        )
        return flat, manifest
