"""Monte Carlo resampling helpers for trade returns."""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

from backtest.schemas import MonteCarloResult


def monte_carlo_resample(
    trade_returns: pd.Series,
    n_sims: int,
    method: Literal["bootstrap", "block_bootstrap"] = "bootstrap",
    seed: int | None = None,
) -> MonteCarloResult:
    """Run n_sims independent bootstrap resamples of trade_returns and
    return the distribution of simulated final-equity outcomes.

    Args:
        trade_returns: A series of period returns to resample from.
        n_sims: Number of independent simulated paths.
        method: Resampling mode. Only bootstrap is currently implemented;
            block_bootstrap is accepted but not yet differentiated from
            plain bootstrap (a known simplification — revisit if
            autocorrelation in returns turns out to matter).
        seed: Optional seed for reproducibility.

    Returns:
        MonteCarloResult: one final-equity multiplier per simulated path
        (1.0 = breakeven), and prob_of_loss as the fraction of simulated
        paths that ended below the starting value.
    """

    if n_sims <= 0:
        raise ValueError("n_sims must be positive")
    if method not in {"bootstrap", "block_bootstrap"}:
        raise ValueError("unsupported method")

    returns_array = trade_returns.to_numpy()
    n_obs = len(returns_array)
    if n_obs == 0:
        raise ValueError("trade_returns must contain at least one observation")

    rng = np.random.default_rng(seed)
    final_equity = np.empty(n_sims)
    for i in range(n_sims):
        resampled = rng.choice(returns_array, size=n_obs, replace=True)
        final_equity[i] = float(np.prod(1.0 + resampled))

    distribution = pd.Series(final_equity, name="final_equity")
    prob_of_loss = float((distribution < 1.0).mean())
    return MonteCarloResult(distribution=distribution, prob_of_loss=prob_of_loss)