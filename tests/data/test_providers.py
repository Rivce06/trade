from __future__ import annotations

from datetime import date

import pandas as pd

from data.providers.base import DataProvider
from data.providers.yfinance_provider import YFinanceProvider


class DummyYFinanceClient:
    def __init__(self, payload: pd.DataFrame) -> None:
        self.payload = payload
        self.calls: list[tuple[str, str, str, str]] = []

    def download(self, ticker: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
        self.calls.append((ticker, start, end, interval))
        return self.payload.copy()


def test_yfinance_provider_schema_conformance() -> None:
    payload = pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [101.0, 102.0],
            "Low": [99.0, 100.0],
            "Close": [100.5, 101.5],
            "Volume": [1000, 1100],
        },
        index=pd.date_range("2024-01-01", periods=2, freq="D", name="date"),
    )
    client = DummyYFinanceClient(payload)
    provider = YFinanceProvider(client=client)

    result = provider.get_history("SPY", date(2024, 1, 1), date(2024, 1, 2))

    assert list(result.columns) == ["open", "high", "low", "close", "volume"]
    assert result.index.name == "date"
    assert len(result) == 2
    assert client.calls[0][0] == "SPY"


def test_provider_interface_is_abstract() -> None:
    assert issubclass(DataProvider, object)
