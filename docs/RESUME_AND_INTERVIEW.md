# 简历与面试定位

## 项目名称

**Digital Asset & Payment Risk Strategy AI Copilot｜实习衍生个人项目**  
副标题：公司式策略测试、支付反欺诈、商户风险、争议证据与 CMS/STR 内部联动平台

## 简历四条（支付风控增强版）

- 基于数字资产交易平台实习中接触的 Rule Engine、FEP、Risk Graph、策略回溯、用户评分与 CMS/STR 产品结构，构建多角色 Risk Strategy AI Copilot；使用 LangGraph/ReAct 与 MCP 式只读工具编排场景、特征模型、图谱行为、支付责任和治理评审。
- 设计结构化 AI Strategy Proposal Schema 与特征白名单，将自然语言风险需求转为 Rule DSL；AI 负责需求拆解、检索、候选草拟、解释与冲突质检，确定性引擎负责 LR/Decision Tree/XGBoost、OOT、状态迁移、稳定性和策略组合评价。
- 在实习后完成支付/反欺诈知识体系 V1.3，并将 Customer-Merchant-Gateway/Orchestrator-PayFac/MOR-Acquirer-Network-Issuer 责任链、14 个支付风险场景、102 项支付特征和六套状态机落为 provider-neutral 合成数据模块。
- 实现 3DS 与 Authorization 分离、Token/凭证生命周期、Card Testing/CNP/ATO/APP、Merchant Underwriting/Reserve、Friendly Fraud/Subscription、Dispute Evidence Contract、Stablecoin 与 Agentic Commerce 治理；所有高影响动作和外部提交保留人工审批。

## 实习经历中可增加的准确表述

- 参与用户风险评分整改与风控产品需求拆解，梳理 Onboarding 初始评分、T+1 动态行为、L1-L4 分层、人工覆盖保护、RFI/EDD、差异化限额及审计留痕。
- 研读并结构化 Rule Engine、FEP、策略回溯、Risk Graph、Fraud 特征、Decision Tree/XGBoost、处罚验证中心、效果工单与 CMS/STR 资料，形成风险场景-字段-特征-规则-模型-图谱-处置-治理知识框架。
- 参与主站 AI 策略能力迁移调研，将自然语言需求、指标/事件检索、MCP/统一接口、策略 JSON、Simulation、审批与效果反馈拆分为分阶段方案。
- 参与 CMS/STR 字段与流程讨论，明确策略标签触发内部候选建案、历史关联、人工复核、保密权限与 MASAK XML/反馈状态边界。

## 90秒面试开场

> 我在 CoinTR 实习期间主要接触风控和合规产品，包括 Rule Engine、FEP、策略回溯、Risk Graph、用户风险评分、处罚验证中心和 CMS/STR，也参与了主站 AI 策略助手的迁移调研。实习结束后，我基于脱敏产品结构用合成数据独立重构了 Risk Strategy AI Copilot。
>
> 系统里，场景、特征模型、图谱行为、支付责任和治理 Agent 并行工作，再由 Lead Agent 汇总。Agent 只做需求理解、检索、候选和质检；数值、规则、OOT、稳定性、策略冲突和状态由确定性引擎控制。
>
> 后来我又把三套支付与反欺诈资料逐篇 OCR 和分类，形成 V1.3 知识体系，并把支付责任链、3DS 与授权分离、14 个场景、六套状态机、商户 Reserve 和 Dispute Evidence Contract 做成 provider-neutral 模块。这个支付模块是实习后个人扩展，不是 CoinTR 的生产系统；所有数据都是合成的，也没有自动处罚、资金执行或监管外发。

## 为什么需要 Agent，而不是只训练一个 XGBoost

- 风险需求包含业务阶段、责任、动作和监管语义，需要先结构化；
- 事件、特征、模型、图谱、历史策略、支付状态和证据来自不同对象；
- 单一 F1 无法判断策略重叠、处置冲突、商户敞口或拒付证据是否完整；
- LLM 适合规划、检索、解释和质检，确定性系统适合数值、状态、权限和不可逆动作。

## 必须主动说明的边界

- 项目是实习衍生个人原型，不是 CoinTR 生产系统；
- 支付模块来自实习后独立研究，不代表 CoinTR 经营银行卡收单或使用该架构；
- 未使用生产 PII 或真实交易明细；
- 模型和支付指标来自固定随机种子或规则化合成数据；
- 不自动处罚、移动资金、决定真实拒付或提交监管报告；
- 团队系统是学习背景，个人成果是知识重构、Agent 架构、代码、合成数据、回测和展示；
- KEP 自动化和 Anti-Fraud 运营指标是另外两个项目。
