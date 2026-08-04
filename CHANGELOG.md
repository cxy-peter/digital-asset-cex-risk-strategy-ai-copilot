# Changelog

## v0.9.0 - 2026-08-05

### Payment risk and anti-fraud extension

- Added provider-neutral payment actor and responsibility catalog covering customer, merchant, gateway/orchestrator, PayFac/MOR, acquirer, card network, issuer and sponsor bank.
- Added fourteen payment-risk scenarios: Card Testing, CNP stolen credential, ATO, APP/BEC, Friendly Fraud, Refund Abuse, Subscription/MIT, Merchant Fraud, Merchant Credit, Transaction Laundering, Payout Mule, Duplicate API, DCC Consent and Agentic Authorization.
- Added deterministic payment-risk assessment with control precedence, reason codes, liability evidence and explicit human-review/no-enforcement boundaries.
- Added six independent state machines for payment order, 3DS, authorization/capture/settlement, risk decision, merchant lifecycle and dispute/case.
- Added Dispute Evidence Contract and expected-net-recovery evaluation.
- Added stablecoin and Agentic-Commerce governance overlays.
- Added `Payment Flow & Liability Agent`, CLI command `risk-copilot payment-ready`, API endpoints and a runnable synthetic suite.

### Knowledge-system mapping

- Mapped the project to the V1.3 payment/anti-fraud knowledge system: actors, lifecycle, 102 payment-domain features, controls, joint metrics and evidence boundaries.
- Kept payment knowledge as a post-internship research extension rather than a claim about CoinTR's production architecture.

### Version and documentation

- Bumped package, API and module version to `0.9.0`.
- Updated README, delivery overview, resume/interview guide and validation documentation.

## v0.7.0 - 2026-07-29

### AI Agent layer

- Added four specialist Risk Strategy Agents and one Lead Agent.
- Added optional LangGraph ReAct reviewers and governed MCP-style read-only tools.
- Added structured AI candidate proposal with feature whitelist and Rule DSL validation.
- Added deterministic offline Agent Board for reproducible demos and tests.

### P0 enhancements

- Added FastAPI interactive strategy console.
- Added strategy overlap, containment, incremental value, duplicate workload and action-conflict analysis.
- Added monthly and bootstrap stability, feature-direction consistency and release gates.
- Integrated AI/stability/conflict findings into the independent-review package and effectiveness ticket.
