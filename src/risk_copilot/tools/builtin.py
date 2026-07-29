from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..config import load_yaml
from ..features.profiling import FeatureProfiler
from ..governance.workflow import StrategyGovernanceWorkflow
from ..governance.disposition import DispositionPlanner
from ..governance.repository import StrategyRegistryRepository
from ..governance.company_lifecycle import CompanyStrategyTestPlanner
from ..governance.effectiveness import StrategyEffectivenessService
from ..integrations.cms_str import CMSSTRIntegrationService
from ..scoring.repository import RiskSnapshotRepository, T1RiskBatchRunner
from ..scoring.service import UserRiskScoringService
from ..knowledge.builder import RiskKnowledgeBuilder
from ..models.trainer import ModelTrainer, TrainedModel
from ..models.tree_rules import TreeRuleExtractor
from ..rules.backtest import MultiObjectiveRanker, StrategyBacktester
from ..rules.generator import CandidateRuleGenerator
from ..schemas import ActionType, Condition, RiskDomain, RuleGroup, StrategyCandidate, StrategyRequest, StrategyTestPlan
from .registry import ToolRegistry


def build_tool_registry(runtime) -> ToolRegistry:
    registry = ToolRegistry()
    settings = runtime.settings
    project_config = runtime.artifacts["project_config"]

    @registry.tool(
        "catalog.list_events",
        "List registered risk events, their domains, allowed actions, and feature availability.",
        tags={"catalog", "event"},
    )
    def list_events(domain: str | None = None) -> list[dict[str, Any]]:
        events = runtime.feature_registry.events
        if domain:
            events = [e for e in events if e.domain.value == domain]
        return [e.model_dump(mode="json") for e in events]

    @registry.tool(
        "catalog.list_products",
        "List risk-control products reconstructed from weekly internship materials.",
        tags={"catalog", "product", "architecture"},
    )
    def list_products(layer: str | None = None, prototype_status: str | None = None) -> list[dict[str, Any]]:
        products = runtime.product_catalog.products
        if layer:
            products = [product for product in products if product.layer == layer]
        if prototype_status:
            products = [product for product in products if product.prototype_status == prototype_status]
        return [product.model_dump(mode="json") for product in products]

    @registry.tool(
        "catalog.map_products",
        "Map a risk requirement to relevant products and their dependency closure.",
        tags={"catalog", "product", "architecture"},
    )
    def map_products(domain: str | None, event_code: str | None, query: str) -> dict[str, Any]:
        return runtime.product_catalog.map_stack(domain=domain, event_code=event_code, query=query)

    @registry.tool(
        "catalog.write_products",
        "Write the full risk product catalog and product architecture diagram.",
        tags={"catalog", "product", "artifact"},
        read_only=False,
    )
    def write_products(output_dir: str) -> dict[str, str]:
        return {key: str(value) for key, value in runtime.product_catalog.write(output_dir).items()}

    @registry.tool(
        "catalog.search_features",
        "Search real-time/offline features by event, domain, tags, or semantic keyword.",
        tags={"catalog", "feature"},
    )
    def search_features(
        text: str = "",
        domain: str | None = None,
        event_code: str | None = None,
        tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        specs = runtime.feature_registry.search(text=text, domain=domain, event_code=event_code, tags=tags)
        return [item.model_dump(mode="json") for item in specs]

    @registry.tool(
        "catalog.validate_decision_time",
        "Validate that candidate features exist, belong to the event, and are available at decision time.",
        tags={"catalog", "governance"},
    )
    def validate_decision_time(feature_names: list[str], event_code: str) -> list[str]:
        return runtime.feature_registry.validate_decision_time(feature_names, event_code)

    @registry.tool(
        "catalog.get_event_contract",
        "Return a versioned event contract with typed feature schemas, actions, lineage warnings, and a reproducible SHA-256 hash.",
        tags={"catalog", "event", "contract", "governance"},
    )
    def get_event_contract(event_code: str) -> dict[str, Any]:
        return runtime.feature_registry.build_event_contract(event_code).model_dump(mode="json")

    @registry.tool(
        "catalog.validate_contracts",
        "Validate all event/feature references and report blocking errors separately from lineage drift warnings.",
        tags={"catalog", "event", "contract", "governance"},
    )
    def validate_contracts() -> dict[str, Any]:
        return runtime.feature_registry.validate_contract_consistency().model_dump(mode="json")

    @registry.tool(
        "data.schema",
        "Return dataset dimensions, columns, dtypes, missingness, and positive-label rate.",
        tags={"data", "quality"},
    )
    def dataset_schema(data: pd.DataFrame, target: str = "fraud_label") -> dict[str, Any]:
        return {
            "rows": int(len(data)),
            "columns": list(data.columns),
            "dtypes": {c: str(data[c].dtype) for c in data.columns},
            "missing_rate": {c: round(float(data[c].isna().mean()), 5) for c in data.columns if data[c].isna().any()},
            "positive_rate": float(data[target].mean()) if target in data else None,
        }

    @registry.tool(
        "knowledge.search",
        "Hybrid lexical/character retrieval over risk scenarios and SOPs.",
        tags={"knowledge", "rag", "sop"},
    )
    def search_knowledge(
        query: str,
        top_k: int = 6,
        industry: str | None = None,
        document_type: str | None = None,
    ) -> list[dict[str, Any]]:
        filters = {"industry": industry} if industry else None
        hits = runtime.knowledge_retriever.search(
            query,
            top_k=top_k,
            filters=filters,
            document_type=document_type,
        )
        return [
            {
                "doc_id": hit.doc_id,
                "score": hit.score,
                "title": hit.title,
                "text": hit.text,
                "metadata": hit.metadata,
            }
            for hit in hits
        ]

    @registry.tool(
        "knowledge.build_system",
        "Generate the internship-derived risk-scenario and strategy knowledge map as Markdown and CSV.",
        tags={"knowledge", "artifact"},
        read_only=False,
    )
    def build_knowledge_system(output_dir: str) -> dict[str, str]:
        paths = RiskKnowledgeBuilder(settings.knowledge_dir / "risk_scenarios.yaml").write(output_dir)
        return {key: str(value) for key, value in paths.items()}

    @registry.tool(
        "graph.enrich_users",
        "Build one-hop/two-hop graph features while down-weighting weak IP relations.",
        tags={"graph", "feature"},
    )
    def enrich_users_graph(force: bool = False) -> pd.DataFrame:
        return runtime.prepare_graph_enriched_users(force=force)

    @registry.tool(
        "graph.explain_user",
        "Return auditable user-to-identifier-to-user paths and one/two-hop risk features.",
        tags={"graph", "explainability"},
    )
    def explain_user_graph(user_id: str) -> dict[str, Any]:
        if "graph_analyzer" not in runtime.artifacts:
            runtime.prepare_graph_enriched_users()
        return runtime.artifacts["graph_analyzer"].explain_user(user_id)

    @registry.tool(
        "features.profile",
        "Compute missingness, AUC, KS, IV/WOE, Lift@10, Cramer's V, PSI, direction, and recommendation.",
        tags={"feature", "profiling", "model"},
    )
    def profile_features(
        data: pd.DataFrame,
        feature_names: list[str] | None = None,
        target: str = "fraud_label",
        time_column: str = "event_date",
    ):
        return FeatureProfiler(target=target, time_column=time_column).profile(data, feature_names=feature_names)

    @registry.tool(
        "features.behavior_contrast",
        "Compare fraud/non-fraud feature distributions and extract interpretable manifestations.",
        tags={"feature", "analysis", "fraud"},
    )
    def behavior_contrast(
        data: pd.DataFrame,
        features: list[str],
        target: str = "fraud_label",
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        y = data[target].astype(int)
        for feature in features:
            if feature not in data:
                continue
            s = pd.to_numeric(data[feature], errors="coerce")
            if s.notna().sum() < 30:
                continue
            fraud_mean = float(s[y == 1].mean())
            normal_mean = float(s[y == 0].mean())
            fraud_median = float(s[y == 1].median())
            normal_median = float(s[y == 0].median())
            top_threshold = float(s.quantile(0.90))
            top_bad_rate = float(y[s >= top_threshold].mean()) if (s >= top_threshold).any() else 0.0
            rows.append(
                {
                    "feature": feature,
                    "fraud_mean": fraud_mean,
                    "normal_mean": normal_mean,
                    "mean_ratio": fraud_mean / max(abs(normal_mean), 1e-9),
                    "fraud_median": fraud_median,
                    "normal_median": normal_median,
                    "p90_threshold": top_threshold,
                    "p90_bad_rate": top_bad_rate,
                    "direction": "higher_in_fraud" if fraud_mean >= normal_mean else "lower_in_fraud",
                }
            )
        return sorted(rows, key=lambda x: abs(np.log(max(abs(x["mean_ratio"]), 1e-9))), reverse=True)

    @registry.tool(
        "scoring.assess_users",
        "Calculate onboarding and T+1 dynamic risk tiers with explicit manual-override and confidentiality controls.",
        tags={"scoring", "user_profile", "governance"},
        allowed_agents={"user_risk_scoring_agent"},
        read_only=False,
    )
    def assess_users(data: pd.DataFrame, top_k: int = 50) -> dict[str, Any]:
        service = UserRiskScoringService()
        if data.empty:
            raise ValueError("scoring input is empty")
        repository = RiskSnapshotRepository(
            settings.output_dir / "user_risk_scoring" / "risk_snapshots.sqlite"
        )
        # A deterministic synthetic override proves that the next T+1 batch reads the durable
        # reviewer decision instead of silently replacing it with the automatic tier.
        automatic_profiles = [service.assess(row) for _, row in data.iterrows()]
        highest_auto = max(
            automatic_profiles,
            key=lambda record: (record["combined_score"], record["user_id"]),
        )
        repository.set_manual_override(
            highest_auto["user_id"],
            "L3.2",
            reason="synthetic reviewer-confirmed tier used to verify T+1 override persistence",
            actor="demo_risk_reviewer",
        )
        if "event_date" in data:
            parsed_dates = pd.to_datetime(data["event_date"], errors="coerce")
            maximum_date = parsed_dates.max()
            as_of_date = (
                maximum_date.date().isoformat()
                if pd.notna(maximum_date)
                else pd.Timestamp.utcnow().date().isoformat()
            )
        else:
            as_of_date = pd.Timestamp.utcnow().date().isoformat()
        flat, batch_manifest = T1RiskBatchRunner(repository, service).run(
            data,
            batch_id=f"T1-DEMO-{as_of_date}",
            as_of_date=as_of_date,
        )
        flat = flat.sort_values(
            ["combined_score", "user_id"],
            ascending=[False, True],
        )
        tier_order = ["L1", "L2", "L3.1", "L3.2", "L3.3", "L4"]
        distribution = {tier: int((flat["final_tier"] == tier).sum()) for tier in tier_order}
        top_profiles = flat.head(top_k).to_dict("records")
        manual_override_demo = repository.current_profile(highest_auto["user_id"])
        override_history = repository.history(highest_auto["user_id"])
        return {
            "profiles": flat,
            "tier_distribution": distribution,
            "highest_tier": next((tier for tier in reversed(tier_order) if distribution[tier] > 0), "L1"),
            "top_profiles": top_profiles,
            "manual_override_demo": manual_override_demo,
            "manual_override_history": {
                "user_id": highest_auto["user_id"],
                "snapshot_count": len(override_history["snapshots"]),
                "override_count": len(override_history["manual_overrides"]),
                "audit_event_count": len(override_history["audit_events"]),
            },
            "batch_manifest": batch_manifest,
            "str_visible_count": int(flat["str_details_visible"].sum()),
            "scoring_policy": {
                "layers": ["onboarding_kyc", "automatic_t1_behavior"],
                "manual_override_preserved": True,
                "manual_override_storage": "SQLite active override + immutable batch snapshot",
                "batch_idempotency_key": ["batch_id", "user_id"],
                "ordinary_profile_can_show_str": False,
            },
        }

    @registry.tool(
        "models.train_benchmarks",
        "Train time-split Logistic Regression, depth-4 Decision Tree, and XGBoost baselines.",
        tags={"model", "training", "benchmark"},
    )
    def train_benchmarks(
        data: pd.DataFrame,
        features: list[str],
        request: StrategyRequest,
    ) -> list[TrainedModel]:
        valid_features = [f for f in features if f in data.columns and data[f].nunique(dropna=True) > 1]
        models = ModelTrainer(
            target=request.target_label,
            time_column=project_config.get("time_column", "event_date"),
            random_seed=settings.random_seed,
        ).train(
            data,
            features=valid_features,
            thresholds=project_config["model_threshold_grid"],
            minimum_precision=request.minimum_precision,
            minimum_recall=request.minimum_recall,
            max_alert_rate=request.max_alert_rate,
        )
        runtime.artifacts["trained_models"] = models
        runtime.artifacts["model_features"] = valid_features
        return models

    @registry.tool(
        "models.extract_tree_rules",
        "Extract high-risk leaves from the depth-4 decision tree into executable rule DSL candidates.",
        tags={"model", "rule", "explainability"},
    )
    def extract_tree_rules(
        trained_models: list[TrainedModel],
        domain: str,
        event_code: str,
        action: str = "MANUAL_REVIEW",
    ) -> list[StrategyCandidate]:
        tree = next((m for m in trained_models if m.name == "decision_tree_depth4"), None)
        if tree is None:
            return []
        estimator = tree.pipeline.named_steps["model"]
        return TreeRuleExtractor().extract(
            estimator,
            transformed_feature_names=tree.feature_names,
            original_feature_names=set(runtime.artifacts.get("model_features", [])),
            domain=RiskDomain(domain),
            event_code=event_code,
            action=ActionType(action),
        )

    @registry.tool(
        "models.global_importance",
        "Return aggregated global feature importance for tree-based models.",
        tags={"model", "explainability"},
    )
    def global_importance(trained_model: TrainedModel, top_k: int = 20) -> list[dict[str, Any]]:
        estimator = trained_model.pipeline.named_steps["model"]
        raw = getattr(estimator, "feature_importances_", None)
        if raw is None:
            coef = getattr(estimator, "coef_", None)
            raw = np.abs(coef[0]) if coef is not None else np.zeros(len(trained_model.feature_names))
        grouped: dict[str, float] = {}
        originals = runtime.artifacts.get("model_features", [])
        for name, value in zip(trained_model.feature_names, raw):
            clean = name.split("__", 1)[-1]
            original = next((f for f in sorted(originals, key=len, reverse=True) if clean == f or clean.startswith(f + "_")), clean)
            grouped[original] = grouped.get(original, 0.0) + float(abs(value))
        return [
            {"feature": feature, "importance": importance}
            for feature, importance in sorted(grouped.items(), key=lambda x: x[1], reverse=True)[:top_k]
        ]

    @registry.tool(
        "rules.generate_candidates",
        "Generate expert-template, quantile, graph, tree, and model-score candidates.",
        tags={"rule", "strategy", "generation"},
    )
    def generate_candidates(
        data: pd.DataFrame,
        profiles: list,
        request: StrategyRequest,
        tree_candidates: list[StrategyCandidate] | None = None,
        trained_models: list[TrainedModel] | None = None,
    ) -> list[StrategyCandidate]:
        generator = CandidateRuleGenerator(settings.config_dir / "strategy_templates.yaml")
        candidates = generator.from_templates(request)
        candidates.extend(generator.quantile_candidates(data, profiles, request, top_features=8))
        candidates.extend(generator.graph_candidates(request))
        candidates.extend(tree_candidates or [])
        # Add model-score rules using thresholds chosen on development data. The frozen
        # candidates are evaluated on OOT only after development ranking.
        for model in trained_models or []:
            if model.dev_metrics is None:
                raise ValueError(
                    f"trained model {model.name!r} has no development metrics"
                )
            score_name = f"model_score__{model.name}"
            candidates.append(
                StrategyCandidate(
                    strategy_id=f"MDL-{model.name}",
                    name=f"{model.name}模型分层",
                    domain=request.domain or RiskDomain.FUND_SECURITY,
                    event_code=request.event_code or "RiskScoreDaily",
                    description=f"使用开发集阈值{model.dev_metrics.threshold:.3f}生成模型分层候选。",
                    rule=RuleGroup(
                        conditions=[
                            Condition(
                                feature=score_name,
                                operator=">=",
                                value=model.dev_metrics.threshold,
                            )
                        ]
                    ),
                    action=request.preferred_actions[0] if request.preferred_actions else ActionType.MANUAL_REVIEW,
                    source="model_score",
                    rationale=[
                        f"Dev ROC-AUC={model.dev_metrics.roc_auc:.4f}",
                        f"Dev KS={model.dev_metrics.ks:.4f}",
                        f"Dev Lift@10={model.dev_metrics.lift_top_10:.2f}",
                    ],
                    required_features=[score_name],
                    tags=["model_score", model.name],
                )
            )
        # De-duplicate stable IDs while preserving the first candidate.
        unique: dict[str, StrategyCandidate] = {}
        for candidate in candidates:
            unique.setdefault(candidate.strategy_id, candidate)
        return list(unique.values())

    @registry.tool(
        "rules.prepare_holdout",
        "Create the common development or OOT frame and attach split-specific model scores.",
        tags={"model", "backtest", "data"},
    )
    def prepare_holdout(
        data: pd.DataFrame,
        trained_models: list[TrainedModel],
        partition: str = "oot",
    ) -> pd.DataFrame:
        if not trained_models:
            raise ValueError("trained_models is empty")
        if partition not in {"dev", "oot"}:
            raise ValueError("partition must be 'dev' or 'oot'")
        index_attr = "dev_index" if partition == "dev" else "oot_index"
        score_attr = "dev_scores" if partition == "dev" else "oot_scores"
        split_index = getattr(trained_models[0], index_attr)
        if split_index is None:
            raise ValueError(
                f"trained model {trained_models[0].name!r} has no {partition} index"
            )
        holdout = data.loc[split_index].copy()
        for model in trained_models:
            model_index = getattr(model, index_attr)
            model_scores = getattr(model, score_attr)
            if model_index is None or model_scores is None:
                raise ValueError(f"trained model {model.name!r} has no {partition} data")
            if not model_index.equals(split_index):
                raise ValueError(f"{partition} indices are not aligned across trained models")
            holdout[f"model_score__{model.name}"] = model_scores
        return holdout.reset_index(drop=True)

    @registry.tool(
        "rules.backtest_rank",
        "Backtest all executable candidates and rank them with a multi-objective, GRPO-inspired group-relative reward.",
        tags={"rule", "backtest", "ranking"},
    )
    def backtest_rank(
        data: pd.DataFrame,
        candidates: list[StrategyCandidate],
        request: StrategyRequest,
    ):
        backtester = StrategyBacktester(
            target=request.target_label,
            loss_column=project_config.get("loss_column", "estimated_loss_amount"),
            time_column=project_config.get("time_column", "event_date"),
            review_capacity=request.review_capacity,
        )
        evaluated = []
        failures = []
        for candidate in candidates:
            missing = [f for f in candidate.required_features if f not in data]
            if missing:
                failures.append({"strategy_id": candidate.strategy_id, "missing_features": missing})
                continue
            try:
                evaluated.append((candidate, backtester.evaluate(data, candidate)))
            except Exception as exc:
                failures.append({"strategy_id": candidate.strategy_id, "error": str(exc)})
        ranked = MultiObjectiveRanker(
            weights=project_config["reward_weights"],
            max_alert_rate=request.max_alert_rate,
        ).rank(evaluated)
        runtime.artifacts["candidate_failures"] = failures
        return ranked

    @registry.tool(
        "governance.review_strategy",
        "Apply lifecycle, decision-time, action, metric, approval, and confidentiality gates.",
        tags={"governance", "strategy"},
    )
    def governance_review(strategy: StrategyCandidate, metrics, request: StrategyRequest):
        workflow = StrategyGovernanceWorkflow(
            settings.config_dir / "governance.yaml", runtime.feature_registry
        )
        decision = workflow.review(strategy, metrics, request)
        payload = workflow.build_engine_payload(strategy, decision, metrics)
        return {"decision": decision, "payload": payload}

    @registry.tool(
        "governance.plan_disposition",
        "Build the L1-L4 action ladder and penalty/verification-center approval controls.",
        tags={"governance", "disposition", "penalty_center"},
        allowed_agents={"disposition_planning_agent"},
    )
    def plan_disposition(strategy: StrategyCandidate) -> dict[str, Any]:
        planner = DispositionPlanner()
        return {
            "tier_matrix": planner.tier_matrix(),
            "selected_strategy_plan": planner.selected_strategy_plan(strategy),
        }

    @registry.tool(
        "governance.persist_strategy",
        "Persist an AI-assisted strategy candidate, simulation metrics, governance transition, and audit event in SQLite.",
        tags={"governance", "registry", "audit"},
        allowed_agents={"governance_agent"},
        read_only=False,
    )
    def persist_strategy(strategy: StrategyCandidate, metrics, governance) -> dict[str, Any]:
        repository = StrategyRegistryRepository(settings.output_dir / "strategy_registry.sqlite")
        record = repository.persist_candidate(strategy, metrics, governance)
        record["history"] = repository.history(strategy.strategy_id)
        return record

    @registry.tool(
        "governance.evaluate_company_test_environment",
        "Build the company-style FEP/Rule-Engine test plan: feature validation, historical backtest, simulation, independent second review, three-day observation, and effectiveness review.",
        tags={"governance", "test_environment", "strategy_backtracking", "fep", "ticket"},
        allowed_agents={"strategy_test_environment_agent"},
    )
    def evaluate_company_test_environment(
        strategy: StrategyCandidate,
        strategy_version: int,
        engine_payload: dict[str, Any],
        metrics,
        governance,
        data_snapshot_id: str,
        feature_catalog_version: str,
        stability_analysis: dict[str, Any] | None = None,
        conflict_analysis: dict[str, Any] | None = None,
        ai_advisory_board: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        plan = CompanyStrategyTestPlanner(settings.config_dir / "test_environment.yaml").build_plan(
            strategy=strategy,
            strategy_version=strategy_version,
            engine_payload=engine_payload,
            metrics=metrics,
            governance=governance,
            data_snapshot_id=data_snapshot_id,
            feature_catalog_version=feature_catalog_version,
            stability_analysis=stability_analysis,
            conflict_analysis=conflict_analysis,
            ai_advisory_board=ai_advisory_board,
        )
        return {"plan": plan}

    @registry.tool(
        "governance.create_effectiveness_ticket",
        "Create a Ticket-Module-style strategy-effectiveness label bound to the exact strategy version, test run, and data snapshot.",
        tags={"governance", "ticket", "effectiveness", "post_launch_review"},
        allowed_agents={"strategy_effectiveness_agent"},
        read_only=False,
    )
    def create_effectiveness_ticket(
        test_plan: dict[str, Any] | StrategyTestPlan,
        metrics,
        conflict_analysis: dict[str, Any] | None = None,
        stability_analysis: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        plan = test_plan if isinstance(test_plan, StrategyTestPlan) else StrategyTestPlan.model_validate(test_plan)
        service = StrategyEffectivenessService(settings.output_dir / "strategy_effectiveness.sqlite")
        ticket = service.create_simulation_ticket(
            plan=plan,
            metrics=metrics,
            conflict_analysis=conflict_analysis,
            stability_analysis=stability_analysis,
        )
        observation_template = service.create_three_workday_observation_template(
            plan=plan, baseline_metrics=metrics
        )
        return {
            "ticket": ticket,
            "observation_template": observation_template,
            "history": service.history(plan.strategy_id),
            "database": str(service.database_path),
        }

    @registry.tool(
        "integration.prepare_cms_str_candidates",
        "For eligible third-level strategy tags, prefill internal CMS/STR candidate cases with evidence snapshots. This never files or submits externally.",
        tags={"integration", "cms", "str", "human_review"},
        allowed_agents={"cms_str_integration_agent"},
        read_only=False,
    )
    def prepare_cms_str_candidates(
        strategy: StrategyCandidate,
        strategy_version: int,
        data: pd.DataFrame,
        data_snapshot_id: str,
        top_k: int = 10,
    ) -> dict[str, Any]:
        return CMSSTRIntegrationService(
            settings.config_dir / "cms_str_integration.yaml",
            settings.output_dir / "cms_str_case_previews.sqlite",
        ).prepare_candidates(
            strategy=strategy,
            strategy_version=strategy_version,
            data=data,
            data_snapshot_id=data_snapshot_id,
            top_k=top_k,
        )

    @registry.tool(
        "governance.strategy_history",
        "Read all versions, approvals, and audit events for a registered strategy.",
        tags={"governance", "registry", "audit"},
    )
    def strategy_history(strategy_id: str) -> dict[str, Any]:
        return StrategyRegistryRepository(settings.output_dir / "strategy_registry.sqlite").history(strategy_id)

    return registry
