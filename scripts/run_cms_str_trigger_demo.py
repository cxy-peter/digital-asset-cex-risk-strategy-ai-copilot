from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import hashlib
import json

from risk_copilot.integrations.cms_str import CMSSTRIntegrationService
from risk_copilot.rules.backtest import StrategyBacktester
from risk_copilot.rules.dsl import rule_to_expression
from risk_copilot.rules.generator import CandidateRuleGenerator
from risk_copilot.runtime import RuntimeContext
from risk_copilot.schemas import RiskDomain, StrategyRequest


def _serialize(value):
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    raise TypeError(f"not JSON serializable: {type(value)!r}")


def main() -> None:
    root = PROJECT_ROOT
    runtime = RuntimeContext.create(root)
    runtime.ensure_demo_data()
    data = runtime.prepare_graph_enriched_users()

    request = StrategyRequest(
        request_id="CMS-STR-TRIGGER-DEMO",
        query="识别KYC后快速入金换币并链上提币、同时存在Risk Graph强关系的高风险用户",
        domain=RiskDomain.FUND_SECURITY,
        event_code="ChainWithdraw",
        max_alert_rate=0.05,
        minimum_precision=0.50,
        minimum_recall=0.01,
        review_capacity=300,
    )
    templates = CandidateRuleGenerator(root / "configs/strategy_templates.yaml").from_templates(request)
    strategy = next(item for item in templates if item.strategy_id == "TPL-rapid_cashout_high_precision")

    metrics = StrategyBacktester(review_capacity=request.review_capacity).evaluate(data, strategy)
    snapshot_basis = {
        "rows": len(data),
        "columns": sorted(map(str, data.columns)),
        "max_event_date": str(data["event_date"].max()),
        "target_rate": float(data[request.target_label].mean()),
    }
    data_snapshot_id = "SNAP-" + hashlib.sha256(
        json.dumps(snapshot_basis, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:16]

    integration = CMSSTRIntegrationService(
        root / "configs/cms_str_integration.yaml",
        root / "outputs/cms_str_case_previews.sqlite",
    ).prepare_candidates(
        strategy=strategy,
        strategy_version=1,
        data=data,
        data_snapshot_id=data_snapshot_id,
        top_k=10,
    )

    output = root / "outputs/cms_str_trigger_demo"
    output.mkdir(parents=True, exist_ok=True)
    payload = {
        "scope": "internal_candidate_case_preview_only",
        "strategy": strategy.model_dump(mode="json"),
        "strategy_expression": rule_to_expression(strategy.rule),
        "synthetic_backtest_metrics": metrics.model_dump(mode="json"),
        "data_snapshot_id": data_snapshot_id,
        "integration": integration,
        "truth_boundary": {
            "synthetic_data": True,
            "human_review_required": True,
            "external_submission_allowed": False,
            "automatic_filing_performed": False,
            "production_connection": False,
        },
    }
    (output / "cms_str_trigger_demo.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=_serialize),
        encoding="utf-8",
    )
    cases = integration.get("cases", [])
    report = [
        "# CMS/STR 一键候选案件联动 Demo",
        "",
        "> 该演示只在合成数据中创建内部候选案件，不连接生产 CMS，不向 MASAK 自动提交。",
        "",
        "## 策略",
        "",
        f"- Strategy ID：`{strategy.strategy_id}`",
        f"- Event：`{strategy.event_code}`",
        f"- Level-3 Tag：`{strategy.tag_level_3}`",
        f"- Expression：`{rule_to_expression(strategy.rule)}`",
        f"- Recommended Action：`{strategy.action.value}`",
        "",
        "## 合成回测",
        "",
        f"- Alerts：{metrics.alerts}",
        f"- Precision：{metrics.precision:.2%}",
        f"- Recall：{metrics.recall:.2%}",
        f"- Alert Rate：{metrics.alert_rate:.2%}",
        "",
        "## 内部候选案件",
        "",
        f"- Enabled：`{integration.get('enabled')}`",
        f"- Case Count：`{integration.get('case_count', 0)}`",
        f"- MASAK Feedback Status：`{integration.get('masak_feedback_status')}`",
        f"- External Submission Allowed：`{integration.get('external_submission_allowed')}`",
        f"- Automatic Filing Performed：`{integration.get('automatic_filing_performed')}`",
        "",
        "| Case ID | User ID | Status | Evidence Hash |",
        "|---|---|---|---|",
    ]
    for case in cases:
        if hasattr(case, "model_dump"):
            case = case.model_dump(mode="json")
        report.append(
            f"| {case['case_id']} | {case['user_id']} | {case['status']} | {case['evidence_hash'][:12]}… |"
        )
    report.extend(
        [
            "",
            "## 严格边界",
            "",
            "- ‘一键 STR’在本原型中只表示预填内部 CMS/STR 候选案件；",
            "- 最终是否形成 STR 必须由合规人员基于完整证据决定；",
            "- 普通用户画像不得展示 STR 机密状态；",
            "- MASAK 反馈字段只是状态模型，不代表发生了真实提交或反馈。",
        ]
    )
    (output / "README.md").write_text("\n".join(report), encoding="utf-8")
    print(f"Strategy: {strategy.name}")
    print(f"Cases: {integration.get('case_count', 0)}")
    print(f"Open: {output / 'README.md'}")


if __name__ == "__main__":
    main()
