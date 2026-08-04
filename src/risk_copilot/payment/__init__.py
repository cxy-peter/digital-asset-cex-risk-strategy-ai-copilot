"""Provider-neutral payment risk and anti-fraud extension.

This module is a post-internship research extension. It uses synthetic contexts and
keeps authentication, issuer authorization, risk decisions, merchant exposure, and
dispute evidence separate from production state changes.
"""

from .demo import demo_contexts, run_payment_ready_suite
from .disputes import EVIDENCE_REQUIREMENTS, evaluate_dispute_evidence
from .knowledge import (
    AGENTIC_GOVERNANCE,
    CONTROL_CATALOG,
    JOINT_METRICS,
    PAYMENT_ACTOR_CATALOG,
    PAYMENT_FEATURE_GROUPS,
    PAYMENT_SCENARIO_CATALOG,
    STABLECOIN_OVERLAY,
    build_payment_brief,
    detect_payment_topics,
)
from .models import *
from .risk_engine import PaymentRiskEngine
from .state_machines import build_default_state_machines

__all__ = [
    "PaymentRiskEngine",
    "build_default_state_machines",
    "evaluate_dispute_evidence",
    "run_payment_ready_suite",
    "demo_contexts",
    "PAYMENT_ACTOR_CATALOG",
    "PAYMENT_SCENARIO_CATALOG",
    "PAYMENT_FEATURE_GROUPS",
    "CONTROL_CATALOG",
    "JOINT_METRICS",
    "STABLECOIN_OVERLAY",
    "AGENTIC_GOVERNANCE",
    "EVIDENCE_REQUIREMENTS",
    "build_payment_brief",
    "detect_payment_topics",
]
