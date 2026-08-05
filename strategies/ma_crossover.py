"""Moving-average trend baseline strategy."""

from __future__ import annotations

import pandas as pd

from strategies.base import Strategy


class MovingAverageCrossover(Strategy):
    """Allocate 100% to SPY when the short SMA exceeds the long SMA."""

    name = "ma_crossover"
    required_symbols = ["SPY"]
    param_grid = {
        "short_window": [2, 3, 5],
        "long_window": [5, 7, 10],
    }

    def generate_weights(
        self,
        data: dict[str, pd.DataFrame],
        memo: object | None = None,
    ) -> pd.Series:
        """Return a bounded one-symbol trend allocation using rolling means."""

        frame = data[self.required_symbols[0]].copy()
        frame = frame.sort_index()
        short_window = int(self.params.get("short_window", 3))
        long_window = int(self.params.get("long_window", 5))
        short = frame["close"].rolling(window=short_window).mean()
        long = frame["close"].rolling(window=long_window).mean()
        signal = short > long
        index = pd.MultiIndex.from_product(
            [frame.index, [self.required_symbols[0]]],
            names=["date", "symbol"],
        )
        weight_values = [1.0 if bool(signal.loc[date]) else 0.0 for date in frame.index]
        return pd.Series(weight_values, index=index)
