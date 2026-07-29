from __future__ import annotations

from pathlib import Path

from ..state import CopilotState
from .base import BaseAgent


class ProductCapabilityAgent(BaseAgent):
    name = "product_capability_agent"
    description = "Map the risk requirement to the full product stack reconstructed from weekly internship materials."

    async def run(self, state: CopilotState):
        mapped = await self.call_tool(
            "catalog.map_products",
            domain=state.request.domain.value,
            event_code=state.request.event_code,
            query=state.request.query,
        )
        output = Path(self.context.runtime.settings.output_dir) / "product_landscape"
        artifacts = await self.call_tool("catalog.write_products", output_dir=str(output))
        structured = {
            **mapped,
            "product_count": len(mapped["products"]),
            "artifacts": artifacts,
            "strategy_stack": [
                product["product_id"]
                for product in mapped["products"]
                if product["layer"] in {
                    "data_access",
                    "feature_platform",
                    "decision_intelligence",
                    "model_platform",
                    "decision_engine",
                    "governance",
                    "disposition",
                }
            ],
        }
        state.merge_context({"product_analysis": structured})
        result = self.result(
            f"将本次风险需求映射到{len(mapped['products'])}项产品能力，并生成产品依赖图与完整产品目录。",
            structured,
        )
        state.add_result(result)
        return result
