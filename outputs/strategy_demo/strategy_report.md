# Digital Asset Risk Strategy Copilot｜策略评估报告

> 所有用户、图谱、案件与效果指标均为脱敏模拟或聚合演示数据；本报告不代表任何生产系统上线结果。

## 1. 风险需求

- Request ID：`SMOKE`
- Query：快速法币入金后链上提币并关联Fraud设备
- Risk Domain：`fund_security`
- Event：`ChainWithdraw`
- Constraints：Precision≥50%，Recall≥5%，Alert Rate≤5%

## 2. Multi-Agent分析

### intent_router

已将需求路由至fund_security/ChainWithdraw，置信度78%。

### scenario_knowledge_agent

检索到8个数字资产风险场景和5份相关SOP。

### product_capability_agent

将本次风险需求映射到16项产品能力，并生成产品依赖图与完整产品目录。

### risk_graph_agent

完成Risk Graph一跳/二跳特征构建；IP仅作为弱关系，入金归集地址默认不作强关联。

### fraud_behavior_agent

完成黑白样本行为对比，将资金闭环、速度、次数、银行、设备、链上和图谱信号转为可解释业务结论。

### feature_intelligence_agent

完成21个候选特征的AUC/KS/IV/Lift/PSI分析，其中19个达到演示推荐标准。

### model_benchmark_agent

完成Logistic、深度4决策树和XGBoost；开发集选择阈值后在OOT集最终评估。开发集首选logistic_regression，OOT ROC-AUC=0.962，KS=0.820；另生成70条高分负样本人工复核队列，不自动改标。

### user_risk_scoring_agent

完成Onboarding+T+1双层风险评分；输出10000条用户画像，最高风险层级为L3.2。

### ai_strategy_proposal_agent

AI策略规划层以deterministic_offline_fallback模式生成2条候选；候选只进入确定性回测，不具备上线或处罚权限。

### strategy_generation_agent

生成33条候选策略，覆盖AI规划、专家模板、分位阈值、Risk Graph、决策树路径和模型分层。

### backtest_ranking_agent

开发集完成33条候选排序并冻结Decision Tree候选规则 1；OOT最终Precision=86.42%，Recall=48.61%。

### strategy_stability_agent

跨月与Bootstrap稳定性结论=STABLE；通过6/6项门槛。

### strategy_conflict_agent

完成与4条兼容策略的冲突分析；建议=REVISE_ACTION_PRECEDENCE，增量召回=0.69%。

### ai_advisory_board_agent

AI专业顾问组完成场景、特征模型、图谱行为和治理复核；Lead Agent建议=REVISE。

### disposition_planning_agent

完成L1-L4分层处置矩阵和处罚/验证中心审批方案；所有动作仅为提议，不允许Agent直接处罚。

### governance_agent

治理结论：SIMULATION->PENDING_REVIEW，decision=approve；候选策略已写入SQLite版本库，但系统不允许Agent直接上线或执行处罚。

### strategy_test_environment_agent

策略测试环境已生成：test_run_id=TESTRUN-TREE-ChainWithdraw-01-019-02cf7b58，当前阶段=independent_second_review，release_status=PENDING_SECOND_REVIEW；不包含生产连接或自动发布。

### strategy_effectiveness_agent

已生成策略效果工单：EFF-TREE-ChainWithdraw-01-019-02cf7b58，simulation label=STRATEGY_CONFLICT；同时生成3个工作日的上线后观察模板，但未执行生产观察。

### cms_str_integration_agent

当前策略不触发CMS/STR候选案件：strategy tag level 3 is MANUAL_REVIEW, not a CMS/STR trigger。

### strategy_report_agent

已生成AI专业顾问组结论、稳定性与冲突分析、策略报告、公司式测试环境、效果工单、CMS/STR内部候选预览、规则Payload和Agent执行轨迹，目录：/mnt/data/cointr-risk-strategy-ai-copilot/outputs/strategy_demo。

## 3. 风控产品栈

