from __future__ import annotations

"""Optional LLM/ReAct review layer.

The deterministic risk engine remains the source of truth for feature validation, model fitting,
backtesting, lifecycle transitions, and disposition controls.  This module adds a financial-advisor-
style ReAct layer that lets several specialist reviewers inspect the validated package with tools and
then produces a consolidated Markdown design review.

The separation is deliberate: a language model may explain, critique, and propose revisions, but it
cannot directly change a strategy status or execute a restriction.
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

from .orchestrator import RiskStrategyCopilot
from .rules.dsl import rule_to_expression
from .schemas import ReviewerBundle, StrategyPackage, StrategyRequest


def _load_llm():
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Install optional dependencies with: pip install -e '.[agent]'") from exc

    api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_COMPATIBLE_BASE_URL")
    model = os.getenv("OPENAI_COMPATIBLE_MODEL", "gpt-4o-mini")
    if not api_key:
        raise RuntimeError("Set OPENAI_COMPATIBLE_API_KEY (or OPENAI_API_KEY) before running ReAct review.")
    kwargs: dict[str, Any] = {
        "model": model,
        "api_key": api_key,
        "temperature": 0.1,
        "max_tokens": 5000,
    }
    if base_url:
        kwargs["base_url"] = base_url
    return ChatOpenAI(**kwargs)


def _last_ai_text(response: dict[str, Any]) -> str:
    messages = response.get("messages", [])
    for message in reversed(messages):
        content = getattr(message, "content", None)
        if content:
            return str(content)
    return "No review generated."


def _package_context(package: StrategyPackage) -> dict[str, Any]:
    return {
        "request": package.request.model_dump(mode="json"),
        "selected_strategy": {
            **package.selected_strategy.model_dump(mode="json"),
            "expression": rule_to_expression(package.selected_strategy.rule),
        },
        "selected_metrics": package.selected_metrics.model_dump(mode="json"),
        "alternatives": [
            {
                "strategy": strategy.model_dump(mode="json"),
                "expression": rule_to_expression(strategy.rule),
                "metrics": metrics.model_dump(mode="json"),
            }
            for strategy, metrics in package.alternatives[:6]
        ],
        "model_benchmarks": [item.model_dump(mode="json") for item in package.model_benchmarks],
        "top_features": [item.model_dump(mode="json") for item in package.feature_profiles[:20]],
        "product_context": package.product_context,
        "risk_scoring": package.risk_scoring,
        "disposition_plan": package.disposition_plan,
        "governance": package.governance.model_dump(mode="json"),
        "registry_record": package.registry_record,
        "evaluation_context": package.evaluation_context,
        "stability_analysis": package.stability_analysis,
        "conflict_analysis": package.conflict_analysis,
        "ai_advisory_board": package.ai_advisory_board,
        "strategy_test_environment": package.strategy_test_environment,
        "effectiveness_ticket": package.effectiveness_ticket,
        "cms_str_integration": package.cms_str_integration,
        "boundary": package.data_disclaimer,
    }


def build_react_tools(copilot: RiskStrategyCopilot, package: StrategyPackage):
    """Create JSON-safe tools for ReAct reviewers.

    These are high-level read-only facades over the same registries used by the deterministic agents.
    """

    try:
        from langchain_core.tools import tool
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install optional dependencies with: pip install -e '.[agent]'") from exc

    runtime = copilot.runtime
    package_context = _package_context(package)

    @tool("get_validated_strategy_package")
    def get_validated_strategy_package() -> str:
        """Return the validated strategy, alternatives, metrics, models, governance and boundary."""
        return json.dumps(package_context, ensure_ascii=False, default=str)

    @tool("search_feature_catalog")
    def search_feature_catalog(text: str = "", domain: str = "", event_code: str = "") -> str:
        """Search feature definitions by keyword, risk domain, or event code."""
        items = runtime.feature_registry.search(
            text=text,
            domain=domain or None,
            event_code=event_code or None,
        )
        return json.dumps([item.model_dump(mode="json") for item in items[:40]], ensure_ascii=False)

    @tool("search_sop_and_typology")
    def search_sop_and_typology(query: str, top_k: int = 8, industry: str = "digital_asset") -> str:
        """Search risk scenarios, black/grey-industry typologies, strategy SOPs, and compliance rules."""
        scenario_hits = runtime.knowledge_retriever.search_scenarios(
            query,
            top_k=top_k,
            industry=industry or None,
        )
        sop_hits = runtime.knowledge_retriever.search_sops(query, top_k=top_k)
        hits = [*scenario_hits, *sop_hits]
        return json.dumps(
            [
                {
                    "doc_id": hit.doc_id,
                    "document_type": hit.metadata.get("type"),
                    "score": hit.score,
                    "title": hit.title,
                    "text": hit.text,
                    "metadata": hit.metadata,
                }
                for hit in hits
            ],
            ensure_ascii=False,
        )

    @tool("map_product_stack")
    def map_product_stack(query: str, domain: str = "", event_code: str = "") -> str:
        """Map a requirement to product capabilities and dependency closure."""
        result = runtime.product_catalog.map_stack(
            domain=domain or package.request.domain.value,
            event_code=event_code or package.request.event_code,
            query=query,
        )
        return json.dumps(result, ensure_ascii=False)

    @tool("list_event_contract")
    def list_event_contract(event_code: str) -> str:
        """Return the versioned event contract, typed feature schemas, hash, and validation issues."""
        contract = runtime.feature_registry.build_event_contract(event_code)
        return contract.model_dump_json()

    @tool("explain_graph_user")
    def explain_graph_user(user_id: str) -> str:
        """Explain one-hop and two-hop graph paths for a synthetic demo user."""
        runtime.prepare_graph_enriched_users()
        return json.dumps(runtime.artifacts["graph_analyzer"].explain_user(user_id), ensure_ascii=False)


    @tool("get_stability_analysis")
    def get_stability_analysis() -> str:
        """Return cross-month, bootstrap, feature-direction, and gate-level stability evidence."""
        return json.dumps(package.stability_analysis, ensure_ascii=False, default=str)

    @tool("get_strategy_conflict_analysis")
    def get_strategy_conflict_analysis() -> str:
        """Return overlap, containment, action-conflict, and incremental-value analysis versus the synthetic strategy portfolio."""
        return json.dumps(package.conflict_analysis, ensure_ascii=False, default=str)

    @tool("get_company_test_environment")
    def get_company_test_environment() -> str:
        """Return the feature-validation, backtest, simulation, independent-review and post-launch observation plan."""
        return json.dumps(package.strategy_test_environment, ensure_ascii=False, default=str)

    @tool("get_cms_str_internal_preview")
    def get_cms_str_internal_preview() -> str:
        """Return internal CMS/STR candidate-case preview and hard safeguards against automatic external submission."""
        return json.dumps(package.cms_str_integration, ensure_ascii=False, default=str)

    @tool("get_strategy_version_history")
    def get_strategy_version_history() -> str:
        """Return version, approval and audit history of the selected strategy."""
        from .governance.repository import StrategyRegistryRepository

        history = StrategyRegistryRepository(
            runtime.settings.output_dir / "strategy_registry.sqlite"
        ).history(package.selected_strategy.strategy_id)
        return json.dumps(history, ensure_ascii=False, default=str)

    return [
        get_validated_strategy_package,
        search_feature_catalog,
        search_sop_and_typology,
        map_product_stack,
        list_event_contract,
        explain_graph_user,
        get_stability_analysis,
        get_strategy_conflict_analysis,
        get_company_test_environment,
        get_cms_str_internal_preview,
        get_strategy_version_history,
    ]


def _extract_json_object(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        candidate = "\n".join(lines).strip()
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("reviewer response does not contain a JSON object")
    value = json.loads(candidate[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("reviewer JSON root must be an object")
    return value


def _parse_reviewer_bundle(
    reviewer: str,
    text: str,
    *,
    attempts: int,
    latency_ms: float,
) -> ReviewerBundle:
    try:
        payload = _extract_json_object(text)
        payload.update(
            {
                "reviewer": reviewer,
                "status": "succeeded",
                "attempts": attempts,
                "latency_ms": latency_ms,
            }
        )
        return ReviewerBundle.model_validate(payload)
    except Exception as exc:
        return ReviewerBundle(
            reviewer=reviewer,
            status="degraded",
            summary="Reviewer returned unstructured output; raw text retained for human review.",
            risks=[f"structured_output_validation_failed: {type(exc).__name__}"],
            acceptance_tests=[
                "Re-run reviewer and require a schema-valid JSON response before relying on its findings."
            ],
            attempts=attempts,
            latency_ms=latency_ms,
            error=f"{type(exc).__name__}: {exc}",
            raw_text=text,
        )


async def _run_specialist(
    name: str,
    system_instruction: str,
    llm,
    tools,
    context: dict[str, Any],
    *,
    timeout_seconds: float = 180.0,
    max_attempts: int = 2,
) -> tuple[str, ReviewerBundle]:
    try:
        from langchain_core.messages import HumanMessage
        from langgraph.prebuilt import create_react_agent
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install optional dependencies with: pip install -e '.[agent]'") from exc

    agent = create_react_agent(llm, tools, prompt=system_instruction)
    compact = json.dumps(
        {
            "query": context["request"]["query"],
            "domain": context["request"]["domain"],
            "event_code": context["request"]["event_code"],
            "selected_strategy_id": context["selected_strategy"]["strategy_id"],
            "selected_expression": context["selected_strategy"]["expression"],
            "selected_metrics": context["selected_metrics"],
        },
        ensure_ascii=False,
    )
    request = f"""Review the validated risk-strategy package for the following task.

