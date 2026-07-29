from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .orchestrator import RiskStrategyCopilot
from .schemas import ActionType, RiskDomain, StrategyRequest

PROJECT_ROOT = Path(os.getenv("RISK_COPILOT_PROJECT_ROOT", Path(__file__).resolve().parents[2]))
copilot = RiskStrategyCopilot.create(PROJECT_ROOT)
app = FastAPI(title="Digital Asset Risk Strategy AI Copilot", version="0.7.0")




CONSOLE_HTML = r"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Risk Strategy AI Copilot Console</title>
<style>body{font-family:system-ui;margin:0;background:#f3f6fa;color:#172033}header{background:#17324d;color:white;padding:24px}main{max-width:1180px;margin:auto;padding:22px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.card{background:white;border:1px solid #d8e1eb;border-radius:12px;padding:18px;box-shadow:0 2px 8px #0001}label{display:block;font-weight:650;margin:10px 0 4px}input,select,textarea{box-sizing:border-box;width:100%;padding:9px;border:1px solid #b9c7d6;border-radius:8px}textarea{min-height:96px}button{margin-top:14px;background:#0f766e;color:white;border:0;border-radius:9px;padding:11px 18px;font-weight:700;cursor:pointer}pre{background:#0f172a;color:#dbeafe;padding:14px;border-radius:9px;overflow:auto;max-height:480px;white-space:pre-wrap}.tag{display:inline-block;background:#dff4ef;color:#115e59;padding:4px 8px;border-radius:999px;margin:2px;font-size:12px}.wide{grid-column:1/-1}@media(max-width:850px){.grid{grid-template-columns:1fr}}</style></head>
<body><header><h1>Digital Asset Risk Strategy AI Copilot</h1><p>自然语言风险需求 → 专业Agent并行分析 → 候选策略 → 回测/稳定性/冲突 → 人工复核包</p></header>
<main><div class="grid">
<section class="card"><h2>策略需求</h2><label>自然语言需求</label><textarea id="query">识别KYC后快速法币入金、换币并链上提币，叠加高风险银行和Risk Graph强关系的可疑用户</textarea><label>风险域</label><select id="domain"><option value="">自动识别</option><option value="fund_security">fund_security</option><option value="account_security">account_security</option><option value="fraud">fraud</option></select><label>事件</label><input id="event" placeholder="ChainWithdraw"><label>最大告警率</label><input id="max_alert" type="number" step="0.01" value="0.05"><label>最低Precision</label><input id="min_precision" type="number" step="0.01" value="0.50"><label>最低Recall</label><input id="min_recall" type="number" step="0.01" value="0.05"><button onclick="runStrategy()">运行AI策略评审</button><p id="status"></p></section>
<section class="card"><h2>AI专业顾问组</h2><div id="decision" class="tag">尚未运行</div><div id="agents"></div><h3>Lead Agent结论</h3><pre id="lead">等待运行</pre></section>
<section class="card"><h2>候选与回测</h2><pre id="strategy">等待运行</pre></section><section class="card"><h2>P0治理结果</h2><pre id="governance">等待运行</pre></section>
<section class="card wide"><h2>完整响应</h2><pre id="raw">等待运行</pre></section></div></main>
<script>async function runStrategy(){const status=document.getElementById('status');status.textContent='运行中：生成候选、训练模型、执行OOT回测、稳定性和冲突分析…';const body={query:document.getElementById('query').value,max_alert_rate:+document.getElementById('max_alert').value,minimum_precision:+document.getElementById('min_precision').value,minimum_recall:+document.getElementById('min_recall').value,review_capacity:300,preferred_actions:['MANUAL_REVIEW','RFI']};const d=document.getElementById('domain').value,e=document.getElementById('event').value;if(d)body.domain=d;if(e)body.event_code=e;try{const r=await fetch('/strategy/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const x=await r.json();if(!r.ok)throw new Error(JSON.stringify(x));const p=x.package,b=p.ai_advisory_board||{};document.getElementById('decision').textContent=b.decision||'NOT_RUN';document.getElementById('lead').textContent=b.executive_summary||'';document.getElementById('agents').innerHTML=Object.keys(b.specialist_reviews||{}).map(k=>'<span class="tag">'+k+'</span>').join('');document.getElementById('strategy').textContent=JSON.stringify({selected:p.selected_strategy,metrics:p.selected_metrics,stability:p.stability_analysis,conflict:p.conflict_analysis},null,2);document.getElementById('governance').textContent=JSON.stringify({governance:p.governance,test_environment:x.test_environment,effectiveness_ticket:x.effectiveness_ticket,cms_str:x.cms_str_internal_preview},null,2);document.getElementById('raw').textContent=JSON.stringify(x,null,2);status.textContent='完成。AI只提出/质检候选，状态迁移与回测由确定性引擎控制。'}catch(e){status.textContent='失败：'+e;}}
</script></body></html>"""


@app.get("/console", response_class=HTMLResponse)
async def console_page() -> str:
    return CONSOLE_HTML


class StrategyRunRequest(BaseModel):
    query: str
    domain: RiskDomain | None = None
    event_code: str | None = None
    max_alert_rate: float = Field(default=0.05, gt=0, le=1)
    minimum_precision: float = Field(default=0.50, ge=0, le=1)
    minimum_recall: float = Field(default=0.05, ge=0, le=1)
    review_capacity: int = Field(default=300, gt=0)
    preferred_actions: list[ActionType] = Field(default_factory=lambda: [ActionType.MANUAL_REVIEW, ActionType.RFI])


def _request(body: StrategyRunRequest) -> StrategyRequest:
    return StrategyRequest(request_id=f"API-{uuid4().hex[:10]}", **body.model_dump())


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "version": app.version,
        "scope": "risk_strategy_test_platform",
        "kep_included": False,
        "anti_fraud_metrics_included": False,
        "production_connection": False,
        "product_count": len(copilot.runtime.product_catalog.products),
        "feature_count": len(copilot.runtime.feature_registry.features),
        "event_count": len(copilot.runtime.feature_registry.events),
    }


@app.get("/catalog/events")
async def events(domain: str | None = None):
    tools = copilot._agent_context().tools
    return (await tools.execute("api", "catalog.list_events", domain=domain)).value


@app.get("/catalog/features")
async def features(text: str = "", domain: str | None = None, event_code: str | None = None):
    tools = copilot._agent_context().tools
    return (await tools.execute("api", "catalog.search_features", text=text, domain=domain, event_code=event_code, tags=None)).value


@app.get("/catalog/products")
async def products(layer: str | None = None, prototype_status: str | None = None):
    items = copilot.runtime.product_catalog.products
    if layer:
        items = [item for item in items if item.layer == layer]
    if prototype_status:
        items = [item for item in items if item.prototype_status == prototype_status]
    return [item.model_dump(mode="json") for item in items]


@app.post("/strategy/run")
async def run_strategy(body: StrategyRunRequest):
    try:
        state = await copilot.run_strategy(_request(body))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}") from exc
    package = state.context["strategy_package"]
    return {
        "package": package.model_dump(mode="json"),
        "ai_strategy_proposal": state.context.get("ai_strategy_proposal", {}),
        "ai_advisory_board": state.context.get("ai_advisory_board", {}),
        "stability_analysis": state.context.get("stability_analysis", {}),
        "conflict_analysis": state.context.get("conflict_analysis", {}),
        "test_environment": state.context.get("strategy_test_environment", {}),
        "effectiveness_ticket": state.context.get("strategy_effectiveness_ticket", {}),
        "cms_str_internal_preview": state.context.get("cms_str_integration", {}),
        "artifacts": {key: str(value) for key, value in state.context["strategy_artifacts"].items()},
        "boundary": {
            "synthetic_or_desensitized_only": True,
            "production_connection": False,
            "automatic_enforcement": False,
            "automatic_regulatory_submission": False,
            "kep_included": False,
        },
    }
