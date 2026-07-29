# Digital Asset Risk Strategy AI Copilot：AI Agent 项目叙事

## 1. 项目为什么不是“XGBoost + 规则引擎 Demo”

该项目采用与股票投资顾问 Agent 相似的专业分工结构，但分析对象从股票基本面、技术面、估值和新闻，替换为数字资产风控中的风险场景、特征模型、Risk Graph 以及策略治理。

大模型不负责计算 Precision、Recall 或改变策略状态，而负责四类更适合 AI 的工作：

1. **理解风险需求**：把自然语言需求拆成风险域、事件、黑灰产路径、候选信号和治理目标；
2. **自主选择工具**：按当前信息缺口调用 FEP、SOP、Risk Graph、回测、稳定性、冲突和 CMS/STR 只读工具；
3. **提出和质检候选策略**：在严格特征白名单与 Rule DSL Schema 下生成可回溯的候选规则；
4. **综合多方意见**：Lead Agent 保留专业 Agent 的分歧，给出 `SUBMIT`、`REVISE` 或 `REJECT_AS_DUPLICATE` 建议。

所有数值结果由确定性 Python 引擎计算；所有状态迁移、处罚和监管提交均由治理层及人工复核控制。

## 2. 五个专业 Agent

| Agent | 类比股票投顾 Agent | 职责 | 典型工具 |
|---|---|---|---|
| Scenario & Typology Agent | 基本面 Agent | 识别风险场景、攻击链、黑灰产角色及 SOP 约束 | `search_sop`、`list_events`、`map_product_stack` |
| Feature & Model Agent | 技术/估值 Agent | 筛选决策时点可用特征，解释 AUC/KS/IV/Lift/PSI，审阅 LR/Tree/XGBoost | `search_features`、`get_model_results`、`get_stability_analysis` |
| Risk Graph & Behavior Agent | 新闻/事件 Agent | 分析设备、邮箱、手机号、KYC、地址关系及快进快出行为 | `explain_graph_path`、`get_behavior_contrast` |
| Governance & CMS/STR Agent | 风险控制 Agent | 检查策略重叠、处置冲突、模拟、双人复核及 CMS/STR 内部建案边界 | `get_strategy_conflict_analysis`、`get_company_test_environment`、`get_cms_str_internal_preview` |
| Lead Risk Strategy Agent | Summary Agent | 汇总四个 Agent，保留冲突，生成独立复核 Memo | 四个专业结论及确定性证据 |

## 3. ReAct 工作流

```text
Thought：当前风险需求缺少哪些事实？
Action：调用一个只读工具
Observation：获得结构化特征、图谱、回测或治理结果
Thought：证据是否充分，是否需要换工具或补充验证？
...
Final：形成策略评审建议和人工复核事项
```

四个专业 Agent 可并行运行；Lead Agent 在所有结果到齐后再汇总。默认离线模式使用确定性专业评审器，保证无需外部 API 也能复现。配置 OpenAI-compatible API 后，可切换 LangGraph ReAct 模式，让模型动态选择工具。

## 4. MCP 式工具体系

工具按能力拆分，而不是把所有信息塞进一个 Prompt：

- **Feature/FEP**：特征搜索、事件契约、缺失率、分位数和决策时点；
- **Knowledge/RAG**：策略生命周期、Risk Graph、RFI/EDD、CMS/STR 等 SOP 与风险类型知识；
- **Behavior/Graph**：资金行为、同人关系、路径证据和强弱关系；
- **Model/Backtest**：模型基线、候选规则、OOT 指标、月度和 bootstrap 稳定性；
- **Portfolio/Governance**：策略重叠、增量召回、处置冲突、版本和审批记录；
- **CMS/STR**：仅生成内部候选案件预览，禁止自动外部提交。

AI 工具全部只读。策略注册、状态变化和审批记录由确定性服务独立执行，模拟了公司系统中的职责分离与最小权限。

