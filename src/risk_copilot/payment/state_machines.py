from __future__ import annotations

from dataclasses import dataclass

from .models import StateTransitionResult


@dataclass(frozen=True)
class StateMachineSpec:
    name: str
    initial_state: str
    terminal_states: frozenset[str]
    transitions: dict[str, frozenset[str]]


class StateMachine:
    """Small deterministic state machine with explicit terminal-state protection."""

    def __init__(self, spec: StateMachineSpec) -> None:
        self.spec = spec

    def transition(self, current: str, target: str) -> StateTransitionResult:
        terminal_before = current in self.spec.terminal_states
        if terminal_before:
            return StateTransitionResult(
                machine=self.spec.name,
                from_state=current,
                to_state=target,
                accepted=False,
                terminal_before=True,
                reason="terminal states are immutable; create a new business object or version instead",
            )
        allowed = self.spec.transitions.get(current, frozenset())
        accepted = target in allowed
        return StateTransitionResult(
            machine=self.spec.name,
            from_state=current,
            to_state=target,
            accepted=accepted,
            terminal_before=False,
            reason="accepted" if accepted else f"transition not allowed; expected one of {sorted(allowed)}",
        )

    def simulate(self, path: list[str]) -> list[StateTransitionResult]:
        if len(path) < 2:
            return []
        return [self.transition(source, target) for source, target in zip(path, path[1:])]


def build_default_state_machines() -> dict[str, StateMachine]:
    """Return the six independent payment/risk state machines used by V1.3.

    Separating these objects prevents a risk score, a 3DS result, an issuer decline,
    and a chargeback outcome from being collapsed into one ambiguous ``status`` field.
    """

    specs = [
        StateMachineSpec(
            name="payment_order",
            initial_state="CREATED",
            terminal_states=frozenset({"CANCELLED", "CLOSED"}),
            transitions={
                "CREATED": frozenset({"PAYMENT_METHOD_SELECTED", "CANCELLED"}),
                "PAYMENT_METHOD_SELECTED": frozenset({"ACCEPTED", "CANCELLED"}),
                "ACCEPTED": frozenset({"PROCESSING", "FAILED", "CANCELLED"}),
                "PROCESSING": frozenset({"SUCCEEDED", "FAILED", "CANCELLED"}),
                "SUCCEEDED": frozenset({"PARTIALLY_REFUNDED", "REFUNDED", "DISPUTED", "CLOSED"}),
                "FAILED": frozenset({"PAYMENT_METHOD_SELECTED", "CANCELLED"}),
                "PARTIALLY_REFUNDED": frozenset({"REFUNDED", "DISPUTED", "CLOSED"}),
                "REFUNDED": frozenset({"DISPUTED", "CLOSED"}),
                "DISPUTED": frozenset({"CLOSED"}),
            },
        ),
        StateMachineSpec(
            name="authentication_3ds",
            initial_state="NOT_STARTED",
            terminal_states=frozenset({"AUTHENTICATED", "FAILED", "UNAVAILABLE", "CANCELLED"}),
            transitions={
                "NOT_STARTED": frozenset({"REQUESTED", "BYPASSED", "CANCELLED"}),
                "REQUESTED": frozenset({"FRICTIONLESS", "CHALLENGE_REQUIRED", "UNAVAILABLE", "FAILED"}),
                "FRICTIONLESS": frozenset({"AUTHENTICATED"}),
                "CHALLENGE_REQUIRED": frozenset({"CHALLENGE_IN_PROGRESS", "FAILED", "CANCELLED"}),
                "CHALLENGE_IN_PROGRESS": frozenset({"AUTHENTICATED", "FAILED", "CANCELLED"}),
                "BYPASSED": frozenset({"AUTHENTICATED", "FAILED"}),
            },
        ),
        StateMachineSpec(
            name="authorization_capture_settlement",
            initial_state="NOT_REQUESTED",
            terminal_states=frozenset({"SETTLED", "VOIDED", "FINAL_DECLINE", "CLOSED"}),
            transitions={
                "NOT_REQUESTED": frozenset({"AUTH_REQUESTED"}),
                "AUTH_REQUESTED": frozenset({"AUTHORIZED", "SOFT_DECLINE", "FINAL_DECLINE", "ERROR"}),
                "SOFT_DECLINE": frozenset({"AUTH_REQUESTED", "FINAL_DECLINE"}),
                "ERROR": frozenset({"AUTH_REQUESTED", "FINAL_DECLINE"}),
                "AUTHORIZED": frozenset({"CAPTURE_PENDING", "REVERSED", "VOIDED"}),
                "CAPTURE_PENDING": frozenset({"PARTIALLY_CAPTURED", "CAPTURED", "REVERSED", "VOIDED"}),
                "PARTIALLY_CAPTURED": frozenset({"CAPTURED", "CLEARED", "REVERSED"}),
                "CAPTURED": frozenset({"CLEARED", "REVERSED"}),
                "CLEARED": frozenset({"SETTLED", "REVERSED"}),
                "REVERSED": frozenset({"CLOSED"}),
            },
        ),
        StateMachineSpec(
            name="risk_decision",
            initial_state="RECEIVED",
            terminal_states=frozenset({"CLOSED", "FAILED"}),
            transitions={
                "RECEIVED": frozenset({"VALIDATED", "FAILED"}),
                "VALIDATED": frozenset({"DECIDED", "FAILED"}),
                "DECIDED": frozenset({"ACKNOWLEDGED", "FAILED"}),
                "ACKNOWLEDGED": frozenset({"FEEDBACK_RECEIVED", "CLOSED", "FAILED"}),
                "FEEDBACK_RECEIVED": frozenset({"CLOSED"}),
            },
        ),
        StateMachineSpec(
            name="merchant_risk_lifecycle",
            initial_state="PROSPECT",
            terminal_states=frozenset({"REJECTED", "EXITED"}),
            transitions={
                "PROSPECT": frozenset({"UNDER_REVIEW"}),
                "UNDER_REVIEW": frozenset({"APPROVED", "REJECTED", "MORE_INFORMATION_REQUIRED"}),
                "MORE_INFORMATION_REQUIRED": frozenset({"UNDER_REVIEW", "REJECTED"}),
                "APPROVED": frozenset({"ACTIVE"}),
                "ACTIVE": frozenset({"WATCHLIST", "RESTRICTED", "SUSPENDED", "EXITED"}),
                "WATCHLIST": frozenset({"ACTIVE", "RESTRICTED", "SUSPENDED", "EXITED"}),
                "RESTRICTED": frozenset({"ACTIVE", "SUSPENDED", "EXITED"}),
                "SUSPENDED": frozenset({"ACTIVE", "EXITED"}),
            },
        ),
        StateMachineSpec(
            name="dispute_case",
            initial_state="NONE",
            terminal_states=frozenset({"WON", "LOST", "ACCEPTED", "CLOSED"}),
            transitions={
                "NONE": frozenset({"INQUIRY", "DISPUTE_OPENED"}),
                "INQUIRY": frozenset({"DISPUTE_OPENED", "ACCEPTED", "CLOSED"}),
                "DISPUTE_OPENED": frozenset({"EVIDENCE_COLLECTION", "ACCEPTED"}),
                "EVIDENCE_COLLECTION": frozenset({"REPRESENTMENT_SUBMITTED", "ACCEPTED"}),
                "REPRESENTMENT_SUBMITTED": frozenset({"WON", "LOST", "PRE_ARBITRATION"}),
                "PRE_ARBITRATION": frozenset({"WON", "LOST", "ACCEPTED"}),
            },
        ),
    ]
    return {spec.name: StateMachine(spec) for spec in specs}
