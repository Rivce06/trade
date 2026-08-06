from __future__ import annotations

import pandas as pd

from backtest.runner import run_backtest
from strategies.buy_and_hold import BuyAndHold
from backtest.schemas import BacktestConfig


def test_run_backtest_returns_zero_drawdown_for_no_trade_strategy() -> None:
    data = {
        "SPY": pd.DataFrame(
            {
                "open": [100.0] * 5,
                "high": [100.0] * 5,
                "low": [100.0] * 5,
                "close": [100.0] * 5,
                "volume": [1000] * 5,
            },
            index=pd.date_range("2024-01-01", periods=5, freq="D", name="date"),
        )
    }
    config = BacktestConfig(
        start="2024-01-01",
        end="2024-01-05",
        initial_capital=1000.0,
        commission_bps=0.0,
        slippage_bps=0.0,
    )

    result = run_backtest(strategy=BuyAndHold(), data=data, config=config)
    assert result.metrics["max_dd"] == 0.0
