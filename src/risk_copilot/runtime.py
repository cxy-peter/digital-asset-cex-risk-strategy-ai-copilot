from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from .config import Settings, load_yaml
from .data.generator import DemoDataGenerator
from .features.registry import FeatureRegistry
from .graph.analyzer import RiskGraphAnalyzer
from .knowledge.retriever import HybridKnowledgeRetriever
from .models.temporal import chronological_train_dev_oot_split
from .products.catalog import ProductCatalog


@dataclass
class RuntimeContext:
    settings: Settings
    data_paths: dict[str, Path] = field(default_factory=dict)
    dataframes: dict[str, pd.DataFrame] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, project_root: str | Path | None = None) -> "RuntimeContext":
        settings = Settings.load(project_root)
        context = cls(settings=settings)
        context.settings.data_dir.mkdir(parents=True, exist_ok=True)
        context.settings.output_dir.mkdir(parents=True, exist_ok=True)
        context.artifacts["project_config"] = load_yaml(settings.config_dir / "settings.yaml")
        context.artifacts["feature_registry"] = FeatureRegistry(
            settings.config_dir / "features.yaml",
            settings.config_dir / "events.yaml",
        )
        context.artifacts["knowledge_retriever"] = HybridKnowledgeRetriever(
            settings.knowledge_dir / "risk_scenarios.yaml",
            settings.project_root / "data/sop",
        )
        context.artifacts["product_catalog"] = ProductCatalog(
            settings.config_dir / "products.yaml"
        )
        return context

    def ensure_demo_data(self, users: int = 10000, cases: int = 2600, force: bool = False) -> dict[str, Path]:
        expected = {
            "users": self.settings.data_dir / "users.csv",
            "edges": self.settings.data_dir / "graph_edges.csv",
            "transactions": self.settings.data_dir / "transactions.csv",
            "cases_full": self.settings.data_dir / "cases_enhanced.csv",
            "cases_current": self.settings.data_dir / "cases_current.csv",
        }
        if force or not all(path.exists() for path in expected.values()):
            expected = DemoDataGenerator(seed=self.settings.random_seed).write_all(
                self.settings.data_dir,
                users=users,
                cases=cases,
            )
        self.data_paths.update(expected)
        return expected

    def load_dataframe(self, name: str, parse_dates: list[str] | None = None) -> pd.DataFrame:
        if name in self.dataframes:
            return self.dataframes[name]
        if name not in self.data_paths:
            self.ensure_demo_data()
        frame = pd.read_csv(self.data_paths[name], parse_dates=parse_dates or [])
        self.dataframes[name] = frame
        return frame

    def prepare_graph_enriched_users(self, force: bool = False) -> pd.DataFrame:
        if not force and "users_enriched" in self.dataframes:
            return self.dataframes["users_enriched"]
        users = self.load_dataframe("users", parse_dates=["event_date"])
        edges = self.load_dataframe("edges")
        # Graph risk features may use only labels from the training snapshot. Development and OOT
        # labels are never exposed to graph enrichment, so changing them cannot alter model
        # thresholds or generated candidates.
        split = chronological_train_dev_oot_split(users, time_column="event_date")
        known_label_user_ids = set(split.train["user_id"].astype(str))
        analyzer = RiskGraphAnalyzer().fit(
            users,
            edges,
            known_label_user_ids=known_label_user_ids,
        )
        enriched = analyzer.transform(users)
        self.artifacts["graph_analyzer"] = analyzer
        self.artifacts["graph_label_snapshot"] = {
            "partition": "train",
            "known_label_users": len(known_label_user_ids),
            "total_users": len(users),
        }
        self.dataframes["users_enriched"] = enriched
        return enriched

    @property
    def feature_registry(self) -> FeatureRegistry:
        return self.artifacts["feature_registry"]

    @property
    def knowledge_retriever(self) -> HybridKnowledgeRetriever:
        return self.artifacts["knowledge_retriever"]

    @property
    def product_catalog(self) -> ProductCatalog:
        return self.artifacts["product_catalog"]
