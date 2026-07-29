from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..schemas import ReviewerBundle, ReviewerFinding
from ..state import CopilotState
from ..rules.dsl import rule_to_expression


@dataclass
class AIAdvisoryBoard:
    """Offline-reproducible specialist board mirroring a financial-advisor multi-agent design.

    In live mode the same specialist roles can be backed by ReAct + LLM tools through react_app.py.
    The default board is deterministic so that the repository can be tested without exposing data to
    an external API.
    """

    def run(self, state: CopilotState) -> dict[str, Any]:
        selected = state.context["selected_strategy"]
        metrics = state.context["selected_metrics"]
        stability = state.context.get("stability_analysis", {})
        conflicts = state.context.get("conflict_analysis", {})
        knowledge = state.context.get("knowledge_analysis", {})
        feature = state.context.get("feature_analysis", {})
        graph = state.context.get("graph_analysis", {})
        behavior = state.context.get("behavior_analysis", {})
        test_env = state.context.get("strategy_test_environment", {})

        reviewers = {
            "scenario_typology_agent": ReviewerBundle(
                reviewer="scenario_typology_agent",
                status="succeeded",
                summary="风险场景与黑灰产链路已和候选规则建立业务映射。",
                findings=[
                    ReviewerFinding(
                        category="scenario_alignment",
                        severity="low",
                        statement=(
                            f"候选策略{selected.name}针对{selected.event_code}，并使用"
                            f"{', '.join(selected.required_features)}构成可解释风险链路。"
                        ),
                        evidence_refs=["knowledge_analysis", "behavior_analysis", selected.strategy_id],
                    )
                ],
                risks=["单一行为信号不能直接替代案件调查。"],
                revisions=["在策略说明中保留风险事件、黑灰产路径和反例。"],
                acceptance_tests=["每个规则条件均能映射到风险场景、字段口径和决策时点。"],
                evidence_refs=["knowledge_analysis", "behavior_analysis"],
            ),
            "feature_model_agent": ReviewerBundle(
                reviewer="feature_model_agent",
                status="succeeded" if stability.get("status") != "UNSTABLE" else "degraded",
                summary="特征、模型和跨月份稳定性已由确定性测试层验证。",
                findings=[
                    ReviewerFinding(
                        category="oot_metrics",
                        severity="low",
                        statement=(
                            f"冻结策略OOT Precision={metrics.precision:.2%}, Recall={metrics.recall:.2%}, "
                            f"FPR={metrics.false_positive_rate:.2%}; stability={stability.get('status', 'UNKNOWN')}."
                        ),
                        evidence_refs=["backtest_analysis", "stability_analysis"],
                    )
                ],
                risks=[
                    "合成数据上的稳定性不能替代生产三工作日观察。",
                    "特征PSI、方向变化和模型阈值需持续监控。",
                ],
                revisions=["将跨月和Bootstrap稳定性作为上线评审必备附件。"],
                acceptance_tests=["OOT不参与阈值选择；Bootstrap区间和月度指标完整输出。"],
                evidence_refs=["feature_analysis", "model_analysis", "stability_analysis"],
            ),
            "graph_behavior_agent": ReviewerBundle(
                reviewer="graph_behavior_agent",
                status="succeeded",
                summary="Risk Graph强弱关系与交易行为证据已分层处理。",
                findings=[
                    ReviewerFinding(
                        category="graph_policy",
                        severity="low",
                        statement=(
                            "Device/Email/Mobile/KYC/Withdraw Address作为强关系；IP降权，"
                            "平台归集型充值地址默认排除。"
                        ),
                        evidence_refs=["graph_analysis", "SOP::risk_graph"],
                    )
                ],
                risks=["多跳扩散会增加噪声，必须和资金行为联合验证。"],
                revisions=["在命中解释中展示关系类型、路径和行为条件。"],
                acceptance_tests=["IP-only或deposit-address-only路径不得触发直接限制。"],
                evidence_refs=["graph_analysis", "behavior_analysis"],
            ),
            "governance_cms_str_agent": ReviewerBundle(
                reviewer="governance_cms_str_agent",
                status="degraded" if conflicts.get("action_conflict_count", 0) else "succeeded",
                summary="策略冲突、人工复核、测试环境和CMS/STR边界已检查。",
                findings=[
                    ReviewerFinding(
                        category="portfolio_conflict",
                        severity="medium" if conflicts.get("action_conflict_count", 0) else "low",
                        statement=(
                            f"组合冲突建议={conflicts.get('recommendation', 'UNKNOWN')}；"
                            f"增量风险召回={conflicts.get('incremental', {}).get('recall_contribution', 0):.2%}."
                        ),
                        evidence_refs=["conflict_analysis"],
                    )
                ],
                risks=["AI候选不得绕过第二人复核、效果工单或STR保密约束。"],
                revisions=["在上线评审前解决高重叠规则和处置动作优先级冲突。"],
                acceptance_tests=["状态保持SIMULATION/PENDING_REVIEW；external_submission_allowed=false。"],
                evidence_refs=["conflict_analysis", "strategy_test_environment", "cms_str_integration"],
            ),
        }

        decision = "REVISE"
        if conflicts.get("recommendation") == "ACCEPT_INCREMENTAL_VALUE" and stability.get("status") == "STABLE":
            decision = "SUBMIT_FOR_INDEPENDENT_REVIEW"
        elif conflicts.get("recommendation") == "REJECT_DUPLICATE":
            decision = "REJECT_AS_DUPLICATE"

        lead = {
            "agent": "lead_risk_strategy_agent",
            "mode": "deterministic_offline_board",
            "decision": decision,
            "strategy_id": selected.strategy_id,
            "strategy_name": selected.name,
            "expression": rule_to_expression(selected.rule),
            "executive_summary": (
                f"四个专业Agent已完成场景、特征模型、图谱行为和治理复核。"
                f"当前建议：{decision}。AI层只提出/解释/质检候选，"
                "实际指标、回测、冲突分析和状态迁移由确定性引擎控制。"
            ),
            "specialist_reviews": {
                name: bundle.model_dump(mode="json") for name, bundle in reviewers.items()
            },
            "evidence_summary": {
                "top_scenario_count": len(knowledge.get("top_scenarios", [])),
                "profiled_features": feature.get("profiled_features", 0),
                "graph_users": graph.get("users", 0),
                "behavior_sample_size": behavior.get("sample_size", 0),
                "stability_status": stability.get("status", "UNKNOWN"),
                "conflict_recommendation": conflicts.get("recommendation", "UNKNOWN"),
                "test_stage": test_env.get("current_stage", "not_created_yet"),
            },
            "human_in_the_loop": True,
            "automatic_enforcement": False,
            "automatic_regulatory_submission": False,
        }
        return lead
