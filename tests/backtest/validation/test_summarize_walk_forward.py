from __future__ import annotations

import pandas as pd

from backtest.schemas import BacktestConfig
from backtest.validation.summarize import summarize_walk_forward
from strategies.base import Strategy
from tests.conftest import make_ohlcv


class RegimeDependentStrategy(Strategy):
    name = "regime_dependent"

    def generate_weights(self, data: dict[str, pd.DataFrame], memo: object | None = None) -> pd.Series:
        dates = list(data["SPY"].index)
        weights: list[tuple[tuple[pd.Timestamp, str], float]] = []
        for idx, date_value in enumerate(dates):
            if idx < len(dates) // 2:
                weight = 0.0
            else:
                weight = 1.0
            weights.append(((date_value, "SPY"), weight))
        return pd.Series([weight for _, weight in weights], index=pd.MultiIndex.from_tuples([key for key, _ in weights], names=["date", "symbol"]))


def test_summarize_walk_forward_detects_regime_shift_instability() -> None:
    data = {"SPY": make_ohlcv("SPY", start=pd.Timestamp("2024-01-01").date(), periods=80)}
    config = BacktestConfig(start="2024-01-01", end="2024-03-21", initial_capital=1000.0)

    summary = summarize_walk_forward(
        strategy=RegimeDependentStrategy(),
        data=data,
        config=config,
        n_splits=4,
        train_ratio=0.5,
    )

    assert summary.n_splits == 4
    assert len(summary.per_split_metrics) >= 2
    assert summary.test_sharpe_std > 0.0
    assert summary.test_sharpe_mean > 0.0
