from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
from typer.testing import CliRunner

from cli import app
from tests.conftest import make_ohlcv


class DummyProvider:
    def __init__(self, frames: dict[str, pd.DataFrame]) -> None:
        self.frames = frames

    def get_history(self, symbol: str, start: date, end: date, interval: str = "1d") -> pd.DataFrame:
        return self.frames[symbol].copy()

    def get_multiple(self, symbols: list[str], start: date, end: date, interval: str = "1d") -> dict[str, pd.DataFrame]:
        return {symbol: self.frames[symbol].copy() for symbol in symbols}


def test_cli_data_pull_command_outputs_provider_rows(monkeypatch: object, tmp_path: Path) -> None:
    provider = DummyProvider(
        {
            "SPY": make_ohlcv("SPY", start=date(2024, 1, 1), periods=12),
            "GLD": make_ohlcv("GLD", start=date(2024, 1, 1), periods=12),
        }
    )
    monkeypatch.setattr("cli._provider_factory", lambda: provider)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "data",
            "pull",
            "SPY",
            "GLD",
            "--start",
            "2024-01-01",
            "--end",
            "2024-01-12",
        ],
    )

    assert result.exit_code == 0
    assert "Data pull complete." in result.stdout
    assert "SPY" in result.stdout
    assert "GLD" in result.stdout


def test_cli_research_command_emits_bundle_paths(monkeypatch: object, tmp_path: Path) -> None:
    provider = DummyProvider(
        {
            "SPY": make_ohlcv("SPY", start=date(2024, 1, 1), periods=12),
            "GLD": make_ohlcv("GLD", start=date(2024, 1, 1), periods=12),
        }
    )
    monkeypatch.setattr("cli._provider_factory", lambda: provider)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "research",
            "SPY",
            "GLD",
            "--start",
            "2024-01-01",
            "--end",
            "2024-01-12",
            "--report-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "Full report bundle created" in result.stdout
    assert "ranking.csv" in result.stdout
    assert "summary.md" in result.stdout
