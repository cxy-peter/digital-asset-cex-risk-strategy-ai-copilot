# Digital Asset Risk Strategy AI Copilot v0.7 — Validation Report

验证日期：2026-07-29（UTC）

## 1. 验证结论

当前版本已从单纯的机器学习/规则回测平台升级为**专业多 Agent 风控策略 Copilot**：四个专业 Agent 并行调用 FEP、SOP、Risk Graph、模型、稳定性、策略冲突及 CMS/STR 只读工具，再由 Lead Risk Strategy Agent 生成独立复核 Memo。数值计算、规则执行和生命周期状态仍由确定性引擎控制。

项目完整主链路、P0 稳定性/冲突分析、公司式测试环境、效果工单、版本治理和 CMS/STR 内部候选案件预览均已实际运行。项目使用固定随机种子的合成数据，不代表 CoinTR 生产部署或真实业务效果。

## 2. 执行命令

```bash
python -m compileall -q src scripts tests
pytest -q -rs
python scripts/run_full_demo.py
python scripts/run_cms_str_trigger_demo.py
```

## 3. 自动测试

```text
34 passed, 3 skipped in 10.15s
```

三个跳过项均来自未安装的可选 Agent/MCP 依赖：

- `langgraph`：1 项；
- `langchain_core`：1 项；
- `mcp.server`：1 项。

确定性多 Agent Board、模型、回测、P0 分析、治理和报告主链路均已执行。覆盖内容包括：

- 事件与特征契约、决策时点和数据泄漏检查；
- Train / Development / OOT 隔离；
- Logistic Regression、浅层 Decision Tree、XGBoost；
- 决策树高风险路径转 Rule DSL；
- Risk Graph 强弱关系和路径解释；
- AI Strategy Proposal 的特征白名单与结构化 Schema；
- 五角色 AI Advisory Board 与 Agent 失败隔离；
- 月度/Bootstrap 稳定性和特征方向一致性；
- 现有策略组合重叠、增量贡献和处置动作冲突；
- Onboarding + T+1 用户风险评分及人工覆盖保护；
- 策略版本、Payload Hash、并发写入和审计记录；
- 公司式策略测试生命周期和效果工单；
- CMS/STR 内部候选案件去重、人工复核和禁止外发；
- FastAPI `/console` 交互页面及 API 输出。

## 4. AI Agent 架构验证

### 4.1 专业 Agent

| Agent | 执行状态 | 核心结论 |
|---|---|---|
| Scenario & Typology Agent | succeeded | 风险场景、黑灰产路径和规则条件已建立业务映射 |
| Feature & Model Agent | succeeded | OOT 指标和跨月份/Bootstrap 稳定性通过确定性引擎验证 |
| Risk Graph & Behavior Agent | succeeded | 强关系、弱关系、资金行为和噪声控制已分层处理 |
| Governance & CMS/STR Agent | degraded | 检测到高重叠策略及处置动作优先级冲突，需要修改 |
| Lead Risk Strategy Agent | completed | 最终建议 `REVISE`，而不是因离线指标良好直接上线 |

AI 层的约束：

```text
human_in_the_loop = true
automatic_enforcement = false
automatic_regulatory_submission = false
```

### 4.2 ReAct/MCP 模式

代码包含四个并行 LangGraph ReAct Reviewer 和 Lead Agent，可通过 OpenAI-compatible API 动态调用只读工具。当前容器未安装全部可选依赖，因此实时 ReAct 集成测试被跳过；默认确定性 Agent Board 可完整复现同一职责分工和结构化结果。

## 5. 完整策略 Demo

固定随机种子的合成数据上，本次冻结候选为：

```text
Strategy ID: TREE-ChainWithdraw-01
Name: Decision Tree候选规则 1
Event: ChainWithdraw
Tag L1: fund_security
Tag L2: rapid_fiat_convert_chain_out
Tag L3: MANUAL_REVIEW
Action: MANUAL_REVIEW
```

规则表达式：

```text
behavior_event_count_30d > 30.5
AND strong_relation_fraud_1hop_count > 0.5
AND strategy_avoidance_ratio_30d > 0.302633
AND behavior_event_count_30d > 42.5
```

OOT 合成结果：

| 指标 | 数值 |
|---|---:|
| Sample Size | 2,000 |
| Alerts | 81 |
| Alert Rate | 4.05% |
| Precision | 86.42% |
| Recall | 48.61% |
| F1 | 62.22% |
| False Positive Rate | 0.59% |
| Lift | 12.00 |
| Captured Loss Rate | 52.15% |
| Stability Score | 98.52% |

这些数字只用于验证代码链路和相对评价机制，不得写成公司真实策略效果。

## 6. P0-A：交互式策略控制台

FastAPI 提供 `/console` 页面，可从自然语言风险需求启动完整流程，并展示：

- 专业 Agent 与 Lead Agent 结论；
- 候选 Rule DSL 和 OOT 指标；
- 稳定性和组合冲突；
- 测试环境、效果工单及 CMS/STR 内部预览；
- 完整结构化 API 响应。

控制台不会提供“直接上线”“执行冻结”或“外部提交 STR”按钮。

