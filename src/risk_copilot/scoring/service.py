from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd


class RiskTier(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L31 = "L3.1"
    L32 = "L3.2"
    L33 = "L3.3"
    L4 = "L4"


TIER_ACTIONS = {
    RiskTier.L1: ["PASS", "MONITOR"],
    RiskTier.L2: ["MONITOR"],
    RiskTier.L31: ["RFI", "MANUAL_REVIEW"],
    RiskTier.L32: ["RFI", "EDD", "DAILY_LIMIT"],
    RiskTier.L33: ["EDD", "WITHDRAWAL_RESTRICTION", "MANUAL_REVIEW"],
    RiskTier.L4: ["FREEZE", "REJECT", "ESCALATE_COMPLIANCE"],
}


@dataclass
class UserRiskScoringService:
    """Two-layer user risk scoring: onboarding KYC + T+1 dynamic behavior.

    Manual overrides are explicit, versioned, and never silently overwritten by the automatic
    batch. STR details are deliberately excluded from the ordinary profile response.
    """

    onboarding_weight: float = 0.42
    dynamic_weight: float = 0.58

    @staticmethod
    def _tier(score: float) -> RiskTier:
        if score < 0.20:
            return RiskTier.L1
        if score < 0.40:
            return RiskTier.L2
        if score < 0.55:
            return RiskTier.L31
        if score < 0.70:
            return RiskTier.L32
        if score < 0.85:
            return RiskTier.L33
        return RiskTier.L4

    @staticmethod
    def _value(row: pd.Series | dict[str, Any], key: str, default: float = 0.0) -> float:
        value = row.get(key, default)
        try:
            if pd.isna(value):
                return default
        except Exception:
            pass
        return float(value)

    def assess(
        self,
        row: pd.Series | dict[str, Any],
        manual_tier: str | None = None,
        manual_reason: str | None = None,
        actor: str | None = None,
    ) -> dict[str, Any]:
        onboarding = np.clip(
            0.15 * self._value(row, "age_risk_score")
            + 0.25 * self._value(row, "occupation_risk_score")
            + 0.25 * self._value(row, "nationality_risk_score")
            + 0.20 * self._value(row, "address_risk_score")
            + 0.10 * self._value(row, "kyc_country_risk")
            + 0.05 * (1.0 if row.get("kyc_level") == "L1" else 0.0),
            0,
            1,
        )
        dynamic = np.clip(
            0.24 * self._value(row, "risk_score_t1")
            + 0.18 * min(self._value(row, "fiat_in_crypto_out_ratio"), 1.0)
            + 0.12 * self._value(row, "high_risk_chain_exposure")
            + 0.12 * self._value(row, "counterparty_fraud_ratio")
            + 0.12 * self._value(row, "fraud_graph_score")
            + 0.08 * min(self._value(row, "bank_fraud_ratio_max"), 1.0)
            + 0.07 * min(self._value(row, "proxy_flag"), 1.0)
            + 0.07 * min(self._value(row, "new_device_flag"), 1.0),
            0,
            1,
        )
        combined = float(np.clip(self.onboarding_weight * onboarding + self.dynamic_weight * dynamic, 0, 1))
        auto_tier = self._tier(combined)
        risk_source = "automatic_t1"
        final_tier = auto_tier
        history = [
            {
                "source": "onboarding",
                "score": round(float(onboarding), 6),
                "calculated_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "source": "automatic_t1",
                "score": round(float(dynamic), 6),
                "combined_score": round(combined, 6),
                "tier": auto_tier.value,
                "calculated_at": datetime.now(timezone.utc).isoformat(),
            },
        ]
        if manual_tier is not None:
            final_tier = RiskTier(manual_tier)
            risk_source = "manual_override"
            history.append(
                {
                    "source": "manual_override",
                    "tier": final_tier.value,
                    "reason": manual_reason or "not_provided",
                    "actor": actor or "unknown",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "preserve_on_next_t1_run": True,
                }
            )

        return {
            "user_id": str(row.get("user_id", "unknown")),
            "onboarding_score": round(float(onboarding), 6),
            "dynamic_t1_score": round(float(dynamic), 6),
            "combined_score": round(combined, 6),
            "automatic_tier": auto_tier.value,
            "final_tier": final_tier.value,
            "risk_source": risk_source,
            "recommended_actions": TIER_ACTIONS[final_tier],
            "risk_history": history,
            "ordinary_profile_fields": {
                "risk_tier": final_tier.value,
                "risk_source": risk_source,
                "restriction_status": "none",
                "rfi_status": "not_started",
            },
            "str_details": None,
            "confidentiality_note": "STR details are restricted to compliance roles and are not shown in ordinary user profiles.",
        }

    def assess_dataframe(self, data: pd.DataFrame, limit: int | None = None) -> pd.DataFrame:
        frame = data.head(limit) if limit else data
        return pd.DataFrame([self.assess(row) for _, row in frame.iterrows()])