| Product | Layer | Purpose | Prototype |
|---|---|---|---|
| Fraud模型与特征实验室 (`fraud_model_lab`) | model_platform | 支持黑白样本构造、特征区分度、LR/Tree/XGBoost、阈值选择、难例分析和模型监控。 | implemented |
| 黑白名单、PEP与制裁名单管理 (`list_management`) | external_intelligence | 管理Fraud黑名单、白名单/豁免、PEP、制裁及高风险标签，并控制可见性与处置差异。 | catalog_only |
| 风控策略命中与定制告警中心 (`custom_alert_center`) | operations | 承接规则引擎与离线策略命中结果，生成带策略版本、特征快照和证据哈希的调查告警。 | implemented |
| 处罚与身份验证中心 (`penalty_verification_center`) | disposition | 对高风险用户执行延迟、限额、暂停出金、交易限制、冻结、VideoKYC等受控处置。 | implemented |
| 实时特征指标平台 (`realtime_feature_platform`) | feature_platform | 管理实时、离线和衍生特征的创建、迭代、下线、释义、标签、应用场景与空置率。 | implemented |
| 风控事件接入与场景配置中心 (`risk_event_hub`) | data_access | 将注册、登录、KYC、法币充提、链上充提、现货、内部转账、活动等业务事件标准化接入风控。 | implemented |
| Risk Graph关联风险分析 (`risk_graph`) | decision_intelligence | 基于设备、邮箱、手机号、KYC证件、提现地址等关系，输出一跳/二跳风险及可审计关联路径。 | implemented |
| 风控知识、SOP与Risk Map中心 (`risk_knowledge_center`) | knowledge | 沉淀行业、业务线、风险场景、黑灰产、特征、规则、模型、处置和监控指标。 | implemented |
| 规则引擎与策略配置中心 (`rule_engine`) | decision_engine | 用可解释DSL配置条件树、阈值、动作、策略标签和版本。 | implemented |
| 策略上线审批、二人复核与效果工单 (`strategy_approval`) | governance | 管理DRAFT、SIMULATION、PENDING_REVIEW、APPROVED、ONLINE、PAUSED、RETIRED状态以及双人复核。 | implemented |
| 策略运营效果打标工单 (`strategy_effectiveness_ticket`) | governance | 由策略运营对上线或模拟策略效果进行版本化打标，为保留、调参、暂停或下线提供依据。 | implemented |
| 策略回溯与测试环境 (`strategy_simulation`) | decision_engine | 基于历史数据和模拟状态完成未上线策略独立回溯、Development选择、OOT验证和发布前效果检查。 | implemented |
| 用户风险画像与L1-L4分层 (`user_risk_profile`) | decision_intelligence | 结合Onboarding KYC与T+1行为评分，维护自动/人工风险来源、历史和差异化处置。 | implemented |
| 银行联防联控与通道风险 (`bank_joint_defense`) | external_intelligence | 通过银行风险比例、卡一致性、联防反馈和高风险通道信息辅助判断资金来源与去向。 | modeled |
| 交易风控逻辑持仓表 (`transaction_position_table`) | data_foundation | 统一交易、持仓和资金变化口径，为交易类策略与回溯提供准确底表。 | catalog_only |
| 180天实时计数器与窗口服务 (`counter_service_180d`) | feature_platform | 为次数、金额、均值、最大值、去重数和时间间隔等策略特征提供统一窗口聚合。 | modeled |

## 4. 用户风险评分与分层

- Scoring：Onboarding KYC + T+1 dynamic behavior；
- Tier Distribution：`{"L1": 3564, "L2": 6187, "L3.1": 236, "L3.2": 13, "L3.3": 0, "L4": 0}`；
- Manual Override Preserved：`True`；
- STR Visible in Ordinary Profile：`0` 条。

## 5. 处置与处罚中心治理

- detection_action：`MANUAL_REVIEW`
- execution_mode：`PROPOSE_ONLY`
- required_approvals：`['risk_strategy', 'risk_operations']`
- direct_execution_allowed：`False`

## 6. 策略版本与审计记录

- SQLite Registry：`/mnt/data/cointr-risk-strategy-ai-copilot/outputs/strategy_registry.sqlite`
- Version：`19`
- Registry Status：`PENDING_REVIEW`

## 7. 时间评估协议

