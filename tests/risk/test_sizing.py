from __future__ import annotations

import pandas as pd

from risk.sizing import apply_position_caps


def test_apply_position_caps_clips_exact_and_over_capacity() -> None:
    weights = pd.Series(
        {("2024-01-01", "SPY"): 0.9, ("2024-01-01", "GLD"): 0.2},
        name="weight",
    )
    weights.index = pd.MultiIndex.from_tuples(weights.index, names=["date", "symbol"])

    capped = apply_position_caps(weights, max_position=0.8, max_gross_exposure=1.0)

    assert capped.loc[("2024-01-01", "SPY")] <= 0.8
    assert capped.loc[("2024-01-01", "GLD")] <= 0.8
