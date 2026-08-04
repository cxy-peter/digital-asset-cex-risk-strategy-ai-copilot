from __future__ import annotations

from ..payment import PaymentRiskEngine, build_payment_brief, demo_contexts, detect_payment_topics
from ..state import CopilotState
from .base import BaseAgent


class PaymentFlowLiabilityAgent(BaseAgent):
    """Map payment requests to actors, states, scenarios, controls, and liability evidence.

    The agent is deliberately advisory. It does not call a PSP, execute a payment,
    change a merchant reserve, or decide a real network dispute.
    """

    name = "payment_flow_liability_agent"
    description = "Payment actors, lifecycle, 3DS/authorization separation, merchant exposure, and dispute evidence."

    async def run(self, state: CopilotState):
        topics = detect_payment_topics(state.request.query)
        explicit_payment = (
            getattr(state.request.domain, "value", None) == "payment_fraud"
            or (state.request.event_code or "").lower().startswith("payment")
            or bool(topics)
        )
        if not explicit_payment:
            output = {
                "applicable": False,
                "topics": [],
                "boundary": {
                    "post_internship_payment_extension": True,
                    "production_connection": False,
                    "automatic_enforcement": False,
                },
            }
            state.merge_context({"payment_risk_analysis": output})
            return self.result("Payment extension not activated for this request.", output)

        brief = build_payment_brief(state.request.query)
        demo = PaymentRiskEngine().assess(demo_contexts()[0])
        output = {
            "applicable": True,
            "topics": topics,
            "knowledge_brief": brief,
            "synthetic_reference_assessment": demo.model_dump(mode="json"),
            "governance": {
                "authentication_is_not_authorization": True,
                "high_impact_actions_require_human_review": True,
                "liability_requires_reason_code_and_contract_review": True,
                "payment_and_risk_state_machines_are_separate": True,
                "production_connection": False,
            },
        }
        state.merge_context({"payment_risk_analysis": output})
        return self.result(
            "Mapped the request to payment actors, lifecycle states, risk scenarios, controls, and liability/evidence boundaries.",
            output,
            citations=["RAR-PAYMENT201", "RAR-HANNA", "RAR-TIANWEN", "KNOWLEDGE-V1.3"],
        )
