from __future__ import annotations

import pandas as pd

from backtest.validation.summarize import summarize_regime
from tests.conftest import make_ohlcv


def test_summarize_regime_uses_all_trading_days() -> None:
    data = make_ohlcv("SPY", start=pd.Timestamp("2024-01-01").date(), periods=40)
    returns = data["close"].pct_change().dropna()
    labels = ["normal", "volatile"] * (len(returns) // 2 + 1)
    regime_labels = pd.Series(labels[: len(returns)], index=returns.index, name="regime")

    summary = summarize_regime(returns, regime_labels)

    assert sum(summary.regime_day_counts.values()) == len(returns)
    assert summary.per_regime_metrics
