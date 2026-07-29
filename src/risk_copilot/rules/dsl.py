from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ..schemas import Condition, RuleGroup


def evaluate_condition(data: pd.DataFrame, condition: Condition) -> pd.Series:
    if condition.feature not in data:
        raise KeyError(f"feature {condition.feature!r} is not present in data")
    series = data[condition.feature]
    op, value = condition.operator, condition.value
    if op == ">": return series > value
    if op == ">=": return series >= value
    if op == "<": return series < value
    if op == "<=": return series <= value
    if op == "==": return series == value
    if op == "!=": return series != value
    if op == "in": return series.isin(value)
    if op == "not_in": return ~series.isin(value)
    if op == "between": return series.between(value[0], value[1], inclusive="both")
    if op == "is_true": return series.fillna(False).astype(bool)
    if op == "is_false": return ~series.fillna(False).astype(bool)
    raise ValueError(f"unsupported operator: {op}")


def evaluate_rule(data: pd.DataFrame, group: RuleGroup) -> pd.Series:
    parts: list[pd.Series] = [evaluate_condition(data, c) for c in group.conditions]
    parts.extend(evaluate_rule(data, child) for child in group.groups)
    if not parts:
        return pd.Series(False, index=data.index)
    result = parts[0].fillna(False)
    for part in parts[1:]:
        result = (result & part.fillna(False)) if group.logic == "AND" else (result | part.fillna(False))
    return result.astype(bool)


def rule_to_expression(group: RuleGroup) -> str:
    def condition_text(c: Condition) -> str:
        if c.operator == "is_true": return f"{c.feature} == true"
        if c.operator == "is_false": return f"{c.feature} == false"
        if c.operator == "between": return f"{c.value[0]} <= {c.feature} <= {c.value[1]}"
        if c.operator in {"in", "not_in"}: return f"{c.feature} {c.operator} {c.value}"
        return f"{c.feature} {c.operator} {repr(c.value)}"
    items = [condition_text(c) for c in group.conditions]
    items += [f"({rule_to_expression(child)})" for child in group.groups]
    return f" {group.logic} ".join(items)


def required_features(group: RuleGroup) -> list[str]:
    names = [condition.feature for condition in group.conditions]
    for child in group.groups:
        names.extend(required_features(child))
    return sorted(set(names))


def engine_json(group: RuleGroup) -> dict[str, Any]:
    return {
        "logic": group.logic,
        "conditions": [condition.model_dump(mode="json") for condition in group.conditions],
        "groups": [engine_json(child) for child in group.groups],
    }
