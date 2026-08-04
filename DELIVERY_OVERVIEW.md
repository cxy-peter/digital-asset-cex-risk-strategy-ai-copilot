# Digital Asset & Payment Risk Strategy AI Copilot v0.9 - 交付概览

## 项目定位

项目由两层组成：

1. **CoinTR 实习衍生核心**：基于实习中接触的 Rule Engine、FEP、策略回溯、Risk Graph、用户风险评分、效果工单与 CMS/STR 产品结构，使用合成数据重构公司式策略测试和治理链路。
2. **支付风控扩展**：基于实习后单独完成的支付/反欺诈知识体系 V1.3，增加银行卡支付、商户风险、争议证据、稳定币与 Agentic Commerce 的 provider-neutral 原型；不代表 CoinTR 使用或部署这些支付能力。

核心边界：

```text
AI Agent：需求理解、检索、候选、解释、质检
确定性引擎：契约、计算、规则、状态、证据完整性、版本和审计
人工/业务系统：高影响动作、真实资金、争议裁定、监管外发
```

## v0.9 新增

| 模块 | 已实现能力 |
|---|---|
| Payment Flow & Liability Agent | 将自然语言支付需求映射到参与方、流程、14场景、控制和责任证据 |
| Payment Risk Engine | 合成交易上下文、场景评分、Reason Code、动作优先级和 Human-in-the-loop 决策 |
| Six State Machines | Payment Order、3DS、Auth/Capture/Settlement、Risk、Merchant、Dispute 分离 |
| Dispute Evidence Contract | 按争议原因检查认证、授权、订单、履约、同意、取消、沟通和退款证据 |
| Stablecoin Overlay | 发行人/储备、地址、制裁、合约、流动性/FX和对账风险 |
| Agentic Governance | 委托额度、Token Scope、Agent Identity、人工授权与不可逆执行边界 |
| API/CLI | `/payment/catalog`、`/payment/assess`、`/payment/dispute` 与 `payment-ready` |

## 运行方式

```bash
pip install -e '.[dev]'
risk-copilot generate-data --force
risk-copilot strategy
risk-copilot payment-ready
pytest -q
```

## 主要产物

- `outputs/index.html`
- `outputs/strategy_demo/*`
- `outputs/payment_ready_suite/payment_ready_suite.json`
- `outputs/payment_ready_suite/PAYMENT_READY_SUITE.md`
- `docs/PAYMENT_RISK_EXTENSION.md`
- `docs/KNOWLEDGE_V1_3_MAPPING.md`
- `docs/RESUME_AND_INTERVIEW.md`

## 真实性边界

- 全部 Demo 使用合成数据；
- 无生产风控、PSP、发卡行、收单行、卡组织或钱包连接；
- 不执行支付、冻结、Reserve、结算 Hold 或拒付裁定；
- 不自动向监管机构提交任何报告；
- 支付模块是实习后个人研究扩展；
- KEP 与 Anti-Fraud 运营指标仍是独立项目。
