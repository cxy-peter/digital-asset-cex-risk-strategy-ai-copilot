from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

from ..schemas import ModelMetrics
from .evaluation import choose_threshold, metrics_at_threshold
from .temporal import TemporalSplit, chronological_train_dev_oot_split


@dataclass
class TrainedModel:
    name: str
    pipeline: Pipeline
    metrics: ModelMetrics
    test_scores: np.ndarray
    test_index: pd.Index
    feature_names: list[str]
    dev_metrics: ModelMetrics | None = None
    dev_scores: np.ndarray | None = None
    dev_index: pd.Index | None = None
    training_manifest: dict[str, Any] | None = None

    @property
    def oot_scores(self) -> np.ndarray:
        """Explicit alias for the backward-compatible ``test_scores`` field."""

        return self.test_scores

    @property
    def oot_index(self) -> pd.Index:
        """Explicit alias for the backward-compatible ``test_index`` field."""

        return self.test_index


@dataclass
class ModelTrainer:
    target: str = "fraud_label"
    time_column: str = "event_date"
    random_seed: int = 20260728

    def _split(
        self,
        data: pd.DataFrame,
        train_fraction: float = 0.60,
        dev_fraction: float = 0.20,
    ) -> TemporalSplit:
        return chronological_train_dev_oot_split(
            data,
            time_column=self.time_column,
            train_fraction=train_fraction,
            dev_fraction=dev_fraction,
        )

    def _preprocessor(self, frame: pd.DataFrame, features: list[str], scale_numeric: bool = True) -> tuple[ColumnTransformer, list[str], list[str]]:
        numeric = [f for f in features if pd.api.types.is_numeric_dtype(frame[f]) or pd.api.types.is_bool_dtype(frame[f])]
        categorical = [f for f in features if f not in numeric]
        numeric_steps = [("imputer", SimpleImputer(strategy="median"))]
        if scale_numeric:
            numeric_steps.append(("scaler", StandardScaler()))
        numeric_pipe = Pipeline(numeric_steps)
        categorical_pipe = Pipeline(
            [("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]
        )
        transformer = ColumnTransformer(
            [("numeric", numeric_pipe, numeric), ("categorical", categorical_pipe, categorical)],
            remainder="drop",
            verbose_feature_names_out=True,
        )
        return transformer, numeric, categorical

    def train(
        self,
        data: pd.DataFrame,
        features: list[str],
        thresholds: list[float],
        minimum_precision: float,
        minimum_recall: float,
        max_alert_rate: float,
    ) -> list[TrainedModel]:
        split = self._split(data)
        train, dev, oot = split.train, split.dev, split.oot
        x_dev, y_dev = dev[features], dev[self.target].astype(int)
        x_oot, y_oot = oot[features], oot[self.target].astype(int)
        models: dict[str, Any] = {
            "logistic_regression": LogisticRegression(max_iter=2000, class_weight="balanced", random_state=self.random_seed),
            "decision_tree_depth4": DecisionTreeClassifier(max_depth=4, min_samples_leaf=20, class_weight="balanced", random_state=self.random_seed),
            "xgboost": XGBClassifier(
                n_estimators=220,
                max_depth=4,
                learning_rate=0.045,
                subsample=0.85,
                colsample_bytree=0.85,
                eval_metric="logloss",
                random_state=self.random_seed,
                n_jobs=2,
                reg_lambda=2.0,
                reg_alpha=0.15,
            ),
        }
        results: list[TrainedModel] = []
        for name, estimator in models.items():
            fit_frame = train
            sampling_manifest: dict[str, Any] = {
                "partition": "train_only",
                "input_rows": int(len(train)),
                "fit_rows": int(len(train)),
                "negative_undersampling": False,
                "development_resampled": False,
                "out_of_time_resampled": False,
            }
            if name == "xgboost":
                positives = train[train[self.target].astype(int) == 1]
                negatives = train[train[self.target].astype(int) == 0]
                maximum_negatives = min(len(negatives), max(1, len(positives) * 4))
                if len(positives) and len(negatives) > maximum_negatives:
                    sampled_negatives = negatives.sample(
                        n=maximum_negatives,
                        random_state=self.random_seed,
                        replace=False,
                    )
                    fit_frame = pd.concat(
                        [positives, sampled_negatives],
                        axis=0,
                    ).sort_values(self.time_column)
                    sampling_manifest.update(
                        {
                            "fit_rows": int(len(fit_frame)),
                            "positive_rows": int(len(positives)),
                            "negative_rows": int(len(sampled_negatives)),
                            "negative_to_positive_ratio": round(
                                len(sampled_negatives) / max(len(positives), 1),
                                6,
                            ),
                            "negative_undersampling": True,
                        }
                    )
            preprocessor, _, _ = self._preprocessor(
                fit_frame,
                features,
                scale_numeric=(name == "logistic_regression"),
            )
            pipeline = Pipeline([("preprocess", preprocessor), ("model", estimator)])
            pipeline.fit(
                fit_frame[features],
                fit_frame[self.target].astype(int),
            )
            dev_scores = pipeline.predict_proba(x_dev)[:, 1]
            threshold = choose_threshold(
                y_dev.to_numpy(),
                dev_scores,
                thresholds,
                minimum_precision=minimum_precision,
                minimum_recall=minimum_recall,
                max_alert_rate=max_alert_rate,
            )
            dev_metrics = metrics_at_threshold(
                name,
                y_dev.to_numpy(),
                dev_scores,
                threshold,
                len(train),
            )
            oot_scores = pipeline.predict_proba(x_oot)[:, 1]
            metrics = metrics_at_threshold(
                name,
                y_oot.to_numpy(),
                oot_scores,
                threshold,
                len(train),
            )
            names = pipeline.named_steps["preprocess"].get_feature_names_out().tolist()
            results.append(
                TrainedModel(
                    name=name,
                    pipeline=pipeline,
                    metrics=metrics,
                    test_scores=oot_scores,
                    test_index=pd.Index(oot["_original_index"].values),
                    feature_names=names,
                    dev_metrics=dev_metrics,
                    dev_scores=dev_scores,
                    dev_index=pd.Index(dev["_original_index"].values),
                    training_manifest=sampling_manifest,
                )
            )
        # Model ordering is a development-set decision. OOT metrics are reporting-only.
        return sorted(
            results,
            key=lambda result: (result.dev_metrics.f1, result.dev_metrics.roc_auc),
            reverse=True,
        )

    @staticmethod
    def save(models: list[TrainedModel], output_dir: str | Path) -> None:
        target = Path(output_dir)
        target.mkdir(parents=True, exist_ok=True)
        for model in models:
            joblib.dump(model.pipeline, target / f"{model.name}.joblib")
