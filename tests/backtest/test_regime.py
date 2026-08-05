from __future__ import annotations

import pandas as pd

from backtest.validation.regime import segment_by_regime


def test_regime_segmenter_flags_volatility_spike() -> None:
    dates = pd.date_range("2024-01-01", periods=8, freq="D", name="date")
    close = [100.0, 100.2, 99.9, 100.1, 100.0, 101.0, 102.0, 105.0]
    frame = pd.DataFrame({"close": close}, index=dates)

    labels = segment_by_regime(frame, method="realized_vol")

    assert labels.index.name == "date"
    assert labels.isna().sum() == 0
