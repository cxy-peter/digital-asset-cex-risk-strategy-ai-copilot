from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .disputes import evaluate_dispute_evidence
from .models import (
    PaymentReadySuiteResult,
    PaymentRiskContext,
    ThreeDSResult,
    TokenType,
)
from .risk_engine import PaymentRiskEngine
from .state_machines import build_default_state_machines


def demo_contexts() -> list[PaymentRiskContext]:
    """Return deterministic synthetic cases spanning the payment-risk map."""

    return [
        PaymentRiskContext(
            transaction_id="DEMO-CARD-TEST-001",
            customer_id="CUS-001",
            merchant_id="MER-ECOM-001",
            amount=8.0,
            currency="USD",
            channel="ecommerce",
            new_device=True,
            proxy_or_datacenter_ip=True,
            card_count_per_device_10m=7,
            authorization_attempts_10m=14,
            small_authorization_count_10m=10,
            decline_ratio_10m=0.79,
            three_ds_result=ThreeDSResult.NOT_REQUESTED,
            token_type=TokenType.NONE,
        ),
        PaymentRiskContext(
            transaction_id="DEMO-ATO-APP-002",
            customer_id="CUS-002",
            merchant_id="MER-A2A-001",
            amount=4800.0,
            currency="USD",
            channel="a2a",
            new_device=True,
            recent_password_or_2fa_change=True,
            first_beneficiary=True,
            beneficiary_risk_score=0.86,
            customer_confirmed_social_engineering=True,
            amount_step_up_ratio=5.4,
            trusted_device_history_days=1,
            new_payout_account=True,
        ),
        PaymentRiskContext(
            transaction_id="DEMO-MERCHANT-003",
            customer_id="CUS-003",
            merchant_id="MER-NEW-003",
            amount=640.0,
            currency="EUR",
            channel="ecommerce",
            cross_border=True,
            merchant_risk_score=0.84,
            merchant_age_days=28,
            expected_volume_gap=7.5,
            product_mcc_mismatch=True,
            descriptor_website_mismatch=True,
            refund_ratio_30d=0.41,
            chargeback_ratio_90d=0.036,
            reserve_coverage_ratio=0.35,
            settlement_exposure=85000.0,
        ),
        PaymentRiskContext(
            transaction_id="DEMO-SUBSCRIPTION-004",
            customer_id="CUS-004",
            merchant_id="MER-SUB-004",
            amount=79.0,
            currency="USD",
            channel="ecommerce",
            three_ds_result=ThreeDSResult.FRICTIONLESS,
            issuer_authorized=True,
            liability_shift=True,
            credential_on_file=True,
            merchant_initiated_transaction=True,
            consent_evidence=False,
            recurring_notice_sent=False,
            easy_cancellation_available=False,
            communication_evidence=False,
            digital_usage_evidence=True,
            prior_dispute_count_180d=2,
        ),
        PaymentRiskContext(
            transaction_id="DEMO-AGENT-STABLE-005",
            customer_id="CUS-005",
            merchant_id="MER-AGENT-005",
            amount=12000.0,
            currency="USDC",
            channel="stablecoin",
            agentic_payment=True,
            delegated_spend_limit=2500.0,
            human_approval_present=False,
            token_scope_risk=0.91,
            agent_identity_assurance=0.42,
            stablecoin_payment=True,
            stablecoin_issuer_risk=0.62,
            wallet_address_risk=0.79,
            sanctioned_address_hit=False,
            smart_contract_risk=0.58,
            liquidity_fx_exposure=0.44,
            reconciliation_break_count=3,
        ),
    ]


def _state_machine_checks() -> dict[str, list]:
    checks: dict[str, list] = {}
    for name, machine in build_default_state_machines().items():
        current = machine.spec.initial_state
        results = []
        # Exercise one legal transition and one illegal/terminal mutation check.
        next_state = sorted(machine.spec.transitions.get(current, []))[0]
        first = machine.transition(current, next_state)
        results.append(first)
        illegal_target = "__INVALID__"
        results.append(machine.transition(next_state, illegal_target))
        checks[name] = results
    return checks


def run_payment_ready_suite(
    output_dir: str | Path,
    *,
    contexts: Iterable[PaymentRiskContext] | None = None,
) -> PaymentReadySuiteResult:
    """Run the post-internship payment extension with synthetic evidence only."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    engine = PaymentRiskEngine()
    cases = list(contexts or demo_contexts())
    assessments = [engine.assess(case) for case in cases]

    dispute_results = [
        evaluate_dispute_evidence(
            cases[3],
            "subscription_or_recurring",
            expected_recovery=79.0,
            operating_cost=25.0,
        ),
        evaluate_dispute_evidence(
            cases[2],
            "goods_not_received",
            expected_recovery=640.0,
            operating_cost=36.0,
        ),
        evaluate_dispute_evidence(
            cases[0],
            "processing_error",
            expected_recovery=8.0,
            operating_cost=20.0,
        ),
    ]
    state_checks = _state_machine_checks()

    result = PaymentReadySuiteResult(
        assessments=assessments,
        dispute_evidence=dispute_results,
        state_machine_checks=state_checks,
    )

    json_path = output / "payment_ready_suite.json"
    json_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    markdown_path = output / "PAYMENT_READY_SUITE.md"
    lines = [
        "# Payment Risk & Anti-Fraud Ready Suite",
        "",
        "> Post-internship extension using synthetic data. No production connection, automatic enforcement, or regulatory submission.",
        "",
        "## Assessments",
        "",
        "| Transaction | Score | Decision | Scenarios | Controls |",
        "|---|---:|---|---|---|",
    ]
    for assessment in assessments:
        lines.append(
            "| {tx} | {score:.1f} | {decision} | {scenarios} | {controls} |".format(
                tx=assessment.transaction_id,
                score=assessment.score,
                decision=assessment.decision.value,
                scenarios=", ".join(item.scenario_id.value for item in assessment.findings) or "none",
                controls=", ".join(item.value for item in assessment.recommended_controls),
            )
        )
    lines.extend(["", "## Dispute Evidence", ""])
    for dispute in dispute_results:
        lines.append(
            f"- `{dispute.reason_code_family}`: completeness {dispute.completeness_score:.1%}; "
            f"recommendation `{dispute.recommendation}`; missing {', '.join(dispute.missing_items) or 'none'}."
        )
    lines.extend(
        [
            "",
            "## Governance Boundary",
            "",
            "- All records are synthetic.",
            "- Payment knowledge is a post-internship research extension, not evidence that CoinTR operated a card-acquiring stack.",
            "- High-impact controls remain candidates requiring deterministic permissions and human review.",
            "- Authentication, issuer authorization, risk decisions, merchant lifecycle, and dispute cases remain separate state machines.",
        ]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result.artifacts.update({"json": str(json_path), "markdown": str(markdown_path)})
    # Re-write JSON with artifact paths included.
    json_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return result
