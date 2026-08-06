"""yfinance-backed data provider implementation for QuantDesk."""

from __future__ import annotations

import inspect
from datetime import date
from typing import Any

import pandas as pd

from data.providers.base import DataProvider
from data.schemas import validate_ohlcv_frame


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
        download = self.client.download
        params = inspect.signature(download).parameters

        kwargs: dict[str, Any] = {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "interval": interval,
        }

        if "tickers" in params:
            kwargs["tickers"] = symbol
        elif "ticker" in params:
            kwargs["ticker"] = symbol
        else:
            kwargs["tickers"] = symbol

        payload = download(**kwargs)
        frame = payload.copy()

        # Handle yfinance MultiIndex columns (e.g., ('Close', 'SPY') -> 'Close')
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = frame.columns.get_level_values(0)

        # Normalize column names
        frame.columns = [str(col).lower() for col in frame.columns]

        # Remove duplicated columns if yfinance creates them
        frame = frame.loc[:, ~frame.columns.duplicated()]

        required_columns = {
            "open",
            "high",
            "low",
            "close",
            "volume",
        }

        # Validate schema
        if not required_columns.issubset(frame.columns):
            missing = required_columns.difference(frame.columns)
            raise ValueError(
                f"Missing required OHLCV columns after normalization: {sorted(missing)}. "
                f"Received columns: {list(frame.columns)}"
            )

        normalized = validate_ohlcv_frame(frame)

        # Protect against accidental future data
        normalized = normalized.loc[
            normalized.index <= pd.Timestamp(end)
        ]

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
            symbol: self.get_history(
                symbol=symbol, start=start, end=end, interval=interval
            )
            for symbol in symbols
        }