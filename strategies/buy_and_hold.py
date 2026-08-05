"""Buy-and-hold baseline strategy."""

from __future__ import annotations

import pandas as pd

from strategies.base import Strategy


class BuyAndHold(Strategy):
    """Allocate 100% to the first required symbol on the first date."""

    name = "buy_and_hold"
    required_symbols = ["SPY"]
    param_grid = {
        "target_symbol": ["SPY", "GLD"],
        "allocation": [1.0],
    }

    def generate_weights(
        self,
        data: dict[str, pd.DataFrame],
        memo: object | None = None,
    ) -> pd.Series:
        """Return a one-shot 100% weight to the selected target symbol."""

        spans: list[tuple[pd.Timestamp, str]] = []
        symbol = str(self.params.get("target_symbol", self.required_symbols[0]))
        allocation = float(self.params.get("allocation", 1.0))
        frame = data[symbol]
        dates = frame.index
        for date_value in dates:
            spans.append((pd.Timestamp(date_value), symbol))
        weights = pd.Series(allocation, index=pd.MultiIndex.from_tuples(spans, names=["date", "symbol"]))
        return weights
