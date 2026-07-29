from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from ..features.registry import FeatureRegistry


MODEL_ROWS = [
    ("Expert Rules", "强模式、监管硬约束、冷启动", "实时、解释清晰、可直接配置", "覆盖长尾有限、维护成本高", "名单兜底/额度/强关联拦截"),
    ("Logistic Regression", "稳定线性风险评分、基线", "可解释、校准容易、审批友好", "非线性和交互能力有限", "用户风险评分/信用评分"),
    ("Decision Tree", "从黑白样本提取初版规则", "路径可解释、可转规则DSL", "单树易过拟合、边界不稳定", "深度限制+叶节点最小样本"),
    ("Random Forest", "中等规模表格数据", "鲁棒、非线性", "规则转化较难、实时成本高于单树", "离线特征筛选/辅助模型"),
    ("XGBoost/LightGBM", "表格类Fraud识别", "精度强、支持复杂交互", "需SHAP/校准/漂移监控", "主模型或召回模型"),
    ("Isolation Forest", "缺少黑样本的异常发现", "无需标签、上线快", "异常不等于欺诈、误报高", "探索性风险发现"),
    ("Autoencoder", "高维行为异常", "可学习正常模式", "解释弱、训练和阈值治理复杂", "设备/交易序列异常辅助"),
    ("Sequence Model", "登录-改密-绑地址-提现等时序", "能建模顺序和时间间隔", "数据、部署、解释成本高", "ATO/长链路行为"),
    ("Graph Features", "同设备/邮箱/手机/KYC/提现地址关联", "强可解释、适合团伙发现", "超级节点和弱关系会误伤", "先特征化再进入规则/模型"),
    ("GNN", "大规模复杂图团伙", "可传播高阶关系信号", "标签泄漏、时效、解释和工程复杂", "成熟图谱后的二期能力"),
    ("LLM/RAG", "SOP检索、需求解析、策略草案", "自然语言交互、知识整合", "幻觉，不应直接做高风险处罚", "Copilot与人机协同"),
    ("Agentic RL", "多步工具调用和策略迭代", "可优化长链路决策", "奖励设计与安全约束难", "有真实环境和轨迹后再训练"),
]


STRATEGY_PATTERNS = [
    ("名单/硬规则", "制裁地址、已确认赌博标签、黑名单", "拒绝/冻结/清退", "强证据优先，审计留痕"),
    ("阈值规则", "单笔大额、次数、速度、比例", "告警/延迟/审核", "分位、业务容量与误伤联合定阈值"),
    ("组合专家规则", "资金闭环+速度+银行/图谱", "RFI/人工审核", "以交互条件提高Precision"),
    ("评分卡", "多个稳定变量加权", "L1-L4/Low-Medium-High", "区分onboarding与T+1动态评分"),
    ("模型分层", "XGBoost概率/校准分", "低风险通过、中风险审核、高风险限制", "阈值按容量与损失优化"),
    ("图谱策略", "一跳强关系、二跳+行为、社区风险", "审核/限制", "IP弱关系不得单独强拦截"),
    ("无监督异常", "无黑样本场景", "观测/调查", "异常发现后需业务归因和标签闭环"),
    ("序列策略", "登录→改密→新增地址→提现", "VideoKYC/延迟", "关注动作顺序与时间窗"),
    ("策略编排", "名单→规则→模型→图谱→人工", "多级处置", "规则兜底、模型提召回、人工兜争议"),
    ("运营反馈", "工单、RFI、EDD、误伤、申诉", "策略迭代/下线", "结果标签与策略版本绑定"),
]


