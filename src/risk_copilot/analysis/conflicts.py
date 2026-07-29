from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..config import load_yaml
from ..rules.dsl import evaluate_rule, rule_to_expression
from ..schemas import ActionType, RiskDomain, RuleGroup, StrategyCandidate


@dataclass
class StrategyConflictAnalyzer:
    target: str = "fraud_label"

    @staticmethod
    def load_portfolio(path: str | Path) -> list[StrategyCandidate]:
        items = load_yaml(path)
        portfolio: list[StrategyCandidate] = []
        for item in items:
            rule = RuleGroup.model_validate(item["rule"])
            portfolio.append(
                StrategyCandidate(
                    strategy_id=item["strategy_id"],
                    name=item["name"],
                    domain=RiskDomain(item["domain"]),
                    event_code=item["event_code"],
                    description=item.get("description", "synthetic existing strategy"),
                    rule=rule,
                    action=ActionType(item["action"]),
                    action_params=item.get("action_params", {}),
                    source="expert",
                    rationale=item.get("rationale", ["synthetic portfolio baseline"]),
                    required_features=sorted({c.feature for c in rule.conditions}),
                    tags=item.get("tags", ["existing_portfolio"]),
                    tag_level_1=item.get("tag_level_1", item["domain"]),
                    tag_level_2=item.get("tag_level_2", "portfolio_baseline"),
                    tag_level_3=item.get("tag_level_3", item["action"]),
                )
            )
        return portfolio

    def analyze(
        self,
        data: pd.DataFrame,
        selected: StrategyCandidate,
        existing: list[StrategyCandidate],
    ) -> dict[str, Any]:
        if data.empty:
            raise ValueError("conflict analysis input is empty")
        if self.target not in data:
            raise KeyError(f"missing target column: {self.target}")
        selected_alert = evaluate_rule(data, selected.rule).to_numpy(dtype=bool)
        y = data[self.target].astype(int).to_numpy()
        compatible = [
            strategy
            for strategy in existing
            if strategy.event_code == selected.event_code or strategy.domain == selected.domain
        ]
        comparisons: list[dict[str, Any]] = []
        existing_union = np.zeros(len(data), dtype=bool)
        for strategy in compatible:
            try:
                alert = evaluate_rule(data, strategy.rule).to_numpy(dtype=bool)
            except Exception as exc:
                comparisons.append(
                    {
                        "strategy_id": strategy.strategy_id,
                        "name": strategy.name,
                        "status": "execution_failed",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                continue
            existing_union |= alert
            overlap = selected_alert & alert
            union = selected_alert | alert
            selected_only = selected_alert & ~alert
            existing_only = alert & ~selected_alert
            action_conflict = selected.action != strategy.action and int(overlap.sum()) > 0
            selected_containment = float(overlap.sum() / max(selected_alert.sum(), 1))
            existing_containment = float(overlap.sum() / max(alert.sum(), 1))
            comparisons.append(
                {
                    "strategy_id": strategy.strategy_id,
                    "name": strategy.name,
                    "status": "evaluated",
                    "event_code": strategy.event_code,
                    "action": strategy.action.value,
                    "expression": rule_to_expression(strategy.rule),
                    "alerts": int(alert.sum()),
                    "overlap_alerts": int(overlap.sum()),
                    "jaccard": float(overlap.sum() / max(union.sum(), 1)),
                    "selected_containment": selected_containment,
                    "existing_containment": existing_containment,
                    "selected_only_alerts": int(selected_only.sum()),
                    "existing_only_alerts": int(existing_only.sum()),
                    "overlap_true_positives": int((overlap & (y == 1)).sum()),
                    "action_conflict": action_conflict,
                    "severity": (
                        "high" if action_conflict and selected_containment >= 0.50
                        else "medium" if action_conflict or selected_containment >= 0.70
                        else "low"
                    ),
                }
            )

        incremental = selected_alert & ~existing_union
        duplicate = selected_alert & existing_union
        total_positive = max(int((y == 1).sum()), 1)
        selected_tp = int((selected_alert & (y == 1)).sum())
        incremental_tp = int((incremental & (y == 1)).sum())
        high_overlap = [row for row in comparisons if row.get("status") == "evaluated" and row.get("selected_containment", 0) >= 0.70]
        action_conflicts = [row for row in comparisons if row.get("action_conflict")]
        if high_overlap and incremental_tp == 0:
            recommendation = "REJECT_DUPLICATE"
        elif action_conflicts:
            recommendation = "REVISE_ACTION_PRECEDENCE"
        elif incremental_tp / total_positive < 0.01 and int(incremental.sum()) > 0:
            recommendation = "REVISE_LOW_INCREMENTAL_VALUE"
        else:
            recommendation = "ACCEPT_INCREMENTAL_VALUE"

        return {
            "selected_strategy": {
                "strategy_id": selected.strategy_id,
                "name": selected.name,
                "event_code": selected.event_code,
                "action": selected.action.value,
                "expression": rule_to_expression(selected.rule),
                "alerts": int(selected_alert.sum()),
                "true_positives": selected_tp,
            },
            "portfolio_size": len(existing),
            "compatible_portfolio_size": len(compatible),
            "comparisons": sorted(
                comparisons,
                key=lambda row: (row.get("status") != "evaluated", -row.get("jaccard", 0.0)),
            ),
            "incremental": {
                "alerts": int(incremental.sum()),
                "true_positives": incremental_tp,
                "precision": float(incremental_tp / max(int(incremental.sum()), 1)),
                "recall_contribution": float(incremental_tp / total_positive),
                "duplicate_alerts": int(duplicate.sum()),
                "duplicate_workload_rate": float(duplicate.sum() / max(selected_alert.sum(), 1)),
            },
            "action_conflict_count": len(action_conflicts),
            "high_overlap_count": len(high_overlap),
            "recommendation": recommendation,
            "requires_human_review": True,
            "synthetic_demo": True,
        }
