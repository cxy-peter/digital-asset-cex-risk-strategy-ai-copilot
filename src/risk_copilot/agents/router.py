from __future__ import annotations

from ..schemas import RiskDomain
from ..state import CopilotState
from .base import BaseAgent


class IntentRouterAgent(BaseAgent):
    name = "intent_router"
    description = "Resolve the risk domain and event from the user's natural-language request."

    KEYWORDS = [
        (RiskDomain.ACCOUNT_SECURITY, "WithdrawAddressAdd", ["盗号", "接管", "登录", "新设备", "改密", "提现地址", "ato"]),
        (RiskDomain.MARKETING_ABUSE, "CampaignReward", ["羊毛", "活动", "奖励", "邀请", "营销", "bonus", "campaign"]),
        (RiskDomain.AML_COMPLIANCE, "RiskScoreDaily", ["洗钱", "aml", "可疑交易", "客户风险", "risk score", "风险评分", "赌博", "制裁"]),
        (RiskDomain.FUND_SECURITY, "InternalTransfer", ["内部转账", "归集", "团伙转账", "共享订单", "internal transfer"]),
        (RiskDomain.FUND_SECURITY, "ChainWithdraw", ["快进快出", "提币", "链上出金", "法币入金", "资金闭环", "提现", "cashout"]),
        (RiskDomain.TRANSACTION_SECURITY, "SpotTrade", ["刷量", "对敲", "异常交易", "现货", "wash trade"]),
    ]

    async def run(self, state: CopilotState):
        request = state.request
        if request.event_code:
            event = self.context.runtime.feature_registry.event(request.event_code)
            domain = event.domain
            confidence = 1.0
            matched = ["explicit_event_code"]
        else:
            query = request.query.lower()
            selected = None
            for domain_value, event_code, keywords in self.KEYWORDS:
                matched_keywords = [keyword for keyword in keywords if keyword.lower() in query]
                if matched_keywords:
                    selected = (domain_value, event_code, matched_keywords)
                    break
            if selected is None:
                selected = (request.domain or RiskDomain.FUND_SECURITY, "ChainWithdraw", ["default_routing"])
            domain, event_code, matched = selected
            event = self.context.runtime.feature_registry.event(event_code)
            confidence = min(0.98, 0.58 + 0.10 * len(matched))

        state.request = request.model_copy(update={"domain": domain, "event_code": event.code})
        state.merge_context(
            {
                "routing": {
                    "domain": domain.value,
                    "event_code": event.code,
                    "event_name": event.display_name,
                    "matched_signals": matched,
                    "confidence": confidence,
                    "allowed_actions": [action.value for action in event.allowed_actions],
                }
            }
        )
        result = self.result(
            f"已将需求路由至{domain.value}/{event.code}，置信度{confidence:.0%}。",
            state.context["routing"],
        )
        state.add_result(result)
        return result