- Split：60% Train / 20% Development / 20% OOT；
- Train：拟合模型并提供Graph已知标签快照；
- Development：特征推荐、阈值选择、候选排序和策略冻结；
- OOT：只报告冻结策略与模型的最终指标，不参与排序和选择；
- Frozen Strategy ID：`TREE-ChainWithdraw-01`。
- Selection Basis：`interpretable_feasible_preferred`。

## 8. Development特征区分度 Top 20

| Feature | AUC | KS | IV | Lift@10 | PSI | Recommended |
|---|---:|---:|---:|---:|---:|---|
| `behavior_event_count_30d` | 0.887 | 0.705 | 2.709 | 7.30 | 0.003 | True |
| `fraud_graph_score` | 0.874 | 0.622 | 2.225 | 6.26 | 0.007 | True |
| `strong_relation_fraud_1hop_count` | 0.858 | 0.627 | 1.804 | 6.09 | 0.000 | True |
| `strategy_avoidance_ratio_30d` | 0.858 | 0.649 | 2.236 | 6.96 | 0.006 | True |
| `community_fraud_ratio` | 0.842 | 0.630 | 1.593 | 5.57 | 0.002 | True |
| `fiat_in_crypto_out_ratio` | 0.835 | 0.610 | 1.992 | 6.61 | 0.004 | True |
| `bank_fraud_ratio_max` | 0.818 | 0.606 | 1.917 | 6.61 | 0.005 | True |
| `small_fiat_deposit_count_24h` | 0.815 | 0.561 | 1.955 | 6.17 | 0.000 | True |
| `fraud_2hop_count` | 0.815 | 0.505 | 1.497 | 4.87 | 0.009 | True |
| `direct_related_user_count` | 0.786 | 0.440 | 1.069 | 3.74 | 0.002 | True |
| `minutes_deposit_to_first_chain_out` | 0.774 | 0.460 | 1.101 | 0.26 | 0.006 | True |
| `chain_out_amount_24h` | 0.764 | 0.445 | 1.078 | 4.61 | 0.010 | True |
| `fund_stay_minutes_median` | 0.761 | 0.430 | 1.024 | 0.43 | 0.008 | True |
| `chain_out_5min_count_30d` | 0.742 | 0.473 | 0.000 | 5.39 | 0.000 | True |
| `chain_withdraw_count_24h` | 0.725 | 0.404 | 0.972 | 4.43 | 0.001 | True |
| `minutes_convert_to_chain_out` | 0.690 | 0.355 | 0.555 | 0.87 | 0.011 | True |
| `single_fiat_deposit_over_10000_cnt_30d` | 0.687 | 0.365 | 0.000 | 4.43 | 0.000 | True |
| `withdraw_address_fraud_1hop_count` | 0.666 | 0.328 | 0.000 | 3.74 | 0.000 | True |
| `behavior_success_ratio_30d` | 0.583 | 0.163 | 0.258 | 2.26 | 0.006 | True |
| `new_withdraw_address_flag` | 0.561 | 0.122 | 0.000 | 1.57 | 0.000 | False |

## 9. OOT模型基线（Threshold由Development选择）

| Model | ROC-AUC | KS | AP | Threshold | Precision | Recall | F1 | FPR | Lift@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logistic_regression | 0.962 | 0.820 | 0.793 | 0.900 | 0.680 | 0.708 | 0.694 | 0.026 | 8.12 |
| decision_tree_depth4 | 0.936 | 0.751 | 0.673 | 0.900 | 0.587 | 0.729 | 0.650 | 0.040 | 7.71 |
| xgboost | 0.959 | 0.814 | 0.801 | 0.900 | 0.860 | 0.597 | 0.705 | 0.008 | 8.06 |

## 10. Development排序与OOT最终评价

