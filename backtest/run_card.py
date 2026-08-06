"""Write reproducible run-card artifacts for backtests."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from backtest.schemas import BacktestResult


def write_run_card(result: BacktestResult, hypothesis_id: str | None = None, output_dir: Path | None = None) -> Path:
    """Write a run card in JSON and markdown form for a completed backtest result.

    Args:
        result: The completed backtest result.
        hypothesis_id: Optional linked hypothesis identifier.
        output_dir: Directory to write the run-card files into.

    Returns:
        Path: The directory containing the run card artifacts.
    """

    run_id = str(uuid4())
    run_dir = Path(output_dir) if output_dir is not None else Path("reports/runs")
    run_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "run_id": run_id,
        "hypothesis_id": hypothesis_id,
        "metrics": result.metrics,
        "config_used": {
            "start": result.config_used.start,
            "end": result.config_used.end,
            "initial_capital": result.config_used.initial_capital,
            "commission_bps": result.config_used.commission_bps,
            "slippage_bps": result.config_used.slippage_bps,
        },
    }

    json_path = run_dir / "run_card.json"
    markdown_path = run_dir / "run_card.md"
    json_path.write_text(json.dumps(payload, indent=2))
    markdown_path.write_text(
        "# Run Card\n\n"
        + f"- Run ID: {run_id}\n"
        + f"- Hypothesis ID: {hypothesis_id}\n"
        + "\n".join(f"- {key}: {value}" for key, value in result.metrics.items())
        + "\n"
    )
    return run_dir
