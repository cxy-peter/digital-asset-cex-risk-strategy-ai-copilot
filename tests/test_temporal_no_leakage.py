from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

import risk_copilot.models.trainer as trainer_module
from risk_copilot.features.profiling import FeatureProfiler
from risk_copilot.graph.analyzer import RiskGraphAnalyzer
from risk_copilot.models.temporal import chronological_train_dev_oot_split
from risk_copilot.models.trainer import ModelTrainer
from risk_copilot.rules.generator import CandidateRuleGenerator
from risk_copilot.schemas import RiskDomain, StrategyRequest


ROOT = Path(__file__).resolve().parents[1]


def _frame(rows: int = 900) -> pd.DataFrame:
    rng = np.random.default_rng(20260728)
    x1 = rng.normal(size=rows)
    x2 = rng.normal(size=rows)
    month_effect = np.linspace(-0.4, 0.4, rows)
    probability = 1 / (1 + np.exp(-(1.3 * x1 - 0.7 * x2 + month_effect)))
    label = rng.binomial(1, probability)
    return pd.DataFrame(
        {
            "event_date": pd.date_range("2025-01-01", periods=rows, freq="h"),
            "x1": x1,
            "x2": x2,
            "fraud_label": label,
            "estimated_loss_amount": rng.lognormal(mean=4, sigma=0.5, size=rows),
        }
    )


def _request() -> StrategyRequest:
    return StrategyRequest(
        request_id="TEMPORAL-TEST",
        query="test development-only candidate generation",
        domain=RiskDomain.FUND_SECURITY,
        event_code="ChainWithdraw",
        minimum_precision=0.0,
        minimum_recall=0.0,
        max_alert_rate=1.0,
    )


def test_chronological_split_is_disjoint_and_ordered():
    data = _frame().sample(frac=1.0, random_state=7)
    split = chronological_train_dev_oot_split(data, "event_date")

    train_ids = set(split.train["_original_index"])
    dev_ids = set(split.dev["_original_index"])
    oot_ids = set(split.oot["_original_index"])
    assert train_ids.isdisjoint(dev_ids)
    assert train_ids.isdisjoint(oot_ids)
    assert dev_ids.isdisjoint(oot_ids)
    assert len(train_ids | dev_ids | oot_ids) == len(data)
    assert split.train["event_date"].max() <= split.dev["event_date"].min()
    assert split.dev["event_date"].max() <= split.oot["event_date"].min()


def test_changing_oot_labels_does_not_change_thresholds_or_candidates(monkeypatch):
    # Keep the regression test fast while preserving the three-model training branch.
    monkeypatch.setattr(
        trainer_module,
        "XGBClassifier",
        lambda **kwargs: DecisionTreeClassifier(
            max_depth=3,
            min_samples_leaf=15,
            random_state=kwargs.get("random_state"),
        ),
    )
    original = _frame()
    changed = original.copy()
    split = chronological_train_dev_oot_split(original, "event_date")
    changed.loc[split.oot["_original_index"], "fraud_label"] = (
        1 - changed.loc[split.oot["_original_index"], "fraud_label"]
    )

    trainer = ModelTrainer(target="fraud_label", time_column="event_date", random_seed=7)
    train_kwargs = {
        "features": ["x1", "x2"],
        "thresholds": [0.2, 0.35, 0.5, 0.65, 0.8],
        "minimum_precision": 0.0,
        "minimum_recall": 0.0,
        "max_alert_rate": 1.0,
    }
    first_models = trainer.train(original, **train_kwargs)
    second_models = trainer.train(changed, **train_kwargs)

    first_thresholds = {
        model.name: model.dev_metrics.threshold for model in first_models
    }
    second_thresholds = {
        model.name: model.dev_metrics.threshold for model in second_models
    }
    assert first_thresholds == second_thresholds
    assert [model.name for model in first_models] == [
        model.name for model in second_models
    ]
    assert [
        model.dev_metrics.model_dump() for model in first_models
    ] == [
        model.dev_metrics.model_dump() for model in second_models
    ]

    profiler = FeatureProfiler(target="fraud_label", time_column="event_date")
    first_profiles = profiler.profile(original, feature_names=["x1", "x2"])
    second_profiles = profiler.profile(changed, feature_names=["x1", "x2"])
    assert [profile.model_dump() for profile in first_profiles] == [
        profile.model_dump() for profile in second_profiles
    ]

    generator = CandidateRuleGenerator(ROOT / "configs/strategy_templates.yaml")
    first_dev = chronological_train_dev_oot_split(original, "event_date").dev
    second_dev = chronological_train_dev_oot_split(changed, "event_date").dev
    first_candidates = generator.quantile_candidates(
        first_dev, first_profiles, _request(), top_features=2
    )
    second_candidates = generator.quantile_candidates(
        second_dev, second_profiles, _request(), top_features=2
    )
    assert [candidate.model_dump(mode="json") for candidate in first_candidates] == [
        candidate.model_dump(mode="json") for candidate in second_candidates
    ]

    # OOT remains an evaluation surface: changing only OOT labels may change final metrics.
    first_oot = {model.name: model.metrics.model_dump() for model in first_models}
    second_oot = {model.name: model.metrics.model_dump() for model in second_models}
    assert first_oot != second_oot


