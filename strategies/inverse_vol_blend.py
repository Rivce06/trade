"""Inverse-volatility multi-asset baseline strategy for SPY/GLD."""

from __future__ import annotations

import pandas as pd

from strategies.base import Strategy


class InverseVolatilityBlend(Strategy):
    """Allocate weights inversely to each symbol's rolling volatility."""

    name = "inverse_vol_blend"
    required_symbols = ["SPY", "GLD"]
    param_grid = {
        "vol_window": [2, 3, 5],
    }

    def generate_weights(
        self,
        data: dict[str, pd.DataFrame],
        memo: object | None = None,
    ) -> pd.Series:
        """Return a normalized inverse-volatility allocation over SPY and GLD."""

        frames = {symbol: data[symbol].copy() for symbol in self.required_symbols}
        vol_window = int(self.params.get("vol_window", 3))
        vol_map: dict[str, float] = {}
        for symbol, frame in frames.items():
            returns = frame["close"].pct_change().dropna()
            vol = returns.rolling(window=vol_window).std().fillna(0.0)
            vol_map[symbol] = float(vol.iloc[-1]) if len(vol) > 0 else 0.0
        inv = {symbol: 1.0 / max(vol, 1e-9) for symbol, vol in vol_map.items()}
        total = sum(inv.values())
        weights = {symbol: inv[symbol] / total for symbol in self.required_symbols}

        dates = frames[self.required_symbols[0]].index
        rows: list[tuple[pd.Timestamp, str, float]] = []
        for date_value in dates:
            for symbol in self.required_symbols:
                rows.append((pd.Timestamp(date_value), symbol, weights[symbol]))

        index = pd.MultiIndex.from_tuples(
            [(date, symbol) for date, symbol, _ in rows],
            names=["date", "symbol"],
        )
        result = pd.Series([value for _, _, value in rows], index=index)

        normalized = result.groupby(level=0).transform(lambda values: values / values.sum())
        return normalized
