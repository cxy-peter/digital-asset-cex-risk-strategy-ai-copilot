from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import load_yaml
from ..rules.dsl import evaluate_rule, rule_to_expression
from ..schemas import CMSSTRCasePreview, StrategyCandidate


@dataclass
class CMSSTRIntegrationService:
    config_path: str | Path
    database_path: str | Path

    def __post_init__(self) -> None:
        self.config: dict[str, Any] = load_yaml(self.config_path)
        self.database_path = Path(self.database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cms_str_case_previews (
                    case_id TEXT PRIMARY KEY,
                    dedup_key TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    strategy_id TEXT NOT NULL,
                    strategy_version INTEGER NOT NULL,
                    event_code TEXT NOT NULL,
                    status TEXT NOT NULL,
                    masak_feedback_status TEXT NOT NULL,
                    preview_json TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _hash(value: Any) -> str:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def prepare_candidates(
        self,
        *,
        strategy: StrategyCandidate,
        strategy_version: int,
        data: pd.DataFrame,
        data_snapshot_id: str,
        top_k: int = 10,
    ) -> dict[str, Any]:
        triggers = set(self.config.get("trigger_level_3_tags", []))
        if strategy.tag_level_3 not in triggers:
            return {
                "enabled": False,
                "reason": f"strategy tag level 3 is {strategy.tag_level_3}, not a CMS/STR trigger",
                "cases": [],
                "external_submission_allowed": False,
                "automatic_filing_performed": False,
            }
        mask = evaluate_rule(data, strategy.rule)
        hit_rows = data.loc[mask].copy().head(top_k)
        expression = rule_to_expression(strategy.rule)
        cases: list[CMSSTRCasePreview] = []
        for _, row in hit_rows.iterrows():
            user_id = str(row.get("user_id", "UNKNOWN"))
            features = {
                feature: (None if pd.isna(row.get(feature)) else row.get(feature))
                for feature in strategy.required_features
                if feature in row.index
            }
            evidence_hash = self._hash(
                {
                    "user_id": user_id,
                    "strategy_id": strategy.strategy_id,
                    "version": strategy_version,
                    "event": strategy.event_code,
                    "features": features,
                    "snapshot": data_snapshot_id,
                }
            )
            dedup_key = self._hash(
                [user_id, strategy.strategy_id, strategy_version, strategy.event_code, evidence_hash]
            )
            case = CMSSTRCasePreview(
                case_id=f"CMSSTR-{strategy.strategy_id}-{dedup_key[:10]}",
                dedup_key=dedup_key,
                user_id=user_id,
                strategy_id=strategy.strategy_id,
                strategy_version=strategy_version,
                event_code=strategy.event_code,
                strategy_tag_level_3=strategy.tag_level_3,
                feature_snapshot=features,
                strategy_expression=expression,
                risk_history_summary={
                    "risk_tier": row.get("final_tier") or row.get("risk_tier") or "UNKNOWN",
                    "fraud_label_in_demo": int(row.get("fraud_label", 0)),
                    "data_snapshot_id": data_snapshot_id,
                },
                graph_path_summary={
                    key: row.get(key)
                    for key in [
                        "device_fraud_1hop_count",
                        "withdraw_address_fraud_1hop_count",
                        "kyc_id_fraud_1hop_count",
                        "fraud_2hop_count",
                        "community_fraud_ratio",
                    ]
                    if key in row.index
                },
                evidence_hash=evidence_hash,
            )
            cases.append(case)
            with sqlite3.connect(self.database_path) as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO cms_str_case_previews(
                        case_id,dedup_key,user_id,strategy_id,strategy_version,event_code,status,
                        masak_feedback_status,preview_json
                    ) VALUES(?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        case.case_id,
                        case.dedup_key,
                        case.user_id,
                        case.strategy_id,
                        case.strategy_version,
                        case.event_code,
                        case.status,
                        case.masak_feedback_status,
                        case.model_dump_json(),
                    ),
                )
        return {
            "enabled": True,
            "one_click_semantics": self.config.get("one_click_semantics"),
            "cases": cases,
            "case_count": len(cases),
            "database": str(self.database_path),
            "external_submission_allowed": False,
            "automatic_filing_performed": False,
            "masak_feedback_status": "NOT_SUBMITTED",
        }
