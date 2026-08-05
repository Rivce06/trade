from __future__ import annotations

import pandas as pd

from backtest.validation.walk_forward import walk_forward_split


def test_no_lookahead_guard_rejects_future_data() -> None:
    frame = pd.DataFrame(
        {"close": [1, 2, 3, 4]},
        index=pd.date_range("2024-01-01", periods=4, freq="D", name="date"),
    )

    train, test = walk_forward_split(frame, n_splits=1, train_ratio=0.5)[0]
    assert train.index.max() < test.index.min()
