from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import asyncio

from risk_copilot.orchestrator import RiskStrategyCopilot
from risk_copilot.schemas import StrategyRequest

root = PROJECT_ROOT
request = StrategyRequest(
    request_id="STRATEGY-DEMO",
    query="识别KYC后快速法币入金并链上提币、且与历史Fraud存在强关系的用户",
)
state = asyncio.run(RiskStrategyCopilot.create(root).run_strategy(request))
print(state.context["strategy_artifacts"])
