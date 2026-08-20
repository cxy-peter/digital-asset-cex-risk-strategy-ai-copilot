# CoinTR OCR / TXT Evidence Alignment Report

> Scope: compare the public synthetic repository with the internship-derived OCR/TXT workflow, then define the changes required for an evidence-grounded AI Strategy Assistant. Raw screenshots, meeting recordings, names, production data, internal thresholds and `other.txt` are intentionally not committed.

## 1. Executive conclusion

The current repository is already **strongly aligned with the middle and downstream risk-strategy workflow**:

- event and feature contracts;
- Development-only feature profiling;
- Logistic Regression, shallow Decision Tree and XGBoost;
- Risk Graph enrichment and path explanations;
- Train / Development / chronological OOT separation;
- Rule DSL and deterministic backtesting;
- monthly/bootstrap stability and portfolio conflict analysis;
- simulation, independent second review and version/payload binding;
- effectiveness tickets and internal CMS/STR candidate previews;
- human-in-the-loop and no automatic external regulatory filing.

The principal gap was not another model. It was the **upstream reasoning and delivery layer**:

1. the `IMG_5716` macro-to-micro decomposition was not a structured output;
2. the full demand/BRD/PRD/engineering/test/acceptance/release/RCA process was not represented;
3. the synthetic data was intentionally designed, but no transparent source-like distribution contract audited it;
4. the hidden synthetic truth was cleaner than real investigation labels and did not expose label maturity, investigator selection and inconclusive outcomes as a separate view;
5. the OCR/TXT model-analysis standards existed in notes but were not available as a single executable playbook.

This update adds those five layers without changing the existing deterministic strategy engine.

## 2. Evidence boundary

The public repository uses four evidence levels:

| Level | Meaning | Permitted wording |
|---|---|---|
| A — direct internship work | Work directly performed or materially supported during the internship | “Participated in”, “developed a checking tool”, “clarified requirements”, “performed research/testing” |
| B — team system/material | Existing or planned team capability observed in screenshots, documents or meetings | “Reviewed”, “mapped”, “participated in requirement analysis”, not “independently built” |
| C — personal prototype | Post-internship reconstruction using synthetic data and sanitized semantics | “Independently reconstructed a synthetic prototype” |
| D — external research | Payment, fraud, credit-risk and market-abuse research | “Extended the knowledge system”, not an internship result |

No public file contains raw OCR/TXT evidence. The assistant records sanitized evidence IDs only.

## 3. Process-alignment matrix

| Source workflow | Current repository | Alignment | Remaining gap / update |
|---|---|---:|---|
| Macro objective → requirement → workflow → system/data → feature/model/function → solved problem | Previously implicit in requests and reports | Partial | Added seven-layer `ProblemLayer` output based on the 5716 method |
| Known / Unknown / Contradiction / Owner / Evidence before cross-team meetings | Event and feature contracts existed | Partial | Added explicit owner/evidence questions to problem decomposition and delivery stages |
| Event centre and decision-time feature contract | `configs/events.yaml`, `configs/features.yaml`, feature registry | Strong | Keep; add source-evidence mapping and distribution audit |
| Real-time / H+1 / T+1 / offline and derived-feature classification | Feature freshness and `available_at` already modeled | Strong | Keep; expose in evidence plan |
| Feature create / iterate / retire | Registry and effectiveness concepts existed | Partial | Added assistant lifecycle `DRAFT → ... → RETIRED` and evidence requirements |
| Black/white sample and full behaviour-chain analysis | Behaviour Agent, transactions, golden AML paths | Strong | Add formal model-analysis playbook and label-maturity view |
| AUC / KS / IV / Lift / PSI and directional checks | `FeatureProfiler` implements them on Development | Strong | Added decision standards and failure actions; avoid universal production claims |
| LR baseline | `ModelTrainer` | Strong | Clarified its role: direction, calibration and comparison anchor |
| Shallow Decision Tree → candidate rule | Tree trainer and rule extraction | Strong | Added leaf-size, monotonicity and path-stability standards |
| XGBoost nonlinear ranking | `ModelTrainer` | Strong | Clarified train-only sampling and Development-only threshold selection |
| LightGBM comparison | Not a dependency in the current CEX repo | Gap by design | Documented as an optional efficiency benchmark, not claimed as implemented |
| Risk Graph one-hop/two-hop, strong/weak relations and super-node control | Graph module and generated relation edges | Strong | Added graph-specific model standards and false-positive controls |
| New/old strategy overlap, incremental contribution and action conflict | Conflict analysis | Strong | Added Swap-in/Swap-out as a mandatory strategy decision step |
| 1:1 simulation before release | Governance test environment | Strong | Kept as a blocking deterministic gate |
| Independent second review and exact version/payload evidence | Company lifecycle | Strong | Kept; added upstream BRD/PRD and acceptance artefacts |
| First working-day observation and weekly/monthly effect review | Blank observation template and effect ticket | Partial | Assistant now links release, operations outcomes and retain/tune/pause/retire |
| CMS/STR AI assistance with human confirmation | Internal candidate preview only | Strong | Boundary retained: no automatic external filing |
| Demand pool → BRD → PRD → design → schedule → development → integration test → test acceptance → production acceptance → release → RCA | Not represented as a structured object | Gap | Added 11-stage `DeliveryStage` playbook with owners, inputs, outputs, gates and rollback |
| Anti-Fraud case ageing, evidence quality and re-reply feedback | Separate case dataset and operational project boundary | Partial | Added as post-launch effectiveness inputs; kept separate from strategy-engine claims |

