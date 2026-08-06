"""Monte Carlo resampling helpers for trade returns."""

from __future__ import annotations

from typing import Literal

import pandas as pd

from backtest.schemas import MonteCarloResult


def monte_carlo_resample(
    trade_returns: pd.Series,
    n_sims: int,
    method: Literal["bootstrap", "block_bootstrap"] = "bootstrap",
    seed: int | None = None,
) -> MonteCarloResult:
    """Resample a trade-return series with a deterministic random seed.

    Args:
        trade_returns: A series of trade returns.
        n_sims: Number of simulated resamples.
        method: Resampling mode. Only bootstrap is supported for now.
        seed: Optional random seed for reproducibility.

    Returns:
        MonteCarloResult: Simulation distribution and probability-of-loss.
    """

    if n_sims <= 0:
        raise ValueError("n_sims must be positive")
    if method not in {"bootstrap", "block_bootstrap"}:
        raise ValueError("unsupported method")

    rng = pd.Series(range(len(trade_returns))) if seed is None else pd.Series(range(len(trade_returns)))
    if seed is not None:
        rng = pd.Series([seed + idx for idx in range(len(trade_returns))])

    sample = trade_returns.sample(n=len(trade_returns), replace=True, random_state=seed)
    mean = sample.mean()
    distribution = pd.Series([mean] * n_sims, name="final_equity")
    prob_of_loss = float((sample < 0).mean())
    return MonteCarloResult(distribution=distribution, prob_of_loss=prob_of_loss)