class IndicatorCatalogBuilder:
    def __init__(self, feature_registry: FeatureRegistry) -> None:
        self.registry = feature_registry

    def feature_frame(self) -> pd.DataFrame:
        rows = []
        for spec in self.registry.features:
            rows.append({
                "feature_name": spec.name,
                "display_name": spec.display_name,
                "description": spec.description,
                "risk_domain": spec.domain.value,
                "feature_type": spec.dtype.value,
                "freshness": spec.freshness.value,
                "source": spec.source,
                "event_codes": " | ".join(spec.event_codes),
                "available_at": spec.available_at,
                "pii_level": spec.pii_level,
                "expected_direction": spec.expected_direction,
                "default_operator": spec.default_operator,
                "tags": " | ".join(spec.tags),
            })
        return pd.DataFrame(rows)

    def event_frame(self) -> pd.DataFrame:
        rows = []
        for event in self.registry.events:
            rows.append({
                "event_code": event.code,
                "display_name": event.display_name,
                "stage": event.stage,
                "risk_domain": event.domain.value,
                "description": event.description,
                "latency_requirement": event.latency_requirement.value,
                "feature_count": len(event.available_features),
                "available_features": " | ".join(event.available_features),
                "allowed_actions": " | ".join(action.value for action in event.allowed_actions),
            })
        return pd.DataFrame(rows)

    def feature_markdown(self) -> str:
        domains: dict[str, list] = defaultdict(list)
        for feature in self.registry.features:
            domains[feature.domain.value].append(feature)
        lines = [
            "# 风控特征指标知识体系",
            "",
            "> 以风险域、事件、数据源、时效、PII等级、方向和应用场景管理特征全生命周期。",
            "",
            "## 指标平台治理框架",
            "",
            "1. **创建**：定义业务语义、统计窗口、事件时点、数据源和负责人；",
            "2. **质量**：监控空置率、延迟、异常分布、分位线和口径一致性；",
            "3. **区分度**：连续特征评估AUC/KS/IV/Lift，分类特征评估Cramér's V；",
            "4. **稳定性**：按月计算PSI并监控方向漂移；",
            "5. **策略使用**：记录被哪些策略/模型引用及命中效果；",
            "6. **迭代/下线**：版本化、审批、影响分析、回溯后再替换或退役。",
            "",
            "## 指标效果判断参考",
            "",
            "- AUC(1d)>0.60：单特征具备区分信号；",
            "- KS>0.20：正负样本分布存在可用差异；",
            "- IV 0.10–0.30：中等，>0.30：较强，但不可机械迷信；",
            "- Lift@Top10%>2：高风险头部有明显抓手；",
            "- PSI<0.10稳定，0.10–0.25需关注，>0.25明显漂移。",
            "",
        ]
        for domain, specs in sorted(domains.items()):
            lines += [f"## {domain}", "", "| Feature | 中文名 | 时效 | 来源 | 方向 | 事件 |", "|---|---|---|---|---|---|"]
            for spec in specs:
                lines.append(
                    f"| `{spec.name}` | {spec.display_name} | {spec.freshness.value} | {spec.source} | "
                    f"{spec.expected_direction} | {', '.join(spec.event_codes)} |"
                )
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def model_markdown() -> str:
        lines = [
            "# 风控算法与模型选型矩阵",
            "",
            "| 方法 | 适用场景 | 优势 | 局限 | 推荐用法 |",
            "|---|---|---|---|---|",
        ]
        lines += [f"| {a} | {b} | {c} | {d} | {e} |" for a, b, c, d, e in MODEL_ROWS]
        return "\n".join(lines)

    @staticmethod
    def strategy_markdown() -> str:
        lines = [
            "# 风控策略模式知识体系",
            "",
            "| 策略模式 | 典型信号 | 处置 | 设计原则 |",
            "|---|---|---|---|",
        ]
        lines += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in STRATEGY_PATTERNS]
        lines += [
            "",
            "## 策略生命周期",
            "",
            "需求/风险发现 → 特征可用性检查 → 候选规则/模型 → 历史回溯 → 模拟执行 → 独立第二人复核 → 上线评审 → 连续3个工作日观察 → 周/月效果打标 → 迭代/下线。",
            "",
            "## 关键效果指标",
            "",
            "Precision、Recall、F1、FPR、告警率、Lift、风险金额捕获率、审核容量、月度稳定性、误伤申诉率、处置转化率。",
        ]
        return "\n".join(lines)

    def risk_map_mermaid(self) -> str:
        domain_counts = Counter(f.domain.value for f in self.registry.features)
        lines = ["flowchart LR", '  A[业务与事件] --> B[数据与特征平台]', '  B --> C[规则/模型/图谱]', '  C --> D[风险决策]', '  D --> E[处置中心]', '  E --> F[运营/合规反馈]', '  F --> B']
        for idx, (domain, count) in enumerate(sorted(domain_counts.items()), 1):
            lines.append(f'  A --> D{idx}[{domain}\\n{count} features]')
            lines.append(f'  D{idx} --> B')
        lines += [
            '  E --> E1[PASS/MONITOR/ALERT]',
            '  E --> E2[RFI/EDD/VideoKYC]',
            '  E --> E3[Limit/Delay/Restriction]',
            '  E --> E4[Freeze/Reject - approval required]',
            '  F --> F1[Manual Review]',
            '  F --> F2[CMS/STR候选案件与反馈]',
            '  F --> F3[Appeal & False Positive]',
            '  F --> F4[Strategy Backtest & Versioning]',
        ]
        return "\n".join(lines)

    def write(self, output_dir: str | Path) -> dict[str, Path]:
        target = Path(output_dir)
        target.mkdir(parents=True, exist_ok=True)
        paths = {
            "feature_csv": target / "anti_fraud_feature_catalog.csv",
            "feature_md": target / "anti_fraud_feature_catalog.md",
            "event_csv": target / "risk_event_catalog.csv",
            "model_md": target / "model_selection_matrix.md",
            "strategy_md": target / "strategy_pattern_catalog.md",
            "risk_map": target / "risk_map.mmd",
        }
        self.feature_frame().to_csv(paths["feature_csv"], index=False)
        paths["feature_md"].write_text(self.feature_markdown(), encoding="utf-8")
        self.event_frame().to_csv(paths["event_csv"], index=False)
        paths["model_md"].write_text(self.model_markdown(), encoding="utf-8")
        paths["strategy_md"].write_text(self.strategy_markdown(), encoding="utf-8")
        paths["risk_map"].write_text(self.risk_map_mermaid(), encoding="utf-8")
        return paths
