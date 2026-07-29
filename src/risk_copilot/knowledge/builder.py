from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pandas as pd

from ..config import load_yaml
from ..schemas import KnowledgeScenario


class RiskKnowledgeBuilder:
    def __init__(self, scenarios_path: str | Path) -> None:
        self.scenarios = [KnowledgeScenario.model_validate(item) for item in load_yaml(scenarios_path)]

    def to_dataframe(self) -> pd.DataFrame:
        rows = []
        for s in self.scenarios:
            rows.append(
                {
                    "scenario_id": s.scenario_id,
                    "industry": s.industry,
                    "business_line": s.business_line,
                    "event_stage": s.event_stage,
                    "risk_domain": s.risk_domain.value,
                    "risk_types": " | ".join(s.risk_types),
                    "definition": s.definition,
                    "attacker_profiles": " | ".join(s.attacker_profiles),
                    "black_grey_tools": " | ".join(s.black_grey_tools),
                    "attack_preferences": " | ".join(s.attack_preferences),
                    "manifestations": " | ".join(s.manifestations),
                    "data_sources": " | ".join(s.data_sources),
                    "candidate_features": " | ".join(s.candidate_features),
                    "expert_rules": " | ".join(s.expert_rules),
                    "recommended_models": " | ".join(s.recommended_models),
                    "actions": " | ".join(a.value for a in s.actions),
                    "monitoring_metrics": " | ".join(s.monitoring_metrics),
                }
            )
        return pd.DataFrame(rows)

    def build_markdown(self) -> str:
        by_industry: dict[str, list[KnowledgeScenario]] = defaultdict(list)
        for scenario in self.scenarios:
            by_industry[scenario.industry].append(scenario)
        lines = [
            "# 风险场景与策略知识地图",
            "",
            "> 依据实习课题组织风险场景、黑灰产、特征、规则、模型、处置和效果指标；它是策略设计知识层，不是人工审核运营指标看板。",
            "",
            "## 总体方法",
            "",
            "名单/硬规则兜底 → 专家规则分层 → 模型与图谱提召回 → 人工复核 → 处置 → 结果回流与策略回溯。",
            "",
        ]
        for industry, scenarios in by_industry.items():
            lines.append(f"# {'银行业' if industry == 'banking' else '数字资产行业'}")
            lines.append("")
            for s in scenarios:
                lines += [
                    f"## {s.scenario_id}｜{s.business_line}｜{s.event_stage}",
                    "",
                    f"**风险域：** {s.risk_domain.value}",
                    "",
                    f"**定义：** {s.definition}",
                    "",
                    f"**风险类型：** {'、'.join(s.risk_types)}",
                    "",
                    f"**黑灰产角色：** {'、'.join(s.attacker_profiles)}",
                    "",
                    f"**作案工具：** {'、'.join(s.black_grey_tools)}",
                    "",
                    f"**攻击偏好：** {'、'.join(s.attack_preferences)}",
                    "",
                    f"**特征表现：** {'、'.join(s.manifestations)}",
                    "",
                    f"**数据源：** {'、'.join(s.data_sources)}",
                    "",
                    f"**候选特征：** `{'`, `'.join(s.candidate_features)}`",
                    "",
                    "**初版专家规则：**",
                ]
                lines += [f"- {rule}" for rule in s.expert_rules]
                lines += ["", "**模型与适用性：**"]
                for model in s.recommended_models:
                    lines.append(f"- **{model}**：{s.model_tradeoffs.get(model, '需结合样本和实时性评估。')}")
                lines += [
                    "",
                    f"**处置：** {'、'.join(action.value for action in s.actions)}",
                    "",
                    f"**效果指标：** {'、'.join(s.monitoring_metrics)}",
                    "",
                ]
        return "\n".join(lines)

    def write(self, output_dir: str | Path) -> dict[str, Path]:
        target = Path(output_dir)
        target.mkdir(parents=True, exist_ok=True)
        md_path = target / "risk_knowledge_system.md"
        csv_path = target / "risk_knowledge_system.csv"
        md_path.write_text(self.build_markdown(), encoding="utf-8")
        self.to_dataframe().to_csv(csv_path, index=False)
        return {"markdown": md_path, "csv": csv_path}
