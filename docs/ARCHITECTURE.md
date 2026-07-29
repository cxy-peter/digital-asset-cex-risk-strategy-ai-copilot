# 系统架构

```mermaid
flowchart TD
    Q[Risk Requirement] --> R[Intent Router]
    R --> G[Risk Graph Agent]
    R --> S[Scenario/SOP Agent]
    R --> P[Product Capability Agent]
    G --> F[Feature Intelligence]
    S --> F
    P --> F
    F --> B[Fraud Behavior Agent]
    F --> M[Model Benchmark Agent]
    F --> U[User Risk Scoring Agent]
    B --> C[Strategy Candidate Generator]
    M --> C
    U --> C
    C --> BT[Development Ranking + OOT Backtest]
    BT --> D[Disposition Planning]
    D --> GOV[Version/Hash Governance]
    GOV --> TEST[Company Test Environment]
    TEST --> TICKET[Effectiveness Ticket]
    TICKET --> CMS[CMS/STR Internal Candidate]
    CMS --> REPORT[Structured Report]
```

## 数据层

- `events.yaml`：事件注册；
- `features.yaml`：FEP式特征目录；
- `labeling.yaml`：黑白样本、成熟时间和禁止标签；
- 合成用户、关系和事件明细。

## 决策层

- 专家规则；
- 分位阈值；
- 深度4决策树路径；
- XGBoost风险分；
- Risk Graph强关系条件；
- 多条件规则DSL。

## 治理层

- 策略版本；
- 三层标签；
- 数据快照；
- 事件契约Hash；
- Payload Hash；
- 双人复核；
- 效果工单；
- CMS/STR内部候选；
- 审计日志。
