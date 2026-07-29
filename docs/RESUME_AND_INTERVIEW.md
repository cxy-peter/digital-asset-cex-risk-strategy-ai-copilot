# 简历与面试定位

## 项目名称

**Digital Asset Risk Strategy AI Copilot｜实习衍生个人项目**  
副标题：公司式策略测试、效果评估与 CMS/STR 内部联动平台

## 简历四条（AI Agent 强化版）

- 基于数字资产交易平台实习中接触的 Rule Engine、FEP、Risk Graph、策略回溯与 CMS/STR 产品结构，构建五角色 Risk Strategy AI Copilot；使用 LangGraph/ReAct 并行编排场景、特征模型、图谱行为和治理 Agent，并通过 MCP 式只读工具完成证据检索与专业评审。
- 设计结构化 AI Strategy Proposal Schema 与特征白名单，将自然语言风险需求转化为可解析 Rule DSL；AI 负责需求拆解、工具选择、候选草拟和冲突质检，确定性引擎负责 LR/Decision Tree/XGBoost、OOT 回测、稳定性和状态控制。
- 增加跨月份/bootstrap 稳定性与策略组合冲突分析，计算告警重叠、Jaccard、增量真阳性/召回、重复运营工作量及处置优先级冲突；由 Lead Agent 综合四个专业 Agent 结论输出 `SUBMIT/REVISE/REJECT_AS_DUPLICATE` 复核 Memo。
- 复刻公司式策略生命周期：Feature Contract、历史回溯、Simulation、独立第二人复核、三工作日观察模板和效果工单；策略三级标签可触发 CMS/STR 内部候选案件预填，但所有处罚和监管外发均保留人工审批。

## 面试开场（约90秒）

> 我在 CoinTR 实习期间接触了 Rule Engine、FEP 特征平台、策略回溯、Risk Graph、用户风险评分、处罚验证中心和 CMS/STR，也参与了主站 AI 策略助手的迁移调研。实习结束后，我基于这些脱敏产品结构独立重构了 Risk Strategy AI Copilot。
>
> 系统的结构类似股票投资顾问的多 Agent：场景与黑灰产 Agent、特征模型 Agent、Risk Graph 与行为 Agent、治理及 CMS/STR Agent 并行工作，最后由 Lead Risk Strategy Agent 汇总。Agent 可以自主调用 FEP、SOP、图谱、模型回测、稳定性和策略冲突工具，而不是只用一个大 Prompt 输出规则。
>
> 数值真值由确定性引擎控制：模型采用 LR、浅层决策树和 XGBoost，Development 选择阈值，OOT 只评价冻结版本；P0 又加入跨月份/bootstrap 稳定性和现有策略组合冲突分析。当前 Demo 的离线指标虽然达到门槛，但 Agent 发现它和一条 RFI 策略高度重叠且处置动作冲突，因此 Lead Agent 给出 REVISE，而不是直接上线。策略最终只进入 Simulation 和独立第二人复核，CMS/STR 也只生成内部候选案件，不允许 Agent 自动处罚或外发监管报告。

## 为什么需要 Agent，而不是直接训练一个 XGBoost

- 风险需求是自然语言，包含风险场景、业务背景、处置约束和监管语义，需要先结构化；
- 特征、模型、图谱、历史策略和 SOP 来自不同系统，需要动态选择工具；
- 单一 F1 无法判断现有策略重叠、处置冲突和治理风险；
- 专业 Agent 分工便于保留分歧、追踪证据和独立调试；
- LLM 适合规划、检索、解释和质检，确定性引擎适合数值计算与状态控制。

## 必须主动说明的边界

- 这是实习衍生个人原型，不是 CoinTR 生产系统；
- 没有使用生产 PII 或真实交易明细；
- 模型指标来自固定随机种子的合成数据；
- 没有自动处罚和自动监管提交；
- 团队系统是学习背景，个人完成的是 Agent 架构、合成数据、代码、回测、P0 能力和展示系统；
- KEP 自动化和 Anti-Fraud 运营指标是另外两个项目。
