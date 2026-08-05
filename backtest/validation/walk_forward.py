"""Walk-forward validation helpers."""

from __future__ import annotations

import pandas as pd


def walk_forward_split(
    data: pd.DataFrame,
    n_splits: int,
    train_ratio: float,
) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
    """Create chronological train/test pairs without overlap.

    Args:
        data: A date-indexed data frame.
        n_splits: Number of train/test windows to produce.
        train_ratio: Fraction of the dataset used for training in each split.

    Returns:
        list[tuple[pd.DataFrame, pd.DataFrame]]: Chronological split windows.
    """

    if n_splits <= 0:
        raise ValueError("n_splits must be positive")
    if not 0.0 < train_ratio < 1.0:
        raise ValueError("train_ratio must be strictly between 0 and 1")

    frame = data.sort_index()
    total = len(frame)
    train_size = max(1, int(total * train_ratio))
    step = max(1, total // (n_splits + 1))
    splits: list[tuple[pd.DataFrame, pd.DataFrame]] = []

    for split_idx in range(n_splits):
        start = split_idx * step
        train_end = start + train_size
        test_end = min(train_end + step, total)
        train_slice = frame.iloc[start:train_end]
        test_slice = frame.iloc[train_end:test_end]
        if len(train_slice) == 0 or len(test_slice) == 0:
            continue
        splits.append((train_slice, test_slice))

    return splits
