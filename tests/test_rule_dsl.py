import pandas as pd

from risk_copilot.rules.dsl import evaluate_rule, rule_to_expression
from risk_copilot.schemas import Condition, RuleGroup


def test_nested_rule_evaluation():
    data = pd.DataFrame({"ratio": [0.9, 0.7, 0.95], "minutes": [100, 100, 800], "graph": [0, 1, 1]})
    rule = RuleGroup(
        logic="AND",
        conditions=[Condition(feature="ratio", operator=">=", value=0.85)],
        groups=[
            RuleGroup(
                logic="OR",
                conditions=[
                    Condition(feature="minutes", operator="<", value=240),
                    Condition(feature="graph", operator=">=", value=1),
                ],
            )
        ],
    )
    assert evaluate_rule(data, rule).tolist() == [True, False, True]
    assert "ratio" in rule_to_expression(rule)
