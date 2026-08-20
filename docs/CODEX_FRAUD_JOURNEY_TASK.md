# Codex task — source-aligned CoinTR Fraud Journey

## Purpose

Replace generic upstream agent expansion with a focused reconstruction of the source Fraud Journey:

```text
objective and baseline
→ label/population contract
→ pair and behavior scope
→ bank data quality
→ numeric/ratio/count feature review
→ single-feature effectiveness
→ black-user full journey
→ behavior sequence
→ on-chain/Risk Graph
→ tree interactions
→ XGBoost/optional LightGBM benchmark
→ online/offline strategy and lifecycle
```

## P0 engineering changes

1. Remove any synthetic feature whose value is generated directly from `fraud_label` or a future case disposition.
2. Add label provenance and maturity: official Fraud, previously cleared Fraud, regulatory feedback, curated white, unlabelled, observed_at.
3. Add account-role flags so internal, market-maker, test and institution accounts can be excluded explicitly.
4. Add pair-level spot fields (`symbol`, `side`, `order_amount_usdt`) and chain destination type (`exchange`, `private`, `unknown`, `risky_service`).
5. Add event origin / parent-event identifiers before implementing the 60-minute session feature.
6. Replace the fixed 1:4 XGBoost undersampling assumption with a Development-only grid over no undersampling and 1:3/1:4/1:5; calibrate and report on natural-distribution chronological OOT.
7. Keep curated white users separate from generic label=0 rows.

## P1 changes

- Derive snapshot counters from event-level transactions and reconcile them with the user table.
- Add bank-code/user-name/masked-card data-quality fixtures.
- Add hard negatives: legitimate API traders, market makers, corporate treasury, shared devices/public IP and legitimate high-volume users.
- Add error-analysis artefacts for high-score label=0 users and missed black users.
- Add optional LightGBM only as a benchmark; do not claim it was used in the source report.

## Acceptance criteria

- Source-aligned analysis report and feature-coverage matrix are generated.
- No direct target-derived feature is available to the model.
- System-derived events cannot influence user-session density.
- 1:4 is not a fixed model default.
- Black/white/unlabelled semantics are explicit and tested.
- AI can summarize or propose, but deterministic code owns metrics and lifecycle state.
