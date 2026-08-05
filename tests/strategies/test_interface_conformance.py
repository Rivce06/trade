from __future__ import annotations

import pandas as pd

from strategies.registry import STRATEGY_REGISTRY
from tests.conftest import make_ohlcv


def test_every_registered_strategy_returns_safe_weights() -> None:
    data = {
        "SPY": make_ohlcv("SPY", start=pd.Timestamp("2024-01-01").date(), periods=12),
        "GLD": make_ohlcv("GLD", start=pd.Timestamp("2024-01-01").date(), periods=12),
    }

    for strategy_cls in STRATEGY_REGISTRY.values():
        strategy = strategy_cls()
        weights = strategy.generate_weights(data)
        assert isinstance(weights, pd.Series)
        assert weights.index.nlevels == 2
        assert weights.notna().all()
        assert weights.between(0.0, 1.0).all()
        assert weights.sum() >= 0.0