## 5. AI 策略候选生成

AI Proposal Agent 接受：

- 风险需求；
- 风险域和事件；
- 已注册且在决策时点可用的特征白名单；
- SOP 检索结果；
- 已有策略和处置约束。

输出必须符合结构化 Schema：

```json
{
  "strategy_name": "...",
  "event_code": "ChainWithdraw",
  "tag_level_1": "fund_security",
  "tag_level_2": "rapid_fiat_convert_chain_out",
  "tag_level_3": "MANUAL_REVIEW",
  "expression": "feature_a > x AND feature_b >= y",
  "required_features": ["feature_a", "feature_b"],
  "action": "MANUAL_REVIEW",
  "rationale": "...",
  "initial_status": "SIMULATION"
}
```

候选必须通过 Feature Contract 和 Rule DSL 解析；模型不能创造不存在的字段，也不能直接进入 `ONLINE`。

## 6. AI 与机器学习的关系

- Logistic Regression、Decision Tree 和 XGBoost 用于产生和评价统计候选；
- Risk Graph 用于补充关系特征与路径解释；
- AI Agent 用于需求拆解、工具编排、候选草拟、证据整合、冲突审阅和报告生成；
- Human-in-the-loop 决定是否进入下一阶段。

因此项目不是“让 LLM 替代 XGBoost”，而是让 AI Agent 编排风控平台中的规则、模型、图谱和治理工具。

## 7. Agent 评价体系

Agent 层不仅评价最终策略指标，还评价：

- 工具选择是否正确；
- 每个结论是否有证据引用；
- 是否使用了未注册或未来时点字段；
- 是否识别现有策略的高重叠和处置冲突；
- 是否保留不确定性和反例；
- 是否遵守 `SIMULATION → PENDING_REVIEW` 的治理边界；
- 是否错误地把内部 STR 候选案件表述为自动监管提交。

## 8. 本次 Demo 的 Agent 结论

四个专业 Agent 均完成评审，其中治理 Agent 因现有策略存在动作优先级冲突而标记为 degraded。Lead Agent 最终返回：

```text
Decision = REVISE
Stability = STABLE
Conflict = REVISE_ACTION_PRECEDENCE
Lifecycle = PENDING_SECOND_REVIEW
```

这比仅按 F1 选择一条“最好规则”更接近真实策略平台：即便离线指标良好，AI Agent 仍要求先解决与已有 RFI/DELAY/MANUAL_REVIEW 策略的处置冲突。

## 9. 简历定位

**Digital Asset Risk Strategy AI Copilot｜Python、LangGraph、MCP、XGBoost、Risk Graph**

- 构建五角色 Risk Strategy Agent 架构，使用 LangGraph/ReAct 编排场景、特征模型、图谱行为和治理 Agent，并通过 MCP 式只读工具接入 FEP、SOP、回测、稳定性、策略冲突和 CMS/STR 内部预览；
- 设计严格结构化 AI Candidate Schema 与特征白名单，将自然语言风险需求转化为可解析 Rule DSL，所有 AI 候选默认进入 Simulation 并保留证据引用和不确定性；
- 将 Agent 结论与 LR、Decision Tree、XGBoost、Risk Graph、OOT 回测、月度/bootstrap 稳定性及策略组合增量贡献联合评审，由 Lead Agent 输出 `SUBMIT/REVISE/REJECT` 人工复核 Memo；
- 实现 Human-in-the-loop 治理，禁止 Agent 自动处罚或监管外发，并通过版本、Hash、独立第二人复核和策略效果工单形成可审计闭环。

## 10. 真实性边界

这是实习后基于脱敏结构和合成数据完成的个人原型。实习期间的真实部分是参与/学习主站 AI 策略助手、Rule Engine、FEP、Risk Graph、策略回溯、CMS/STR 和测试验收；个人原型部分是五 Agent 架构、代码实现、合成数据、回测、P0 能力和展示系统。
