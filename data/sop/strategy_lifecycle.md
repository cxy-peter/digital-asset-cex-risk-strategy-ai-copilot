# 风控策略全生命周期SOP

DRAFT → SIMULATION → PENDING_REVIEW → APPROVED → ONLINE → PAUSED/RETIRED。

- 上线前进行历史回溯与模拟，记录样本窗口、标签口径、Precision、Recall、FPR、告警量和稳定性。
- 独立第二人复核；高影响处置需要额外审批。
- 上线后持续监控命中量、坏样本率、误伤、申诉与业务指标。
