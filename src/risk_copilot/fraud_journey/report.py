from __future__ import annotations

from pathlib import Path

import pandas as pd

from .analysis import audit_summary, feature_coverage_frame
from .catalog import COHORT_DEFINITIONS, MODEL_GRID, SOURCE_ANALYSIS_STEPS


def render_focused_report(users: pd.DataFrame | None = None) -> str:
    coverage = feature_coverage_frame(users.columns if users is not None else [])
    summary = audit_summary(coverage)
    lines: list[str] = [
        "# CoinTR Fraud Journey — Source-Aligned Analysis Plan",
        "",
        "> Focused reconstruction of the 7/10 Q4 Fraud report and expanded TXT notes. This is not a generic AI-agent architecture document.",
        "",
        "## 1. Core workflow",
        "",
    ]
    for step in SOURCE_ANALYSIS_STEPS:
        lines.extend(
            [
                f"### {step.order}. {step.stage}",
                f"- Question: {step.question}",
                f"- Source method: {step.source_method}",
                f"- Output: {step.output}",
                f"- Gate: {step.gate}",
                "",
            ]
        )
    lines.extend(["## 2. Cohort contract", ""])
    for item in COHORT_DEFINITIONS:
        lines.extend(
            [
                f"### {item['cohort']}",
                f"- Definition: {item['definition']}",
                f"- Warning: {item['warning']}",
                "",
            ]
        )
    lines.extend(
        [
            "## 3. Model experiment policy",
            "",
            f"- Negative:positive candidates: {list(MODEL_GRID['negative_to_positive_ratio'])}",
            f"- Depth candidates: {list(MODEL_GRID['max_depth'])}",
            f"- Probability thresholds: {list(MODEL_GRID['probability_threshold'])}",
            "- 1:4 is a candidate, not a fixed default.",
            "- Selection belongs to Development; final OOT keeps the natural class distribution.",
            "",
            "## 4. Current public-demo feature coverage",
            "",
            f"- Exact: {summary['EXACT']}",
            f"- Derivable: {summary['DERIVABLE']}",
            f"- Approximate: {summary['APPROXIMATE']}",
            f"- Missing: {summary['MISSING']}",
            f"- Lineage risk: {summary['LINEAGE_RISK']}",
            "",
            coverage[["source_feature", "github_feature", "status", "note"]].to_markdown(index=False),
            "",
            "## 5. Truthfulness boundary",
            "",
            "- Curated white users are not equivalent to all synthetic label=0 rows.",
            "- Source thresholds and model results are historical analysis artefacts, not universal production targets.",
            "- Exchange-versus-private withdrawal preference was a hypothesis in the source report, not a confirmed aggregate result.",
            "- The public project uses synthetic data and does not claim CoinTR production deployment or real business performance.",
        ]
    )
    return "\n".join(lines)


def write_focused_report(path: str | Path, users: pd.DataFrame | None = None) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_focused_report(users), encoding="utf-8")
    return target
