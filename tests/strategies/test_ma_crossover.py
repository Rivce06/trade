from __future__ import annotations

import pandas as pd

from strategies.ma_crossover import MovingAverageCrossover
from tests.conftest import make_ohlcv


def test_ma_crossover_weights_stay_bounded() -> None:
    data = {
        "SPY": make_ohlcv("SPY", start=pd.Timestamp("2024-01-01").date(), periods=12),
    }
    weights = MovingAverageCrossover().generate_weights(data)

    assert weights.notna().all()
    assert weights.between(0.0, 1.0).all()
