from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class TemporalSplit:
    """A deterministic chronological train/development/out-of-time split."""

    train: pd.DataFrame
    dev: pd.DataFrame
    oot: pd.DataFrame
    time_column: str

    def summary(self) -> dict[str, object]:
        def describe(frame: pd.DataFrame) -> dict[str, object]:
            timestamps = pd.to_datetime(frame[self.time_column], errors="coerce")
            return {
                "rows": int(len(frame)),
                "start": timestamps.min().isoformat() if timestamps.notna().any() else None,
                "end": timestamps.max().isoformat() if timestamps.notna().any() else None,
            }

        return {
            "method": "chronological_train_dev_oot",
            "train": describe(self.train),
            "dev": describe(self.dev),
            "oot": describe(self.oot),
        }


def chronological_train_dev_oot_split(
    data: pd.DataFrame,
    time_column: str,
    train_fraction: float = 0.60,
    dev_fraction: float = 0.20,
) -> TemporalSplit:
    """Split rows once, chronologically, without allowing OOT rows into model selection.

    The original index is retained in ``_original_index`` so model scores can later be attached
    to the exact source rows. A stable sort makes repeated runs deterministic when timestamps tie.
    """

    if time_column not in data:
        raise KeyError(f"time column {time_column!r} not found")
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1")
    if not 0 < dev_fraction < 1:
        raise ValueError("dev_fraction must be between 0 and 1")
    if train_fraction + dev_fraction >= 1:
        raise ValueError("train_fraction + dev_fraction must be less than 1")
    if len(data) < 15:
        raise ValueError("at least 15 rows are required for a train/dev/OOT split")
    if not data.index.is_unique:
        raise ValueError("data index must be unique for score alignment")

    frame = data.copy()
    timestamps = pd.to_datetime(frame[time_column], errors="coerce")
    if timestamps.isna().any():
        raise ValueError(f"time column {time_column!r} contains missing or invalid timestamps")
    frame[time_column] = timestamps
    frame["_original_index"] = frame.index
    frame["_split_order"] = range(len(frame))
    frame = (
        frame.sort_values([time_column, "_split_order"], kind="mergesort")
        .drop(columns="_split_order")
        .reset_index(drop=True)
    )

    train_end = max(1, int(len(frame) * train_fraction))
    dev_end = max(train_end + 1, int(len(frame) * (train_fraction + dev_fraction)))
    dev_end = min(dev_end, len(frame) - 1)
    train = frame.iloc[:train_end].copy()
    dev = frame.iloc[train_end:dev_end].copy()
    oot = frame.iloc[dev_end:].copy()
    if train.empty or dev.empty or oot.empty:
        raise ValueError("train, dev, and OOT splits must all be non-empty")

    return TemporalSplit(train=train, dev=dev, oot=oot, time_column=time_column)
