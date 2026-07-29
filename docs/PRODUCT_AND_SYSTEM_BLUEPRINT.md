# Risk Strategy Test Platform 产品与系统蓝图

## 1. 项目范围

本仓库只实现实习材料中与风险策略直接相关的产品链路：Rule Engine、FEP 特征管理、策略标签、策略回溯、模拟状态、独立复核、效果工单、用户风险画像、Risk Graph、处罚/验证建议以及 CMS/STR 内部候选案件联动。Anti-Fraud 运营指标为独立项目；其他实习任务不在此仓库实现。

## 2. 产品能力矩阵

| 产品域 | 输入 | 核心处理 | 输出 | 本原型状态 |
|---|---|---|---|---|
| Risk Event Contract | 事件码、字段、时效、允许动作 | 白名单、时点与字段契约校验 | 事件契约 Hash | implemented |
| FEP Feature Platform | 特征定义、来源、窗口、时效 | 注册、版本、空置率、分位、AUC/KS/IV/Lift/PSI | 特征目录与质量报告 | implemented |
| Rule Engine | 风险需求、规则表达式、标签 | DSL、阈值、动作、Payload | 模拟策略包 | implemented |
| Strategy Backtracking | 历史数据和标签 | Train/Dev/OOT、容量、误伤、稳定性 | 候选排行榜和冻结策略 | implemented |
| Strategy Test Environment | 规则、版本、数据快照 | 特征校验、回溯、模拟、第二复核、上线评审 | 测试计划与证据包 | implemented |
| Ticket Module | 策略版本和观察结果 | 有效性打标、建议、审计 | Effectiveness Ticket | implemented |
| User Risk Profile | KYC初始风险、T+1行为、人工覆盖 | L1-L4分层、历史和来源保护 | 用户风险画像 | implemented |
| Risk Graph | 用户—设备/证件/手机号/地址/IP关系 | 强弱关系、一跳/二跳、噪声过滤 | 图谱特征和解释路径 | implemented |
| Penalty / Verification Center | 风险等级和策略动作 | RFI、EDD、VideoKYC、限额、限制审批建议 | 处置建议，不自动执行 | modeled |
| CMS / STR Internal Linkage | 三级策略标签、命中证据和风险历史 | 去重、一键预填、人工复核、MASAK反馈状态 | 内部候选案件 | implemented |

## 3. 策略测试生命周期

```text
Feature Contract Validation
→ Historical Backtest
→ Simulation Execution
→ Independent Second Review
→ Release Readiness Review
→ Post-Launch 3-Working-Day Observation
→ Weekly / Monthly Effectiveness Review
```

个人原型只运行到模拟、评审包和效果工单；没有生产风控引擎连接，也不会自动执行处罚或监管提交。

## 4. 核心数据对象

- `EventSpec`：事件码、阶段、域、可用特征、允许动作和延迟要求；
- `FeatureSpec`：特征释义、来源、窗口、时效、PII等级和决策时点；
- `StrategyCandidate`：规则、阈值、动作、三级标签、所需特征和依据；
- `BacktestMetrics`：Dev/OOT效果、告警率、审核容量和稳定性；
- `StrategyTestPlan`：测试运行、快照、Hash、阶段、阻塞项和回滚阈值；
- `StrategyEffectivenessTicket`：精确版本效果标签和复盘建议；
- `CMSSTRCasePreview`：内部候选案件、去重键、证据 Hash、风险历史和反馈状态。

## 5. 安全与真实性边界

- 只使用合成数据和脱敏业务语义；
- 策略默认 `DRAFT/SIMULATION`；
- 所有高影响动作必须人工复核；
- STR状态不进入普通用户画像；
- 一键 STR 仅表示内部候选案件预填，不表示自动向监管外发；
- 所有 Demo 指标只能说明代码链路工作，不能作为公司生产效果。
