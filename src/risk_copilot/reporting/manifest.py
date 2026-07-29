from __future__ import annotations

import ast
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _python_loc(root: Path) -> tuple[int, int]:
    files = [p for p in (root / "src").rglob("*.py") if "__pycache__" not in p.parts]
    return len(files), sum(len(p.read_text(encoding="utf-8").splitlines()) for p in files)


def _test_inventory(root: Path) -> tuple[int, int]:
    files = list((root / "tests").glob("test_*.py"))
    count = 0
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        count += sum(
            1 for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
        )
    return len(files), count


def build_project_manifest(runtime, state=None) -> dict[str, Any]:
    root = runtime.settings.project_root
    python_files, python_loc = _python_loc(root)
    test_files, test_cases = _test_inventory(root)
    tools = runtime.artifacts.get("tool_registry")
    tool_manifest = tools.discover() if tools is not None else []
    contract = runtime.feature_registry.validate_contract_consistency()
    product_layers = Counter(p.layer for p in runtime.product_catalog.products)
    output_files = sorted(
        str(p.relative_to(runtime.settings.output_dir)).replace("\\", "/")
        for p in runtime.settings.output_dir.rglob("*") if p.is_file()
    )
    return {
        "project": "Digital Asset Risk Strategy AI Copilot",
        "version": "4.1",
        "boundary": (
            "Internship-derived personal prototype using synthetic/desensitized structures. "
            "No production connection, automatic penalty, automatic regulatory filing, KEP workflow, "
            "or Anti-Fraud operations dashboard is included."
        ),
        "company_style_scope": [
            "Rule Engine and three-level strategy tags",
            "FEP-style feature/event contracts and 180-day counters",
            "historical backtest and simulation-state independent evaluation",
            "independent second-person review and version/hash-bound approval",
            "three-working-day initial observation",
            "Ticket Module strategy-effectiveness labeling",
            "CMS one-click internal STR candidate case and MASAK feedback status",
            "Risk Graph, onboarding plus T+1 user risk scoring, penalty/verification recommendations",
        ],
        "architecture": {
            "orchestration": "native asyncio plus optional LangGraph fan-out/fan-in",
            "tools": "local typed registry plus optional FastMCP facades",
            "state": "CopilotState plus Pydantic domain schemas",
            "models": ["LogisticRegression", "Depth4DecisionTree", "XGBoost"],
            "strategy_registry": "SQLite atomic version and audit registry",
            "human_in_the_loop": True,
        },
        "inventory": {
            "executed_agents": len(state.agent_results) if state is not None else None,
            "python_files": python_files,
            "python_loc": python_loc,
            "local_tools": len(tool_manifest),
            "features": len(runtime.feature_registry.features),
            "events": len(runtime.feature_registry.events),
            "products": len(runtime.product_catalog.products),
            "product_layers": dict(sorted(product_layers.items())),
            "test_files": test_files,
            "test_cases": test_cases,
            "contract_errors": contract.error_count,
            "contract_warnings": contract.warning_count,
            "output_artifacts": len(output_files),
        },
        "tool_manifest": tool_manifest,
        "contract_validation": contract.model_dump(mode="json"),
        "agent_run_trace": [x.model_dump(mode="json") for x in state.run_trace] if state is not None else [],
        "output_files": output_files,
    }


def write_project_manifest(runtime, state=None) -> dict[str, Path]:
    manifest = build_project_manifest(runtime, state)
    out = runtime.settings.output_dir
    json_path = out / "project_manifest.json"
    md_path = out / "project_statistics.md"
    contract_path = out / "event_contract_validation.json"
    json_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    contract_path.write_text(json.dumps(manifest["contract_validation"], ensure_ascii=False, indent=2), encoding="utf-8")
    inv = manifest["inventory"]
    rows = "\n".join(f"| {k} | {v} |" for k, v in inv.items())
    md_path.write_text(
        f"""# Project Statistics

> {manifest['boundary']}

## Inventory

| Dimension | Value |
|---|---:|
{rows}

## Company-style lifecycle

"""
        + "\n".join(f"- {x}" for x in manifest["company_style_scope"]),
        encoding="utf-8",
    )
    return {"project_manifest": json_path, "project_statistics": md_path, "event_contract_validation": contract_path}