| Dev Rank | Strategy | Source | Dev Reward | Dev Advantage | Dev Precision | Dev Recall | OOT Alerts | OOT Alert Rate | OOT Precision | OOT Recall | OOT F1 |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | xgboost模型分层 | model_score | 0.7549 | 1.48 | 81.40% | 60.87% | 100 | 5.00% | 86.00% | 59.72% | 0.705 |
| 2 | logistic_regression模型分层 | model_score | 0.7484 | 1.46 | 70.34% | 72.17% | 150 | 7.50% | 68.00% | 70.83% | 0.694 |
| 3 | Decision Tree候选规则 1 | tree | 0.7321 | 1.39 | 87.32% | 53.91% | 81 | 4.05% | 86.42% | 48.61% | 0.622 |
| 4 | decision_tree_depth4模型分层 | model_score | 0.7174 | 1.34 | 62.76% | 79.13% | 179 | 8.95% | 58.66% | 72.92% | 0.650 |
| 5 | 二跳关联叠加快进快出 | graph | 0.6372 | 1.03 | 63.04% | 50.43% | 101 | 5.05% | 65.35% | 45.83% | 0.539 |
| 6 | AI建议：快进快出与高风险银行组合 | ai_planner | 0.6198 | 0.96 | 56.64% | 55.65% | 115 | 5.75% | 62.61% | 50.00% | 0.556 |
| 7 | 快进快出高精度组合 | expert | 0.5895 | 0.84 | 91.43% | 27.83% | 31 | 1.55% | 100.00% | 21.53% | 0.354 |
| 8 | 快进快出召回型规则 | expert | 0.5863 | 0.83 | 52.10% | 53.91% | 115 | 5.75% | 60.00% | 47.92% | 0.533 |
| 9 | AI建议：Risk Graph强关系叠加资金闭环 | ai_planner | 0.5540 | 0.71 | 44.87% | 60.87% | 178 | 8.90% | 47.19% | 58.33% | 0.522 |
| 10 | behavior_event_count_30d分位阈值规则 | quantile | 0.5196 | 0.57 | 40.76% | 74.78% | 238 | 11.90% | 41.18% | 68.06% | 0.513 |
| 11 | strategy_avoidance_ratio_30d分位阈值规则 | quantile | 0.5006 | 0.50 | 40.00% | 69.57% | 199 | 9.95% | 46.23% | 63.89% | 0.536 |
| 12 | bank_fraud_ratio_max分位阈值规则 | quantile | 0.4822 | 0.43 | 38.00% | 66.09% | 203 | 10.15% | 42.86% | 60.42% | 0.501 |
| 13 | fiat_in_crypto_out_ratio分位阈值规则 | quantile | 0.4776 | 0.41 | 38.00% | 66.09% | 227 | 11.35% | 37.89% | 59.72% | 0.464 |
| 14 | fraud_graph_score分位阈值规则 | quantile | 0.4612 | 0.35 | 35.12% | 62.61% | 236 | 11.80% | 39.83% | 65.28% | 0.495 |
| 15 | 图社区风险叠加资金归集 | graph | 0.4451 | 0.29 | 100.00% | 0.87% | 4 | 0.20% | 50.00% | 1.39% | 0.027 |
| 16 | community_fraud_ratio分位阈值规则 | quantile | 0.4056 | 0.13 | 30.81% | 56.52% | 254 | 12.70% | 31.10% | 54.86% | 0.397 |
| 17 | Decision Tree候选规则 3 | tree | 0.3746 | 0.01 | 52.94% | 7.83% | 28 | 1.40% | 39.29% | 7.64% | 0.128 |
| 18 | Decision Tree候选规则 4 | tree | 0.3705 | -0.00 | 60.00% | 7.83% | 21 | 1.05% | 57.14% | 8.33% | 0.145 |
| 19 | Decision Tree候选规则 2 | tree | 0.3613 | -0.04 | 62.50% | 4.35% | 19 | 0.95% | 36.84% | 4.86% | 0.086 |
| 20 | Decision Tree候选规则 8 | tree | 0.2808 | -0.35 | 28.57% | 3.48% | 15 | 0.75% | 13.33% | 1.39% | 0.025 |
| 21 | Decision Tree候选规则 5 | tree | 0.2625 | -0.42 | 17.65% | 5.22% | 30 | 1.50% | 16.67% | 3.47% | 0.057 |
| 22 | small_fiat_deposit_count_24h分位阈值规则 | quantile | 0.2418 | -0.50 | 23.01% | 67.83% | 335 | 16.75% | 25.37% | 59.03% | 0.355 |
| 23 | Decision Tree候选规则 7 | tree | 0.2292 | -0.55 | 12.50% | 1.74% | 26 | 1.30% | 26.92% | 4.86% | 0.082 |
| 24 | 强关系一跳Fraud | graph | 0.2246 | -0.57 | 23.48% | 70.43% | 398 | 19.90% | 26.63% | 73.61% | 0.391 |
| 25 | Decision Tree候选规则 6 | tree | 0.2007 | -0.66 | 0.00% | 0.00% | 4 | 0.20% | 0.00% | 0.00% | 0.000 |
| 26 | behavior_event_count_30d分位阈值规则 | quantile | 0.1912 | -0.70 | 23.36% | 83.48% | 476 | 23.80% | 24.79% | 81.94% | 0.381 |
| 27 | strategy_avoidance_ratio_30d分位阈值规则 | quantile | 0.1704 | -0.78 | 22.50% | 78.26% | 427 | 21.35% | 24.36% | 72.22% | 0.364 |
| 28 | fraud_graph_score分位阈值规则 | quantile | 0.1652 | -0.80 | 21.57% | 76.52% | 446 | 22.30% | 26.23% | 81.25% | 0.397 |
| 29 | community_fraud_ratio分位阈值规则 | quantile | 0.1476 | -0.86 | 20.69% | 73.04% | 484 | 24.20% | 22.73% | 76.39% | 0.350 |
| 30 | bank_fraud_ratio_max分位阈值规则 | quantile | 0.1382 | -0.90 | 20.00% | 69.57% | 408 | 20.40% | 24.02% | 68.06% | 0.355 |
| 31 | fiat_in_crypto_out_ratio分位阈值规则 | quantile | 0.1353 | -0.91 | 20.25% | 70.43% | 429 | 21.45% | 21.68% | 64.58% | 0.325 |
| 32 | strong_relation_fraud_1hop_count分位阈值规则 | quantile | 0.0921 | -1.08 | 20.17% | 82.61% | 540 | 27.00% | 22.59% | 84.72% | 0.357 |
| 33 | small_fiat_deposit_count_24h分位阈值规则 | quantile | -0.5629 | -3.61 | 10.41% | 82.61% | 889 | 44.45% | 11.81% | 72.92% | 0.203 |

