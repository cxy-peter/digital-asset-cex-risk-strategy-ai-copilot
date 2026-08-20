# Digital Asset & Payment Risk Strategy AI Copilot

> **Internship-derived personal prototype with post-internship evidence and payment extensions.** The CoinTR-derived core reconstructs desensitized Rule Engine, FEP, strategy backtracking, Risk Graph, user-scoring, Ticket and CMS/STR concepts with synthetic data. The evidence-grounded assistant abstracts OCR/TXT-derived problem decomposition and delivery workflows without publishing raw materials. The payment module is provider-neutral research added after the internship; it does **not** claim that CoinTR operated a card-acquiring stack or that this code was deployed in production.

The project separates three responsibilities:

- **AI Agents** understand natural-language risk requests, retrieve SOP/typology/product knowledge, propose candidates, inspect graph and payment-liability evidence, preserve disagreement, and draft review memos.
- **Deterministic engines** own feature contracts, point-in-time validation, Train/Development/OOT separation, model fitting, Rule DSL execution, state machines, stability/conflict metrics, dispute-evidence completeness, distribution audits and audit records.
- **Human reviewers and permissioned business systems** own high-impact enforcement, merchant restrictions, dispute decisions, release acceptance, and external regulatory filing.

An Agent may recommend or explain. It cannot silently change production state, execute punishment, move funds, decide a real network dispute, or submit a regulatory report.

## 1. Architecture

```text
Natural-language risk request
        ↓
Evidence-grounded 5716 decomposition
        ↓
Intent Router Agent
        ↓
┌──────────────────────────────────────────────────────────┐
│ Scenario & Typology Agent                                │
│ Feature & Model Agent                                    │
│ Risk Graph & Behavior Agent                              │
│ Payment Flow & Liability Agent                           │
│ Governance & CMS/STR Agent                               │
└──────────────────────────────────────────────────────────┘
        ↓ parallel evidence gathering
AI Strategy Proposal Agent
        ↓
Candidate Strategy Generator
        ↓
Deterministic Backtest / Stability / Conflict Engines
        ↓
Lead Risk Strategy Agent
        ↓
Simulation package + independent-review memo
        ↓
Product delivery / acceptance / effectiveness lifecycle
```

The default mode is offline and reproducible. Optional LangGraph ReAct reviewers can call governed, read-only MCP-style tools; the deterministic board remains runnable without an external model.

## 2. CoinTR-derived strategy test platform

```text
Risk request / historical black samples
→ event and FEP feature-contract validation
→ expert / AI-planned / decision-tree / XGBoost / graph candidates
→ Train → Development → OOT evaluation
→ SIMULATION
→ independent second review
→ release-readiness package
→ blank three-working-day observation template
→ effectiveness ticket
→ weekly/monthly retain, tune, pause or retire decision
```

Core controls include:

- registered, decision-time-available features only;
- real-time, H+1, T+1 and offline semantics;
- missingness, quantiles, AUC, KS, IV, Lift, PSI and direction profiling;
- Rule DSL, three-level tags, action precedence, white-list and conflict checks;
- monthly/bootstrap stability;
- strategy overlap, Jaccard, containment, incremental true positives/recall and duplicate workload;
- user Onboarding + T+1 scoring with durable manual-override protection;
- CMS/STR **internal candidate case** generation only, with human review and no external submission.

## 3. Evidence-grounded AI Strategy Assistant (v0.10)

The new assistant adds the upstream reasoning and delivery objects that were previously implicit in the OCR/TXT evidence.

### 3.1 Seven-layer macro-to-micro decomposition

1. macro objective;
2. regulatory or business requirement;
3. business flow and state;
4. system, event and data;
5. risk intelligence;
6. strategy, action and governance;
7. validation, outcome and ownership.

Each layer generates an interview-ready answer template, required evidence and a concrete output object.

### 3.2 Thirteen-stage model-analysis playbook

The playbook covers:

