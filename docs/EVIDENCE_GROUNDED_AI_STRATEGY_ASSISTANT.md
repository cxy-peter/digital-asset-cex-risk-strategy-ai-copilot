# Evidence-Grounded AI Strategy Assistant

## Purpose

This module converts internship-derived, sanitized process knowledge into a reproducible planning package for the existing synthetic Risk Strategy Copilot.

It is deliberately not a second, competing model pipeline. The current repository already provides feature profiling, LR/Tree/XGBoost, Risk Graph, Rule DSL, temporal OOT, simulation, stability, conflict analysis, second review and effect tickets. The new module supplies the missing upstream reasoning, label realism, source-like distribution checks and complete product-delivery workflow.

## Run

```bash
risk-copilot generate-data --force
python scripts/run_evidence_strategy_assistant.py \
  --request-id REQ-ATO-001 \
  --query "Detect account takeover after a new device and sensitive-security change before chain withdrawal" \
  --business-objective "Reduce account-takeover loss while controlling user friction and manual-review workload" \
  --risk-domain account_security \
  --event-code ChainWithdraw
```

Default output directory:

```text
outputs/evidence_strategy_assistant/
```

The generated `strategy_request.json` is compatible with the existing `StrategyRequest` schema and can be used to start the current deterministic strategy workflow.

## Seven-layer interview/problem structure

1. Macro objective
2. Regulatory or business requirement
3. Business flow and state
4. System, event and data
5. Risk intelligence
6. Strategy, action and governance
7. Validation, outcome and ownership

Each layer contains a ready-to-use answer template, required evidence and a concrete output object.

## Source privacy

The public module stores only abstracted playbooks and evidence IDs. It does not include:

- raw screenshots;
- meeting recordings;
- raw `other.txt`;
- production schema or identifiers;
- real customer data;
- internal thresholds, performance or staff metrics.

## Label maturity

`LabelMaturitySimulator` creates a synthetic observed-label view:

- hidden `fraud_label` remains offline evaluation truth;
- investigation selection is non-random;
- labels are observed after a long-tailed lag;
- some outcomes are `INCONCLUSIVE`;
- unselected/pending rows remain unlabelled.

This demonstrates why unlabelled users cannot be treated as clean negatives and why threshold selection must use mature Development labels only.

## Distribution audit

The public profile checks broad qualitative properties:

- class imbalance;
- multi-month coverage;
- uncommon but observable risk scenarios;
- rare sanctions/PEP hits;
- long-tailed amounts and losses;
- risk-signal separation with noise;
- delayed event labels;
- case duplicates, priorities and long-tail handling time.

The ranges are public synthetic design targets, never production estimates.

## Integration boundary

```text
EvidenceGroundedStrategyAssistant
  -> evidence_grounded_strategy_plan.json
  -> strategy_request.json
  -> existing RiskStrategyCopilot
  -> deterministic backtest / stability / conflict / governance
```

The assistant cannot:

- mark a strategy online;
- execute restrictions, freeze or rejection;
- move funds;
- file a regulatory report;
- transform synthetic metrics into production claims.
