from __future__ import annotations

import pandas as pd

from backtest.validation.summarize import summarize_monte_carlo


def test_summarize_monte_carlo_is_deterministic_and_probabilistic() -> None:
    returns = pd.Series([0.02, -0.01, 0.03, -0.02, 0.01, 0.04, -0.03, 0.02], name="return")

    summary_a = summarize_monte_carlo(returns, initial_capital=1000.0, n_sims=200, seed=7)
    summary_b = summarize_monte_carlo(returns, initial_capital=1000.0, n_sims=200, seed=7)

    assert 0.0 <= summary_a.prob_of_loss <= 1.0
    assert summary_a.final_equity_p05 <= summary_a.final_equity_p50 <= summary_a.final_equity_p95
    assert summary_a.final_equity_p05 <= summary_a.final_equity_p50 <= summary_a.final_equity_p95
    assert summary_a.final_equity_p05 == summary_b.final_equity_p05
    assert summary_a.final_equity_p50 == summary_b.final_equity_p50
    assert summary_a.final_equity_p95 == summary_b.final_equity_p95