- business decision and operations capacity;
- label source, maturity and selection bias;
- full-path black-sample analysis;
- Point-in-Time and feature lineage;
- AUC, KS, IV/WOE, Lift and PSI;
- Logistic Regression, shallow Decision Tree and XGBoost;
- Risk Graph relationship evidence;
- chronological OOT and bootstrap stability;
- strategy overlap, Swap-in/Swap-out and incremental value;
- 1:1 simulation, second review and post-launch effectiveness.

### 3.3 Synthetic distribution and observed-label audits

The assistant checks broad public design ranges for class imbalance, long-tailed amounts, rare screening hits, overlapping scenarios, delayed event labels and case-operation noise. These are **not production distribution estimates**.

A separate simulated observed-label view adds non-random investigation selection, delayed maturity and `INCONCLUSIVE` outcomes while retaining `fraud_label` as hidden synthetic evaluation truth.

### 3.4 Eleven-stage delivery workflow

```text
Demand intake
→ BRD
→ PRD
→ technical design
→ schedule/admission
→ development/unit test
→ integration test
→ joint test acceptance
→ joint production acceptance
→ release
→ RCA and iteration
```

The assistant records owners, collaborators, inputs, outputs, exit gates and rollback paths.

Run it with:

```bash
risk-copilot generate-data --force
python scripts/run_evidence_strategy_assistant.py \
  --request-id REQ-ATO-001 \
  --query "Detect account takeover after a new device and sensitive-security change before chain withdrawal" \
  --business-objective "Reduce account-takeover loss while controlling user friction and manual-review workload" \
  --risk-domain account_security \
  --event-code ChainWithdraw
```

The generated `strategy_request.json` is compatible with the existing deterministic strategy workflow.

## 4. Payment Risk & Anti-Fraud extension (v0.9)

The payment module translates the V1.3 knowledge system into runnable, provider-neutral objects.

### 4.1 Responsibility and control map

It distinguishes the information, control authority and exposure of:

- customer and merchant;
- gateway and payment orchestrator;
- PayFac and Merchant of Record;
- acquirer, card network and issuer;
- sponsor bank.

This prevents a merchant-side model from being described as if it had issuer, network or acquirer data and powers.

### 4.2 Fourteen scenarios

- Card Testing;
- CNP stolen credential;
- Account Takeover followed by payment/payout;
- APP/BEC scam;
- Friendly Fraud;
- Refund Abuse;
- Subscription/MIT dispute;
- Merchant Fraud/non-fulfilment;
- Merchant Credit/settlement exposure;
- Transaction Laundering;
- Payout Mule;
- Duplicate Payment/API idempotency failure;
- DCC consent/disclosure failure;
- Agentic-Commerce delegated-authority failure.

### 4.3 Six independent state machines

1. payment order;
2. 3DS/authentication;
3. authorization-capture-clearing-settlement;
4. risk decision;
5. merchant risk lifecycle;
6. dispute/case.

Terminal states are immutable and illegal transitions are rejected. Authentication success does not imply issuer authorization, capture or settlement.

### 4.4 Payment controls and evidence

The deterministic module can recommend, but not execute:

- Request 3DS / step-up authentication;
- request network token;
- guarded retry / alternative acquirer route;
- manual capture / delay;
- beneficiary warning;
- manual review;
- refund limit;
- reserve hold / settlement delay / payout restriction;
- block or compliance-escalation candidate.

The dispute-evidence contract maps reason-code families to authentication, authorization, order, fulfillment/usage, consent, cancellation, communication, idempotency and refund/reversal evidence. It also compares expected recovery with operating cost before recommending representment review.

### 4.5 Stablecoin and Agentic-Commerce overlays

Stablecoin assessment adds issuer/reserve, wallet/address, sanctions, smart-contract/bridge, liquidity/FX and reconciliation evidence. Agentic commerce adds delegated spend limits, purpose/token scope, agent identity, real-time notification and human approval. LLMs never own irreversible execution.

## 5. Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e '.[dev]'

