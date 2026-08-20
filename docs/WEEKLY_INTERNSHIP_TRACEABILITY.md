# 四周实习到项目的追溯

## 第一周：系统和流程认知

- 学习 CMS/STR、MASAK XML、风控后台、审计和产品验收；
- 映射为：CMS/STR 内部候选、人工复核、端到端测试边界。

## 第二周：产品流程和安全治理

- 学习 BRD/PRD、处罚审批、RBAC、数据字段缺口；
- 映射为：审批门禁、最小权限、版本审计和配置 Schema。

## 第三周：数据、模型和风险场景

- 接触数仓字段、用户风险评分、策略回溯、Risk Graph、专家规则和 XGBoost；
- 映射为：特征目录、模型基线、图谱特征、策略 DSL 和回测。

## 第四周：产品体系和策略生命周期

- 研读 FEP、规则引擎、三层标签、工单效果打标、STR 历史、AI 辅助配置和完整策略 SOP；
- 映射为：公司式测试环境、效果工单、CMS/STR 联动和多 Agent 原型。

## V0.10：全量 OCR/TXT 的新增映射

- `IMG_5716` 的宏观目标—监管/业务要求—业务链路—系统数据—功能/模型—最终问题，映射为七层 `ProblemLayer`；
- 7 月 1 日 KYC/VKYC 讨论中的字段时点、Known/Unknown/Contradiction/Owner/Evidence，映射为 Point-in-Time 合同与会前问题树；
- 风控产品需求池、BRD、PRD、技术方案、开发、测试、联合验收、上线与复盘，映射为 11 阶段 `DeliveryStage`；
- 7 月 10 日 Fraud 特征、LR/Tree/XGBoost、Risk Graph、策略重叠与运营反馈，映射为 13 阶段模型分析 Playbook；
- 特征全生命周期、1:1 Simulation、效果量化和策略下线逻辑，映射为 `DRAFT → DATA_READY → OFFLINE_BACKTEST → SHADOW → PENDING_REVIEW → APPROVED → ONLINE → DEGRADED → PAUSED → RETIRED`；
- 生产标签不可完整观察的问题，映射为调查选择、标签成熟延迟与 `INCONCLUSIVE` 的合成观察层。

所有新增代码仍属于实习后个人合成数据重构，不代表公司生产部署或真实指标。