Context summary:
{compact}

Use tools whenever a factual detail is needed. Do not claim production deployment or real company
performance. Do not reveal chain-of-thought. Return JSON only, using exactly this schema:
{{
  "summary": "concise reviewer decision",
  "findings": [
    {{
      "category": "short category",
      "severity": "low|medium|high|critical",
      "statement": "factual finding",
      "evidence_refs": ["tool/document/strategy evidence id"]
    }}
  ],
  "risks": ["risk or gap"],
  "revisions": ["concrete revision"],
  "acceptance_tests": ["observable pass/fail acceptance test"],
  "evidence_refs": ["all evidence ids used"]
}}
"""
    started = time.perf_counter()
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            async with asyncio.timeout(timeout_seconds):
                response = await agent.ainvoke(
                    {"messages": [HumanMessage(content=request)]}
                )
            text = _last_ai_text(response)
            bundle = _parse_reviewer_bundle(
                name,
                text,
                attempts=attempt,
                latency_ms=(time.perf_counter() - started) * 1000,
            )
            if bundle.status == "succeeded" or attempt == max_attempts:
                return name, bundle
            request += (
                "\nYour prior response failed schema validation. Return one valid JSON object "
                "and no Markdown fences or prose outside it."
            )
        except TimeoutError as exc:
            last_error = exc
            if attempt == max_attempts:
                return name, ReviewerBundle(
                    reviewer=name,
                    status="timed_out",
                    summary="Reviewer timed out; deterministic pipeline results remain available.",
                    risks=["reviewer_timeout"],
                    attempts=attempt,
                    latency_ms=(time.perf_counter() - started) * 1000,
                    error=f"TimeoutError: exceeded {timeout_seconds:.1f}s",
                )
        except Exception as exc:
            last_error = exc
            if attempt == max_attempts:
                return name, ReviewerBundle(
                    reviewer=name,
                    status="failed",
                    summary="Reviewer failed; deterministic pipeline results remain available.",
                    risks=["reviewer_execution_failed"],
                    attempts=attempt,
                    latency_ms=(time.perf_counter() - started) * 1000,
                    error=f"{type(exc).__name__}: {exc}",
                )
    raise RuntimeError(f"unreachable reviewer state: {last_error}")


async def run_react_review(
    request: StrategyRequest,
    project_root: str | Path | None = None,
) -> dict[str, Any]:  # pragma: no cover - requires external model
    """Run deterministic pipeline, then four parallel ReAct reviewers and one synthesizer."""

    copilot = RiskStrategyCopilot.create(project_root)
    state = await copilot.run_strategy(request)
    package: StrategyPackage = state.context["strategy_package"]
    context = _package_context(package)
    llm = _load_llm()
    tools = build_react_tools(copilot, package)

    reviewer_prompts = {
        "scenario_typology_agent": (
            "You are a digital-asset fraud-scenario and typology agent. Use SOP and risk-map tools to verify the "
            "attack chain, black/grey-industry methods, behavioral manifestations, counterexamples, and whether "
            "the candidate rule has a coherent business rationale rather than a purely statistical correlation."
        ),
        "feature_model_agent": (
            "You are a feature and model validation agent. Focus on decision-time leakage, missingness, AUC/KS/IV/"
            "Lift/PSI, Train/Development/OOT separation, LR/tree/XGBoost trade-offs, threshold and review-capacity "
            "constraints, cross-month/bootstrap stability, and whether rule extraction preserves model intent."
        ),
        "graph_behavior_agent": (
            "You are a Risk Graph and transaction-behavior agent. Validate strong versus weak identifiers, one-hop/"
            "two-hop evidence, shared-device/address noise, rapid-fund-flow and closed-loop behavior. Require path "
            "evidence and reject IP-only or platform-deposit-address-only conclusions."
        ),
        "governance_cms_str_agent": (
            "You are a strategy-governance and CMS/STR agent. Focus on portfolio overlap, incremental contribution, "
            "action precedence, FEP/event contracts, simulation, independent second review, version/hash binding, "
            "three-workday observation, effectiveness tickets, RFI/EDD/VideoKYC/limits, STR confidentiality and "
            "internal-case-only CMS/STR generation. Never authorize automatic filing or punishment."
        ),
    }

    review_bundles = dict(
        await asyncio.gather(
            *[
                _run_specialist(name, prompt, llm, tools, context)
                for name, prompt in reviewer_prompts.items()
            ]
        )
    )
    serialized_reviews = {
        name: bundle.model_dump(mode="json")
        for name, bundle in review_bundles.items()
    }

    synthesis_prompt = f"""You are the Lead Risk Strategy Agent. Synthesize the four specialist Agent reviews below into a
