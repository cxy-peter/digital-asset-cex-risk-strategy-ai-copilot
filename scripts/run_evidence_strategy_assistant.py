from __future__ import annotations

import argparse
from pathlib import Path

from risk_copilot.evidence_assistant import AssistantRequest, EvidenceGroundedStrategyAssistant


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an evidence-grounded synthetic CEX risk-strategy work package.")
    parser.add_argument("--project-root", default=None)
    parser.add_argument("--request-id", default="REQ-EVID-001")
    parser.add_argument("--query", default="Identify rapid fiat-in, conversion and chain-withdrawal risk with graph evidence.")
    parser.add_argument("--business-objective", default="Reduce suspicious fund-flow exposure while keeping false positives and manual-review volume within capacity.")
    parser.add_argument("--risk-domain", default="fund_security")
    parser.add_argument("--event-code", default="ChainWithdraw")
    parser.add_argument("--target-label", default="fraud_label")
    parser.add_argument("--max-alert-rate", type=float, default=0.05)
    parser.add_argument("--minimum-precision", type=float, default=0.50)
    parser.add_argument("--minimum-recall", type=float, default=0.05)
    parser.add_argument("--review-capacity", type=int, default=300)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--skip-distribution-audit", action="store_true")
    parser.add_argument("--skip-label-maturity", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    assistant = EvidenceGroundedStrategyAssistant.create(args.project_root)
    request = AssistantRequest(request_id=args.request_id, query=args.query, business_objective=args.business_objective, risk_domain=args.risk_domain, event_code=args.event_code, target_label=args.target_label, maximum_alert_rate=args.max_alert_rate, minimum_precision=args.minimum_precision, minimum_recall=args.minimum_recall, review_capacity=args.review_capacity)
    plan, paths = assistant.run(request, audit_demo_data=not args.skip_distribution_audit, simulate_label_maturity=not args.skip_label_maturity, output_dir=args.output_dir)
    print(f"decision={plan.decision.value}")
    print(f"scenario={plan.inferred_scenario}")
    if plan.distribution_audit is not None:
        print(f"distribution_status={plan.distribution_audit.overall_status.value}")
    for name, path in paths.items():
        print(f"{name}={Path(path)}")


if __name__ == "__main__":
    main()