## 11. 推荐策略

**Decision Tree候选规则 1** (`TREE-ChainWithdraw-01`)

- Source：tree
- Event：ChainWithdraw
- Action：MANUAL_REVIEW
- Strategy Tags：`fund_security / rapid_fiat_convert_chain_out / MANUAL_REVIEW`
- Rule：`behavior_event_count_30d > 30.5 AND strong_relation_fraud_1hop_count > 0.5 AND strategy_avoidance_ratio_30d > 0.302633 AND behavior_event_count_30d > 42.5`
- Selection：Development排序后冻结；
- OOT Precision：86.42%
- OOT Recall：48.61%
- OOT Alert Rate：4.05%
- OOT Captured Loss Rate：52.15%

## 12. AI Strategy Advisory Board

- Proposal Mode：`deterministic_offline_fallback`
- Lead Agent Decision：`REVISE`
- AI Boundary：候选生成、解释和质检；确定性引擎负责回测、冲突、状态迁移和审批。
- Human in the Loop：`True`

四个专业Agent已完成场景、特征模型、图谱行为和治理复核。当前建议：REVISE。AI层只提出/解释/质检候选，实际指标、回测、冲突分析和状态迁移由确定性引擎控制。

### Specialist Agents

#### scenario_typology_agent

风险场景与黑灰产链路已和候选规则建立业务映射。

- [LOW] scenario_alignment: 候选策略Decision Tree候选规则 1针对ChainWithdraw，并使用behavior_event_count_30d, strategy_avoidance_ratio_30d, strong_relation_fraud_1hop_count构成可解释风险链路。

Risks:
- 单一行为信号不能直接替代案件调查。

#### feature_model_agent

特征、模型和跨月份稳定性已由确定性测试层验证。

- [LOW] oot_metrics: 冻结策略OOT Precision=86.42%, Recall=48.61%, FPR=0.59%; stability=STABLE.

Risks:
- 合成数据上的稳定性不能替代生产三工作日观察。
- 特征PSI、方向变化和模型阈值需持续监控。

#### graph_behavior_agent

Risk Graph强弱关系与交易行为证据已分层处理。

