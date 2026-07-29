from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..schemas import ActionType, StrategyCandidate
from ..scoring.service import RiskTier, TIER_ACTIONS


@dataclass
class DispositionPlanner:
    """Build a controlled action ladder rather than directly executing punishment.

    The plan separates *detection* (strategy hit) from *disposition* (RFI/EDD/limit/restriction)
    and adds customer-segment approval gates for KA/VIP/EXEMPT users.
    """

    high_impact_actions: tuple[str, ...] = (
        ActionType.WITHDRAWAL_RESTRICTION.value,
        ActionType.TRANSACTION_RESTRICTION.value,
        ActionType.FREEZE.value,
        ActionType.REJECT.value,
    )

    def tier_matrix(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for tier in RiskTier:
            actions = list(TIER_ACTIONS[tier])
            rows.append(
                {
                    "risk_tier": tier.value,
                    "normal_customer_actions": actions,
                    "ka_vip_exempt_actions": actions,
                    "ka_vip_exempt_extra_approval": True,
                    "requires_compliance": any(
                        action in {
                            ActionType.RFI.value,
                            ActionType.EDD.value,
                            ActionType.FREEZE.value,
                            ActionType.REJECT.value,
                            ActionType.ESCALATE_COMPLIANCE.value,
                        }
                        for action in actions
                    ),
                    "direct_execution_allowed": False,
                }
            )
        return rows

    def selected_strategy_plan(self, strategy: StrategyCandidate) -> dict[str, Any]:
        action = strategy.action.value
        approvals = ["risk_strategy", "risk_operations"]
        if action in {
            ActionType.RFI.value,
            ActionType.EDD.value,
            ActionType.ESCALATE_COMPLIANCE.value,
            *self.high_impact_actions,
        }:
            approvals.append("compliance")
        if action in self.high_impact_actions:
            approvals.append("risk_owner")
        return {
            "strategy_id": strategy.strategy_id,
            "detection_action": action,
            "execution_mode": "PROPOSE_ONLY",
            "required_approvals": list(dict.fromkeys(approvals)),
            "customer_segment_gate": {
                "segments": ["KA", "VIP", "EXEMPT"],
                "extra_approval": True,
                "reason": "avoid material customer mis-penalty and preserve auditability",
            },
            "release_controls": {
                "batch_release_supported": True,
                "release_requires_reason": True,
                "operator_and_approver_separation": True,
            },
            "notification_required": action not in {ActionType.MONITOR.value, ActionType.PASS.value},
            "direct_execution_allowed": False,
        }
