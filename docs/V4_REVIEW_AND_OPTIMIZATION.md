# V4评估与V4.1优化结论

## 1. 原V4总体评价

原V4在工程和算法层面已经具备较高完成度：事件/特征注册、时间切分、XGBoost、决策树规则抽取、Risk Graph、策略DSL、版本审计和合成数据测试均是有效能力。问题不在“代码太简单”，而在**项目边界过宽、与实习平台的产品结构还不够像**。

### 原V4优点

- 有严格的point-in-time标签与Train/Development/OOT；
- 对XGBoost欠采样范围、阈值冻结和OOT只评估做了约束；
- 有Rule DSL、策略版本、Payload Hash、双人审批和SQLite审计；
- Risk Graph有强弱关系与训练快照边界；
- 能在无外部LLM时完成确定性主链路；
- 原始版本测试通过，说明不是只写文档。

### 原V4主要问题

1. 将智能交易监控、行为链、KYC、SAR/STR撰写、监管报告和合规问答全部作为主产品，像通用AML作品集；
2. 通用软件发布阶段与公司策略平台的实际治理语言不一致；
3. 没有显式复刻策略一/二/三级标签；
4. 没有把“策略运营工单100%打标”做成核心对象；
5. CMS一键STR、AML策略触发STR、STR历史查询和MASAK反馈没有被建模为统一闭环；
6. Anti-Fraud运营指标与策略Agent混在一起，降低了两个项目各自的清晰度。

## 2. V4.1为什么更符合实习衍生项目

V4.1不是引入更多外部模型，而是减少外来叙事，将实习材料中的产品结构直接转成代码对象：

- FEP → `FeatureSpec`、事件契约、特征版本和时点检查；
- Rule Engine → Rule DSL、策略Payload和三层标签；
- Strategy Backtracking → Train/Dev/OOT与simulation执行；
- Strategy Approval → 独立第二人复核、版本/Hash绑定；
- Ticket Module → `StrategyEffectivenessTicket`；
- User Risk Profile → Onboarding+T+1风险分层与人工覆盖保护；
- Penalty/Verification Center → RFI/EDD/VideoKYC/限额/限制建议；
- CMS/STR → 内部候选案件、一键建案、历史证据、MASAK反馈状态；
- Graph V2 → 一跳/二跳、多跳关系解释和噪声控制。

## 3. 仍可继续增强的地方

### P0：真实测试环境交互页

当前已有HTML报告，但还可以增加一个可操作页面，允许用户：

- 选择事件；
- 选择已注册特征；
- 编辑规则表达式；
- 运行历史回测；
- 比较Development/OOT；
- 填写第二复核人；
- 创建效果工单；
- 预览CMS/STR候选案件。

### P0：策略效果反馈数据模型

当前效果工单已实现，但后续可加入逐日观察记录：

```text
strategy_id/version/date/hit_count/confirmed_count/false_positive_count/
user_feedback/business_metric_delta/feature_psi/operator_comment
```

这样可真实演示“上线后至少3个工作日观察”和周/月复盘。

### P1：六类Fraud标签字典

材料只确认覆盖6类Fraud，但没有找到六类的最终枚举。当前项目不应自行伪造公司口径。拿到原表后，应新增：

- 标签Schema；
- 标注规则；
- 样本成熟期；
- 标签一致性；
- 漏标复核；
- 按Fraud类型的策略效果矩阵。

### P1：策略冲突与叠加分析

增加策略间：

- 重复命中率；
- 包含/被包含关系；
- 处置冲突；
- 白名单覆盖；
- 告警增量贡献；
- 下线影响分析。

### P1：模型到规则的稳定性验证

除单次决策树抽规则外，可增加bootstrap：对多个时间窗口训练浅树，保留重复出现的稳定路径，再转成专家规则候选。

## 4. 最终建议

该项目最适合投递：风控策略、风控产品、合规科技、Risk Data/Decisioning和AI应用产品岗位。它不应包装成基础模型训练项目；核心卖点是**把风控产品结构、数据、算法和治理做成一套可运行的策略测试环境**。
