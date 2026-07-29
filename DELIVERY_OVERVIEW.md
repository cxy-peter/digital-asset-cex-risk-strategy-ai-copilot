# Digital Asset Risk Strategy AI Copilot v0.7 — 交付概览

## 项目定位

该项目是基于数字资产交易平台实习中接触的 Rule Engine、FEP、策略回溯、Risk Graph、效果工单和 CMS/STR 产品结构完成的**实习衍生个人原型**。它不是通用 AML Agent 拼盘，也不是单一 XGBoost/规则引擎 Demo。

核心设计是：

```text
AI Agent 负责理解需求、选择工具、提出候选、整合证据和质检
确定性引擎负责数据契约、模型、回测、稳定性、冲突和状态治理
人工复核负责最终策略与高影响处置决策
```

## AI Agent 组成

- Scenario & Typology Agent；
- Feature & Model Agent；
- Risk Graph & Behavior Agent；
- Governance & CMS/STR Agent；
- Lead Risk Strategy Agent。

四个专业 Agent 可通过 LangGraph ReAct 并行调用只读 MCP 式工具；无外部 API 时，默认确定性 Agent Board 仍可完整运行。

## 本轮新增的 P0

| P0 | 已实现能力 |
|---|---|
| Interactive Strategy Console | `/console` 从自然语言需求展示完整 Agent、回测和治理结果 |
| Strategy Conflict & Incremental Value | 告警重叠、Jaccard、containment、增量真阳性/召回、重复工作量和处置冲突 |
| Cross-month & Bootstrap Stability | 月度指标、200轮 Bootstrap 区间、特征方向一致性和稳定性门禁 |

## 本轮 Demo 的关键结论

- OOT Precision 86.42%、Recall 48.61%、F1 62.22%；
- 稳定性：`STABLE`；
- 策略冲突：`REVISE_ACTION_PRECEDENCE`；
- Lead Agent：`REVISE`；
- 测试环境：`PENDING_SECOND_REVIEW`；
- 效果工单：`STRATEGY_CONFLICT`。

这里的价值不在于合成指标本身，而在于系统不会因 F1 高就直接推荐上线；Agent 发现已有策略覆盖和处置冲突后，会要求修改和独立复核。

## 建议阅读顺序

1. `README.md`；
2. `docs/AI_AGENT_PROJECT_NARRATIVE_CN.md`；
3. `docs/AI_AGENT_ARCHITECTURE.md`；
4. `docs/P0_ENHANCEMENTS.md`；
5. `docs/RESUME_AND_INTERVIEW.md`；
6. `VALIDATION_REPORT.md`；
7. `outputs/index.html`；
8. `outputs/strategy_demo/ai_advisory_board.md`。

## 安全与真实性边界

- 全部数据为合成数据；
- 无生产风控引擎连接；
- Agent 不能自动处罚或改变生产状态；
- CMS/STR 仅生成内部候选案件；
- 无外部监管提交；
- KEP 和 Anti-Fraud 运营指标是独立项目；
- 团队产品能力只作为学习背景和产品目录，不归为个人生产成果。
