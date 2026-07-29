from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.metrics import roc_auc_score, roc_curve

from ..models.temporal import chronological_train_dev_oot_split
from ..schemas import FeatureProfile


def _safe_auc(y: pd.Series, x: pd.Series) -> float | None:
    mask = x.notna() & y.notna()
    if mask.sum() < 30 or y[mask].nunique() < 2 or x[mask].nunique() < 2:
        return None
    auc = roc_auc_score(y[mask], x[mask])
    return float(max(auc, 1 - auc))


def _ks(y: pd.Series, x: pd.Series) -> float | None:
    mask = x.notna() & y.notna()
    if mask.sum() < 30 or y[mask].nunique() < 2 or x[mask].nunique() < 2:
        return None
    fpr, tpr, _ = roc_curve(y[mask], x[mask])
    return float(np.max(np.abs(tpr - fpr)))


def _lift_top(y: pd.Series, score: pd.Series, fraction: float = 0.10) -> float | None:
    mask = score.notna() & y.notna()
    if mask.sum() < 30 or y[mask].mean() == 0:
        return None
    temp = pd.DataFrame({"y": y[mask], "score": score[mask]}).sort_values("score", ascending=False)
    k = max(1, int(len(temp) * fraction))
    return float(temp.head(k)["y"].mean() / temp["y"].mean())


def _iv_numeric(y: pd.Series, x: pd.Series, bins: int = 10) -> float | None:
    mask = x.notna() & y.notna()
    if mask.sum() < 50 or y[mask].nunique() < 2 or x[mask].nunique() < 3:
        return None
    try:
        bucket = pd.qcut(x[mask], q=min(bins, x[mask].nunique()), duplicates="drop")
    except ValueError:
        return None
    table = pd.crosstab(bucket, y[mask])
    for col in [0, 1]:
        if col not in table:
            table[col] = 0
    good = table[0].astype(float) + 0.5
    bad = table[1].astype(float) + 0.5
    good_dist = good / good.sum()
    bad_dist = bad / bad.sum()
    woe = np.log(bad_dist / good_dist)
    iv = ((bad_dist - good_dist) * woe).sum()
    return float(max(0, iv))


def _cramer_v(y: pd.Series, x: pd.Series) -> float | None:
    mask = x.notna() & y.notna()
    if mask.sum() < 30 or x[mask].nunique() < 2 or y[mask].nunique() < 2:
        return None
    table = pd.crosstab(x[mask], y[mask])
    chi2 = chi2_contingency(table, correction=False)[0]
    n = table.values.sum()
    phi2 = chi2 / max(n, 1)
    r, k = table.shape
    phi2_corr = max(0, phi2 - ((k - 1) * (r - 1)) / max(n - 1, 1))
    r_corr = r - ((r - 1) ** 2) / max(n - 1, 1)
    k_corr = k - ((k - 1) ** 2) / max(n - 1, 1)
    denom = max(min(k_corr - 1, r_corr - 1), 1e-12)
    return float(math.sqrt(phi2_corr / denom))


def _psi(expected: pd.Series, actual: pd.Series, bins: int = 10) -> float | None:
    expected = expected.dropna()
    actual = actual.dropna()
    if len(expected) < 50 or len(actual) < 50 or expected.nunique() < 3:
        return None
    try:
        quantiles = np.unique(expected.quantile(np.linspace(0, 1, bins + 1)).values)
        if len(quantiles) < 3:
            return None
        quantiles[0], quantiles[-1] = -np.inf, np.inf
        e = pd.cut(expected, quantiles, include_lowest=True).value_counts(normalize=True, sort=False)
        a = pd.cut(actual, quantiles, include_lowest=True).value_counts(normalize=True, sort=False)
        e = e.reindex(e.index, fill_value=0).clip(lower=1e-6)
        a = a.reindex(e.index, fill_value=0).clip(lower=1e-6)
        return float(((a - e) * np.log(a / e)).sum())
    except (ValueError, TypeError):
        return None


@dataclass
class FeatureProfiler:
    target: str = "fraud_label"
    time_column: str = "event_date"

    def profile(
        self,
        data: pd.DataFrame,
        feature_names: Iterable[str] | None = None,
        train_fraction: float = 0.60,
        dev_fraction: float = 0.20,
    ) -> list[FeatureProfile]:
        if self.target not in data:
            raise KeyError(f"target column {self.target!r} not found")
        split = chronological_train_dev_oot_split(
            data,
            time_column=self.time_column,
            train_fraction=train_fraction,
            dev_fraction=dev_fraction,
        )
        train, dev = split.train, split.dev
        excluded = {self.target, self.time_column, "user_id", "estimated_loss_amount"}
        names = list(
            feature_names
            or [c for c in data.columns if c not in excluded and not c.startswith("latent_")]
        )
        profiles: list[FeatureProfile] = []
        # Feature selection metrics are calculated on development rows only. The OOT partition is
        # deliberately not referenced until the final strategy evaluation.
        y = dev[self.target].astype(int)
        for name in names:
            if name not in dev:
                continue
            s = dev[name]
            missing = float(s.isna().mean())
            unique = int(s.nunique(dropna=True))
            notes: list[str] = ["Feature selection statistics use the development split only."]
            if pd.api.types.is_numeric_dtype(s) or pd.api.types.is_bool_dtype(s):
                numeric = pd.to_numeric(s, errors="coerce")
                auc = _safe_auc(y, numeric)
                ks = _ks(y, numeric)
                iv = _iv_numeric(y, numeric)
                lift = _lift_top(y, numeric)
                psi = _psi(
                    pd.to_numeric(train[name], errors="coerce"),
                    pd.to_numeric(dev[name], errors="coerce"),
                )
                direction = "higher_risk"
                try:
                    mean_bad = numeric[y == 1].mean()
                    mean_good = numeric[y == 0].mean()
                    if mean_bad < mean_good:
                        direction = "lower_risk"
                except Exception:
                    direction = "unknown"
                recommended = bool(
                    missing < 0.40
                    and ((auc is not None and auc >= 0.58) or (ks is not None and ks >= 0.18) or (iv is not None and iv >= 0.10))
                    and (psi is None or psi < 0.25)
                )
                if psi is not None and psi >= 0.25:
                    notes.append("PSI>=0.25，存在明显时间漂移。")
                if lift is not None and lift >= 2:
                    notes.append("Top10% Lift>=2，具备策略抓手。")
                profiles.append(
                    FeatureProfile(
                        feature=name,
                        dtype="numeric",
                        missing_rate=missing,
                        unique_count=unique,
                        auc_1d=auc,
                        ks_1d=ks,
                        iv=iv,
                        lift_top_10=lift,
                        psi=psi,
                        direction=direction,
                        recommended=recommended,
                        notes=notes,
                    )
                )
            else:
                cv = _cramer_v(y, s.astype(str))
                recommended = bool(missing < 0.40 and cv is not None and cv >= 0.10)
                profiles.append(
                    FeatureProfile(
                        feature=name,
                        dtype="categorical",
                        missing_rate=missing,
                        unique_count=unique,
                        cramer_v=cv,
                        recommended=recommended,
                        notes=notes,
                    )
                )
        return sorted(
            profiles,
            key=lambda p: (
                p.recommended,
                p.auc_1d or 0,
                p.ks_1d or 0,
                p.iv or 0,
                p.cramer_v or 0,
            ),
            reverse=True,
        )

    @staticmethod
    def to_frame(profiles: list[FeatureProfile]) -> pd.DataFrame:
        return pd.DataFrame([p.model_dump() for p in profiles])
