from __future__ import annotations

from dataclasses import dataclass

from sklearn.tree import _tree

from ..schemas import ActionType, Condition, RiskDomain, RuleGroup, StrategyCandidate


@dataclass
class TreeRuleExtractor:
    min_leaf_samples: int = 20
    min_leaf_positive_rate: float = 0.30
    max_rules: int = 8

    def extract(
        self,
        tree_model,
        transformed_feature_names: list[str],
        original_feature_names: set[str],
        domain: RiskDomain,
        event_code: str,
        action: ActionType = ActionType.MANUAL_REVIEW,
    ) -> list[StrategyCandidate]:
        """Convert interpretable tree paths back into raw-feature rule conditions.

        Numeric features are not standardized in the tree pipeline, so thresholds remain in the
        original business units. One-hot categorical splits are converted from ``x_category<=0.5``
        into ``feature != category`` and the right branch into ``feature == category``.
        """
        tree = tree_model.tree_
        candidates: list[tuple[float, int, list[Condition]]] = []
        originals = sorted(original_feature_names, key=len, reverse=True)

        def split_conditions(raw_name: str, threshold: float) -> tuple[Condition, Condition] | None:
            prefix, clean = (raw_name.split("__", 1) if "__" in raw_name else ("numeric", raw_name))
            if prefix == "numeric" and clean in original_feature_names:
                return (
                    Condition(feature=clean, operator="<=", value=round(float(threshold), 6)),
                    Condition(feature=clean, operator=">", value=round(float(threshold), 6)),
                )
            if prefix == "categorical":
                original = next((name for name in originals if clean.startswith(name + "_")), None)
                if original is None:
                    return None
                category = clean[len(original) + 1 :]
                return (
                    Condition(feature=original, operator="!=", value=category),
                    Condition(feature=original, operator="==", value=category),
                )
            if clean in original_feature_names:
                return (
                    Condition(feature=clean, operator="<=", value=round(float(threshold), 6)),
                    Condition(feature=clean, operator=">", value=round(float(threshold), 6)),
                )
            return None

        def walk(node: int, conditions: list[Condition]) -> None:
            if tree.feature[node] != _tree.TREE_UNDEFINED:
                raw_name = transformed_feature_names[tree.feature[node]]
                pair = split_conditions(raw_name, float(tree.threshold[node]))
                if pair is None:
                    return
                left_condition, right_condition = pair
                walk(tree.children_left[node], conditions + [left_condition])
                walk(tree.children_right[node], conditions + [right_condition])
                return

            samples = int(tree.n_node_samples[node])
            values = tree.value[node][0]
            positive_rate = float(values[1] / max(values.sum(), 1e-12)) if len(values) > 1 else 0.0
            if samples >= self.min_leaf_samples and positive_rate >= self.min_leaf_positive_rate and conditions:
                candidates.append((positive_rate, samples, conditions))

        walk(0, [])
        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        result: list[StrategyCandidate] = []
        for idx, (positive_rate, samples, conditions) in enumerate(candidates[: self.max_rules], 1):
            result.append(
                StrategyCandidate(
                    strategy_id=f"TREE-{event_code}-{idx:02d}",
                    name=f"Decision Tree候选规则 {idx}",
                    domain=domain,
                    event_code=event_code,
                    description=(
                        f"从深度受限决策树高风险叶节点提取，叶节点坏样本率={positive_rate:.1%}，"
                        f"样本={samples}。"
                    ),
                    rule=RuleGroup(logic="AND", conditions=conditions),
                    action=action,
                    source="tree",
                    rationale=["深度受限以提高可解释性", "原始单位阈值，可直接进入规则回测", "候选规则仍需独立回测和人工审批"],
                    required_features=sorted({condition.feature for condition in conditions}),
                    tags=["tree_extracted", "interpretable"],
                    tag_level_1=domain.value,
                    tag_level_2=(
                        "rapid_fiat_convert_chain_out"
                        if domain == RiskDomain.FUND_SECURITY
                        else "data_driven_tree_rule"
                    ),
                    tag_level_3="MANUAL_REVIEW",
                )
            )
        return result