## 4. Data-distribution comparison

### 4.1 What already matches qualitatively

The current synthetic generator already mirrors the **shape of the problem**, not production values:

- highly imbalanced fraud labels;
- overlapping latent mechanisms: rapid cash-out, ATO, campaign abuse, AML and graph rings;
- log-normal / long-tailed transaction and loss amounts;
- rare sanctions and PEP hits;
- risk signals with noise rather than deterministic one-feature labels;
- account, device, IP, email, KYC ID and withdrawal-address relations;
- weak IP edges and stronger identity/device/address edges;
- fiat-in → convert → chain-out and internal-layering golden paths;
- transaction labels observed after a delay;
- case data with duplicate records, missing evidence, status dwell time and long-tail handling time.

These properties are materially closer to the OCR workflows than a balanced classification toy dataset.

### 4.2 What cannot be claimed

The OCR/TXT evidence does not contain a complete, disclosable production data dictionary or actual population distributions. Therefore the project cannot claim that any of the following match CoinTR exactly:

- fraud prevalence;
- ATO, AML or rapid-cashout prevalence;
- transaction amount or loss distribution;
- KYC-level distribution;
- strategy precision, recall or lift;
- case backlog or SLA distribution;
- investigator selection or label-maturity period.

The new `synthetic_distribution_profile.yaml` uses broad, sanitized design ranges solely to prevent an unrealistic demo.

### 4.3 Remaining synthetic-data gaps

1. **Latent truth is easier than real labels.** Fraud truth is generated from known synthetic mechanisms, while real labels are delayed, incomplete and investigation-selected.
2. **Snapshot counters are often generated directly.** A production feature platform would recompute many counters from event-level data.
3. **Time drift is limited.** The current uniform 180-day window does not fully model attack waves, product changes or macro/channel shifts.
4. **Normal-but-risky archetypes need expansion.** Market makers, corporate treasury, travel, household-device sharing and legitimate high-frequency users should deliberately resemble risk signals.
5. **Outcome feedback is simplified.** Real RFI/EDD/CMS outcomes can be inconclusive, corrected, reopened or delayed.

The update addresses item 1 with a simulated observed-label view and item 2 partially through an explicit recommendation to reconcile event-derived and snapshot features. Items 3–5 remain future data-generator work.

## 5. New evidence-grounded AI Strategy Assistant

The new assistant is an upstream planning and quality-control layer around the existing strategy workflow.

```text
Risk request
  ↓
5716 seven-layer decomposition
  ↓
Evidence map + business flow + owner/decision-time questions
  ↓
Synthetic-distribution and label-maturity audit
  ↓
Feature-family and model-analysis playbook
  ↓
Versioned strategy-design object
  ↓
Existing AI proposal + deterministic backtest/stability/conflict pipeline
  ↓
11-stage delivery workflow
  ↓
Effectiveness ticket and retain/tune/pause/retire decision
```

### 5.1 AI responsibilities

- interpret the business/risk request;
- retrieve the sanitized playbook and evidence IDs;
- propose feature families, transformations and candidate strategy objects;
- explain model, graph and operational evidence;
- identify missing owners, data or acceptance criteria;
- draft BRD/PRD/test-review artefacts.

### 5.2 Deterministic responsibilities

- data lineage and point-in-time validation;
- feature calculation;
- AUC, KS, IV/WOE, Lift, PSI, PR-AUC and calibration;
- LR/Tree/XGBoost training;
- Rule DSL execution;
- OOT, bootstrap, overlap and incremental-value calculations;
- lifecycle state transitions, versions, payload hashes and audit records.

### 5.3 Human responsibilities

