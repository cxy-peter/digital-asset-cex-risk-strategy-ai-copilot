from __future__ import annotations

from collections import OrderedDict
from typing import Callable

from .knowledge import JOINT_METRICS, STABLECOIN_OVERLAY
from .models import (
    LiabilityAssessment,
    LiabilityOwner,
    PaymentControl,
    PaymentDecision,
    PaymentRiskAssessment,
    PaymentRiskContext,
    PaymentScenarioId,
    ScenarioFinding,
    ThreeDSResult,
    TokenType,
)


CONTROL_PRIORITY = OrderedDict(
    [
        (PaymentControl.REJECT, 100),
        (PaymentControl.BLOCK, 95),
        (PaymentControl.ESCALATE_COMPLIANCE, 90),
        (PaymentControl.PAYOUT_RESTRICTION, 85),
        (PaymentControl.RESERVE_HOLD, 80),
        (PaymentControl.SETTLEMENT_DELAY, 75),
        (PaymentControl.MANUAL_REVIEW, 70),
        (PaymentControl.DELAY, 65),
        (PaymentControl.STEP_UP_AUTHENTICATION, 60),
        (PaymentControl.REQUEST_3DS, 55),
        (PaymentControl.BENEFICIARY_WARNING, 50),
        (PaymentControl.REFUND_LIMIT, 45),
        (PaymentControl.MANUAL_CAPTURE, 40),
        (PaymentControl.REQUEST_NETWORK_TOKEN, 35),
        (PaymentControl.GUARDED_RETRY, 30),
        (PaymentControl.ROUTE_TO_ALTERNATIVE_ACQUIRER, 25),
        (PaymentControl.MONITOR, 10),
        (PaymentControl.PASS, 0),
    ]
)


