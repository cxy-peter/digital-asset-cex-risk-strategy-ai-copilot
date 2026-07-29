# AI Agent Architecture

## 1. Why the project is an Agent system rather than only a model/rule demo

The system contains an explicit planning–tool–observation–synthesis loop:

1. A natural-language risk request is routed to a risk domain and event.
2. Specialist Agents retrieve different evidence instead of sharing one oversized prompt.
3. The AI proposal layer produces auditable candidate Rule DSL objects from a strict feature whitelist.
4. Deterministic tools return model, backtest, graph, stability and conflict observations.
5. The Lead Risk Strategy Agent synthesizes the specialist findings and recommends the next review action.
6. Human review and deterministic governance remain authoritative.

The system therefore uses AI for **planning, evidence selection, explanation and critique**, while numerical truth and lifecycle control stay outside the language model.

## 2. Comparison with the stock-investment-advisor Agent structure

| Stock adviser structure | Risk Strategy AI Copilot |
|---|---|
| Fundamental Agent | Scenario & Typology Agent |
| Technical Agent | Feature & Model Agent |
| Valuation Agent | Risk Graph & Behavior Agent |
| News Agent | Governance & CMS/STR Agent |
| Summary Agent | Lead Risk Strategy Agent |
| Market-data MCP tools | FEP, SOP, graph, backtest, stability, conflict and CMS tools |
| Investment report | Strategy-review and simulation-release package |

The structure is borrowed, but the business semantics, tools, constraints and artifacts are reconstructed from the internship platform rather than from the stock project.

## 3. AI modes

### Deterministic offline board

Runs without an external model and produces reproducible structured reviewer bundles. It is used in tests and default demos.

### Live ReAct board

Uses LangGraph `create_react_agent` and an OpenAI-compatible endpoint. Four reviewers run in parallel and call read-only tools. The Lead Agent then creates a professional review memo.

The live board cannot call status-changing or punitive tools.

## 4. Tool boundary

Read-only AI tools include:

- validated strategy package;
- feature search and event contracts;
- SOP/typology hybrid retrieval;
- product dependency mapping;
- graph path explanation;
- stability analysis;
- strategy overlap/incremental-value analysis;
- test-environment and CMS/STR previews;
- strategy version history.

State-changing operations are deterministic and separately permissioned.

## 5. Acceptance criteria

- no feature outside the registered whitelist may appear in an AI candidate;
- every AI rule must parse into the Rule DSL schema;
- AI candidates always start as Draft/Simulation-only;
- OOT is never used to select thresholds;
- Lead Agent recommendations cannot mutate strategy status;
- CMS/STR output remains internal and human-reviewed;
- all AI findings retain evidence references and explicit uncertainty.
