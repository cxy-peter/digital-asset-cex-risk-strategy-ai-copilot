from __future__ import annotations

from risk_copilot.payment import (
    PaymentDecision,
    PaymentRiskContext,
    PaymentRiskEngine,
    ThreeDSResult,
    build_default_state_machines,
    evaluate_dispute_evidence,
    run_payment_ready_suite,
)


def test_card_testing_generates_high_impact_candidate_without_enforcement() -> None:
    context = PaymentRiskContext(
        transaction_id="TEST-CARD-001",
        small_authorization_count_10m=9,
        authorization_attempts_10m=12,
        card_count_per_device_10m=6,
        decline_ratio_10m=0.75,
        new_device=True,
    )
    result = PaymentRiskEngine().assess(context)
    assert result.decision in {PaymentDecision.REVIEW, PaymentDecision.BLOCK_CANDIDATE}
    assert any(item.scenario_id.value == "PAY-CARD-TESTING" for item in result.findings)
    assert result.human_review_required is True
    assert result.automatic_enforcement_performed is False
    assert result.production_connection is False


def test_authentication_and_authorization_remain_separate() -> None:
    context = PaymentRiskContext(
        transaction_id="TEST-AUTH-002",
        three_ds_result=ThreeDSResult.CHALLENGE_SUCCEEDED,
        liability_shift=True,
        issuer_authorized=False,
    )
    result = PaymentRiskEngine().assess(context)
    assert result.liability.liability_shift_recognized is True
    assert any("authorization" in item.lower() for item in result.liability.rationale)


def test_dispute_contract_marks_missing_subscription_consent() -> None:
    context = PaymentRiskContext(
        transaction_id="TEST-SUB-003",
        merchant_initiated_transaction=True,
        credential_on_file=True,
        consent_evidence=False,
        recurring_notice_sent=False,
        easy_cancellation_available=False,
    )
    result = evaluate_dispute_evidence(
        context,
        "subscription_or_recurring",
        expected_recovery=50,
        operating_cost=10,
    )
    assert "consent_and_terms" in result.missing_items
    assert result.recommendation == "ACCEPT_OR_REFUND"


def test_six_state_machines_reject_illegal_transition() -> None:
    machines = build_default_state_machines()
    assert len(machines) == 6
    for machine in machines.values():
        invalid = machine.transition(machine.spec.initial_state, "__INVALID__")
        assert invalid.accepted is False


def test_payment_ready_suite_writes_artifacts(tmp_path) -> None:
    result = run_payment_ready_suite(tmp_path)
    assert len(result.assessments) >= 5
    assert result.boundary["payment_extension_is_post_internship_research"] is True
    assert (tmp_path / "payment_ready_suite.json").exists()
    assert (tmp_path / "PAYMENT_READY_SUITE.md").exists()
