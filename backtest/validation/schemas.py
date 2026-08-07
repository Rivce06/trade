from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WalkForwardSummary:
    n_splits: int
    per_split_metrics: list[dict[str, float]]
    test_sharpe_mean: float
    test_sharpe_std: float


@dataclass(frozen=True)
class MonteCarloSummary:
    n_sims: int
    final_equity_p05: float
    final_equity_p50: float
    final_equity_p95: float
    max_drawdown_p95: float
    prob_of_loss: float


@dataclass(frozen=True)
class RegimeSummary:
    regime_method: str
    per_regime_metrics: dict[str, dict[str, float]]
    regime_day_counts: dict[str, int]


@dataclass(frozen=True)
class ValidationSummary:
    walk_forward: WalkForwardSummary
    monte_carlo: MonteCarloSummary
    regime: RegimeSummary