- [LOW] graph_policy: Device/Email/Mobile/KYC/Withdraw Address作为强关系；IP降权，平台归集型充值地址默认排除。

Risks:
- 多跳扩散会增加噪声，必须和资金行为联合验证。

#### governance_cms_str_agent

策略冲突、人工复核、测试环境和CMS/STR边界已检查。

- [MEDIUM] portfolio_conflict: 组合冲突建议=REVISE_ACTION_PRECEDENCE；增量风险召回=0.69%.

Risks:
- AI候选不得绕过第二人复核、效果工单或STR保密约束。

## 13. 跨月份与Bootstrap稳定性

- Status：`STABLE`
- Months：`3`
- Monthly Precision CV：`0.0132`
- Monthly Alert Rate CV：`0.2062`
- Feature Direction Consistency：`100.00%`
- Gates：`6/6`

| Month | Sample | Alerts | Alert Rate | Precision | Recall | F1 | FPR |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-04 | 714 | 18 | 2.52% | 88.89% | 38.10% | 0.533 | 0.30% |
| 2026-05 | 1748 | 72 | 4.12% | 86.11% | 59.62% | 0.705 | 0.61% |
| 2026-06 | 1538 | 62 | 4.03% | 87.10% | 47.79% | 0.617 | 0.56% |

### Bootstrap 95%区间

| Metric | Mean | Std | 2.5% | 97.5% |
|---|---:|---:|---:|---:|
| precision | 0.8693 | 0.0260 | 0.8201 | 0.9177 |
| recall | 0.5121 | 0.0306 | 0.4539 | 0.5770 |
| f1 | 0.6440 | 0.0273 | 0.5925 | 0.6994 |
| false_positive_rate | 0.0053 | 0.0011 | 0.0032 | 0.0075 |
| alert_rate | 0.0382 | 0.0029 | 0.0332 | 0.0440 |

## 14. 策略冲突与增量贡献

- Recommendation：`REVISE_ACTION_PRECEDENCE`
- Compatible Existing Strategies：`4`
- High-overlap Strategies：`1`
- Action Conflicts：`2`
- Incremental Alerts：`4`
- Incremental Risk Recall：`0.69%`
- Duplicate Workload Rate：`95.06%`

| Existing Strategy | Action | Jaccard | Selected Containment | Incremental/Conflict | Severity |
|---|---|---:|---:|---|---|
| 高风险银行快速链上提币 | MANUAL_REVIEW | 35.65% | 50.62% | action_conflict=False | low |
| 强关系Fraud用户链上提现 | RFI | 32.19% | 92.59% | action_conflict=True | high |
| 新设备与代理IP提现保护 | DELAY | 1.08% | 1.23% | action_conflict=True | medium |
| 高风险链上暴露 | WITHDRAWAL_RESTRICTION | 0.00% | 0.00% | action_conflict=False | low |

## 15. 治理结论

- Decision：`approve`
- Lifecycle：`SIMULATION` → `PENDING_REVIEW`
- Required Approvals：risk_strategy, risk_operations

- simulation gate passed: sample_size=2000
- simulation gate passed: precision=0.8642
- simulation gate passed: recall=0.4861
- simulation gate passed: false_positive_rate=0.0059
- simulation gate passed: alert_rate=0.0405
- eligible to enter independent human review; not approved for production

## 16. 公司式策略测试环境与上线有效性闭环

- Test Run ID：`TESTRUN-TREE-ChainWithdraw-01-019-02cf7b58`
- Data Snapshot：`SNAP-1f3606e3f9f1627b`
- Current Stage：`independent_second_review`
- Release Status：`PENDING_SECOND_REVIEW`
- Required Approvals：`['risk_strategy', 'risk_operations', 'independent_second_reviewer', 'strategy_action_precedence_reviewer', 'ai_advisory_findings_owner']`
- Initial Observation：`3` working days
- Production Connection：`False`
- Dispatch Performed：`False`
- Blockers：`[]`