- business objective and action approval;
- resolution of requirement contradictions;
- high-impact restriction/freeze decisions;
- second review and release acceptance;
- RFI/EDD/CMS/STR conclusions and external regulatory submission.

## 6. Model-analysis sequence, key points and standards

The assistant exposes a 13-stage playbook. The order matters.

### 6.1 Decision before model

Define event, population, action, alert-rate limit, review capacity and harm. A model with a high AUC but no operational decision is not a strategy.

### 6.2 Label contract

Document label source, maturity, selection bias and inconclusive outcomes. Unlabelled rows are not automatically clean. OOT labels must remain hidden until the candidate is frozen.

### 6.3 Full-path black-sample analysis

Walk through registration/KYC, login/security changes, funding, trading/convert, internal transfer, chain withdrawal, device/IP and graph relations. Identify both the risk mechanism and normal-business alternatives.

### 6.4 Data/feature contract

For every feature record source, owner, type, freshness, window, aggregation, `available_at`, PII level, expected direction and lifecycle. Any point-in-time violation is blocking.

### 6.5 Single-feature effectiveness

Evaluate coverage, missingness, bad/good distributions, AUC, KS, IV/WOE, Lift at actual operating depth, PSI and direction consistency. The repository's current numeric defaults are demo gates, not universal production thresholds.

### 6.6 Logistic Regression

Use it as a linear direction/calibration baseline. Unexpected coefficient direction or poor calibration is a reason to inspect features, encoding, segment mixing or leakage.

### 6.7 Shallow Decision Tree

Use it to discover explainable interactions and candidate thresholds. Reject tiny, unstable or risk-order-reversing leaves. Tree paths enter simulation; they are not automatically online rules.

### 6.8 XGBoost and optional LightGBM

Use XGBoost for nonlinear tabular ranking after label/data quality is established. Sampling belongs to Train only; Development and OOT retain natural distributions. LightGBM can be added as an efficiency comparison, but the current CEX repository does not claim it is implemented.

### 6.9 Risk Graph

Use typed strong/weak relations, one-hop/two-hop policies and super-node suppression. A graph score must be accompanied by a path and supporting behaviour/fund-flow evidence.

### 6.10 Chronological OOT and robustness

Evaluate by period, bootstrap confidence intervals, feature-direction consistency and drift. OOT cannot be repeatedly used to select features or thresholds.

### 6.11 Strategy translation and incremental value

Convert evidence into:

```text
Event + Population + Feature/Window + Threshold + Exclusion
+ Action + Version + Evidence + Monitoring + Rollback
```

Then test containment, Jaccard, incremental true positives/recall, duplicate workload, action conflicts and Swap-in/Swap-out.

### 6.12 Simulation and second review

Bind the exact data snapshot, event contract, feature version and payload hash. High-impact actions require additional approval. AI cannot change status.

### 6.13 Post-release effect loop

Monitor confirmed-positive rate, case ageing, evidence quality, complaints/appeals, feature PSI and action outcomes. Feed outcomes back as governed labels and decide retain, tune, pause or retire.

## 7. Resume/project wording

Recommended project wording after the branch is merged:

> **Digital-Asset Risk Strategy AI Copilot — personal synthetic-data project**  
> Based on internship-derived, sanitized risk-product and strategy-governance workflows, reconstructed an evidence-grounded AI Strategy Assistant covering macro-to-micro problem decomposition, event/feature contracts, label-maturity simulation, feature effectiveness (AUC/KS/IV/Lift/PSI), LR/Decision Tree/XGBoost and Risk Graph analysis, Rule DSL, chronological OOT, portfolio overlap, 1:1 simulation, independent review and strategy lifecycle management. AI proposes and explains candidates; deterministic engines calculate metrics and control state transitions; all high-impact actions and regulatory filing remain human-controlled.

Do not write that it was deployed at CoinTR, used production customer data, automatically froze accounts or submitted STRs.

## 8. Implemented files

```text
src/risk_copilot/evidence_assistant/
├── models.py
├── catalog.py
├── distribution.py
├── playbook.py
├── assistant.py
└── __init__.py

configs/
├── evidence_strategy_assistant.yaml
└── synthetic_distribution_profile.yaml

scripts/run_evidence_strategy_assistant.py
tests/test_evidence_strategy_assistant.py
```

The assistant writes:

- `evidence_grounded_strategy_plan.json`;
- `EVIDENCE_GROUNDED_STRATEGY_PLAN.md`;
- an existing-pipeline-compatible `strategy_request.json`;
- `proposal_context.json` for the AI planning layer;
- a synthetic-distribution audit;
- a compact simulated label-maturity preview.