class PaymentRiskEngine:
    """Deterministic payment-risk assessment for synthetic demonstrations.

    The engine intentionally returns candidate controls rather than executing a
    payment, changing a merchant state, or filing a dispute. It is designed to
    demonstrate how payment-domain evidence can be connected to the existing
    Risk Strategy AI Copilot while preserving human-in-the-loop governance.
    """

    def assess(self, context: PaymentRiskContext) -> PaymentRiskAssessment:
        findings: list[ScenarioFinding] = []
        for builder in self._builders():
            finding = builder(context)
            if finding is not None:
                findings.append(finding)
        findings.sort(key=lambda item: item.score, reverse=True)

        top_score = findings[0].score if findings else 0.0
        score = min(100.0, top_score + min(20.0, max(0, len(findings) - 1) * 4.0))
        decision = self._decision(score)
        controls = self._merge_controls(findings, score)
        liability = self.assess_liability(context)
        stablecoin_overlay = self._stablecoin_overlay(context)
        if stablecoin_overlay.get("blocked_by_sanctions"):
            score = max(score, 95.0)
            decision = PaymentDecision.BLOCK_CANDIDATE
            controls = self._ordered_unique(
                [PaymentControl.BLOCK, PaymentControl.ESCALATE_COMPLIANCE, *controls]
            )

        reason_codes = list(
            dict.fromkeys(code for finding in findings for code in finding.reason_codes)
        )
        high_impact = any(
            control
            in {
                PaymentControl.BLOCK,
                PaymentControl.REJECT,
                PaymentControl.PAYOUT_RESTRICTION,
                PaymentControl.RESERVE_HOLD,
                PaymentControl.SETTLEMENT_DELAY,
                PaymentControl.ESCALATE_COMPLIANCE,
            }
            for control in controls
        )
        return PaymentRiskAssessment(
            transaction_id=context.transaction_id,
            score=score,
            decision=decision,
            findings=findings,
            recommended_controls=controls,
            reason_codes=reason_codes,
            liability=liability,
            stablecoin_overlay=stablecoin_overlay,
            human_review_required=score >= 60 or high_impact,
        )

    @staticmethod
    def _decision(score: float) -> PaymentDecision:
        if score < 20:
            return PaymentDecision.PASS
        if score < 40:
            return PaymentDecision.MONITOR
        if score < 60:
            return PaymentDecision.CHALLENGE
        if score < 80:
            return PaymentDecision.REVIEW
        return PaymentDecision.BLOCK_CANDIDATE

    @staticmethod
    def _ordered_unique(controls: list[PaymentControl]) -> list[PaymentControl]:
        unique = list(dict.fromkeys(controls))
        return sorted(unique, key=lambda item: CONTROL_PRIORITY[item], reverse=True)

    def _merge_controls(self, findings: list[ScenarioFinding], score: float) -> list[PaymentControl]:
        controls = [control for finding in findings for control in finding.controls]
        if not controls:
            controls = [PaymentControl.PASS]
        elif score < 40:
            controls.append(PaymentControl.MONITOR)
        return self._ordered_unique(controls)

    @staticmethod
    def _finding(
        scenario_id: PaymentScenarioId,
        score: float,
        evidence: list[str],
        controls: list[PaymentControl],
        reason_codes: list[str],
        explanation: str,
        metrics: list[str] | None = None,
    ) -> ScenarioFinding:
        return ScenarioFinding(
            scenario_id=scenario_id,
            score=min(100.0, max(0.0, score)),
            evidence=evidence,
            controls=controls,
            reason_codes=reason_codes,
            metrics=metrics or JOINT_METRICS,
            explanation=explanation,
        )

    def _builders(self) -> list[Callable[[PaymentRiskContext], ScenarioFinding | None]]:
        return [
            self._card_testing,
            self._cnp_stolen,
            self._account_takeover,
            self._app_bec,
            self._friendly_fraud,
            self._refund_abuse,
            self._subscription,
            self._merchant_fraud,
            self._merchant_credit,
            self._transaction_laundering,
            self._payout_mule,
            self._duplicate_api,
            self._dcc_consent,
            self._agentic_authorization,
        ]

    def _card_testing(self, c: PaymentRiskContext) -> ScenarioFinding | None:
        evidence: list[str] = []
        score = 0.0
        if c.small_authorization_count_10m >= 5:
            score += 30
            evidence.append(f"small_authorization_count_10m={c.small_authorization_count_10m}")
        if c.authorization_attempts_10m >= 8:
            score += 25
            evidence.append(f"authorization_attempts_10m={c.authorization_attempts_10m}")
        if c.decline_ratio_10m >= 0.5:
            score += 25
            evidence.append(f"decline_ratio_10m={c.decline_ratio_10m:.2f}")
        if c.card_count_per_device_10m >= 4:
            score += 25
            evidence.append(f"card_count_per_device_10m={c.card_count_per_device_10m}")
        if score < 35:
            return None
        return self._finding(
            PaymentScenarioId.CARD_TESTING,
            score,
            evidence,
            [PaymentControl.BLOCK, PaymentControl.REQUEST_3DS, PaymentControl.MANUAL_REVIEW],
            ["CARD_TESTING_VELOCITY", "MULTI_CARD_DEVICE", "HIGH_DECLINE_RATIO"],
            "Small repeated authorizations, multi-card device usage, and high declines form a credential-validation pattern.",
        )

    def _cnp_stolen(self, c: PaymentRiskContext) -> ScenarioFinding | None:
        evidence: list[str] = []
        score = 0.0
        if c.channel in {"ecommerce", "mobile"}:
            score += 5
        if c.new_device:
            score += 18
            evidence.append("new_device")
        if c.cross_border or c.ip_country_bin_mismatch:
            score += 18
            evidence.append("cross_border_or_bin_ip_mismatch")
        if c.shipping_billing_mismatch:
            score += 12
            evidence.append("shipping_billing_mismatch")
        if c.three_ds_result in {
            ThreeDSResult.NOT_REQUESTED,
            ThreeDSResult.CHALLENGE_FAILED,
            ThreeDSResult.UNAVAILABLE,
        }:
            score += 18
            evidence.append(f"three_ds_result={c.three_ds_result.value}")
        if c.amount_step_up_ratio >= 3:
            score += 14
            evidence.append(f"amount_step_up_ratio={c.amount_step_up_ratio:.2f}")
        if c.token_type == TokenType.NONE:
            score += 7
            evidence.append("raw_or_unscoped_credential")
        if score < 40:
            return None
        controls = [PaymentControl.REQUEST_3DS, PaymentControl.MANUAL_REVIEW]
        if c.token_type == TokenType.NONE:
            controls.append(PaymentControl.REQUEST_NETWORK_TOKEN)
        if score >= 75:
            controls.append(PaymentControl.BLOCK)
        return self._finding(
            PaymentScenarioId.CNP_STOLEN_CREDENTIAL,
            score,
            evidence,
            controls,
            ["CNP_STOLEN_CREDENTIAL", "AUTHENTICATION_GAP"],
            "CNP risk should combine device, geography, authentication, amount, and credential-lifecycle evidence rather than rely on a single field.",
        )

    def _account_takeover(self, c: PaymentRiskContext) -> ScenarioFinding | None:
        evidence: list[str] = []
        score = 0.0
        if c.recent_password_or_2fa_change:
            score += 30
            evidence.append("recent_password_or_2fa_change")
        if c.new_device:
            score += 20
            evidence.append("new_device")
        if c.first_beneficiary or c.new_payout_account:
            score += 20
            evidence.append("new_beneficiary_or_payout_account")
        if c.amount_step_up_ratio >= 2.5:
            score += 15
            evidence.append("amount_above_customer_baseline")
        if c.trusted_device_history_days < 7:
            score += 10
            evidence.append("thin_trusted_device_history")
        if score < 40:
            return None
        controls = [
            PaymentControl.STEP_UP_AUTHENTICATION,
            PaymentControl.DELAY,
            PaymentControl.MANUAL_REVIEW,
        ]
        if score >= 80:
            controls.append(PaymentControl.BLOCK)
        return self._finding(
            PaymentScenarioId.ACCOUNT_TAKEOVER,
            score,
            evidence,
            controls,
            ["ACCOUNT_CONTROL_CHANGE", "NEW_BENEFICIARY", "BASELINE_DEVIATION"],
            "The control point should sit before payment or payout becomes irreversible; recent security changes are evidence of changed account control, not proof by themselves.",
        )

    def _app_bec(self, c: PaymentRiskContext) -> ScenarioFinding | None:
        evidence: list[str] = []
        score = 0.0
        if c.first_beneficiary:
            score += 25
            evidence.append("first_beneficiary")
        if c.beneficiary_risk_score >= 0.7:
            score += 25
            evidence.append(f"beneficiary_risk_score={c.beneficiary_risk_score:.2f}")
        if c.customer_confirmed_social_engineering:
            score += 35
            evidence.append("customer_confirmed_social_engineering")
        if c.amount_step_up_ratio >= 3:
            score += 15
            evidence.append("large_transfer_vs_baseline")
        if score < 40:
            return None
        controls = [
            PaymentControl.BENEFICIARY_WARNING,
            PaymentControl.DELAY,
            PaymentControl.MANUAL_REVIEW,
        ]
        if score >= 85:
            controls.append(PaymentControl.BLOCK)
        return self._finding(
            PaymentScenarioId.APP_BEC_SCAM,
            score,
            evidence,
            controls,
            ["APP_SCAM", "BENEFICIARY_RISK", "SOCIAL_ENGINEERING"],
            "Because the user may have authorized the transfer, authentication alone cannot resolve APP/BEC risk; beneficiary intelligence and contextual warnings are required.",
        )

    def _friendly_fraud(self, c: PaymentRiskContext) -> ScenarioFinding | None:
        score = 0.0
        evidence: list[str] = []
        if c.prior_dispute_count_180d >= 2:
            score += 25
            evidence.append(f"prior_dispute_count_180d={c.prior_dispute_count_180d}")
        if c.delivery_evidence or c.digital_usage_evidence:
            score += 20
            evidence.append("fulfillment_or_usage_evidence_present")
        if c.three_ds_result in {ThreeDSResult.FRICTIONLESS, ThreeDSResult.CHALLENGE_SUCCEEDED}:
            score += 15
            evidence.append("successful_authentication")
        if c.communication_evidence:
            score += 10
            evidence.append("customer_communication_present")
        if score < 35:
            return None
        return self._finding(
            PaymentScenarioId.FRIENDLY_FRAUD,
            score,
            evidence,
            [PaymentControl.MONITOR, PaymentControl.MANUAL_REVIEW],
            ["FIRST_PARTY_DISPUTE", "FULFILLMENT_EVIDENCE"],
            "Friendly-fraud assessment is a post-transaction evidence problem; it should not be converted into an automatic customer punishment.",
        )

    def _refund_abuse(self, c: PaymentRiskContext) -> ScenarioFinding | None:
        score = 0.0
        evidence: list[str] = []
        if c.refund_ratio_30d >= 0.35:
            score += 35
            evidence.append(f"refund_ratio_30d={c.refund_ratio_30d:.2f}")
        if c.refund_to_alternative_instrument:
            score += 35
            evidence.append("refund_to_alternative_instrument")
        if c.prior_dispute_count_180d >= 3:
            score += 15
            evidence.append("repeat_dispute_history")
        if score < 35:
            return None
        controls = [PaymentControl.REFUND_LIMIT, PaymentControl.MANUAL_REVIEW]
        if score >= 80:
            controls.append(PaymentControl.BLOCK)
        return self._finding(
            PaymentScenarioId.REFUND_ABUSE,
            score,
            evidence,
            controls,
            ["REFUND_VELOCITY", "ALTERNATIVE_REFUND_INSTRUMENT"],
            "Refund controls should preserve legitimate service while preventing conversion of refunds into a separate payout rail.",
        )

    def _subscription(self, c: PaymentRiskContext) -> ScenarioFinding | None:
        if not (c.merchant_initiated_transaction or c.credential_on_file):
            return None
        score = 15.0
        evidence = ["merchant_initiated_or_credential_on_file"]
        if not c.consent_evidence:
            score += 30
            evidence.append("missing_consent_evidence")
        if not c.recurring_notice_sent:
            score += 20
            evidence.append("missing_recurring_notice")
        if not c.easy_cancellation_available:
            score += 25
            evidence.append("cancellation_friction")
        if c.prior_dispute_count_180d >= 2:
            score += 10
            evidence.append("repeat_subscription_disputes")
        if score < 35:
            return None
        return self._finding(
            PaymentScenarioId.SUBSCRIPTION_DISPUTE,
            score,
            evidence,
            [PaymentControl.MONITOR, PaymentControl.MANUAL_REVIEW, PaymentControl.REFUND_LIMIT],
            ["RECURRING_CONSENT_GAP", "CANCELLATION_FRICTION", "MIT_NOTICE_GAP"],
            "Subscription risk is often created by weak consent, notice, cancellation, and support design rather than stolen credentials.",
        )

    def _merchant_fraud(self, c: PaymentRiskContext) -> ScenarioFinding | None:
        score = 0.0
        evidence: list[str] = []
        if c.merchant_risk_score >= 0.7:
            score += 25
            evidence.append(f"merchant_risk_score={c.merchant_risk_score:.2f}")
        if c.expected_volume_gap >= 4:
            score += 20
            evidence.append(f"expected_volume_gap={c.expected_volume_gap:.2f}")
        if c.refund_ratio_30d >= 0.25 or c.chargeback_ratio_90d >= 0.02:
            score += 25
            evidence.append("refund_or_chargeback_spike")
        if not (c.delivery_evidence or c.digital_usage_evidence):
            score += 15
            evidence.append("weak_fulfillment_evidence")
        if c.descriptor_website_mismatch:
            score += 20
            evidence.append("descriptor_website_mismatch")
        if score < 40:
            return None
        controls = [
            PaymentControl.RESERVE_HOLD,
            PaymentControl.SETTLEMENT_DELAY,
            PaymentControl.MANUAL_REVIEW,
        ]
        if score >= 85:
            controls.append(PaymentControl.PAYOUT_RESTRICTION)
        return self._finding(
            PaymentScenarioId.MERCHANT_FRAUD,
            score,
            evidence,
            controls,
            ["MERCHANT_FULFILLMENT_RISK", "VOLUME_SPIKE", "CHARGEBACK_SPIKE"],
            "Merchant risk must be managed through underwriting, reserve, settlement, monitoring, and exit controls rather than transaction blocking alone.",
        )

    def _merchant_credit(self, c: PaymentRiskContext) -> ScenarioFinding | None:
        score = 0.0
        evidence: list[str] = []
        if c.settlement_exposure > 0 and c.reserve_coverage_ratio < 0.8:
            score += 40
            evidence.append(
                f"reserve_coverage_ratio={c.reserve_coverage_ratio:.2f}; settlement_exposure={c.settlement_exposure:.2f}"
            )
        if c.chargeback_ratio_90d >= 0.02:
            score += 25
            evidence.append("elevated_chargeback_ratio")
        if c.expected_volume_gap >= 5:
            score += 20
            evidence.append("rapid_volume_growth")
        if c.merchant_age_days < 90:
            score += 15
            evidence.append("young_merchant")
        if score < 40:
            return None
        return self._finding(
            PaymentScenarioId.MERCHANT_CREDIT_RISK,
            score,
            evidence,
            [
                PaymentControl.RESERVE_HOLD,
                PaymentControl.SETTLEMENT_DELAY,
                PaymentControl.PAYOUT_RESTRICTION,
                PaymentControl.MANUAL_REVIEW,
            ],
            ["MERCHANT_CREDIT_EXPOSURE", "RESERVE_SHORTFALL"],
            "Chargebacks and refunds create future merchant liabilities; reserve and settlement design are credit controls, not only fraud operations.",
        )

    def _transaction_laundering(self, c: PaymentRiskContext) -> ScenarioFinding | None:
        score = 0.0
        evidence: list[str] = []
        if c.product_mcc_mismatch:
            score += 35
            evidence.append("product_mcc_mismatch")
        if c.descriptor_website_mismatch:
            score += 30
            evidence.append("descriptor_website_mismatch")
        if c.expected_volume_gap >= 4:
            score += 20
            evidence.append("volume_outside_underwriting_profile")
        if c.merchant_risk_score >= 0.8:
            score += 20
            evidence.append("high_merchant_risk")
        if score < 40:
            return None
        return self._finding(
            PaymentScenarioId.TRANSACTION_LAUNDERING,
            score,
            evidence,
            [PaymentControl.MANUAL_REVIEW, PaymentControl.RESERVE_HOLD, PaymentControl.ESCALATE_COMPLIANCE],
            ["UNDECLARED_PROCESSING", "MCC_PRODUCT_MISMATCH", "WEBSITE_DESCRIPTOR_MISMATCH"],
            "Transaction laundering requires merchant, website, product, descriptor, and traffic consistency checks; payment data alone may not reveal the true commercial flow.",
        )

    def _payout_mule(self, c: PaymentRiskContext) -> ScenarioFinding | None:
        score = 0.0
        evidence: list[str] = []
        if c.payout_fan_in_24h >= 8:
            score += 25
            evidence.append(f"payout_fan_in_24h={c.payout_fan_in_24h}")
        if c.payout_fan_out_24h >= 8:
            score += 25
            evidence.append(f"payout_fan_out_24h={c.payout_fan_out_24h}")
        if c.fund_stay_minutes_median < 60:
            score += 25
            evidence.append(f"fund_stay_minutes_median={c.fund_stay_minutes_median:.1f}")
        if c.new_payout_account:
            score += 20
            evidence.append("new_payout_account")
        if c.beneficiary_risk_score >= 0.7:
            score += 15
            evidence.append("high_beneficiary_risk")
        if score < 40:
            return None
        return self._finding(
            PaymentScenarioId.PAYOUT_MULE,
            score,
            evidence,
            [PaymentControl.DELAY, PaymentControl.PAYOUT_RESTRICTION, PaymentControl.MANUAL_REVIEW],
            ["PAYOUT_FAN_IN_OUT", "SHORT_FUND_STAY", "NEW_PAYOUT_ACCOUNT"],
            "Payout-mule detection should combine money-flow topology, holding time, beneficiary risk, and account history before funds leave the system.",
        )

    def _duplicate_api(self, c: PaymentRiskContext) -> ScenarioFinding | None:
        score = 0.0
        evidence: list[str] = []
        if c.idempotency_key_reused_with_different_payload:
            score += 75
            evidence.append("idempotency_key_reused_with_different_payload")
        if c.duplicate_webhook_count >= 2:
            score += 20
            evidence.append(f"duplicate_webhook_count={c.duplicate_webhook_count}")
        if c.retry_count >= 3 and not c.soft_decline:
            score += 15
            evidence.append("unguarded_retries")
        if score < 35:
            return None
        return self._finding(
            PaymentScenarioId.DUPLICATE_PAYMENT_API,
            score,
            evidence,
            [PaymentControl.BLOCK, PaymentControl.MANUAL_CAPTURE, PaymentControl.MANUAL_REVIEW],
            ["IDEMPOTENCY_CONFLICT", "DUPLICATE_WEBHOOK", "UNGUARDED_RETRY"],
            "Idempotency and asynchronous webhook handling are payment-integrity controls; duplicate operations should be prevented before risk scoring is considered.",
        )

    def _dcc_consent(self, c: PaymentRiskContext) -> ScenarioFinding | None:
        if not c.dcc_applied:
            return None
        score = 15.0
        evidence = ["dcc_applied"]
        if not c.dcc_explicit_consent:
            score += 45
            evidence.append("missing_dcc_consent")
        if not c.fx_disclosure_present:
            score += 35
            evidence.append("missing_fx_disclosure")
        if score < 35:
            return None
        return self._finding(
            PaymentScenarioId.DCC_CONSENT,
            score,
            evidence,
            [PaymentControl.BLOCK, PaymentControl.MANUAL_REVIEW],
            ["DCC_CONSENT_GAP", "FX_DISCLOSURE_GAP"],
            "DCC is not only a pricing choice; explicit consent and transparent FX disclosure are part of the payment evidence contract.",
        )

    def _agentic_authorization(self, c: PaymentRiskContext) -> ScenarioFinding | None:
        if not c.agentic_payment:
            return None
        score = 10.0
        evidence = ["agentic_payment"]
        if c.delegated_spend_limit is None:
            score += 35
            evidence.append("missing_delegated_spend_limit")
        elif c.amount > c.delegated_spend_limit:
            score += 45
            evidence.append("amount_exceeds_delegated_limit")
        if c.token_scope_risk >= 0.6:
            score += 20
            evidence.append("broad_or_unsafe_token_scope")
        if c.agent_identity_assurance < 0.6:
            score += 20
            evidence.append("weak_agent_identity_assurance")
        if score >= 55 and not c.human_approval_present:
            score += 20
            evidence.append("missing_human_approval")
        if score < 35:
            return None
        return self._finding(
            PaymentScenarioId.AGENTIC_AUTHORIZATION,
            score,
            evidence,
            [PaymentControl.BLOCK, PaymentControl.STEP_UP_AUTHENTICATION, PaymentControl.MANUAL_REVIEW],
            ["DELEGATED_AUTHORITY_GAP", "AGENT_TOKEN_SCOPE", "HUMAN_APPROVAL_REQUIRED"],
            "An AI agent may select or explain a purchase, but deterministic policy must own spend limits, credential scope, purpose binding, and execution approval.",
        )

    @staticmethod
    def assess_liability(c: PaymentRiskContext) -> LiabilityAssessment:
        rationale: list[str] = []
        unresolved: list[str] = []
        successful_3ds = c.three_ds_result in {
            ThreeDSResult.FRICTIONLESS,
            ThreeDSResult.CHALLENGE_SUCCEEDED,
            ThreeDSResult.ATTEMPT_ACKNOWLEDGED,
        }
        recognized = bool(c.liability_shift and successful_3ds)
        if recognized:
            owner = LiabilityOwner.ISSUER
            rationale.append("successful 3DS/SCA evidence and a recognized liability-shift flag are present")
        elif c.merchant_initiated_transaction:
            owner = LiabilityOwner.MERCHANT
            rationale.append("merchant-initiated transactions generally require merchant-held consent and credential-on-file evidence")
        elif c.issuer_authorized is True and c.delivery_evidence:
            owner = LiabilityOwner.SHARED
            rationale.append("issuer authorization and merchant fulfillment evidence exist, but dispute reason and network rules still determine allocation")
        elif c.issuer_authorized is False:
            owner = LiabilityOwner.ISSUER
            rationale.append("issuer authorization was declined; no merchant capture should be treated as a successful payment")
        else:
            owner = LiabilityOwner.UNDETERMINED
            unresolved.extend([
                "network and reason-code rules",
                "authentication evidence",
                "capture and settlement timeline",
                "merchant fulfillment and consent evidence",
            ])
        if c.issuer_authorized is False:
            rationale.append("issuer authorization was declined; authentication success does not create an approved payment")
        if c.token_type in {TokenType.NETWORK_TOKEN, TokenType.WALLET_TOKEN}:
            rationale.append("scoped token and cryptogram evidence reduce credential-exposure risk but do not alone determine dispute liability")
        return LiabilityAssessment(
            likely_owner=owner,
            liability_shift_recognized=recognized,
            rationale=rationale,
            unresolved_questions=unresolved,
        )

    @staticmethod
    def _stablecoin_overlay(c: PaymentRiskContext) -> dict[str, object]:
        if not c.stablecoin_payment:
            return {}
        warnings: list[str] = []
        if c.stablecoin_issuer_risk >= 0.6:
            warnings.append("stablecoin issuer or reserve risk is elevated")
        if c.wallet_address_risk >= 0.6:
            warnings.append("wallet/address risk is elevated")
        if c.smart_contract_risk >= 0.6:
            warnings.append("smart-contract or bridge risk is elevated")
        if c.liquidity_fx_exposure >= 0.6:
            warnings.append("liquidity or FX exposure is elevated")
        if c.reconciliation_break_count > 0:
            warnings.append("reconciliation breaks require investigation")
        return {
            **STABLECOIN_OVERLAY,
            "warnings": warnings,
            "blocked_by_sanctions": c.sanctioned_address_hit,
            "recommended_controls": (
                [PaymentControl.BLOCK.value, PaymentControl.ESCALATE_COMPLIANCE.value]
                if c.sanctioned_address_hit
                else [PaymentControl.MONITOR.value, PaymentControl.MANUAL_REVIEW.value]
            ),
        }
