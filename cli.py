"""Typer command surface for the deterministic QuantDesk research stack.

This CLI is intentionally thin: it exposes existing Phase 1–3 research,
backtest, optimization, and data interfaces without reimplementing their
business logic.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Annotated

import typer

from backtest.runner import run_backtest
from backtest.schemas import BacktestConfig, BacktestResult
from backtest.run_card import write_run_card
from backtest.validation.summarize import summarize_validation
from data.providers.base import DataProvider
from data.providers.yfinance_provider import YFinanceProvider
from research.optimizer import StrategyOptimizer
from research.runner import ResearchRunner
from strategies.base import Strategy
from strategies.registry import STRATEGY_REGISTRY

app = typer.Typer(help="QuantDesk deterministic research and validation CLI")
data_app = typer.Typer(help="Market data orchestration commands")
app.add_typer(data_app, name="data")


def _provider_factory() -> DataProvider:
    """Return the default provider implementation used by the CLI layer."""
    return YFinanceProvider()


def _resolve_strategy(strategy_name: str) -> Strategy:
    """Instantiate a registered strategy from the registry."""
    if strategy_name not in STRATEGY_REGISTRY:
        typer.echo(f"Unknown strategy: {strategy_name}", err=True)
        raise typer.Exit(code=1)
    return STRATEGY_REGISTRY[strategy_name]()


@data_app.command("pull")
def data_pull(
    symbols: Annotated[list[str], typer.Argument(help="One or more ticker symbols to pull.")],
    start: str = typer.Option(..., "--start", help="Inclusive start date (YYYY-MM-DD)."),
    end: str = typer.Option(..., "--end", help="Inclusive end date (YYYY-MM-DD)."),
    interval: str = typer.Option("1d", "--interval", help="Bar interval to request."),
) -> None:
    """Fetch market data through the existing provider interface."""

    provider = _provider_factory()
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    typer.echo(f"Fetching data for {', '.join(symbols)} ...")
    frames = provider.get_multiple(symbols=symbols, start=start_date, end=end_date, interval=interval)
    for symbol, frame in frames.items():
        typer.echo(f"- {symbol}: {len(frame)} rows from {frame.index.min().date()} to {frame.index.max().date()}")
    typer.echo("Data pull complete.")
    raise typer.Exit(code=0)


@app.command("backtest")
def backtest_command(
    strategy: Annotated[str, typer.Argument(help="Registered strategy name to backtest.")],
    symbols: Annotated[list[str], typer.Argument(help="Ticker symbols to backtest.")],
    start: str = typer.Option(..., "--start", help="Inclusive start date (YYYY-MM-DD)."),
    end: str = typer.Option(..., "--end", help="Inclusive end date (YYYY-MM-DD)."),
    report_dir: str = typer.Option("reports/runs", "--report-dir", help="Root directory for output artifacts."),
) -> None:
    """Run a single strategy backtest using the existing deterministic runner."""

    provider = _provider_factory()
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    typer.echo(f"Loading market data for {', '.join(symbols)} ...")
    data = provider.get_multiple(symbols=symbols, start=start_date, end=end_date)
    strategy_cls = _resolve_strategy(strategy)
    strategy_instance = strategy_cls()
    config = BacktestConfig(
        start=start_date.isoformat(),
        end=end_date.isoformat(),
        initial_capital=1000.0,
        commission_bps=0.0,
        slippage_bps=0.0,
    )
    typer.echo(f"Running backtest for {strategy} ...")
    result = run_backtest(strategy=strategy_instance, data=data, config=config)
    portfolio_returns = result.equity_curve.pct_change().dropna()
    validation = summarize_validation(
        strategy=strategy_instance,
        data=data,
        config=config,
        portfolio_returns=portfolio_returns,
        initial_capital=config.initial_capital,
        n_splits=4,
        train_ratio=0.5,
        n_sims=100,
        seed=7,
    )
    result = BacktestResult(
        equity_curve=result.equity_curve,
        trades=result.trades,
        metrics=result.metrics,
        config_used=result.config_used,
        validation=validation,
    )
    target_dir = Path(report_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    run_card_dir = target_dir / "latest"
    run_card_dir.mkdir(parents=True, exist_ok=True)
    write_run_card(result, hypothesis_id=None, output_dir=str(run_card_dir))
    typer.echo(f"Backtest metrics: {result.metrics}")
    typer.echo(f"Run-card directory: {run_card_dir}")
    raise typer.Exit(code=0)


@app.command("research")
def research_command(
    symbols: Annotated[list[str], typer.Argument(help="One or more ticker symbols to compare.")],
    start: str = typer.Option(..., "--start", help="Inclusive start date (YYYY-MM-DD)."),
    end: str = typer.Option(..., "--end", help="Inclusive end date (YYYY-MM-DD)."),
    strategy: str | None = typer.Option(None, "--strategy", help="Single strategy to run; omit to generate the full compare bundle."),
    report_dir: str = typer.Option("reports/runs", "--report-dir", help="Root directory for output artifacts."),
    n_splits: int = typer.Option(4, "--n-splits", help="Number of walk-forward folds to evaluate."),
    train_ratio: float = typer.Option(0.5, "--train-ratio", help="Training fraction for each walk-forward fold."),
    n_sims: int = typer.Option(100, "--n-sims", help="Number of Monte Carlo simulations to run."),
    seed: int = typer.Option(7, "--seed", help="Random seed for deterministic validation summaries."),
) -> None:
    """Generate a deterministic research report bundle through the existing runner."""

    provider = _provider_factory()
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    runner = ResearchRunner(provider=provider, report_base_dir=report_dir)
    typer.echo(f"Preparing research run for {', '.join(symbols)} ...")
    if strategy is not None:
        result = runner.run(
            strategy_name=strategy,
            symbols=symbols,
            start=start_date,
            end=end_date,
            n_splits=n_splits,
            train_ratio=train_ratio,
            n_sims=n_sims,
            seed=seed,
        )
        typer.echo(f"Single-strategy run created at: {result.run_dir}")
        typer.echo(f"Strategy: {result.strategy_name}")
        typer.echo(f"Metrics: {result.backtest.metrics}")
        if result.backtest.validation is not None:
            typer.echo(
                f"Validation: Walk-forward Sharpe: {result.backtest.validation.walk_forward.test_sharpe_mean:.2f}±{result.backtest.validation.walk_forward.test_sharpe_std:.2f} across {result.backtest.validation.walk_forward.n_splits} splits | Monte Carlo P(loss): {result.backtest.validation.monte_carlo.prob_of_loss:.0%}"
            )
        raise typer.Exit(code=0)

    report_result = runner.generate_report(
        symbols=symbols,
        start=start_date,
        end=end_date,
        n_splits=n_splits,
        train_ratio=train_ratio,
        n_sims=n_sims,
        seed=seed,
    )
    typer.echo(f"Full report bundle created at: {report_result.run_dir}")
    typer.echo(f"Ranking table: {report_result.ranking_path}")
    typer.echo(f"Summary report: {report_result.summary_path}")
    raise typer.Exit(code=0)


@app.command("optimize")
def optimize_command(
    strategy: Annotated[str, typer.Argument(help="Registered strategy name to optimize.")],
    symbols: Annotated[list[str], typer.Argument(help="Ticker symbols used by the optimizer.")],
    start: str = typer.Option(..., "--start", help="Inclusive start date (YYYY-MM-DD)."),
    end: str = typer.Option(..., "--end", help="Inclusive end date (YYYY-MM-DD)."),
    method: str = typer.Option("grid", "--method", help="Optimization method: grid, randomized, or bayesian."),
    objective: str = typer.Option("sharpe", "--objective", help="Objective metric to maximize."),
    walk_forward_splits: int = typer.Option(2, "--walk-forward-splits", help="Number of walk-forward folds to evaluate."),
    n_samples: int = typer.Option(5, "--n-samples", help="Number of randomized or Bayesian iterations."),
    report_dir: str = typer.Option("reports/runs", "--report-dir", help="Root directory for output artifacts."),
) -> None:
    """Run the local strategy optimizer through the existing optimizer engine."""

    provider = _provider_factory()
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    optimizer = StrategyOptimizer(provider=provider, report_base_dir=report_dir)
    typer.echo(f"Starting {method} optimization for {strategy} ...")
    result = optimizer.optimize(
        strategy_name=strategy,
        symbols=symbols,
        start=start_date,
        end=end_date,
        method=method,
        objective=objective,
        walk_forward_splits=walk_forward_splits,
        n_samples=n_samples,
    )
    typer.echo(f"Optimization run directory: {result.run_dir}")
    typer.echo(f"Best parameters: {result.best_parameters}")
    typer.echo(f"Optimization results: {result.results_path}")
    typer.echo(f"Optimization report: {result.report_path}")
    raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