risk-copilot generate-data --force
python scripts/run_evidence_strategy_assistant.py
risk-copilot ai-agent
risk-copilot strategy
risk-copilot payment-ready
pytest -q
```

Start the API and interactive console:

```bash
risk-copilot serve --host 127.0.0.1 --port 8000
# http://127.0.0.1:8000/console
```

Payment endpoints:

- `GET /payment/catalog`
- `POST /payment/assess`
- `POST /payment/dispute`

Optional live ReAct reviewers:

```bash
pip install -e '.[agent]'
cp .env.example .env
risk-copilot ai-agent --live-react
```

## 6. Repository structure

```text
src/risk_copilot/
├── agents/                 # deterministic and AI-facing Agent nodes
├── ai/                     # candidate proposal and specialist advisory board
├── analysis/               # stability and portfolio-conflict engines
├── evidence_assistant/     # 5716 decomposition, model playbook, data/label audit and delivery workflow
├── features/               # FEP registry and feature profiling
├── models/                 # LR, Tree and XGBoost pipelines
├── graph/                  # Risk Graph enrichment and explanation
├── rules/                  # Rule DSL, generation and backtest
├── governance/             # simulation, review, version and effectiveness ticket
├── integrations/           # internal CMS/STR candidate preview
├── payment/                # actors, 14 scenarios, 6 state machines, dispute evidence
├── reporting/              # Markdown/HTML/JSON/CSV artifacts
├── react_app.py            # optional live LLM/ReAct specialist board
├── mcp_server.py           # optional governed MCP tool server
├── api.py                  # FastAPI console and payment endpoints
└── orchestrator.py         # end-to-end multi-Agent workflow
```

## 7. Key outputs

- `outputs/evidence_strategy_assistant/EVIDENCE_GROUNDED_STRATEGY_PLAN.md`
- `outputs/evidence_strategy_assistant/evidence_grounded_strategy_plan.json`
- `outputs/evidence_strategy_assistant/synthetic_distribution_audit.json`
- `outputs/evidence_strategy_assistant/strategy_request.json`
- `outputs/index.html`
- `outputs/strategy_demo/strategy_dashboard.html`
- `outputs/strategy_demo/ai_advisory_board.md`
- `outputs/strategy_demo/strategy_stability_analysis.json`
- `outputs/strategy_demo/strategy_conflict_analysis.json`
- `outputs/strategy_demo/strategy_test_environment.json`
- `outputs/strategy_demo/strategy_effectiveness_ticket.json`
- `outputs/strategy_demo/cms_str_integration.json`
- `outputs/payment_ready_suite/payment_ready_suite.json`
- `outputs/payment_ready_suite/PAYMENT_READY_SUITE.md`

## 8. Technology stack

- Python, Pandas, NumPy, SciPy;
- scikit-learn and XGBoost;
- NetworkX Risk Graph;
- Pydantic schemas and deterministic payment state machines;
- SQLite strategy/version/effectiveness registry;
- FastAPI interactive console;
- Plotly/Jinja2 reporting;
- optional LangGraph ReAct and FastMCP tool services.

## 9. Truthfulness and resume wording

Accurate description:

> During the internship I participated in digital-asset risk-product, user-scoring, Risk Graph, CMS/STR and main-site AI capability research. After the internship, I independently reconstructed a synthetic-data Risk Strategy AI Copilot, added an evidence-grounded problem/model/delivery planning layer, and later extended it with provider-neutral card-payment, merchant-risk, dispute-evidence, stablecoin and agentic-commerce modules based on separately built risk knowledge systems.

Do not claim:

- production deployment at CoinTR;
- use of real customer PII or production transactions;
- that CoinTR operated the payment stack modeled here;
- automatic enforcement, fund movement or regulatory filing;
- that all team products were personally developed;
- production performance based on synthetic metrics;
- that raw OCR/TXT evidence is stored in this public repository.

KEP regulatory-email automation and the Anti-Fraud operations metrics system are maintained as separate projects.

See `docs/COINTR_OCR_PROCESS_ALIGNMENT_REPORT.md`, `docs/EVIDENCE_GROUNDED_AI_STRATEGY_ASSISTANT.md`, `docs/PAYMENT_RISK_EXTENSION.md`, `docs/KNOWLEDGE_V1_3_MAPPING.md` and `docs/RESUME_AND_INTERVIEW.md` for detailed scope and interview wording.
