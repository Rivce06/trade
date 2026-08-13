from __future__ import annotations

import pandas as pd

from backtest.runner import run_backtest
from backtest.schemas import BacktestConfig
from strategies.buy_and_hold import BuyAndHold
from strategies.ma_crossover import MovingAverageCrossover


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
            index=pd.date_range(
                "2024-01-01",
                periods=5,
                freq="D",
                name="date",
            ),
        )
    }

    config = BacktestConfig(
        start="2024-01-01",
        end="2024-01-05",
        initial_capital=1000.0,
        commission_bps=0.0,
        slippage_bps=0.0,
    )

    result = run_backtest(
        strategy=BuyAndHold(),
        data=data,
        config=config,
    )

    assert result.metrics["max_dd"] == 0.0


def test_commission_reduces_returns_for_trading_strategy() -> None:
    """Commission should reduce returns when the strategy actually trades."""

    dates = pd.date_range(
        "2024-01-01",
        periods=30,
        freq="D",
        name="date",
    )

    # Deliberately alternating price trend.
    # This causes the 3-day SMA to repeatedly move above and below
    # the 5-day SMA, producing multiple position changes.
    prices = [
        100,
        101,
        102,
        103,
        104,
        105,
        104,
        103,
        102,
        101,
        100,
        99,
        98,
        99,
        100,
        101,
        102,
        103,
        104,
        105,
        104,
        103,
        102,
        101,
        100,
        99,
        98,
        99,
        100,
        101,
    ]

    data = {
        "SPY": pd.DataFrame(
            {
                "open": prices,
                "high": [price + 0.5 for price in prices],
                "low": [price - 0.5 for price in prices],
                "close": prices,
                "volume": [1000] * len(prices),
            },
            index=dates,
        )
    }

    strategy = MovingAverageCrossover()

    config_free = BacktestConfig(
        start="2024-01-01",
        end="2024-01-30",
        initial_capital=1000.0,
        commission_bps=0.0,
        slippage_bps=0.0,
    )

    config_costly = BacktestConfig(
        start="2024-01-01",
        end="2024-01-30",
        initial_capital=1000.0,
        commission_bps=50.0,
        slippage_bps=0.0,
    )

    result_free = run_backtest(
        strategy=strategy,
        data=data,
        config=config_free,
    )

    result_costly = run_backtest(
        strategy=strategy,
        data=data,
        config=config_costly,
    )

    assert result_costly.metrics["cagr"] < result_free.metrics["cagr"]