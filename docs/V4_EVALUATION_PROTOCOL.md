# 评价协议

## 数据切分

- Train：模型拟合和XGBoost欠采样；
- Development：阈值、候选策略和排序；
- OOT：冻结版本最终评价。

## 模型指标

ROC-AUC、KS、Average Precision、Precision、Recall、F1、FPR、Alert Rate。

## 策略指标

- 命中量与告警率；
- Precision/Recall/F1；
- 风险金额捕获；
- 审核容量；
- 用户反馈与申诉；
- 业务指标波动；
- 特征PSI；
- 与已有策略的重复和冲突。

## 测试门禁

1. 事件已注册；
2. 特征已注册且决策时点可用；
3. 数据快照和契约Hash已保存；
4. 历史回测完成；
5. simulation执行完成；
6. 独立第二人复核；
7. 监控和回滚指标明确；
8. 效果工单已创建；
9. CMS/STR只允许内部候选状态；
10. 生产连接必须关闭。
