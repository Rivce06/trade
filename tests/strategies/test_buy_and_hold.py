from __future__ import annotations

import pandas as pd

from strategies.buy_and_hold import BuyAndHold
from tests.conftest import make_ohlcv


def test_buy_and_hold_weights_are_unitized() -> None:
    data = {
        "SPY": make_ohlcv("SPY", start=pd.Timestamp("2024-01-01").date(), periods=12),
    }
    weights = BuyAndHold().generate_weights(data)

    assert weights.index.nlevels == 2
    assert weights.notna().all()
    assert weights.loc[(weights.index.get_level_values(0)[0], "SPY")] == 1.0
