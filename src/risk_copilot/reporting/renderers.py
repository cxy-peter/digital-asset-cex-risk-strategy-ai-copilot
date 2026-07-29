from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..rules.dsl import rule_to_expression
from ..schemas import StrategyPackage


class StrategyReportRenderer:
    def __init__(self, template_dir: str | Path) -> None:
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    @staticmethod
    def _candidate_rows(package: StrategyPackage) -> list[dict[str, Any]]:
        evaluations = package.evaluation_context.get("candidate_evaluations", [])
        if evaluations:
            return [
                {
                    "development_rank": rank,
                    "strategy_id": item["strategy_id"],
                    "name": item["name"],
                    "source": item["source"],
                    "action": item["action"],
                    "expression": item["expression"],
                    "selected": item.get("selected", False),
                    "development_precision": item["development"]["precision"],
                    "development_recall": item["development"]["recall"],
                    "development_f1": item["development"]["f1"],
                    "development_alert_rate": item["development"]["alert_rate"],
                    "development_reward": item["development"]["reward"],
                    "development_relative_advantage": item["development"][
                        "relative_advantage"
                    ],
                    "reward": item["development"]["reward"],
                    "relative_advantage": item["development"][
                        "relative_advantage"
                    ],
                    "alerts": item["out_of_time"]["alerts"],
                    "alert_rate": item["out_of_time"]["alert_rate"],
                    "precision": item["out_of_time"]["precision"],
                    "recall": item["out_of_time"]["recall"],
                    "f1": item["out_of_time"]["f1"],
                    "fpr": item["out_of_time"]["false_positive_rate"],
                    "lift": item["out_of_time"]["lift"],
                    "captured_loss_rate": item["out_of_time"][
                        "captured_loss_rate"
                    ],
                    "oot_reward_reporting_only": item["out_of_time"]["reward"],
                }
                for rank, item in enumerate(evaluations, start=1)
            ]
        rows = []
        all_items = [(package.selected_strategy, package.selected_metrics)] + package.alternatives
        seen = set()
        for strategy, metrics in all_items:
            if strategy.strategy_id in seen:
                continue
            seen.add(strategy.strategy_id)
            rows.append(
                {
                    "strategy_id": strategy.strategy_id,
                    "name": strategy.name,
                    "source": strategy.source,
                    "action": strategy.action.value,
                    "expression": rule_to_expression(strategy.rule),
                    "alerts": metrics.alerts,
                    "alert_rate": metrics.alert_rate,
                    "precision": metrics.precision,
                    "recall": metrics.recall,
                    "f1": metrics.f1,
                    "fpr": metrics.false_positive_rate,
                    "lift": metrics.lift,
                    "captured_loss_rate": metrics.captured_loss_rate,
                    "reward": metrics.reward,
                    "relative_advantage": metrics.relative_advantage,
                    "development_reward": metrics.reward,
                    "development_relative_advantage": metrics.relative_advantage,
                }
            )
        return rows

    def markdown(self, package: StrategyPackage) -> str:
        selected = package.selected_strategy
        metrics = package.selected_metrics
        lines = [
            "# Digital Asset Risk Strategy Copilot｜策略评估报告",
            "",
            "> 所有用户、图谱、案件与效果指标均为脱敏模拟或聚合演示数据；本报告不代表任何生产系统上线结果。",
            "",
            "## 1. 风险需求",
            "",
            f"- Request ID：`{package.request.request_id}`",
            f"- Query：{package.request.query}",
            f"- Risk Domain：`{package.request.domain.value}`",
            f"- Event：`{package.request.event_code}`",
            f"- Constraints：Precision≥{package.request.minimum_precision:.0%}，Recall≥{package.request.minimum_recall:.0%}，Alert Rate≤{package.request.max_alert_rate:.0%}",
            "",
            "## 2. Multi-Agent分析",
            "",
        ]
        for result in package.agent_results:
            lines += [f"### {result.agent}", "", result.summary, ""]
            if result.warnings:
                lines += ["**Warnings**", ""] + [f"- {warning}" for warning in result.warnings] + [""]

        product_rows = package.product_context.get("products", [])[:18]
        lines += [
            "## 3. 风控产品栈",
            "",
            "| Product | Layer | Purpose | Prototype |",
            "|---|---|---|---|",
        ]
        for product in product_rows:
            lines.append(
                f"| {product.get('name')} (`{product.get('product_id')}`) | {product.get('layer')} | "
                f"{product.get('purpose')} | {product.get('prototype_status')} |"
            )

        tier_distribution = package.risk_scoring.get("tier_distribution", {})
        lines += [
            "",
            "## 4. 用户风险评分与分层",
            "",
            "- Scoring：Onboarding KYC + T+1 dynamic behavior；",
            f"- Tier Distribution：`{json.dumps(tier_distribution, ensure_ascii=False)}`；",
            f"- Manual Override Preserved：`{package.risk_scoring.get('scoring_policy', {}).get('manual_override_preserved', True)}`；",
            f"- STR Visible in Ordinary Profile：`{package.risk_scoring.get('str_visible_count', 0)}` 条。",
            "",
            "## 5. 处置与处罚中心治理",
            "",
        ]
        selected_plan = package.disposition_plan.get("selected_strategy_plan", {})
        for key in ["detection_action", "execution_mode", "required_approvals", "direct_execution_allowed"]:
            if key in selected_plan:
                lines.append(f"- {key}：`{selected_plan[key]}`")
        if package.registry_record:
            lines += [
                "",
                "## 6. 策略版本与审计记录",
                "",
                f"- SQLite Registry：`{package.registry_record.get('database')}`",
                f"- Version：`{package.registry_record.get('version')}`",
                f"- Registry Status：`{package.registry_record.get('status')}`",
            ]

        lines += [
            "",
            "## 7. 时间评估协议",
            "",
            "- Split：60% Train / 20% Development / 20% OOT；",
            "- Train：拟合模型并提供Graph已知标签快照；",
            "- Development：特征推荐、阈值选择、候选排序和策略冻结；",
            "- OOT：只报告冻结策略与模型的最终指标，不参与排序和选择；",
            f"- Frozen Strategy ID：`{package.evaluation_context.get('frozen_strategy_id')}`。",
            f"- Selection Basis：`{package.evaluation_context.get('selection_basis')}`。",
            "",
            "## 8. Development特征区分度 Top 20",
            "",
            "| Feature | AUC | KS | IV | Lift@10 | PSI | Recommended |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
        for profile in package.feature_profiles[:20]:
            lines.append(
                f"| `{profile.feature}` | {profile.auc_1d or 0:.3f} | {profile.ks_1d or 0:.3f} | "
                f"{profile.iv or 0:.3f} | {profile.lift_top_10 or 0:.2f} | {profile.psi or 0:.3f} | {profile.recommended} |"
            )

        lines += [
            "",
            "## 9. OOT模型基线（Threshold由Development选择）",
            "",
            "| Model | ROC-AUC | KS | AP | Threshold | Precision | Recall | F1 | FPR | Lift@10 |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for model in package.model_benchmarks:
            lines.append(
                f"| {model.model_name} | {model.roc_auc:.3f} | {model.ks:.3f} | {model.average_precision:.3f} | "
                f"{model.threshold:.3f} | {model.precision:.3f} | {model.recall:.3f} | {model.f1:.3f} | "
                f"{model.false_positive_rate:.3f} | {model.lift_top_10:.2f} |"
            )

        lines += [
            "",
            "## 10. Development排序与OOT最终评价",
            "",
            "| Dev Rank | Strategy | Source | Dev Reward | Dev Advantage | Dev Precision | Dev Recall | OOT Alerts | OOT Alert Rate | OOT Precision | OOT Recall | OOT F1 |",
            "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for row in self._candidate_rows(package):
            lines.append(
                f"| {row.get('development_rank', '-')} | {row['name']} | {row['source']} | "
                f"{row['development_reward']:.4f} | {row['development_relative_advantage']:.2f} | "
                f"{row.get('development_precision', row['precision']):.2%} | "
                f"{row.get('development_recall', row['recall']):.2%} | {row['alerts']} | "
                f"{row['alert_rate']:.2%} | {row['precision']:.2%} | {row['recall']:.2%} | "
                f"{row['f1']:.3f} |"
            )

        lines += [
            "",
            "## 11. 推荐策略",
            "",
            f"**{selected.name}** (`{selected.strategy_id}`)",
            "",
            f"- Source：{selected.source}",
            f"- Event：{selected.event_code}",
            f"- Action：{selected.action.value}",
            f"- Strategy Tags：`{selected.tag_level_1} / {selected.tag_level_2} / {selected.tag_level_3}`",
            f"- Rule：`{rule_to_expression(selected.rule)}`",
            "- Selection：Development排序后冻结；",
            f"- OOT Precision：{metrics.precision:.2%}",
            f"- OOT Recall：{metrics.recall:.2%}",
            f"- OOT Alert Rate：{metrics.alert_rate:.2%}",
            f"- OOT Captured Loss Rate：{metrics.captured_loss_rate:.2%}",
            "",
        ]

        ai_board = package.ai_advisory_board or {}
        proposal_mode = next(
            (
                result.structured_output.get("mode")
                for result in package.agent_results
                if result.agent == "ai_strategy_proposal_agent"
            ),
            "unknown",
        )
        lines += [
            "## 12. AI Strategy Advisory Board",
            "",
            f"- Proposal Mode：`{proposal_mode}`",
            f"- Lead Agent Decision：`{ai_board.get('decision', 'NOT_RUN')}`",
            "- AI Boundary：候选生成、解释和质检；确定性引擎负责回测、冲突、状态迁移和审批。",
            f"- Human in the Loop：`{ai_board.get('human_in_the_loop', True)}`",
            "",
        ]
        if ai_board:
            lines += [ai_board.get("executive_summary", ""), "", "### Specialist Agents", ""]
            for name, review in ai_board.get("specialist_reviews", {}).items():
                lines += [f"#### {name}", "", review.get("summary", ""), ""]
                for finding in review.get("findings", [])[:5]:
                    lines.append(
                        f"- [{finding.get('severity', 'low').upper()}] {finding.get('category')}: "
                        f"{finding.get('statement')}"
                    )
                if review.get("risks"):
                    lines += ["", "Risks:"] + [f"- {item}" for item in review.get("risks", [])]
                lines.append("")

        stability = package.stability_analysis or {}
        lines += [
            "## 13. 跨月份与Bootstrap稳定性",
            "",
            f"- Status：`{stability.get('status', 'NOT_RUN')}`",
            f"- Months：`{stability.get('summary', {}).get('months', 0)}`",
            f"- Monthly Precision CV：`{stability.get('summary', {}).get('monthly_precision_cv', 0):.4f}`",
            f"- Monthly Alert Rate CV：`{stability.get('summary', {}).get('monthly_alert_rate_cv', 0):.4f}`",
            f"- Feature Direction Consistency：`{stability.get('summary', {}).get('feature_direction_consistency', 0):.2%}`",
            f"- Gates：`{stability.get('summary', {}).get('gates_passed', 0)}/{stability.get('summary', {}).get('gates_total', 0)}`",
            "",
            "| Month | Sample | Alerts | Alert Rate | Precision | Recall | F1 | FPR |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for row in stability.get("monthly", []):
            lines.append(
                f"| {row.get('period')} | {row.get('sample_size')} | {row.get('alerts')} | "
                f"{row.get('alert_rate', 0):.2%} | {row.get('precision', 0):.2%} | "
                f"{row.get('recall', 0):.2%} | {row.get('f1', 0):.3f} | "
                f"{row.get('false_positive_rate', 0):.2%} |"
            )
        lines += ["", "### Bootstrap 95%区间", "", "| Metric | Mean | Std | 2.5% | 97.5% |", "|---|---:|---:|---:|---:|"]
        for metric_name, stats in stability.get("bootstrap", {}).items():
            lines.append(
                f"| {metric_name} | {stats.get('mean', 0):.4f} | {stats.get('std', 0):.4f} | "
                f"{stats.get('ci_lower_95', 0):.4f} | {stats.get('ci_upper_95', 0):.4f} |"
            )

        conflict = package.conflict_analysis or {}
        lines += [
            "",
            "## 14. 策略冲突与增量贡献",
            "",
            f"- Recommendation：`{conflict.get('recommendation', 'NOT_RUN')}`",
            f"- Compatible Existing Strategies：`{conflict.get('compatible_portfolio_size', 0)}`",
            f"- High-overlap Strategies：`{conflict.get('high_overlap_count', 0)}`",
            f"- Action Conflicts：`{conflict.get('action_conflict_count', 0)}`",
            f"- Incremental Alerts：`{conflict.get('incremental', {}).get('alerts', 0)}`",
            f"- Incremental Risk Recall：`{conflict.get('incremental', {}).get('recall_contribution', 0):.2%}`",
            f"- Duplicate Workload Rate：`{conflict.get('incremental', {}).get('duplicate_workload_rate', 0):.2%}`",
            "",
            "| Existing Strategy | Action | Jaccard | Selected Containment | Incremental/Conflict | Severity |",
            "|---|---|---:|---:|---|---|",
        ]
        for row in conflict.get("comparisons", [])[:12]:
            if row.get("status") != "evaluated":
                continue
            lines.append(
                f"| {row.get('name')} | {row.get('action')} | {row.get('jaccard', 0):.2%} | "
                f"{row.get('selected_containment', 0):.2%} | action_conflict={row.get('action_conflict')} | "
                f"{row.get('severity')} |"
            )

        lines += [
            "",
            "## 15. 治理结论",
            "",
            f"- Decision：`{package.governance.decision}`",
            f"- Lifecycle：`{package.governance.current_status.value}` → `{package.governance.next_status.value}`",
            f"- Required Approvals：{', '.join(package.governance.required_approvals)}",
            "",
        ]
        lines += [f"- {reason}" for reason in package.governance.reasons]
        deployment = package.strategy_test_environment
        lines += [
            "",
            "## 16. 公司式策略测试环境与上线有效性闭环",
            "",
            f"- Test Run ID：`{deployment.get('test_run_id')}`",
            f"- Data Snapshot：`{deployment.get('data_snapshot_id')}`",
            f"- Current Stage：`{deployment.get('current_stage', 'simulation_execution')}`",
            f"- Release Status：`{deployment.get('release_status', 'REVISION_REQUIRED')}`",
            f"- Required Approvals：`{deployment.get('required_approvals', [])}`",
            f"- Initial Observation：`{deployment.get('monitoring_workdays', 3)}` working days",
            f"- Production Connection：`{deployment.get('production_connection', False)}`",
            f"- Dispatch Performed：`{deployment.get('dispatch_performed', False)}`",
            f"- Blockers：`{deployment.get('blockers', [])}`",
            "",
            "| Stage | Status | Entry Gates | Exit Gates | Evidence |",
            "|---|---|---|---|---|",
        ]
        for stage in deployment.get("stages", []):
            lines.append(
                f"| `{stage.get('name')}` | `{stage.get('status')}` | "
                f"{'; '.join(stage.get('entry_gates', []))} | "
                f"{'; '.join(stage.get('exit_gates', []))} | "
                f"{'; '.join(stage.get('evidence_refs', []))} |"
            )
        observation_template = deployment.get("post_launch_observation_template", [])
        lines += [
            "",
            "### 上线后连续3个工作日观察模板",
            "",
            "> 这些记录为待生产团队填写的空白模板，不能用离线回测指标冒充生产有效性。",
            "",
            "| Workday | Date | Status | Hit | Confirmed | False Positive | PSI | User Feedback |",
            "|---:|---|---|---:|---:|---:|---:|---:|",
        ]
        for record in observation_template:
            lines.append(
                f"| {record.get('workday_index')} | {record.get('observation_date')} | "
                f"`{record.get('status')}` | {record.get('hit_count')} | "
                f"{record.get('confirmed_risk_count')} | {record.get('false_positive_count')} | "
                f"{record.get('feature_psi')} | {record.get('user_feedback_count')} |"
            )
        ticket = package.effectiveness_ticket
        lines += [
            "",
            "### Strategy Ticket Module：上线效果打标",
            "",
            f"- Ticket ID：`{ticket.get('ticket_id')}`",
            f"- Evaluation Phase：`{ticket.get('evaluation_phase')}`",
            f"- Effectiveness Label：`{ticket.get('label')}`",
            f"- Recommendation：{ticket.get('recommendation')}",
            f"- Synthetic Demo：`{ticket.get('synthetic_demo', True)}`",
            "",
            "### CMS/STR内部候选案件",
            "",
            f"- Enabled：`{package.cms_str_integration.get('enabled', False)}`",
            f"- Case Count：`{package.cms_str_integration.get('case_count', 0)}`",
            f"- MASAK Feedback Status：`{package.cms_str_integration.get('masak_feedback_status', 'NOT_SUBMITTED')}`",
            f"- External Submission Allowed：`{package.cms_str_integration.get('external_submission_allowed', False)}`",
            f"- Automatic Filing Performed：`{package.cms_str_integration.get('automatic_filing_performed', False)}`",
        ]
        lines += [
            "",
            "## 17. 风控引擎Payload",
            "",
            "```json",
            json.dumps(package.engine_payload, ensure_ascii=False, indent=2),
            "```",
            "",
            "## 18. 边界声明",
            "",
            "- 本项目为实习衍生、脱敏重构的个人原型；",
            "- Agent只生成候选策略并进入模拟/人工审核，不自动执行生产处罚；",
            "- STR明细不进入普通用户画像；",
            "- 手工风险调整必须保留risk_source和历史，不得被T+1任务静默覆盖；",
            "- KEP监管邮件自动化不属于本项目，已从Risk Strategy代码和叙事中排除；",
            "- Anti-Fraud人工审核指标体系为独立项目，只通过strategy_id/version与效果工单做可选关联。",
        ]
        return "\n".join(lines)

    def write(self, package: StrategyPackage, output_dir: str | Path) -> dict[str, Path]:
        target = Path(output_dir)
        target.mkdir(parents=True, exist_ok=True)
        md_path = target / "strategy_report.md"
        json_path = target / "strategy_package.json"
        payload_path = target / "risk_engine_payload.json"
        trace_path = target / "agent_trace.json"
        candidate_path = target / "candidate_ranking.csv"
        feature_path = target / "feature_profiles.csv"
        model_path = target / "model_benchmarks.csv"
        development_model_path = target / "model_development_benchmarks.csv"
        evaluation_path = target / "evaluation_protocol.json"
        product_path = target / "relevant_product_stack.csv"
        scoring_path = target / "risk_scoring_context.json"
        disposition_path = target / "disposition_context.json"
        registry_path = target / "registry_record.json"
        deployment_path = target / "strategy_test_environment.json"
        effectiveness_path = target / "strategy_effectiveness_ticket.json"
        observation_path = target / "post_launch_observation_template.csv"
        cms_str_path = target / "cms_str_integration.json"
        stability_path = target / "strategy_stability_analysis.json"
        monthly_stability_path = target / "monthly_stability.csv"
        bootstrap_stability_path = target / "bootstrap_stability.csv"
        feature_direction_path = target / "feature_direction_stability.csv"
        conflict_path = target / "strategy_conflict_analysis.json"
        conflict_comparison_path = target / "strategy_conflict_comparisons.csv"
        ai_board_path = target / "ai_advisory_board.json"
        ai_board_md_path = target / "ai_advisory_board.md"
        label_review_path = target / "suspected_mislabel_review_queue.csv"
        html_path = target / "strategy_dashboard.html"

        md_path.write_text(self.markdown(package), encoding="utf-8")
        json_path.write_text(package.model_dump_json(indent=2), encoding="utf-8")
        payload_path.write_text(json.dumps(package.engine_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        trace_path.write_text(
            json.dumps([result.model_dump(mode="json") for result in package.agent_results], ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        candidate_rows = self._candidate_rows(package)
        pd.DataFrame(candidate_rows).to_csv(candidate_path, index=False)
        pd.DataFrame([profile.model_dump(mode="json") for profile in package.feature_profiles]).to_csv(feature_path, index=False)
        pd.DataFrame([model.model_dump(mode="json") for model in package.model_benchmarks]).to_csv(model_path, index=False)
        pd.DataFrame(
            package.evaluation_context.get("development_model_benchmarks", [])
        ).to_csv(development_model_path, index=False)
        evaluation_path.write_text(
            json.dumps(
                package.evaluation_context,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        pd.DataFrame(package.product_context.get("products", [])).to_csv(product_path, index=False)
        scoring_path.write_text(json.dumps(package.risk_scoring, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        disposition_path.write_text(json.dumps(package.disposition_plan, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        registry_path.write_text(json.dumps(package.registry_record, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        deployment_path.write_text(
            json.dumps(
                package.strategy_test_environment,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        effectiveness_path.write_text(
            json.dumps(package.effectiveness_ticket, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        pd.DataFrame(
            package.strategy_test_environment.get("post_launch_observation_template", [])
        ).to_csv(observation_path, index=False)
        cms_str_path.write_text(
            json.dumps(package.cms_str_integration, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        stability_path.write_text(
            json.dumps(package.stability_analysis, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        pd.DataFrame(package.stability_analysis.get("monthly", [])).to_csv(monthly_stability_path, index=False)
        pd.DataFrame(
            [
                {"metric": name, **stats}
                for name, stats in package.stability_analysis.get("bootstrap", {}).items()
            ]
        ).to_csv(bootstrap_stability_path, index=False)
        pd.DataFrame(
            [
                {key: value for key, value in row.items() if key != "monthly"}
                for row in package.stability_analysis.get("feature_direction", [])
            ]
        ).to_csv(feature_direction_path, index=False)
        conflict_path.write_text(
            json.dumps(package.conflict_analysis, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        pd.DataFrame(package.conflict_analysis.get("comparisons", [])).to_csv(conflict_comparison_path, index=False)
        ai_board_path.write_text(
            json.dumps(package.ai_advisory_board, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        ai_lines = [
            "# AI Risk Strategy Advisory Board",
            "",
            f"- Mode: `{package.ai_advisory_board.get('mode', 'not_run')}`",
            f"- Decision: `{package.ai_advisory_board.get('decision', 'not_run')}`",
            "",
            package.ai_advisory_board.get("executive_summary", ""),
            "",
        ]
        for name, review in package.ai_advisory_board.get("specialist_reviews", {}).items():
            ai_lines += [f"## {name}", "", review.get("summary", ""), ""]
            ai_lines += [f"- {item}" for item in review.get("risks", [])]
            ai_lines.append("")
        ai_board_md_path.write_text("\n".join(ai_lines), encoding="utf-8")
        pd.DataFrame(
            package.evaluation_context.get("suspected_mislabel_queue", [])
        ).to_csv(label_review_path, index=False)

        candidate_df = pd.DataFrame(candidate_rows)
        scatter_html = ""
        if not candidate_df.empty:
            fig = px.scatter(
                candidate_df,
                x="recall",
                y="precision",
                size="alerts",
                color="source",
                hover_name="name",
                hover_data=["alert_rate", "f1", "fpr", "reward", "expression"],
                title="Candidate Strategy Frontier",
            )
            fig.update_xaxes(tickformat=".0%")
            fig.update_yaxes(tickformat=".0%")
            scatter_html = fig.to_html(full_html=False, include_plotlyjs="inline")

        model_df = pd.DataFrame([model.model_dump(mode="json") for model in package.model_benchmarks])
        model_html = ""
        if not model_df.empty:
            melted = model_df.melt(
                id_vars=["model_name"],
                value_vars=["roc_auc", "ks", "average_precision", "precision", "recall", "f1"],
                var_name="metric",
                value_name="value",
            )
            fig = px.bar(melted, x="model_name", y="value", color="metric", barmode="group", title="Model Benchmarks")
            model_html = fig.to_html(full_html=False, include_plotlyjs=False)

        template = self.env.get_template("strategy_dashboard.html")
        html_path.write_text(
            template.render(
                package=package,
                selected_expression=rule_to_expression(package.selected_strategy.rule),
                candidates=candidate_rows,
                scatter_html=scatter_html,
                model_html=model_html,
                engine_payload=json.dumps(package.engine_payload, ensure_ascii=False, indent=2),
                product_rows=package.product_context.get("products", []),
                tier_distribution=package.risk_scoring.get("tier_distribution", {}),
                disposition_plan=package.disposition_plan.get("selected_strategy_plan", {}),
                registry_record=package.registry_record,
                deployment_plan=package.strategy_test_environment,
                effectiveness_ticket=package.effectiveness_ticket,
                cms_str_integration=package.cms_str_integration,
                stability_analysis=package.stability_analysis,
                conflict_analysis=package.conflict_analysis,
                ai_advisory_board=package.ai_advisory_board,
            ),
            encoding="utf-8",
        )
        return {
            "markdown": md_path,
            "html": html_path,
            "json": json_path,
            "engine_payload": payload_path,
            "trace": trace_path,
            "candidate_csv": candidate_path,
            "feature_csv": feature_path,
            "model_csv": model_path,
            "development_model_csv": development_model_path,
            "evaluation_protocol_json": evaluation_path,
            "product_stack_csv": product_path,
            "risk_scoring_json": scoring_path,
            "disposition_json": disposition_path,
            "registry_record_json": registry_path,
            "strategy_test_environment_json": deployment_path,
            "effectiveness_ticket_json": effectiveness_path,
            "post_launch_observation_csv": observation_path,
            "cms_str_integration_json": cms_str_path,
            "strategy_stability_json": stability_path,
            "monthly_stability_csv": monthly_stability_path,
            "bootstrap_stability_csv": bootstrap_stability_path,
            "feature_direction_stability_csv": feature_direction_path,
            "strategy_conflict_json": conflict_path,
            "strategy_conflict_comparisons_csv": conflict_comparison_path,
            "ai_advisory_board_json": ai_board_path,
            "ai_advisory_board_markdown": ai_board_md_path,
            "suspected_mislabel_review_csv": label_review_path,
        }
