from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from research.runner import ResearchRunner, ResearchReportResult, run_research
from tests.conftest import make_ohlcv


class DummyProvider:
    def __init__(self, frames: dict[str, pd.DataFrame]) -> None:
        self.frames = frames

    def get_history(self, symbol: str, start: date, end: date, interval: str = "1d") -> pd.DataFrame:
        return self.frames[symbol].copy()

    def get_multiple(self, symbols: list[str], start: date, end: date, interval: str = "1d") -> dict[str, pd.DataFrame]:
        return {symbol: self.frames[symbol].copy() for symbol in symbols}


def test_research_runner_emits_artifacts_in_timestamped_reports_dir(tmp_path: Path) -> None:
    provider = DummyProvider(
        {
            "SPY": make_ohlcv("SPY", start=date(2024, 1, 1), periods=12),
            "GLD": make_ohlcv("GLD", start=date(2024, 1, 1), periods=12),
        }
    )
    runner = ResearchRunner(provider=provider, report_base_dir=tmp_path)

    result = runner.run(
        strategy_name="buy_and_hold",
        symbols=["SPY", "GLD"],
        start=date(2024, 1, 1),
        end=date(2024, 1, 12),
    )

    assert result.run_dir.exists()
    assert (result.run_dir / "run_card.json").exists()
    assert (result.run_dir / "run_card.md").exists()
    assert any((result.run_dir).glob("tearsheet_*.html"))


def test_research_runner_generates_complete_report_bundle(tmp_path: Path) -> None:
    provider = DummyProvider(
        {
            "SPY": make_ohlcv("SPY", start=date(2024, 1, 1), periods=12),
            "GLD": make_ohlcv("GLD", start=date(2024, 1, 1), periods=12),
        }
    )
    runner = ResearchRunner(provider=provider, report_base_dir=tmp_path)

    result = runner.generate_report(
        symbols=["SPY", "GLD"],
        start=date(2024, 1, 1),
        end=date(2024, 1, 12),
    )

    assert isinstance(result, ResearchReportResult)
    assert result.run_dir.exists()
    assert result.summary_path.exists()
    assert result.ranking_path.exists()
    assert result.ranking_path.suffix == ".csv"
    assert len(result.strategy_results) >= 2
    assert any((result.run_dir).glob("*/run_card.json"))
    assert any((result.run_dir).glob("*/tearsheet_*.html"))
    assert "best" in result.summary_path.read_text().lower()


def test_run_research_returns_reproducible_run_metadata() -> None:
    provider = DummyProvider(
        {
            "SPY": make_ohlcv("SPY", start=date(2024, 1, 1), periods=12),
        }
    )

    result_a = run_research(
        strategy_name="buy_and_hold",
        symbols=["SPY"],
        start=date(2024, 1, 1),
        end=date(2024, 1, 12),
        provider=provider,
    )
    result_b = run_research(
        strategy_name="buy_and_hold",
        symbols=["SPY"],
        start=date(2024, 1, 1),
        end=date(2024, 1, 12),
        provider=provider,
    )

    assert result_a.strategy_name == result_b.strategy_name
    assert result_a.run_dir.name != result_b.run_dir.name
    assert result_a.backtest.metrics == result_b.backtest.metrics
