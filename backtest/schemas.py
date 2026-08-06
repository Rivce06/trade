"""Schemas for the validation engine and result capture."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class BacktestConfig:
    """Reusable configuration for a backtest run."""

    start: str
    end: str
    initial_capital: float = 1000.0
    commission_bps: float = 0.0
    slippage_bps: float = 0.0


@dataclass(frozen=True)
class BacktestResult:
    """Small result envelope returned by the runner."""

    equity_curve: pd.Series
    trades: pd.DataFrame
    metrics: dict[str, float]
    config_used: BacktestConfig


@dataclass(frozen=True)
class MonteCarloResult:
    """Summary object for Monte Carlo trade resampling."""

    distribution: pd.Series
    prob_of_loss: float


@dataclass(frozen=True)
class RunCard:
    """Serialized metadata for a backtest artifact."""

    run_id: str
    result: BacktestResult
    hypothesis_id: str | None = None
    extra: dict[str, Any] | None = None