| Stage | Status | Entry Gates | Exit Gates | Evidence |
|---|---|---|---|---|
| `feature_contract_validation` | `completed` | registered event code; registered decision-time features | event contract has zero blocking errors; feature lineage is recorded | 049911eb70a9b37aceb3d0de08988360913c79dc85cfa27ecb1bf40db45ac666 |
| `historical_backtest` | `completed` | frozen Train/Development/OOT split; mature point-in-time labels | OOT metrics generated; alert volume and review capacity checked | SNAP-1f3606e3f9f1627b; strategy_stability_analysis |
| `simulation_execution` | `completed` | historical backtest completed; engine payload confirmed | simulation metrics satisfy governance thresholds; no production mutation | TESTRUN-TREE-ChainWithdraw-01-019-02cf7b58 |
| `independent_second_review` | `ready` | risk-strategy reviewer independent from creator; exact version and payload hash bound | reviewer 1 approved; reviewer 2 approved; high-impact action compliance review if needed; strategy action precedence conflict resolved | 02cf7b58cabdad3f54905590a5fd0d826b329b5ec4b94e7fc40e1b82fbe37228; strategy_conflict_analysis; ai_advisory_board |
| `release_readiness` | `pending` | two-person review completed; rollback and monitoring plan confirmed | release owner confirms execution window; strategy ticket created |  |
| `post_launch_observation` | `not_started` | release completed outside this prototype; first three working days observation enabled | false positives, user feedback, business metrics and feature PSI reviewed |  |
| `weekly_monthly_effectiveness_review` | `pending` | effectiveness ticket linked to strategy version | retain, tune, pause or retire decision recorded |  |

### 上线后连续3个工作日观察模板

> 这些记录为待生产团队填写的空白模板，不能用离线回测指标冒充生产有效性。

| Workday | Date | Status | Hit | Confirmed | False Positive | PSI | User Feedback |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | 2026-07-29 | `PLANNED_NOT_EXECUTED` | None | None | None | None | None |
| 2 | 2026-07-30 | `PLANNED_NOT_EXECUTED` | None | None | None | None | None |
| 3 | 2026-07-31 | `PLANNED_NOT_EXECUTED` | None | None | None | None | None |

### Strategy Ticket Module：上线效果打标

- Ticket ID：`EFF-TREE-ChainWithdraw-01-019-02cf7b58`
- Evaluation Phase：`SIMULATION`
- Effectiveness Label：`STRATEGY_CONFLICT`
- Recommendation：候选与现有策略存在高重叠或处置动作优先级冲突；先完成策略合并、增量贡献和动作优先级复核。
- Synthetic Demo：`True`

### CMS/STR内部候选案件

- Enabled：`False`
- Case Count：`0`
- MASAK Feedback Status：`NOT_SUBMITTED`
- External Submission Allowed：`False`
- Automatic Filing Performed：`False`

## 17. 风控引擎Payload

