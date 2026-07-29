from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import load_yaml
from ..schemas import RiskProductSpec


@dataclass
class ProductCatalog:
    path: str | Path

    def __post_init__(self) -> None:
        raw = load_yaml(self.path)
        self.products = [RiskProductSpec.model_validate(item) for item in raw.get("products", [])]
        self.by_id = {item.product_id: item for item in self.products}
        missing = {
            dependency
            for product in self.products
            for dependency in product.dependencies
            if dependency not in self.by_id
        }
        if missing:
            raise ValueError(f"unknown product dependencies: {sorted(missing)}")

    @staticmethod
    def _tokens(text: str) -> set[str]:
        import re

        return {token.lower() for token in re.findall(r"[A-Za-z0-9_+.-]+|[\u4e00-\u9fff]{2,}", text or "")}

    def relevant(self, domain: str | None, event_code: str | None, query: str = "", limit: int = 14) -> list[RiskProductSpec]:
        query_tokens = self._tokens(query)
        scored: list[tuple[float, RiskProductSpec]] = []
        for product in self.products:
            score = 0.0
            if domain and domain in product.domains:
                score += 5.0
            if event_code and event_code in product.event_codes:
                score += 7.0
            haystack = " ".join(
                [product.name, product.purpose, *product.capabilities, *product.data_objects, *product.source_evidence]
            )
            product_tokens = self._tokens(haystack)
            score += min(5.0, 0.8 * len(query_tokens.intersection(product_tokens)))
            if product.prototype_status == "implemented":
                score += 0.3
            if score > 0:
                scored.append((score, product))
        scored.sort(key=lambda item: (-item[0], item[1].product_id))
        seeds = [product for _, product in scored[:limit]]
        return self.dependency_closure(seeds)

    def dependency_closure(self, seeds: list[RiskProductSpec]) -> list[RiskProductSpec]:
        queue = deque(product.product_id for product in seeds)
        visited: set[str] = set()
        ordered: list[str] = []
        while queue:
            product_id = queue.popleft()
            if product_id in visited:
                continue
            visited.add(product_id)
            ordered.append(product_id)
            queue.extend(self.by_id[product_id].dependencies)
        return [self.by_id[product_id] for product_id in ordered]

    def map_stack(self, domain: str | None, event_code: str | None, query: str) -> dict[str, Any]:
        relevant = self.relevant(domain=domain, event_code=event_code, query=query)
        ids = {item.product_id for item in relevant}
        dependencies = [
            {"from": dependency, "to": item.product_id}
            for item in relevant
            for dependency in item.dependencies
            if dependency in ids
        ]
        layers: dict[str, list[str]] = {}
        for item in relevant:
            layers.setdefault(item.layer, []).append(item.product_id)
        return {
            "domain": domain,
            "event_code": event_code,
            "products": [item.model_dump(mode="json") for item in relevant],
            "dependencies": dependencies,
            "layers": layers,
            "implemented_in_prototype": [item.product_id for item in relevant if item.prototype_status == "implemented"],
            "modeled_or_catalog_only": [item.product_id for item in relevant if item.prototype_status != "implemented"],
        }

    def write(self, output_dir: str | Path) -> dict[str, Path]:
        target = Path(output_dir)
        target.mkdir(parents=True, exist_ok=True)
        rows = [item.model_dump(mode="json") for item in self.products]
        csv_path = target / "risk_product_catalog.csv"
        pd.DataFrame(rows).to_csv(csv_path, index=False)

        md_path = target / "risk_product_landscape.md"
        lines = [
            "# CoinTR实习材料重构｜风险产品全景",
            "",
            "> 产品状态是对实习材料和本原型覆盖程度的描述，不代表所有能力均由实习生独立建设或已在生产上线。",
            "",
            "| Layer | Product | Purpose | Prototype | Dependencies | Evidence |",
            "|---|---|---|---|---|---|",
        ]
        for item in self.products:
            lines.append(
                f"| {item.layer} | **{item.name}** (`{item.product_id}`) | {item.purpose} | "
                f"{item.prototype_status} | {', '.join(item.dependencies) or '-'} | {', '.join(item.source_evidence)} |"
            )
        md_path.write_text("\n".join(lines), encoding="utf-8")

        mermaid_path = target / "risk_product_architecture.mmd"
        graph = ["flowchart LR"]
        for item in self.products:
            label = item.name.replace('"', "'")
            graph.append(f'  {item.product_id}["{label}"]')
        for item in self.products:
            for dependency in item.dependencies:
                graph.append(f"  {dependency} --> {item.product_id}")
        mermaid_path.write_text("\n".join(graph), encoding="utf-8")
        return {"product_csv": csv_path, "product_markdown": md_path, "product_mermaid": mermaid_path}
