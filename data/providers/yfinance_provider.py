"""yfinance-backed data provider implementation for QuantDesk."""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from data.schemas import validate_ohlcv_frame
from data.providers.base import DataProvider


class YFinanceProvider(DataProvider):
    """Fetch OHLCV data using `yfinance`'s download API."""

    def __init__(self, client: Any | None = None) -> None:
        self.client = client or __import__("yfinance")

    def get_history(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Fetch a single symbol from yfinance and normalize the schema."""

        payload = self.client.download(
            ticker=symbol,
            start=start.isoformat(),
            end=end.isoformat(),
            interval=interval,
        )
        frame = payload.copy()
        if hasattr(frame, "columns") and len(frame.columns) > 0:
            frame.columns = [str(col).lower() for col in frame.columns]
            frame = frame.rename(
                columns={
                    "open": "open",
                    "high": "high",
                    "low": "low",
                    "close": "close",
                    "volume": "volume",
                }
            )
        if not {"open", "high", "low", "close", "volume"}.issubset(frame.columns):
            frame = frame.rename(
                columns={
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Volume": "volume",
                }
            )
        normalized = validate_ohlcv_frame(frame)
        normalized = normalized.loc[normalized.index <= pd.Timestamp(end)]
        return normalized

    def get_multiple(
        self,
        symbols: list[str],
        start: date,
        end: date,
        interval: str = "1d",
    ) -> dict[str, pd.DataFrame]:
        """Fetch multiple symbols and return a mapping keyed by symbol."""

        return {
            symbol: self.get_history(symbol=symbol, start=start, end=end, interval=interval)
            for symbol in symbols
        }
