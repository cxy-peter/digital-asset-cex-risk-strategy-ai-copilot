from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import asyncio
from uuid import uuid4

from risk_copilot.orchestrator import RiskStrategyCopilot
from risk_copilot.schemas import StrategyRequest


async def main() -> None:
    root = PROJECT_ROOT
    copilot = RiskStrategyCopilot.create(root)
    request = StrategyRequest(
        request_id=f"DEMO-{uuid4().hex[:8]}",
        query="识别KYC后快速法币入金、换币并链上提币，叠加高风险银行和Risk Graph强关系的可疑用户",
        max_alert_rate=0.05,
        minimum_precision=0.50,
        minimum_recall=0.05,
        review_capacity=300,
    )
    state = await copilot.run_full_suite(request)
    package = state.context["strategy_package"]
    print(f"Selected: {package.selected_strategy.name}")
    print(f"Precision={package.selected_metrics.precision:.2%}, Recall={package.selected_metrics.recall:.2%}")
    print(f"Governance={package.governance.next_status.value}")
    print(f"Open: {copilot.runtime.settings.output_dir / 'index.html'}")


if __name__ == "__main__":
    asyncio.run(main())
