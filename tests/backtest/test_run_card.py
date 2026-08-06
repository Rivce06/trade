from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from backtest.run_card import write_run_card
from backtest.schemas import BacktestConfig, BacktestResult


def test_run_card_json_and_markdown_round_trip(tmp_path: Path) -> None:
    result = BacktestResult(
        equity_curve=pd.Series([100.0, 101.0], index=pd.date_range("2024-01-01", periods=2, freq="D", name="date")),
        trades=pd.DataFrame({"symbol": ["SPY"]}),
        metrics={"cagr": 0.1, "sharpe": 1.0, "sortino": 0.9, "max_dd": 0.2, "calmar": 0.5, "win_rate": 0.6},
        config_used=BacktestConfig(
            start="2024-01-01",
            end="2024-01-02",
            initial_capital=1000.0,
            commission_bps=0.0,
            slippage_bps=0.0,
        ),
    )

    card_path = write_run_card(result, output_dir=tmp_path)

    assert card_path.exists()
    json_path = card_path / "run_card.json"
    assert json_path.exists()
    payload = json.loads(json_path.read_text())
    assert payload["metrics"]["cagr"] == 0.1

    md_path = card_path / "run_card.md"
    assert md_path.exists()
    assert "cagr" in md_path.read_text().lower()