def test_graph_candidate_ids_are_deterministic():
    first = CandidateRuleGenerator.graph_candidates(_request())
    second = CandidateRuleGenerator.graph_candidates(_request())
    assert [candidate.model_dump(mode="json") for candidate in first] == [
        candidate.model_dump(mode="json") for candidate in second
    ]


def test_graph_enrichment_ignores_dev_and_oot_labels():
    users = pd.DataFrame(
        {
            "user_id": [f"U{i}" for i in range(20)],
            "event_date": pd.date_range("2026-01-01", periods=20, freq="D"),
            "fraud_label": [0, 1] * 10,
        }
    )
    edges = pd.DataFrame(
        [
            {
                "user_id": f"U{i}",
                "relation_type": "device",
                "identifier": f"D{i // 2}",
                "relation_weight": 1.0,
            }
            for i in range(20)
        ]
    )
    split = chronological_train_dev_oot_split(users, "event_date")
    known = set(split.train["user_id"])
    changed = users.copy()
    unknown = ~changed["user_id"].isin(known)
    changed.loc[unknown, "fraud_label"] = 1 - changed.loc[unknown, "fraud_label"]

    first = RiskGraphAnalyzer().fit(
        users, edges, known_label_user_ids=known
    ).transform(users)
    second = RiskGraphAnalyzer().fit(
        changed, edges, known_label_user_ids=known
    ).transform(changed)
    graph_columns = [
        column
        for column in first.columns
        if column.endswith("_count")
        or column.endswith("_ratio")
        or column == "fraud_graph_score"
    ]
    pd.testing.assert_frame_equal(first[graph_columns], second[graph_columns])


def test_xgboost_undersamples_negatives_only_in_train(monkeypatch):
    monkeypatch.setattr(
        trainer_module,
        "XGBClassifier",
        lambda **kwargs: DecisionTreeClassifier(
            max_depth=3,
            min_samples_leaf=5,
            random_state=kwargs.get("random_state"),
        ),
    )
    data = _frame(1000)
    data["fraud_label"] = 0
    data.loc[data.index % 20 == 0, "fraud_label"] = 1
    models = ModelTrainer(
        target="fraud_label",
        time_column="event_date",
        random_seed=9,
    ).train(
        data,
        features=["x1", "x2"],
        thresholds=[0.3, 0.5, 0.7],
        minimum_precision=0.0,
        minimum_recall=0.0,
        max_alert_rate=1.0,
    )
    xgboost = next(model for model in models if model.name == "xgboost")
    manifest = xgboost.training_manifest

    assert manifest is not None
    assert manifest["partition"] == "train_only"
    assert manifest["negative_undersampling"] is True
    assert manifest["negative_to_positive_ratio"] <= 4.0
    assert manifest["development_resampled"] is False
    assert manifest["out_of_time_resampled"] is False
