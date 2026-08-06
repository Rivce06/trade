"""Regime-based deleveraging overlay for QuantDesk."""

from __future__ import annotations

import pandas as pd


def apply_regime_deleverage(
    weights: pd.Series,
    regime_labels: pd.Series,
    deleverage_map: dict[str, float],
) -> pd.Series:
    """Reduce exposure for dates whose regime is flagged for deleveraging."""

    scaled = weights.copy()
    normalized_dates = [pd.Timestamp(date_value) for date_value in regime_labels.index]
    for date_value, regime in zip(normalized_dates, regime_labels.tolist(), strict=False):
        if regime not in deleverage_map:
            continue
        factor = deleverage_map[regime]
        date_mask = scaled.index.get_level_values(0).astype("datetime64[ns]") == date_value
        scaled.loc[date_mask] = scaled.loc[date_mask] * factor
    return scaled
