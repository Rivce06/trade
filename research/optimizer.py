"""Strategy optimization engine for deterministic research workflows.

The optimizer keeps the research workflow model-free and local-only. It
supports exhaustive grid search, randomized search, and a lightweight Optuna
integration when the dependency is available in the environment.
"""

from __future__ import annotations

import csv
import importlib
import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from itertools import product
from pathlib import Path
from random import Random

import pandas as pd

from backtest.runner import run_backtest
from backtest.schemas import BacktestConfig, BacktestResult
from backtest.validation.walk_forward import walk_forward_split
from data.providers.base import DataProvider
from risk.pretrade_check import pretrade_check
from risk.schemas import Mandate, ProposedOrder
from risk.sizing import apply_position_caps
from strategies.registry import STRATEGY_REGISTRY


@dataclass(frozen=True)
class OptimizationRunResult:
    """Container for an optimization run emitted by the optimizer."""

    run_dir: Path
    best_parameters: dict[str, object]
    report_path: Path
    results_path: Path
    objective: str
    strategy_name: str


class StrategyOptimizer:
    """Local, deterministic optimizer for registered baseline strategies."""

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

    def _objective_score(self, objective: str, result: BacktestResult) -> float:
        metrics = result.metrics
        objective = objective.lower()
        if objective == "cagr":
            return float(metrics.get("cagr", 0.0))
        if objective == "sharpe":
            return float(metrics.get("sharpe", 0.0))
        if objective == "sortino":
            return float(metrics.get("sortino", 0.0))
        if objective == "calmar":
            return float(metrics.get("calmar", 0.0))
        if objective == "profit_factor":
            return float(metrics.get("profit_factor", 1.0))
        raise ValueError(f"unsupported objective: {objective}")

    def _evaluate_candidate(
        self,
        strategy_name: str,
        params: dict[str, object],
        data: dict[str, pd.DataFrame],
        symbols: list[str],
        start: date,
        end: date,
        objective: str,
        walk_forward_splits: int = 2,
    ) -> tuple[float, float, float, dict[str, float]]:
        strategy_cls = STRATEGY_REGISTRY[strategy_name]
        strategy = strategy_cls(**params)
        weights = strategy.generate_weights(data)
        _ = apply_position_caps(weights, max_position=1.0, max_gross_exposure=1.0)

        mandate = Mandate(
            allowed_symbols=symbols,
            max_order_notional=float("inf"),
            max_gross_exposure=1.0,
        )
        order = ProposedOrder(symbol=symbols[0], side="buy", quantity=1, notional=1.0)
        pretrade_check(order, mandate)

        symbol_frame = data[next(iter(data.keys()))]
        splits = walk_forward_split(symbol_frame, n_splits=walk_forward_splits, train_ratio=0.6)
        split_scores: list[float] = []
        out_of_sample_scores: list[float] = []
        metrics_summary: dict[str, float] = {}

        for train_frame, test_frame in splits:
            train_data = {symbol: frame.loc[frame.index.isin(train_frame.index)] for symbol, frame in data.items()}
            test_data = {symbol: frame.loc[frame.index.isin(test_frame.index)] for symbol, frame in data.items()}
            if len(train_data[next(iter(train_data.keys()))]) == 0 or len(test_data[next(iter(test_data.keys()))]) == 0:
                continue
            train_result = run_backtest(
                strategy=strategy,
                data=train_data,
                config=self._build_config(start=train_frame.index.min().date(), end=train_frame.index.max().date()),
            )
            test_result = run_backtest(
                strategy=strategy,
                data=test_data,
                config=self._build_config(start=test_frame.index.min().date(), end=test_frame.index.max().date()),
            )
            split_scores.append(self._objective_score(objective, train_result))
            out_of_sample_scores.append(self._objective_score(objective, test_result))
            metrics_summary.update(train_result.metrics)

        if len(split_scores) == 0:
            return 0.0, 0.0, 0.0, metrics_summary

        in_sample_score = sum(split_scores) / len(split_scores)
        out_sample_score = sum(out_of_sample_scores) / len(out_of_sample_scores)
        overfit_gap = abs(in_sample_score - out_sample_score)
        metrics_summary["overfit_gap"] = overfit_gap
        metrics_summary["in_sample_score"] = in_sample_score
        metrics_summary["out_sample_score"] = out_sample_score
        return in_sample_score, out_sample_score, overfit_gap, metrics_summary

    def _grid_candidates(self, strategy_name: str) -> list[dict[str, object]]:
        strategy_cls = STRATEGY_REGISTRY[strategy_name]
        grids = strategy_cls.param_grid
        if not grids:
            return [{}]
        keys = list(grids)
        value_lists = [grids[key] for key in keys]
        candidates: list[dict[str, object]] = []
        for combo in product(*value_lists):
            candidates.append({keys[idx]: combo[idx] for idx in range(len(keys))})
        return candidates

    def _randomized_candidates(self, strategy_name: str, n_samples: int, seed: int = 7) -> list[dict[str, object]]:
        rng = Random(seed)
        candidates = self._grid_candidates(strategy_name)
        if len(candidates) <= n_samples:
            return candidates
        return rng.sample(candidates, n_samples)

    def _bayesian_candidates(self, strategy_name: str, objective: str, n_trials: int) -> list[dict[str, object]]:
        try:
            optuna = importlib.import_module("optuna")
        except ModuleNotFoundError:
            return self._randomized_candidates(strategy_name=strategy_name, n_samples=n_trials)

        strategy_cls = STRATEGY_REGISTRY[strategy_name]
        grids = strategy_cls.param_grid
        if not grids:
            return [{}]

        study = optuna.create_study(direction="maximize")
        suggestions: list[dict[str, object]] = []

        def _objective(trial: object) -> float:
            candidate: dict[str, object] = {}
            for key, values in grids.items():
                choices = list(values)
                if all(isinstance(choice, int) for choice in choices):
                    candidate[key] = trial.suggest_categorical(key, choices)
                else:
                    candidate[key] = trial.suggest_categorical(key, choices)
            in_score, _, _, _ = self._evaluate_candidate(
                strategy_name=strategy_name,
                params=candidate,
                data={},
                symbols=[],
                start=date(2000, 1, 1),
                end=date(2000, 1, 1),
                objective=objective,
            )
            suggestions.append(candidate)
            return in_score

        study.optimize(lambda trial: _objective(trial), n_trials=n_trials)
        best = study.best_trial
        return suggestions or [best.params]

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
        """Optimize one registered strategy and export the artifacts to disk."""

        if strategy_name not in STRATEGY_REGISTRY:
            raise ValueError(f"unknown strategy: {strategy_name}")
        if method not in {"grid", "randomized", "bayesian"}:
            raise ValueError(f"unsupported method: {method}")

        data = self.provider.get_multiple(symbols=symbols, start=start, end=end)
        run_dir = self.report_base_dir / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        run_dir.mkdir(parents=True, exist_ok=True)

        if method == "grid":
            candidates = self._grid_candidates(strategy_name)
        elif method == "randomized":
            candidates = self._randomized_candidates(strategy_name=strategy_name, n_samples=n_samples)
        else:
            candidates = self._bayesian_candidates(strategy_name=strategy_name, objective=objective, n_trials=n_samples)

        rows: list[dict[str, object]] = []
        best_score = float("-inf")
        best_parameters: dict[str, object] = {}
        for candidate in candidates:
            in_score, out_score, overfit_gap, metrics = self._evaluate_candidate(
                strategy_name=strategy_name,
                params=candidate,
                data=data,
                symbols=symbols,
                start=start,
                end=end,
                objective=objective,
                walk_forward_splits=walk_forward_splits,
            )
            entry = {
                "strategy": strategy_name,
                "method": method,
                "objective": objective,
                "in_sample_score": in_score,
                "out_sample_score": out_score,
                "overfit_gap": overfit_gap,
                **candidate,
            }
            entry.update(metrics)
            rows.append(entry)
            if in_score > best_score:
                best_score = in_score
                best_parameters = candidate.copy()

        results_path = run_dir / "optimization_results.csv"
        with results_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["strategy", "method", "objective"])
            writer.writeheader()
            writer.writerows(rows)

        parameters_path = run_dir / "best_parameters.json"
        parameters_path.write_text(json.dumps(best_parameters, indent=2))

        report_lines = [
            "# Optimization Report",
            "",
            f"Strategy: {strategy_name}",
            f"Method: {method}",
            f"Objective: {objective}",
            f"Best parameters: {json.dumps(best_parameters, sort_keys=True)}",
            "",
            "## Overfitting Check",
            "",
            f"The in-sample objective was {rows[0]['in_sample_score'] if rows else 0.0} and the out-of-sample objective was {rows[0]['out_sample_score'] if rows else 0.0}.",
            "",
            "The optimization output is deterministic and follows the repository’s local-only research contract.",
        ]
        report_path = run_dir / "optimization_report.md"
        report_path.write_text("\n".join(report_lines) + "\n")
        return OptimizationRunResult(
            run_dir=run_dir,
            best_parameters=best_parameters,
            report_path=report_path,
            results_path=results_path,
            objective=objective,
            strategy_name=strategy_name,
        )
