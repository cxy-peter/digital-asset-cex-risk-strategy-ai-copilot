# P0 Enhancements

## Interactive Console

Implemented in `risk_copilot.api` at `/console`. It provides an internal-tool-style flow from risk requirement to Agent review, strategy evidence, P0 analyses and governance artifacts.

## Strategy Conflict and Incremental Value

Implemented in `analysis/conflicts.py`. The analysis compares a frozen candidate against a synthetic portfolio, evaluates overlap/containment, incremental alerts and risk recall, operational duplication and disposition conflicts. Action conflicts are added to the independent second-review conditions.

## Cross-month and Bootstrap Stability

Implemented in `analysis/stability.py`. The frozen candidate is evaluated by month and by bootstrap resampling. Feature-direction consistency is included to detect unstable or sign-flipping behavior.

## Governance integration

- `UNSTABLE` results block second-review readiness;
- `REJECT_DUPLICATE` blocks release progression;
- action conflicts require a dedicated precedence reviewer;
- effectiveness tickets can be labelled `STRATEGY_CONFLICT`;
- AI advisory findings remain non-binding but are attached to review evidence.
