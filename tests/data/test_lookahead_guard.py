from __future__ import annotations

from datetime import date

import pandas as pd

from data.providers.yfinance_provider import YFinanceProvider


class GuardedYFinanceClient:
    def download(self, tickers: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
        idx = pd.date_range(start=start, end=end, freq="D", name="date")
        data = pd.DataFrame(
            {
                "Open": range(len(idx)),
                "High": range(len(idx)),
                "Low": range(len(idx)),
                "Close": range(len(idx)),
                "Volume": [1000] * len(idx),
            },
            index=idx,
        )
        return data


def test_provider_never_returns_bar_after_requested_end() -> None:
    provider = YFinanceProvider(client=GuardedYFinanceClient())
    result = provider.get_history("SPY", date(2024, 1, 1), date(2024, 1, 3))
    assert result.index.max().date() <= date(2024, 1, 3)
