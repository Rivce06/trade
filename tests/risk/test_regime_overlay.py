from __future__ import annotations

import pandas as pd

from risk.regime_overlay import apply_regime_deleverage


def test_regime_deleverage_only_hits_flagged_periods() -> None:
    weights = pd.Series(
        {
            ("2024-01-01", "SPY"): 0.6,
            ("2024-01-01", "GLD"): 0.4,
            ("2024-01-02", "SPY"): 0.7,
            ("2024-01-02", "GLD"): 0.3,
        },
        name="weight",
    )
    weights.index = pd.MultiIndex.from_tuples(weights.index, names=["date", "symbol"])
    regimes = pd.Series(["volatile", "normal"], index=pd.to_datetime(["2024-01-01", "2024-01-02"]), name="regime")

    adjusted = apply_regime_deleverage(weights, regimes, {"volatile": 0.5})

    assert adjusted.loc[("2024-01-01", "SPY")] < 0.6
    assert adjusted.loc[("2024-01-02", "SPY")] == 0.7
