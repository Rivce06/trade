from __future__ import annotations

import pandas as pd

from backtest.validation.walk_forward import walk_forward_split


def test_walk_forward_splits_are_chronological_and_non_overlapping() -> None:
    frame = pd.DataFrame(
        {"close": range(20)},
        index=pd.date_range("2024-01-01", periods=20, freq="D", name="date"),
    )

    splits = walk_forward_split(frame, n_splits=2, train_ratio=0.5)

    assert len(splits) == 2
    for train, test in splits:
        assert train.index.max() < test.index.min()
        assert len(train) > 0
        assert len(test) > 0
