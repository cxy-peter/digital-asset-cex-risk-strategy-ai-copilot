from __future__ import annotations

from .models import DisputeEvidenceResult, PaymentRiskContext


EVIDENCE_REQUIREMENTS: dict[str, list[str]] = {
    "fraud_or_cardholder_denial": [
        "identity_authentication",
        "three_ds_or_sca",
        "issuer_authorization",
        "device_and_ip",
        "order_details",
        "delivery_or_usage",
        "customer_communication",
    ],
    "goods_not_received": [
        "order_details",
        "delivery_or_usage",
        "customer_communication",
        "refund_and_cancellation",
    ],
    "not_as_described": [
        "order_details",
        "product_terms",
        "delivery_or_usage",
        "customer_communication",
        "refund_and_cancellation",
    ],
    "subscription_or_recurring": [
        "consent_and_terms",
        "recurring_notice",
        "cit_mit_indicator",
        "easy_cancellation",
        "customer_communication",
        "refund_and_cancellation",
    ],
    "processing_error": [
        "idempotency_and_order_link",
        "authorization_capture_timeline",
        "refund_and_reversal",
        "customer_communication",
    ],
    "refund_not_processed": [
        "refund_and_reversal",
        "order_details",
        "customer_communication",
    ],
}


def _evidence_presence(context: PaymentRiskContext) -> dict[str, bool]:
    return {
        "identity_authentication": context.three_ds_result.value
        in {"FRICTIONLESS", "CHALLENGE_SUCCEEDED", "ATTEMPT_ACKNOWLEDGED"},
        "three_ds_or_sca": context.three_ds_result.value != "NOT_REQUESTED",
        "issuer_authorization": context.issuer_authorized is True,
        "device_and_ip": not context.proxy_or_datacenter_ip,
        "order_details": bool(context.transaction_id and context.merchant_id),
        "delivery_or_usage": context.delivery_evidence or context.digital_usage_evidence,
        "customer_communication": context.communication_evidence,
        "refund_and_cancellation": context.cancellation_evidence or context.refund_ratio_30d > 0,
        "product_terms": context.consent_evidence,
        "consent_and_terms": context.consent_evidence,
        "recurring_notice": context.recurring_notice_sent,
        "cit_mit_indicator": context.merchant_initiated_transaction or context.credential_on_file,
        "easy_cancellation": context.easy_cancellation_available,
        "idempotency_and_order_link": not context.idempotency_key_reused_with_different_payload,
        "authorization_capture_timeline": context.issuer_authorized is not None,
        "refund_and_reversal": context.cancellation_evidence or context.refund_ratio_30d > 0,
    }


def evaluate_dispute_evidence(
    context: PaymentRiskContext,
    reason_code_family: str,
    *,
    expected_recovery: float,
    operating_cost: float,
) -> DisputeEvidenceResult:
    """Evaluate whether a candidate dispute has enough evidence to justify review.

    This is not a network-rule engine. It formalizes the evidence contract so that
    checkout, authentication, fulfillment, support, cancellation, and refund data
    are collected before a dispute rather than reconstructed after the fact.
    """

    family = reason_code_family.strip().lower()
    required = EVIDENCE_REQUIREMENTS.get(family)
    if required is None:
        required = sorted({item for items in EVIDENCE_REQUIREMENTS.values() for item in items})

    presence = _evidence_presence(context)
    present = [item for item in required if presence.get(item, False)]
    missing = [item for item in required if item not in present]
    completeness = len(present) / max(len(required), 1)
    expected_net_value = expected_recovery - operating_cost

    rationale = [
        f"evidence completeness={completeness:.1%}",
        f"expected net recovery={expected_net_value:.2f}",
    ]
    if family == "subscription_or_recurring" and not context.consent_evidence:
        recommendation = "ACCEPT_OR_REFUND"
        rationale.append("recurring consent evidence is missing")
    elif expected_net_value <= 0:
        recommendation = "ACCEPT_OR_REFUND"
        rationale.append("representment cost is not justified by expected recovery")
    elif completeness >= 0.75:
        recommendation = "REPRESENTMENT_CANDIDATE"
        rationale.append("evidence package is sufficiently complete for human review")
    elif completeness >= 0.45:
        recommendation = "COLLECT_MORE_EVIDENCE"
        rationale.append("some evidence exists, but the contract is incomplete")
    else:
        recommendation = "MANUAL_REVIEW_REQUIRED"
        rationale.append("evidence is too incomplete for deterministic recommendation")

    return DisputeEvidenceResult(
        reason_code_family=family,
        required_items=required,
        present_items=present,
        missing_items=missing,
        completeness_score=completeness,
        expected_recovery=expected_recovery,
        operating_cost=operating_cost,
        expected_net_value=expected_net_value,
        recommendation=recommendation,
        rationale=rationale,
    )