single professional Markdown document. Preserve disagreements. The output must include: executive decision,
validated architecture, recommended strategy revision, feature/model validation plan, product implementation
roadmap, company-style test-environment acceptance criteria, governance gates, and explicit prototype boundaries.
Do not reveal private chain-of-thought.

{json.dumps(serialized_reviews, ensure_ascii=False)}
"""
    async with asyncio.timeout(180):
        response = await llm.ainvoke(synthesis_prompt)
        synthesis = str(getattr(response, "content", response))

    output_dir = copilot.runtime.settings.output_dir / "react_review"
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, bundle in review_bundles.items():
        (output_dir / f"{name}.json").write_text(
            bundle.model_dump_json(indent=2),
            encoding="utf-8",
        )
        finding_lines = "\n".join(
            (
                f"- [{finding.severity.upper()}] {finding.category}: "
                f"{finding.statement}"
            )
            for finding in bundle.findings
        )
        (output_dir / f"{name}.md").write_text(
            "\n".join(
                [
                    f"# {name}",
                    "",
                    f"Status: `{bundle.status}`",
                    "",
                    bundle.summary,
                    "",
                    "## Findings",
                    "",
                    finding_lines or "- No schema-valid findings.",
                    "",
                    "## Risks",
                    "",
                    *[f"- {item}" for item in bundle.risks],
                    "",
                    "## Revisions",
                    "",
                    *[f"- {item}" for item in bundle.revisions],
                    "",
                    "## Acceptance tests",
                    "",
                    *[f"- {item}" for item in bundle.acceptance_tests],
                ]
            ),
            encoding="utf-8",
        )
    summary_path = output_dir / "lead_risk_strategy_agent_review.md"
    summary_path.write_text(synthesis, encoding="utf-8")
    manifest_path = output_dir / "react_review_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "request": request.model_dump(mode="json"),
                "selected_strategy": package.selected_strategy.strategy_id,
                "reviewers": serialized_reviews,
                "status_counts": {
                    status: sum(bundle.status == status for bundle in review_bundles.values())
                    for status in ["succeeded", "degraded", "failed", "timed_out"]
                },
                "artifacts": {
                    name: str(output_dir / f"{name}.md")
                    for name in review_bundles
                },
                "summary": str(summary_path),
                "boundary": package.data_disclaimer,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "state": state,
        "reviews": serialized_reviews,
        "synthesis": synthesis,
        "artifacts": {
            "summary": str(summary_path),
            "manifest": str(manifest_path),
        },
    }
