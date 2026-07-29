# 公司式策略测试环境重构

## 1. 从实习材料恢复出的系统主干

```text
风险事件接入
  → FEP特征管理（创建/迭代/下线）
  → 长窗口计数器与实时特征
  → Rule Engine策略表达式
  → 一/二/三级策略标签
  → 未上线策略历史回溯
  → simulation状态独立效果评估
  → 标准化上线审批
  → 策略运营工单效果打标
  → 3个工作日初期观察
  → 周/月复盘、参数调整或下线
```

## 2. 测试记录必须保存

- test_run_id；
- strategy_id/version；
- event_code；
- 一/二/三级标签；
- data_snapshot_id；
- event_contract_hash；
- feature_catalog_version；
- payload_hash；
- Development和OOT指标；
- reviewer_1/reviewer_2；
- effectiveness_ticket_id；
- created_at/updated_at。

## 3. 测试阶段

| 阶段 | 核心检查 | 输出 |
|---|---|---|
| Feature Contract | 事件、特征、时点、数据质量 | 契约Hash与缺口 |
| Historical Backtest | 历史数据、黑白样本、容量和误伤 | Development/OOT结果 |
| Simulation | 不进入生产的1:1规则执行 | 命中明细与决策建议 |
| Second Review | 独立人员检查逻辑、阈值和处置 | 审核记录 |
| Release Readiness | 监控、回滚、负责人、告警 | 上线评审包 |
| Initial Observation | 连续3个工作日观察 | 逐日效果记录 |
| Periodic Review | 周/月复盘 | 效果标签与迭代建议 |

## 4. CMS/STR联动边界

- 规则或AML策略命中可以创建内部CMS/STR候选案件；
- 同一事件和证据应通过去重键防止重复建案；
- 合规审核员可查看用户风控历史；
- 最终是否形成STR由人工决定；
- MASAK反馈作为后续状态回写；
- 普通用户画像不直接显示STR机密状态。
