# 实习材料与V4.1代码映射

| 实习材料/工作 | 在V4.1中的实现 | 归属边界 |
|---|---|---|
| 实时特征生命周期、FEP、180天计数器 | Feature Registry、event contracts、freshness、长窗口特征 | 团队产品为学习背景；代码为个人重构 |
| 标准化策略上线审批与三层标签 | Strategy taxonomy、Governance、SQLite registry | 个人原型 |
| 未上线策略回溯、simulation独立评估 | Train/Dev/OOT、Backtest、CompanyTestPlan | 个人原型 |
| 策略上线后工单打标 | StrategyEffectivenessTicket | 个人原型 |
| Risk Graph V2、多跳与关键字段检索 | weighted graph features/path explanation | 团队方法学习+个人重构 |
| Q4 Fraud特征、决策树、XGBoost | Feature profiling、Tree DSL、XGBoost benchmark | 个人基于合成数据复现 |
| 用户Onboarding+T+1评分与人工调整 | Scoring service、risk_source和history | 需求理解+个人原型 |
| 处罚/验证中心、RFI/EDD/VideoKYC | Disposition plan和审批门禁 | 个人原型，不执行生产动作 |
| CMS一键STR、AML触发、STR历史、MASAK反馈 | Internal candidate preview和feedback status | 个人原型，不外部提交 |
| 主站AI辅助指标/规则配置 | Intent/Feature/Strategy Agent + tool layer | 迁移思路重构 |

KEP和Anti-Fraud运营指标不属于本仓库。
