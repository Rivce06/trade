from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
import quantstats as qs

from backtest.schemas import BacktestConfig
from backtest.validation.monte_carlo import monte_carlo_resample
from backtest.validation.regime import segment_by_regime
from backtest.validation.schemas import MonteCarloSummary, RegimeSummary, ValidationSummary, WalkForwardSummary
from backtest.validation.walk_forward import walk_forward_split
from strategies.base import Strategy


def _metric_payload(portfolio_returns: pd.Series, equity_curve: pd.Series) -> dict[str, float]:
    gains = portfolio_returns[portfolio_returns > 0].sum()
    losses = -portfolio_returns[portfolio_returns < 0].sum()
    return {
        "cagr": float(qs.stats.cagr(portfolio_returns)),
        "sharpe": float(qs.stats.sharpe(portfolio_returns)),
        "sortino": float(qs.stats.sortino(portfolio_returns)),
        "max_dd": float(qs.stats.max_drawdown(equity_curve)),
        "calmar": float(qs.stats.calmar(portfolio_returns)),
        "win_rate": float((portfolio_returns > 0).mean()) if len(portfolio_returns) else 0.0,
        "profit_factor": float(gains / losses) if losses > 0 else (float("inf") if gains > 0 else 1.0),
    }


def summarize_walk_forward(
    strategy: Strategy,
    data: dict[str, pd.DataFrame],
    config: BacktestConfig,
    n_splits: int,
    train_ratio: float,
) -> WalkForwardSummary:
    if not data:
        raise ValueError("data must contain at least one symbol")

    primary_symbol = next(iter(data.keys()))
    frame = data[primary_symbol]
    splits = walk_forward_split(frame, n_splits=n_splits, train_ratio=train_ratio)

    per_split_metrics: list[dict[str, float]] = []
    sharpe_values: list[float] = []
    for train_frame, test_frame in splits:
        if len(train_frame) == 0 or len(test_frame) == 0:
            continue
        train_prices = train_frame["close"]
        test_prices = test_frame["close"]
        synthetic_returns = pd.concat([train_prices.pct_change().dropna(), test_prices.pct_change().dropna()])
        if synthetic_returns.empty:
            continue
        portfolio_returns = synthetic_returns.copy()
        equity_curve = (config.initial_capital * (1.0 + portfolio_returns).cumprod()).rename("equity")
        metrics = _metric_payload(portfolio_returns, equity_curve)
        per_split_metrics.append(metrics)
        sharpe_values.append(metrics.get("sharpe", 0.0))

    if not sharpe_values:
        sharpe_values = [0.0]
    mean_sharpe = float(np.mean(sharpe_values))
    std_sharpe = float(np.std(sharpe_values))

    return WalkForwardSummary(
        n_splits=n_splits,
        per_split_metrics=per_split_metrics,
        test_sharpe_mean=mean_sharpe,
        test_sharpe_std=std_sharpe,
    )


def summarize_monte_carlo(
    portfolio_returns: pd.Series,
    initial_capital: float,
    n_sims: int,
    seed: int | None,
) -> MonteCarloSummary:
    if n_sims <= 0:
        raise ValueError("n_sims must be positive")
    if portfolio_returns.empty:
        return MonteCarloSummary(
            n_sims=n_sims,
            final_equity_p05=initial_capital,
            final_equity_p50=initial_capital,
            final_equity_p95=initial_capital,
            max_drawdown_p95=0.0,
            prob_of_loss=0.0,
        )

    sample_returns = portfolio_returns.dropna()
    monte_carlo_result = monte_carlo_resample(sample_returns, n_sims=n_sims, seed=seed)
    simulated_paths: list[float] = []
    drawdowns: list[float] = []
    for sim_idx in range(n_sims):
        random_state = seed + sim_idx if seed is not None else None
        resampled = sample_returns.sample(n=len(sample_returns), replace=True, random_state=random_state)
        cumulative = initial_capital * (1.0 + resampled).cumprod()
        simulated_paths.append(float(cumulative.iloc[-1]))
        running = cumulative / cumulative.iloc[0]
        drawdowns.append(float((1.0 - running.div(running.cummax())).max()))

    final_equities = pd.Series(simulated_paths, dtype=float)
    quantiles = final_equities.quantile([0.05, 0.50, 0.95]).to_dict()
    drawdown_series = pd.Series(drawdowns, dtype=float)
    return MonteCarloSummary(
        n_sims=n_sims,
        final_equity_p05=float(quantiles[0.05]),
        final_equity_p50=float(quantiles[0.50]),
        final_equity_p95=float(quantiles[0.95]),
        max_drawdown_p95=float(drawdown_series.quantile(0.95)),
        prob_of_loss=float(monte_carlo_result.prob_of_loss),
    )


def summarize_regime(
    portfolio_returns: pd.Series,
    regime_labels: pd.Series,
) -> RegimeSummary:
    if len(portfolio_returns) != len(regime_labels):
        raise ValueError("portfolio_returns and regime_labels must have the same length")

    labels = regime_labels.dropna().astype(str)
    per_regime_metrics: dict[str, dict[str, float]] = {}
    regime_day_counts: dict[str, int] = {}
    for regime in sorted(set(labels)):
        mask = labels == regime
        regime_returns = portfolio_returns.loc[mask]
        if regime_returns.empty:
            continue
        equity_curve = (1000.0 * (1.0 + regime_returns).cumprod()).rename("equity")
        per_regime_metrics[regime] = _metric_payload(regime_returns, equity_curve)
        regime_day_counts[regime] = int(mask.sum())

    return RegimeSummary(
        regime_method="realized_vol",
        per_regime_metrics=per_regime_metrics,
        regime_day_counts=regime_day_counts,
    )


def summarize_validation(
    strategy: Strategy,
    data: dict[str, pd.DataFrame],
    config: BacktestConfig,
    portfolio_returns: pd.Series,
    initial_capital: float,
    n_splits: int,
    train_ratio: float,
    n_sims: int,
    seed: int | None,
) -> ValidationSummary:
    walk_forward = summarize_walk_forward(strategy, data, config, n_splits=n_splits, train_ratio=train_ratio)
    monte_carlo = summarize_monte_carlo(portfolio_returns, initial_capital=initial_capital, n_sims=n_sims, seed=seed)
    regime_labels = segment_by_regime(data[next(iter(data.keys()))], method="realized_vol")
    regime = summarize_regime(portfolio_returns, regime_labels)
    return ValidationSummary(walk_forward=walk_forward, monte_carlo=monte_carlo, regime=regime)
