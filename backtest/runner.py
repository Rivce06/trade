"""Backtest runner for deterministic validation experiments."""

from __future__ import annotations

from typing import Literal

import pandas as pd

from backtest.schemas import BacktestConfig, BacktestResult
from strategies.base import Strategy


def run_backtest(
    strategy: Strategy,
    data: dict[str, pd.DataFrame],
    config: BacktestConfig,
    engine: Literal["backtesting_py", "vectorbt"] = "vectorbt",
) -> BacktestResult:
    """Run a faux deterministic backtest and return a result envelope.

    This Phase 2 implementation intentionally stays model- and broker-free.
    The runner is a stable, testable contract that returns a small result
    envelope suitable for validation and run-card generation.
    """

    if len(data) == 0:
        raise ValueError("data must contain at least one symbol")

    weights = strategy.generate_weights(data)
    equity_curve = pd.Series(
        [config.initial_capital] * len(next(iter(data.values())).index),
        index=next(iter(data.values())).index,
        name="equity",
    )
    trades = pd.DataFrame({"symbol": [next(iter(data.keys()))]})
    metrics = {
        "cagr": 0.0,
        "sharpe": 0.0,
        "sortino": 0.0,
        "max_dd": 0.0,
        "calmar": 0.0,
        "win_rate": 1.0,
        "profit_factor": 1.0,
    }
    return BacktestResult(
        equity_curve=equity_curve,
        trades=trades,
        metrics=metrics,
        config_used=config,
    )
