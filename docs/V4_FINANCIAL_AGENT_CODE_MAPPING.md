# 与参考Financial-Agent代码的工程映射

参考项目的有效结构是：共享State、专业Agent并行、MCP工具发现、ReAct调用和Summary汇聚。本项目保留这些模式，但将领域对象换为风险策略测试对象。

| 参考实现 | 本项目 |
|---|---|
| `StateGraph`并行四个股票Agent | `orchestrator.py` / `langgraph_app.py`并行风险专业Agent |
| `create_react_agent`绑定全部金融工具 | 本地Typed Tool Registry + 可选FastMCP，按职责限制工具 |
| Agent输出自由文本 | Pydantic结构化Feature/Strategy/TestPlan/Ticket/CMSCase |
| Summary生成Markdown | Report Agent生成Markdown/HTML/JSON/CSV |
| 股票API数据Schema | 事件契约、特征注册、数据快照和标签时点 |
| 投资结论 | 模拟策略、审核建议、效果标签和内部案件候选 |

风控系统比投顾报告多出的关键能力：point-in-time、防泄漏、审核容量、误伤、处置审批、版本/Hash、效果工单和监管机密边界。