## 7. P0-B：跨月份与 Bootstrap 稳定性

冻结策略在三个月份上均产生有效告警：

| 月份 | Precision | Recall | F1 | Alert Rate |
|---|---:|---:|---:|---:|
| 2026-04 | 88.89% | 38.10% | 53.33% | 2.52% |
| 2026-05 | 86.11% | 59.62% | 70.45% | 4.12% |
| 2026-06 | 87.10% | 47.79% | 61.71% | 4.03% |

稳定性门禁：

- Monthly Precision CV：1.32%；
- Monthly Alert Rate CV：20.62%；
- Feature Direction Consistency：100%；
- 200-round Bootstrap Precision 95% CI：82.01%–91.77%；
- 200-round Bootstrap Recall 95% CI：45.39%–57.70%；
- 6/6 稳定性 Gate 通过；
- Status：`STABLE`。

这只代表合成 OOT 内的稳定性，不能替代真实上线后三个工作日观察。

## 8. P0-C：策略冲突与增量贡献

候选策略与五条合成存量策略进行组合对比，其中四条事件兼容：

- 与 `EXIST-CHAIN-002` 的 selected containment 为 92.59%；
- 候选 81 条告警中，77 条已被存量策略覆盖；
- 增量告警 4 条，增量真阳性 1 条；
- 增量 Recall 贡献仅 0.69%；
- 重复运营工作量率 95.06%；
- 检测到 `MANUAL_REVIEW` 与 `RFI/DELAY` 的处置动作冲突；
- Recommendation：`REVISE_ACTION_PRECEDENCE`。

因此 Lead Agent 返回 `REVISE`，策略即使离线 F1 较高，也不能直接进入发布流程。这一结果验证了 Agent 不是装饰性总结器，而是在模型指标之外执行组合策略质检。

## 9. 公司式策略测试环境

当前测试记录：

```text
test_run_id = TESTRUN-TREE-ChainWithdraw-01-016-e819955b
current_stage = independent_second_review
release_status = PENDING_SECOND_REVIEW
production_connection = false
```

必须审批角色：

- `risk_strategy`；
- `risk_operations`；
- `independent_second_reviewer`；
- `strategy_action_precedence_reviewer`；
- `ai_advisory_findings_owner`。

三个工作日观察模板均保持：

```text
status = PLANNED_NOT_EXECUTED
production_observation_performed = false
```

## 10. 策略有效性工单

```text
ticket_id = EFF-TREE-ChainWithdraw-01-016-e819955b
evaluation_phase = SIMULATION
label = STRATEGY_CONFLICT
status = PENDING_REVIEW
```

工单没有把高离线指标直接标记为最终有效，而是将策略组合冲突作为优先处理问题。

## 11. CMS/STR 内部候选案件 Demo

主策略三级标签为 `MANUAL_REVIEW`，不会自动创建 STR 候选案件。专项 Demo 使用：

```text
strategy_id = TPL-rapid_cashout_high_precision
tag_level_3 = CMS_STR_CANDIDATE
internal_candidate_cases = 10
```

专项合成回测：

| 指标 | 数值 |
|---|---:|
| Precision | 94.77% |
| Recall | 23.42% |
| Alert Rate | 1.53% |
| Lift | 15.31 |

每个案件均满足：

```text
human_review_required = true
external_submission_allowed = false
automatic_filing_performed = false
masak_feedback_status = NOT_SUBMITTED
```

## 12. 工程清单

| 维度 | 数量 |
|---|---:|
| 执行工作流模块 | 20 |
| Python 文件 | 87 |
| Python LOC | 10,425 |
| MCP 式本地工具 | 29 |
| 注册特征 | 120 |
| 注册事件 | 21 |
| 产品目录 | 26 |
| 自动测试用例 | 37 |
| 事件契约阻断错误 | 0 |
| 事件契约提示 | 56 |
| 输出产物 | 47 |

“产品目录”包含 `implemented / modeled / catalog_only` 状态，不能把团队产品目录全部描述为个人开发成果。

## 13. 范围与边界检查

- KEP 自动化不在本项目实现范围；
- Anti-Fraud 运营指标已拆分为独立项目；
- 普通用户画像不展示 STR 机密状态；
- Agent 不允许直接上线策略、执行处罚或提交监管报告；
- 所有数据均为合成数据或脱敏语义；
- OOT 不参与候选阈值选择；
- AI 候选只能使用已注册且决策时点可用的特征；
- 生成的 SQLite 仅保存 Demo 策略、效果工单和内部候选案件。

## 14. 重点产物

- `outputs/index.html`；
- `outputs/strategy_demo/strategy_dashboard.html`；
- `outputs/strategy_demo/ai_advisory_board.md`；
- `outputs/strategy_demo/strategy_stability_analysis.json`；
- `outputs/strategy_demo/strategy_conflict_analysis.json`；
- `outputs/strategy_demo/strategy_test_environment.json`；
- `outputs/strategy_demo/strategy_effectiveness_ticket.json`；
- `outputs/strategy_demo/cms_str_integration.json`；
- `docs/AI_AGENT_ARCHITECTURE.md`；
- `docs/AI_AGENT_PROJECT_NARRATIVE_CN.md`。
