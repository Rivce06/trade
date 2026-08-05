"""Abstract strategy interface for baseline QuantDesk strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class Strategy(ABC):
    """Abstract interface for all allocation strategies."""

    name: str = "base"
    required_symbols: list[str] = []
    param_grid: dict[str, list[object]] = {}

    def __init__(self, **kwargs: object) -> None:
        """Populate a strategy instance with optimizer-friendly defaults."""
        self.params: dict[str, object] = {}
        for key, choices in self.param_grid.items():
            self.params[key] = choices[0]
        for key, value in kwargs.items():
            self.params[key] = value

    @abstractmethod
    def generate_weights(
        self,
        data: dict[str, pd.DataFrame],
        memo: object | None = None,
    ) -> pd.Series:
        """Return point-in-time-safe target weights for the provided data.

        Args:
            data: Mapping of symbol to OHLCV price data frames.
            memo: Optional research memo; advisory-only and not required.

        Returns:
            pd.Series: A series indexed by `(date, symbol)` whose values are
            bounded target weights.
        """
