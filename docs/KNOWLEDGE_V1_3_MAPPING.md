# Knowledge System V1.3 to Code Mapping

| V1.3 knowledge object | Repository implementation | Output |
|---|---|---|
| Payment actors and responsibility | `payment/knowledge.py::PAYMENT_ACTOR_CATALOG` | `/payment/catalog` |
| 14 payment-risk scenarios | `payment/knowledge.py`, `payment/risk_engine.py` | `PaymentRiskAssessment.findings` |
| 102 payment features | `payment/knowledge.py::PAYMENT_FEATURE_GROUPS` | feature-group catalog |
| Six state machines | `payment/state_machines.py` | transition checks in payment suite |
| 3DS vs authorization separation | `PaymentRiskContext`, `assess_liability` | liability rationale |
| Token/credential lifecycle | token type, cryptogram and scope fields | CNP/agentic assessment |
| Routing/retry/idempotency | retry, decline and webhook fields | duplicate/API and optimization controls |
| Merchant underwriting and reserve | merchant, reserve and settlement fields | merchant fraud/credit findings |
| Dispute Evidence Contract | `payment/disputes.py` | completeness and net-recovery recommendation |
| Stablecoin overlay | stablecoin risk fields and overlay | warnings and sanctions boundary |
| Agentic authority | delegated limit, token scope, identity and approval | `PAY-AGENTIC-AUTH` |
| Joint business-risk metrics | `JOINT_METRICS` | catalog and scenario context |
| AI boundary | `PaymentFlowLiabilityAgent` | advisory context only |
| Deterministic truth/action boundary | risk engine and state machines | no automatic enforcement |

## Internship versus personal extension

**Internship-supported:** digital-asset risk-product research, Rule Engine/FEP/Risk Graph/CMS/STR structures, user-risk scoring, strategy lifecycle and main-site AI migration research.

**Post-internship personal work:** payment knowledge extraction, actors/lifecycle/14-scenario taxonomy, payment-specific feature catalog, deterministic payment engine, dispute evidence, state machines, stablecoin and Agentic-Commerce modules.
