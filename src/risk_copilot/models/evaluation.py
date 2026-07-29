from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from ..schemas import ModelMetrics


def ks_statistic(y_true: np.ndarray, scores: np.ndarray) -> float:
    fpr, tpr, _ = roc_curve(y_true, scores)
    return float(np.max(np.abs(tpr - fpr)))


def lift_at_fraction(y_true: np.ndarray, scores: np.ndarray, fraction: float = 0.10) -> float:
    frame = pd.DataFrame({"y": y_true, "s": scores}).sort_values("s", ascending=False)
    if frame["y"].mean() == 0:
        return 0.0
    k = max(1, int(len(frame) * fraction))
    return float(frame.head(k)["y"].mean() / frame["y"].mean())


def metrics_at_threshold(
    model_name: str,
    y_true: np.ndarray,
    scores: np.ndarray,
    threshold: float,
    train_size: int,
) -> ModelMetrics:
    pred = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    return ModelMetrics(
        model_name=model_name,
        roc_auc=float(roc_auc_score(y_true, scores)),
        ks=ks_statistic(y_true, scores),
        average_precision=float(average_precision_score(y_true, scores)),
        precision=float(precision_score(y_true, pred, zero_division=0)),
        recall=float(recall_score(y_true, pred, zero_division=0)),
        f1=float(f1_score(y_true, pred, zero_division=0)),
        false_positive_rate=float(fp / max(fp + tn, 1)),
        threshold=float(threshold),
        lift_top_10=lift_at_fraction(y_true, scores, 0.10),
        train_size=int(train_size),
        test_size=int(len(y_true)),
    )


def choose_threshold(
    y_true: np.ndarray,
    scores: np.ndarray,
    thresholds: list[float],
    minimum_precision: float = 0.50,
    minimum_recall: float = 0.05,
    max_alert_rate: float = 0.05,
) -> float:
    candidates = []
    for threshold in thresholds:
        pred = scores >= threshold
        alert_rate = float(pred.mean())
        precision = precision_score(y_true, pred, zero_division=0)
        recall = recall_score(y_true, pred, zero_division=0)
        f1 = f1_score(y_true, pred, zero_division=0)
        feasible = precision >= minimum_precision and recall >= minimum_recall and alert_rate <= max_alert_rate
        score = f1 + 0.15 * precision + 0.10 * recall - 0.15 * max(alert_rate - max_alert_rate, 0)
        candidates.append((feasible, score, threshold))
    candidates.sort(reverse=True)
    return float(candidates[0][2])
