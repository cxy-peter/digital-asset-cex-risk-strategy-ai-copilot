# CoinTR实习材料重构｜风险产品全景

> 产品状态是对实习材料和本原型覆盖程度的描述，不代表所有能力均由实习生独立建设或已在生产上线。

| Layer | Product | Purpose | Prototype | Dependencies | Evidence |
|---|---|---|---|---|---|
| data_access | **风控事件接入与场景配置中心** (`risk_event_hub`) | 将注册、登录、KYC、法币充提、链上充提、现货、内部转账、活动等业务事件标准化接入风控。 | implemented | - | W28_IMG_5710_5714_event_catalog, weekly_event_configuration_review |
| feature_platform | **实时特征指标平台** (`realtime_feature_platform`) | 管理实时、离线和衍生特征的创建、迭代、下线、释义、标签、应用场景与空置率。 | implemented | risk_event_hub | W25_core_risk_system_OKR, W28_feature_platform_OKR |
| feature_platform | **180天实时计数器与窗口服务** (`counter_service_180d`) | 为次数、金额、均值、最大值、去重数和时间间隔等策略特征提供统一窗口聚合。 | modeled | risk_event_hub, realtime_feature_platform | W25_main_site_180d_counter_migration, W28_counter_capability |
| data_foundation | **交易风控逻辑持仓表** (`transaction_position_table`) | 统一交易、持仓和资金变化口径，为交易类策略与回溯提供准确底表。 | catalog_only | risk_event_hub | W28_transaction_position_table_accuracy |
| decision_engine | **规则引擎与策略配置中心** (`rule_engine`) | 用可解释DSL配置条件树、阈值、动作、策略标签和版本。 | implemented | realtime_feature_platform, risk_event_hub | W25_rule_engine_approval, W27_test_environment_rule_engine, W28_AI_assisted_rule_configuration |
| decision_engine | **策略回溯与测试环境** (`strategy_simulation`) | 基于历史数据和模拟状态完成未上线策略独立回溯、Development选择、OOT验证和发布前效果检查。 | implemented | rule_engine, realtime_feature_platform, transaction_position_table | W25_strategy_backtracking_1to1_simulation, W28_simulation_state_independent_evaluation |
| governance | **策略上线审批、二人复核与效果工单** (`strategy_approval`) | 管理DRAFT、SIMULATION、PENDING_REVIEW、APPROVED、ONLINE、PAUSED、RETIRED状态以及双人复核。 | implemented | rule_engine, strategy_simulation, strategy_effectiveness_ticket | W25_standardized_strategy_approval, W28_strategy_lifecycle_governance |
| operations | **风控策略命中与定制告警中心** (`custom_alert_center`) | 承接规则引擎与离线策略命中结果，生成带策略版本、特征快照和证据哈希的调查告警。 | implemented | rule_engine, strategy_approval | W25_custom_alert, W28_ticket_effectiveness_feedback |
| disposition | **处罚与身份验证中心** (`penalty_verification_center`) | 对高风险用户执行延迟、限额、暂停出金、交易限制、冻结、VideoKYC等受控处置。 | implemented | custom_alert_center, strategy_approval, user_risk_profile | W26_KA_exempt_manual_penalty_approval, W28_penalty_center_expansion |
| decision_intelligence | **用户风险画像与L1-L4分层** (`user_risk_profile`) | 结合Onboarding KYC与T+1行为评分，维护自动/人工风险来源、历史和差异化处置。 | implemented | realtime_feature_platform, counter_service_180d, risk_graph | W27_user_profile_audit_remediation, systematic_automatic_customer_specific_scoring |
| decision_intelligence | **Risk Graph关联风险分析** (`risk_graph`) | 基于设备、邮箱、手机号、KYC证件、提现地址等关系，输出一跳/二跳风险及可审计关联路径。 | implemented | risk_event_hub | W28_RiskGraph_Fraud_analysis, W27_graph_PRD_assignment |
| external_intelligence | **链上地址标签与KYT风险中心** (`chainalysis_label_center`) | 接入高风险、制裁、混币器、赌博等链上标签并沉淀多级标签管理。 | modeled | risk_event_hub | W28_Chainalysis_tag_landing, AML_fund_monitoring |
| model_platform | **Fraud模型与特征实验室** (`fraud_model_lab`) | 支持黑白样本构造、特征区分度、LR/Tree/XGBoost、阈值选择、难例分析和模型监控。 | implemented | realtime_feature_platform, risk_graph, strategy_simulation | W28_Q4_fraud_feature_mining, decision_tree_xgboost_test |
| external_intelligence | **银行联防联控与通道风险** (`bank_joint_defense`) | 通过银行风险比例、卡一致性、联防反馈和高风险通道信息辅助判断资金来源与去向。 | modeled | risk_event_hub, fraud_model_lab | W28_bank_joint_defense, Q4_fraud_bank_features |
| monitoring | **账户安全H+1/T+1监控** (`account_security_monitor`) | 监控注册、登录、设备、IP和敏感信息变更的异常波动并快速触发告警。 | modeled | counter_service_180d, custom_alert_center | W28_account_security_monitoring |
| decision_engine | **资金安全与兜底策略中心** (`fund_security_control`) | 覆盖内部转账、共享订单、平台出金、异常资金转移和系统账户等资金安全场景。 | modeled | rule_engine, risk_graph, chainalysis_label_center | W28_fund_security_strategy_OKR |
| compliance_automation | **CMS合规案件管理** (`cms_case_management`) | 管理案件创建、审核、监管回复、补充材料、完成/取消等生命周期及审计日志。 | implemented | - | W25_W28_CMS_upgrade, anti_fraud_case_fields |
| compliance_automation | **STR一键内部候选案件与历史查询** (`str_workflow`) | 支持AML策略命中后一键创建内部CMS/STR候选案件、查询用户风控历史并记录MASAK反馈；所有提交均需合规人工复核。 | implemented | rule_engine, cms_case_management, strategy_approval, strategy_effectiveness_ticket | W28_IMG_5737_CMS_one_click_STR, W28_AML_strategy_auto_STR, W28_STR_MASAK_feedback |
| compliance_control | **Travel Rule信息与豁免审批** (`travel_rule`) | 管理订单金额、币种、对手方VASP信息、豁免名单和审批链路。 | catalog_only | risk_event_hub, list_management | W27_W28_Travel_Rule_optimization |
| identity | **KYC智能分流与EDD辅助** (`kyc_kyb_vkyc`) | 消费上游核验、字段一致性、PEP/制裁、资金来源及实际/预期活动偏离，路由人工RFI、EDD或VideoKYC。 | implemented | risk_event_hub | W27_KYC_fields, MASAK_occupation_list, W28_VKYC |
| external_intelligence | **黑白名单、PEP与制裁名单管理** (`list_management`) | 管理Fraud黑名单、白名单/豁免、PEP、制裁及高风险标签，并控制可见性与处置差异。 | catalog_only | - | W25_blacklist_followup, W27_sanctions_pep_filter |
| governance | **审计证据与系统拓扑资料中心** (`audit_evidence_hub`) | 管理审计控制项、交付材料、系统架构、数据口径、负责人、状态和证据追踪。 | modeled | strategy_approval, cms_case_management, str_workflow | W25_system_topology, W28_audit_delivery_matrix |
| knowledge | **风控知识、SOP与Risk Map中心** (`risk_knowledge_center`) | 沉淀行业、业务线、风险场景、黑灰产、特征、规则、模型、处置和监控指标。 | implemented | realtime_feature_platform, rule_engine | W27_Sylvia_anti_fraud_knowledge_assignment |
| monitoring | **风控大盘与冻结客户看板** (`risk_dashboard`) | 汇总冻结状态、解除情况、异常案件、客户处理结果、周报/月报和风险域趋势。 | modeled | user_risk_profile, custom_alert_center, strategy_effectiveness_ticket | W28_risk_dashboard_and_frozen_customers |
| external_intelligence | **Kline行情与市场异常数据服务** (`market_kline_feed`) | 为现货异常交易、价格偏离和市场操纵场景提供行情与K线特征。 | catalog_only | risk_event_hub | W28_kline_data_capture |
| governance | **策略运营效果打标工单** (`strategy_effectiveness_ticket`) | 由策略运营对上线或模拟策略效果进行版本化打标，为保留、调参、暂停或下线提供依据。 | implemented | strategy_simulation, strategy_approval, custom_alert_center | W28_Ticket_Module_100pct_effectiveness_tagging, strategy_full_lifecycle_SOP |