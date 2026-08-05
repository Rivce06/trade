from __future__ import annotations

from datetime import date, timedelta

import pandas as pd


def make_ohlcv(symbol: str, start: date, periods: int = 10, seed: int = 0) -> pd.DataFrame:
    """Build a tiny deterministic OHLCV fixture for strategy and provider tests."""
    idx = pd.date_range(start=start, periods=periods, freq="D")
    base = pd.Series(range(periods), index=idx)
    close = 100 + base * 0.5 + seed
    data = pd.DataFrame(
        {
            "open": close - 0.5,
            "high": close + 0.6,
            "low": close - 0.7,
            "close": close,
            "volume": 1000 + base * 10,
        },
        index=idx,
    )
    data.index.name = "date"
    data.columns = ["open", "high", "low", "close", "volume"]
    data = data.rename_axis("date")
    return data
