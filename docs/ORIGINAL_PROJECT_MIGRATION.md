# 从股票投资顾问Agent到Risk Strategy Test Platform

| 股票Agent结构 | 风控策略平台映射 |
|---|---|
| 基本面/技术面/估值/新闻并行Agent | 图谱/场景/特征/模型/用户评分并行Agent |
| Baostock MCP工具 | 事件、特征、图谱、回测和治理工具 |
| 总结Agent | 策略候选、回测、治理和报告Agent |
| 投资报告 | 策略测试包、效果工单和CMS/STR候选 |
| 数据一致性 | 事件契约、特征版本、数据快照和Hash |
| 并行执行与缓存 | asyncio/LangGraph fan-out/fan-in |

关键区别：本项目不是把股票字段替换成风控字段，而是新增了策略回测环境、标签成熟、人工审批、处置边界和上线效果治理，这些是风险策略系统的核心。
