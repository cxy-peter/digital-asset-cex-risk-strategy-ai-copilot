# Payment Risk & Anti-Fraud Extension

## 1. Why this module exists

The original prototype reconstructed digital-asset strategy governance. The V1.3 knowledge-system work added a complete traditional-payment layer: actors and responsibility, payment lifecycle, 3DS, authorization, credential lifecycle, merchant underwriting, disputes, cross-border localization, stablecoins, Agentic Commerce and payment-specific strategy engineering.

The code turns that knowledge into **auditable synthetic objects**, not a generic payment chatbot.

## 2. Responsibility before modeling

A payment-risk result is meaningful only when the decision owner, available evidence, action authority and liability exposure are explicit.

| Actor | Typical evidence | Typical control | Main exposure |
|---|---|---|---|
| Merchant | order, customer account, fulfilment, support | checkout, 3DS request, capture/refund, evidence retention | CNP fraud, friendly fraud, false decline |
| Gateway/Orchestrator | route, retry, token and PSP response | token, routing, guarded retry, webhook normalization | duplicate payment, channel concentration |
| PayFac/MOR | sub-merchant, portfolio, settlement | underwriting, reserve, settlement delay | merchant fraud, laundering, credit exposure |
| Acquirer | merchant portfolio, clearing and network data | acceptance, funding and network controls | scheme monitoring, chargebacks |
| Network | cross-ecosystem auth/dispute signals | message rules, 3DS/token programs, reason codes | ecosystem integrity and liability allocation |
| Issuer | account, credential, limits and cross-merchant history | authorization, step-up, credential suspension | stolen credential, ATO, cardholder protection |

## 3. Authentication is not authorization

The module models 3DS and issuer authorization separately:

- 3DS may be frictionless, challenged, failed, unavailable or only acknowledged.
- A successful authentication may support liability evidence but does not create issuer approval.
- Authorization, capture, clearing and settlement remain separate transitions.
- Liability assessment is only a prototype explanation; real network rules, contract terms, reason code and evidence deadlines remain decisive.

## 4. Fourteen scenarios

Each scenario has signals, controls, reason codes and an explanation. Thresholds are synthetic demonstration values.

1. `PAY-CARD-TESTING`
2. `PAY-CNP-STOLEN`
3. `PAY-ATO`
4. `PAY-APP-BEC`
5. `PAY-FRIENDLY-FRAUD`
6. `PAY-REFUND-ABUSE`
7. `PAY-SUBSCRIPTION`
8. `PAY-MERCHANT-FRAUD`
9. `PAY-MERCHANT-CREDIT`
10. `PAY-TRANSACTION-LAUNDERING`
11. `PAY-PAYOUT-MULE`
12. `PAY-DUPLICATE-API`
13. `PAY-DCC-CONSENT`
14. `PAY-AGENTIC-AUTH`

## 5. Six state machines

The following objects are intentionally not merged into one `risk_status`:

- payment order;
- authentication/3DS;
- authorization-capture-settlement;
- risk decision;
- merchant risk lifecycle;
- dispute/case.

Illegal transitions and terminal-state mutation are rejected by deterministic code.

## 6. Control layer

Recommended controls are ordered by impact and conflict precedence. A recommendation does not perform an action.

- reversible/low-friction: PASS, MONITOR, network token, route, guarded retry;
- evidence-gathering: 3DS, step-up, warning, manual capture, delay, review;
- exposure controls: refund limit, reserve hold, settlement delay, payout restriction;
- high impact: block/reject/compliance escalation candidate.

Real execution requires a business-system permission check, object state validation, audit log and human review where required.

## 7. Dispute Evidence Contract

Evidence is designed during checkout and fulfilment rather than reconstructed after a chargeback. Reason families are mapped to:

- identity and authentication;
- issuer authorization;
- device/IP;
- order and price;
- fulfilment or digital usage;
- consent and recurring notice;
- cancellation and refund;
- customer communication;
- idempotency, authorization/capture and reversal timeline.

The service returns evidence completeness, missing fields, expected recovery, operating cost and a review recommendation. It never submits representment automatically.

## 8. Merchant lifecycle

Merchant risk combines three dimensions:

- compliance: KYB/UBO, industry, geography and sanctions;
- fraud: non-fulfilment, transaction laundering, deceptive descriptor/website and abnormal refunds;
- credit: unsettled chargebacks, negative balance and reserve shortfall.

Underwriting therefore links to reserve, delayed settlement, payout restriction, ongoing monitoring, remediation and exit.

## 9. Joint optimization

Approval uplift alone is not treated as success. The catalog includes:

- checkout conversion;
- authentication success/challenge;
- authorization approval;
- soft-decline recovery and false decline;
- fraud, refund and chargeback;
- alert/review capacity;
- captured loss;
- dispute win and evidence completeness;
- operating cost, settlement exposure and net loss.

## 10. Stablecoin and Agentic-Commerce overlays

Stablecoin payments add issuer/reserve, wallet/address, sanctions, smart-contract/bridge, liquidity/FX and reconciliation risks. Agentic payments add delegated authority, spend limit, token/purpose scope, agent identity, human approval, notification and revocation.

## 11. Boundary

- synthetic data only;
- provider-neutral schema;
- post-internship research extension;
- no production connection;
- no automatic enforcement;
- no real dispute determination;
- no regulatory filing.
