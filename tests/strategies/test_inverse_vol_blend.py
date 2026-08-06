from __future__ import annotations

import pandas as pd

from strategies.inverse_vol_blend import InverseVolatilityBlend
from tests.conftest import make_ohlcv


def test_inverse_vol_blend_weights_sum_to_one() -> None:
    data = {
        "SPY": make_ohlcv("SPY", start=pd.Timestamp("2024-01-01").date(), periods=12),
        "GLD": make_ohlcv("GLD", start=pd.Timestamp("2024-01-01").date(), periods=12),
    }
    weights = InverseVolatilityBlend().generate_weights(data)

    assert weights.notna().all()
    assert weights.index.nlevels == 2
    assert weights.groupby(level=0).sum().sub(1.0).abs().max() < 1e-9
