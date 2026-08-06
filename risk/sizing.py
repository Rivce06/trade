"""Position sizing and exposure-cap utilities for QuantDesk."""

from __future__ import annotations

import pandas as pd


def apply_position_caps(
    weights: pd.Series,
    max_position: float,
    max_gross_exposure: float,
) -> pd.Series:
    """Clip weights to the allowed position range and gross exposure budget.

    The implementation is deterministic and designed for unit-testable
    position-scaling logic.
    """

    clipped = weights.clip(lower=0.0, upper=max_position)
    gross = clipped.groupby(level=0).sum()
    if (gross > max_gross_exposure).any():
        clipped = clipped / gross
    return clipped
