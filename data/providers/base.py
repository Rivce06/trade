"""Abstract interfaces for market data providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

import pandas as pd


class DataProvider(ABC):
    """Abstract base class for all market-data providers."""

    @abstractmethod
    def get_history(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Return a normalized OHLCV history for one symbol.

        Args:
            symbol: The ticker symbol to fetch.
            start: Inclusive start date.
            end: Inclusive end date.
            interval: Bar interval string.

        Returns:
            pd.DataFrame: A price frame with columns
            `open`, `high`, `low`, `close`, and `volume`.
        """

    @abstractmethod
    def get_multiple(
        self,
        symbols: list[str],
        start: date,
        end: date,
        interval: str = "1d",
    ) -> dict[str, pd.DataFrame]:
        """Return a normalized OHLCV history for multiple symbols."""