```json
{
  "strategyId": "TREE-ChainWithdraw-01",
  "strategyName": "Decision Tree候选规则 1",
  "domain": "fund_security",
  "eventCode": "ChainWithdraw",
  "strategyTags": {
    "level1": "fund_security",
    "level2": "rapid_fiat_convert_chain_out",
    "level3": "MANUAL_REVIEW",
    "flat": [
      "tree_extracted",
      "interpretable"
    ]
  },
  "eventContract": {
    "version": "ChainWithdraw@sha256:049911eb70a9",
    "sha256": "049911eb70a9b37aceb3d0de08988360913c79dc85cfa27ecb1bf40db45ac666",
    "warningCount": 16,
    "errorCount": 0
  },
  "version": 1,
  "status": "PENDING_REVIEW",
  "executionMode": "SIMULATION_ONLY",
  "conditionTree": {
    "logic": "AND",
    "conditions": [
      {
        "feature": "behavior_event_count_30d",
        "operator": ">",
        "value": 30.5
      },
      {
        "feature": "strong_relation_fraud_1hop_count",
        "operator": ">",
        "value": 0.5
      },
      {
        "feature": "strategy_avoidance_ratio_30d",
        "operator": ">",
        "value": 0.302633
      },
      {
        "feature": "behavior_event_count_30d",
        "operator": ">",
        "value": 42.5
      }
    ],
    "groups": []
  },
  "expression": "behavior_event_count_30d > 30.5 AND strong_relation_fraud_1hop_count > 0.5 AND strategy_avoidance_ratio_30d > 0.302633 AND behavior_event_count_30d > 42.5",
  "action": {
    "type": "MANUAL_REVIEW",
    "parameters": {},
    "requiresHumanApproval": true
  },
  "guardrails": {
    "directOnlineRelease": false,
    "requiredApprovals": [
      "risk_strategy",
      "risk_operations"
    ],
    "strDetailsVisibleInOrdinaryProfile": false,
    "manualRiskOverridePreserved": true,
    "kaVipExemptExtraApproval": true,
    "cmsOneClickCreatesInternalCaseOnly": true,
    "automaticRegulatorySubmission": false,
    "strategyEffectivenessTicketRequired": true
  },
  "simulationSnapshot": {
    "selectionPartition": "development",
    "evaluationPartition": "out_of_time",
    "sampleSize": 2000,
    "alerts": 81,
    "precision": 0.8641975308641975,
    "recall": 0.4861111111111111,
    "f1": 0.6222222222222222,
    "falsePositiveRate": 0.005926724137931034,
    "alertRate": 0.0405,
    "lift": 12.002743484224967,
    "capturedLossRate": 0.5214790341032601,
    "stabilityScore": 0.985162036862479,
    "reward": 0.708605735461994,
    "relativeAdvantage": 1.4008069279243056
  },
  "audit": {
    "request_id": "SMOKE",
    "strategy_id": "TREE-ChainWithdraw-01",
    "event_code": "ChainWithdraw",
    "event_contract_version": "ChainWithdraw@sha256:049911eb70a9",
    "event_contract_hash": "049911eb70a9b37aceb3d0de08988360913c79dc85cfa27ecb1bf40db45ac666",
    "event_contract_warning_count": 16,
    "event_contract_error_count": 0,
    "domain": "fund_security",
    "action": "MANUAL_REVIEW",
    "strategy_tags": {
      "level_1": "fund_security",
      "level_2": "rapid_fiat_convert_chain_out",
      "level_3": "MANUAL_REVIEW",
      "flat": [
        "tree_extracted",
        "interpretable"
      ]
    },
    "rule_expression": "behavior_event_count_30d > 30.5 AND strong_relation_fraud_1hop_count > 0.5 AND strategy_avoidance_ratio_30d > 0.302633 AND behavior_event_count_30d > 42.5",
    "required_features": [
      "behavior_event_count_30d",
      "strategy_avoidance_ratio_30d",
      "strong_relation_fraud_1hop_count"
    ],
    "risk_source": "ai_assisted_candidate",
    "manual_override_policy": {
      "risk_source_field": "risk_source",
      "manual_value_not_silently_overwritten": true,
      "history_required": true
    },
    "str_confidentiality": {
      "str_details_roles": [
        "compliance"
      ],
      "ordinary_profile_can_show_str": false,
      "audit_log_required": true
    },
    "reviewed_at": "2026-07-29T14:27:18.570710+00:00",
    "data_scope": "synthetic_or_aggregated_demo"
  },
  "disclaimer": "Synthetic/desensitized prototype; payload is not connected to any production system.",
  "dispositionProposal": {
    "strategy_id": "TREE-ChainWithdraw-01",
    "detection_action": "MANUAL_REVIEW",
    "execution_mode": "PROPOSE_ONLY",
    "required_approvals": [
      "risk_strategy",
      "risk_operations"
    ],
    "customer_segment_gate": {
      "segments": [
        "KA",
        "VIP",
        "EXEMPT"
      ],
      "extra_approval": true,
      "reason": "avoid material customer mis-penalty and preserve auditability"
    },
    "release_controls": {
      "batch_release_supported": true,
      "release_requires_reason": true,
      "operator_and_approver_separation": true
    },
    "notification_required": true,
    "direct_execution_allowed": false
  }
}
```

## 18. 边界声明

- 本项目为实习衍生、脱敏重构的个人原型；
- Agent只生成候选策略并进入模拟/人工审核，不自动执行生产处罚；
- STR明细不进入普通用户画像；
- 手工风险调整必须保留risk_source和历史，不得被T+1任务静默覆盖；
- KEP监管邮件自动化不属于本项目，已从Risk Strategy代码和叙事中排除；
- Anti-Fraud人工审核指标体系为独立项目，只通过strategy_id/version与效果工单做可选关联。