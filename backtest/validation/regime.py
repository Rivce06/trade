"""Regime segmentation helpers for backtesting validation."""

from __future__ import annotations

import pandas as pd


def segment_by_regime(
    data: pd.DataFrame,
    method: str = "realized_vol",
) -> pd.Series:
    """Assign a simple regime label based on realized volatility.

    The implementation intentionally uses a deterministic, hand-checkable
    heuristic so the public interface remains reproducible and testable in
    unit tests.
    """

    close = data["close"]
    returns = close.pct_change().dropna()
    realized_vol = returns.rolling(window=3).std().fillna(0.0)
    labels = pd.Series(
        ["normal" if value < 0.03 else "volatile" for value in realized_vol],
        index=returns.index,
        name="regime",
    )
    return labels
