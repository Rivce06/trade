from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from research.runner import ResearchRunner
from research.optimizer import StrategyOptimizer
from tests.conftest import make_ohlcv


class DummyProvider:
    def __init__(self, frames: dict[str, pd.DataFrame]) -> None:
        self.frames = frames

    def get_history(self, symbol: str, start: date, end: date, interval: str = "1d") -> pd.DataFrame:
        return self.frames[symbol].copy()

    def get_multiple(self, symbols: list[str], start: date, end: date, interval: str = "1d") -> dict[str, pd.DataFrame]:
        return {symbol: self.frames[symbol].copy() for symbol in symbols}


def test_strategy_optimizer_exports_expected_artifacts(tmp_path: Path) -> None:
    provider = DummyProvider(
        {
            "SPY": make_ohlcv("SPY", start=date(2024, 1, 1), periods=12),
            "GLD": make_ohlcv("GLD", start=date(2024, 1, 1), periods=12),
        }
    )
    optimizer = StrategyOptimizer(provider=provider, report_base_dir=tmp_path)

    result = optimizer.optimize(
        strategy_name="ma_crossover",
        symbols=["SPY", "GLD"],
        start=date(2024, 1, 1),
        end=date(2024, 1, 12),
        method="grid",
        objective="sharpe",
    )

    assert result.run_dir.exists()
    assert (result.run_dir / "optimization_results.csv").exists()
    assert (result.run_dir / "best_parameters.json").exists()
    assert (result.run_dir / "optimization_report.md").exists()
    assert result.best_parameters
    assert "best" in result.report_path.read_text().lower()


def test_research_runner_integrates_optimizer(tmp_path: Path) -> None:
    provider = DummyProvider(
        {
            "SPY": make_ohlcv("SPY", start=date(2024, 1, 1), periods=12),
            "GLD": make_ohlcv("GLD", start=date(2024, 1, 1), periods=12),
        }
    )
    runner = ResearchRunner(provider=provider, report_base_dir=tmp_path)

    result = runner.optimize(
        strategy_name="ma_crossover",
        symbols=["SPY", "GLD"],
        start=date(2024, 1, 1),
        end=date(2024, 1, 12),
        method="randomized",
        objective="cagr",
    )

    assert result.run_dir.exists()
    assert result.best_parameters
