from __future__ import annotations

import pandas as pd

from backtest.validation.monte_carlo import monte_carlo_resample


def test_monte_carlo_result_is_deterministic_for_fixed_seed() -> None:
    trade_returns = pd.Series([0.02, -0.01, 0.03, -0.02, 0.01], name="return")

    result_a = monte_carlo_resample(trade_returns, n_sims=5, seed=7)
    result_b = monte_carlo_resample(trade_returns, n_sims=5, seed=7)

    assert result_a.distribution.equals(result_b.distribution)
    assert result_a.prob_of_loss == result_b.prob_of_loss


def test_bootstrap_mean_converges_to_input_mean() -> None:
    trade_returns = pd.Series([0.01, -0.02, 0.04, 0.03, -0.01, 0.02], name="return")
    result = monte_carlo_resample(trade_returns, n_sims=1000, seed=42)

    n_obs = len(trade_returns)
    expected_compounded_growth = (1.0 + trade_returns.mean()) ** n_obs

    assert len(result.distribution) == 1000
    assert result.distribution.nunique() > 1  # genuinely independent paths, not the old repeated-mean bug
    assert abs(result.distribution.mean() - expected_compounded_growth) < 0.5
    assert 0.0 <= result.prob_of_loss <= 1.0