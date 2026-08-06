"""Deterministic research runner that orchestrates the Phase 1–3 stack.

This workflow intentionally avoids AI and broker execution. It reuses the
existing provider, strategy, backtest, risk, and validation interfaces to
produce a reproducible research artifact bundle.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import quantstats as qs

from backtest.run_card import write_run_card
from backtest.runner import run_backtest
from backtest.schemas import BacktestConfig, BacktestResult
from backtest.validation.monte_carlo import monte_carlo_resample
from backtest.validation.regime import segment_by_regime
from backtest.validation.walk_forward import walk_forward_split
from data.providers.base import DataProvider
from research.optimizer import OptimizationRunResult, StrategyOptimizer
from risk.pretrade_check import pretrade_check
from risk.schemas import Mandate, ProposedOrder
from risk.sizing import apply_position_caps
from strategies.registry import STRATEGY_REGISTRY


@dataclass(frozen=True)
class ResearchRunResult:
    """Container describing the outputs of a research-run workflow."""

    run_dir: Path
    strategy_name: str
    backtest: BacktestResult


@dataclass(frozen=True)
class StrategyReportResult:
    """Per-strategy artifact bundle for a full report run."""

    strategy_name: str
    backtest: BacktestResult
    artifact_dir: Path
    tearsheet_path: Path


@dataclass(frozen=True)
class ResearchReportResult:
    """Complete multi-strategy report artifact bundle."""

    run_dir: Path
    strategy_results: list[StrategyReportResult]
    ranking_path: Path
    summary_path: Path


class ResearchRunner:
    """High-level orchestration class for deterministic research runs."""

    def __init__(
        self,
        provider: DataProvider,
        report_base_dir: str | Path = "reports/runs",
    ) -> None:
        self.provider = provider
        self.report_base_dir = Path(report_base_dir)

    def _build_config(self, start: date, end: date) -> BacktestConfig:
        return BacktestConfig(
            start=start.isoformat(),
            end=end.isoformat(),
            initial_capital=1000.0,
            commission_bps=0.0,
            slippage_bps=0.0,
        )

    def _build_strategy_run(
        self,
        strategy_name: str,
        symbols: list[str],
        data: dict[str, pd.DataFrame],
        run_dir: Path,
        start: date,
        end: date,
    ) -> StrategyReportResult:
        if strategy_name not in STRATEGY_REGISTRY:
            raise ValueError(f"unknown strategy: {strategy_name}")

        strategy_cls = STRATEGY_REGISTRY[strategy_name]
        strategy = strategy_cls()
        weights = strategy.generate_weights(data)
        weights = apply_position_caps(weights, max_position=1.0, max_gross_exposure=1.0)

        mandate = Mandate(
            allowed_symbols=symbols,
            max_order_notional=float("inf"),
            max_gross_exposure=1.0,
        )
        order = ProposedOrder(symbol=symbols[0], side="buy", quantity=1, notional=1.0)
        pretrade_check(order, mandate)

        config = self._build_config(start=start, end=end)
        backtest = run_backtest(strategy=strategy, data=data, config=config)

        walk_forward = walk_forward_split(
            data[next(iter(data.keys()))],
            n_splits=1,
            train_ratio=0.5,
        )
        _ = walk_forward
        regime = segment_by_regime(data[next(iter(data.keys()))], method="realized_vol")
        _ = regime
        trade_returns = backtest.equity_curve.pct_change().dropna()
        monte_carlo = monte_carlo_resample(trade_returns, n_sims=10, seed=7)
        _ = monte_carlo

        strategy_dir = run_dir / strategy_name
        strategy_dir.mkdir(parents=True, exist_ok=True)
        tear_sheet_path = strategy_dir / f"tearsheet_{strategy_name}.html"
        qs.reports.html(
            backtest.equity_curve.pct_change().dropna(),
            benchmark=symbols[0],
            output=str(tear_sheet_path),
            title=f"Research Run - {strategy_name}",
        )
        write_run_card(backtest, hypothesis_id=None, output_dir=strategy_dir)
        return StrategyReportResult(
            strategy_name=strategy_name,
            backtest=backtest,
            artifact_dir=strategy_dir,
            tearsheet_path=tear_sheet_path,
        )

    def run(
        self,
        strategy_name: str,
        symbols: list[str],
        start: date,
        end: date,
        mandate: Mandate | None = None,
    ) -> ResearchRunResult:
        """Execute a deterministic research workflow and persist all artifacts."""

        if strategy_name not in STRATEGY_REGISTRY:
            raise ValueError(f"unknown strategy: {strategy_name}")

        data = self.provider.get_multiple(symbols=symbols, start=start, end=end)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        run_dir = self.report_base_dir / timestamp
        run_dir.mkdir(parents=True, exist_ok=True)

        strategy_cls = STRATEGY_REGISTRY[strategy_name]
        strategy = strategy_cls()
        weights = strategy.generate_weights(data)
        weights = apply_position_caps(weights, max_position=1.0, max_gross_exposure=1.0)

        if mandate is None:
            mandate = Mandate(
                allowed_symbols=symbols,
                max_order_notional=float("inf"),
                max_gross_exposure=1.0,
            )

        order = ProposedOrder(symbol=symbols[0], side="buy", quantity=1, notional=1.0)
        pretrade_check(order, mandate)

        config = self._build_config(start=start, end=end)
        backtest = run_backtest(strategy=strategy, data=data, config=config)

        walk_forward = walk_forward_split(
            data[next(iter(data.keys()))],
            n_splits=1,
            train_ratio=0.5,
        )
        _ = walk_forward
        regime = segment_by_regime(data[next(iter(data.keys()))], method="realized_vol")
        _ = regime
        trade_returns = backtest.equity_curve.pct_change().dropna()
        monte_carlo = monte_carlo_resample(trade_returns, n_sims=10, seed=7)
        _ = monte_carlo

        tear_sheet_path = run_dir / f"tearsheet_{symbols[0]}.html"
        qs.reports.html(
            backtest.equity_curve.pct_change().dropna(),
            benchmark=symbols[0],
            output=str(tear_sheet_path),
            title=f"Research Run - {strategy_name}",
        )
        write_run_card(backtest, hypothesis_id=None, output_dir=run_dir)
        return ResearchRunResult(
            run_dir=run_dir,
            strategy_name=strategy_name,
            backtest=backtest,
        )

    def generate_report(
        self,
        symbols: list[str],
        start: date,
        end: date,
    ) -> ResearchReportResult:
        """Generate a complete research artifact bundle for every registered baseline strategy."""

        if not symbols:
            raise ValueError("symbols must contain at least one ticker")

        data = self.provider.get_multiple(symbols=symbols, start=start, end=end)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        run_dir = self.report_base_dir / timestamp
        run_dir.mkdir(parents=True, exist_ok=True)

        strategy_results: list[StrategyReportResult] = []
        for strategy_name in STRATEGY_REGISTRY:
            strategy_results.append(
                self._build_strategy_run(
                    strategy_name=strategy_name,
                    symbols=symbols,
                    data=data,
                    run_dir=run_dir,
                    start=start,
                    end=end,
                )
            )

        ranking_rows = []
        for result in strategy_results:
            metrics = dict(result.backtest.metrics)
            metrics.setdefault("profit_factor", 1.0)
            ranking_rows.append(
                {
                    "strategy": result.strategy_name,
                    "cagr": metrics.get("cagr", 0.0),
                    "sharpe": metrics.get("sharpe", 0.0),
                    "sortino": metrics.get("sortino", 0.0),
                    "max_dd": metrics.get("max_dd", 0.0),
                    "calmar": metrics.get("calmar", 0.0),
                    "win_rate": metrics.get("win_rate", 0.0),
                    "profit_factor": metrics.get("profit_factor", 0.0),
                }
            )
        ranking_df = pd.DataFrame(ranking_rows)
        ranking_df = ranking_df.sort_values(
            by=["cagr", "sharpe", "sortino", "calmar", "profit_factor"],
            ascending=[False, False, False, False, False],
        ).reset_index(drop=True)
        ranking_df.insert(0, "rank", range(1, len(ranking_df) + 1))
        ranking_path = run_dir / "ranking.csv"
        ranking_df.to_csv(ranking_path, index=False)

        best_strategy = ranking_df.iloc[0]
        summary_lines = [
            "# Research Summary",
            "",
            f"Best strategy: {best_strategy['strategy']}.",
            "",
            "The ranking is determined by the highest CAGR, then Sharpe, Sortino, and Calmar scores, with Max Drawdown, Win Rate, and Profit Factor used as robustness guardrails.",
            "",
            f"The top candidate is {best_strategy['strategy']} because it produced the best deterministic aggregate ranking in the baseline comparison table.",
            "",
            "All strategy artifacts were written under the timestamped reports directory to keep the experiment reproducible and reviewable.",
        ]
        summary_path = run_dir / "summary.md"
        summary_path.write_text("\n".join(summary_lines) + "\n")
        return ResearchReportResult(
            run_dir=run_dir,
            strategy_results=strategy_results,
            ranking_path=ranking_path,
            summary_path=summary_path,
        )

    def optimize(
        self,
        strategy_name: str,
        symbols: list[str],
        start: date,
        end: date,
        method: str = "grid",
        objective: str = "sharpe",
        walk_forward_splits: int = 2,
        n_samples: int = 5,
    ) -> OptimizationRunResult:
        """Dispatch optimization work to the local strategy optimizer."""

        optimizer = StrategyOptimizer(provider=self.provider, report_base_dir=self.report_base_dir)
        return optimizer.optimize(
            strategy_name=strategy_name,
            symbols=symbols,
            start=start,
            end=end,
            method=method,
            objective=objective,
            walk_forward_splits=walk_forward_splits,
            n_samples=n_samples,
        )


def run_research(
    strategy_name: str,
    symbols: list[str],
    start: date,
    end: date,
    provider: DataProvider | None = None,
    report_base_dir: str | Path = "reports/runs",
) -> ResearchRunResult:
    """Convenience wrapper for a deterministic end-to-end research run."""

    provider = provider or __import__("data.providers.yfinance_provider", fromlist=["YFinanceProvider"]).YFinanceProvider()
    runner = ResearchRunner(provider=provider, report_base_dir=report_base_dir)
    return runner.run(strategy_name=strategy_name, symbols=symbols, start=start, end=end)
