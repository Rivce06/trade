"""Backtest runner for deterministic validation experiments."""

from __future__ import annotations

from typing import Literal

import pandas as pd
import quantstats as qs

from backtest.schemas import BacktestConfig, BacktestResult
from strategies.base import Strategy


def run_backtest(
    strategy: Strategy,
    data: dict[str, pd.DataFrame],
    config: BacktestConfig,
    engine: Literal["backtesting_py", "vectorbt"] = "vectorbt",
) -> BacktestResult:
    """Run a weight-driven backtest and return a result envelope."""

    if len(data) == 0:
        raise ValueError("data must contain at least one symbol")

    weights = strategy.generate_weights(data)  # MultiIndex (date, symbol)

    returns_by_symbol = {
        symbol: df["close"].pct_change().rename(symbol)
        for symbol, df in data.items()
    }
    returns_df = pd.concat(returns_by_symbol.values(), axis=1)

    weights_df = weights.unstack("symbol").reindex(returns_df.index).fillna(0.0)
    weights_shifted = weights_df.shift(1).fillna(0.0)

    portfolio_returns = (weights_shifted * returns_df).sum(axis=1).fillna(0.0)
    equity_curve = config.initial_capital * (1.0 + portfolio_returns).cumprod()
    equity_curve.name = "equity"

    gains = portfolio_returns[portfolio_returns > 0].sum()
    losses = -portfolio_returns[portfolio_returns < 0].sum()

    metrics = {
        "cagr": float(qs.stats.cagr(portfolio_returns)),
        "sharpe": float(qs.stats.sharpe(portfolio_returns)),
        "sortino": float(qs.stats.sortino(portfolio_returns)),
        "max_dd": float(qs.stats.max_drawdown(equity_curve)),
        "calmar": float(qs.stats.calmar(portfolio_returns)),
        "win_rate": float((portfolio_returns > 0).mean()) if len(portfolio_returns) else 0.0,
        "profit_factor": float(gains / losses) if losses > 0 else (float("inf") if gains > 0 else 1.0),
    }

    trades = pd.DataFrame({"symbol": list(data.keys())})

    return BacktestResult(
        equity_curve=equity_curve,
        trades=trades,
        metrics=metrics,
        config_used=config,
    )
