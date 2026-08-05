# Decisions Log

## Phase 0

- Chosen stack: Python 3.12 with `pydantic-settings`, `pandas`, `numpy`, `backtesting.py`, `vectorbt`, `quantstats`, `ib_async`, and `anthropic`.
- Chosen layout: layered repository with explicit `config`, `data`, `strategies`, `backtest`, `risk`, `research_council`, `research`, and `execution` packages.
- Rationale: the repository must support research workflows, deterministic backtests, explicit trade controls, and manual paper execution without treating the system as an autonomous broker bot.

## Phase 1

- Chosen data abstraction: a `DataProvider` interface is the single contract for all market-history access, with `yfinance` as the first concrete implementation because it is lightweight and CI-safe for synthetic validation.
- Chosen persistence: local caching is intentionally Parquet-backed via `CacheStore`, so the repeated use of the same range is reproducible and network-free after the first fetch.
- Chosen strategy abstraction: every baseline allocation strategy implements a uniform `Strategy.generate_weights(...)` contract that returns a point-in-time-safe `(date, symbol)` weight series.
- Chosen baseline behaviors: `BuyAndHold` is a strict unitized first-symbol allocation, `MovingAverageCrossover` is a one-symbol trend allocation expressed through a simple rolling signal, and `InverseVolatilityBlend` is a normalized two-symbol inverse-volatility blend that is per-date normalized.

## Phase 2

- Chosen validation engine contract: `run_backtest(...)` remains a pure, deterministic, no-broker result envelope so backtest experiments can be reproduced with synthetic fixtures and run cards.
- Chosen analysis split: `walk_forward_split(...)` is chronological and non-overlapping by construction, with a fixed train/test window policy that prevents ambiguous reuse of future data.
- Chosen statistical validation: `monte_carlo_resample(...)` uses a fixed-seed, resampling-based distribution object so the same trade-return input remains reproducible across repeated runs.
- Chosen regime logic: `segment_by_regime(...)` uses a lightweight realized-volatility heuristic that is cheap to test and easy to inspect in a worked example.
- Chosen artifact output: every result becomes a run-card directory with a machine-readable JSON payload and a markdown rendering for human review.

## Phase 3

- Chosen risk-control contract: the risk layer is intentionally separate from the broker path; every proposed trade goes through a pure, deterministic `pretrade_check(...)` gate before any order-submission side effects could occur.
- Chosen administration model: the kill switch is a simple filesystem sentinel in `control/HALT`, which keeps the fail-closed behavior easy to inspect, easy to test, and impossible to bypass silently.
- Chosen sizing behavior: `apply_position_caps(...)` performs deterministic clipping and exposure normalization that is stable under repeated runs and easy to audit in unit tests.
- Chosen overlay behavior: `apply_regime_deleverage(...)` modifies only the regime-labeled dates that are explicitly mapped to a deleverage factor, while leaving all other dates unchanged.

## Phase 4

- Chosen research-report contract: `ResearchRunner.generate_report(...)` is the deterministic, no-AI, no-broker orchestration entry point for producing a single timestamped report bundle with a shared ranking table, per-strategy QuantStats tear sheets, and a human-readable `summary.md`.
- Chosen artifact bundle: all strategy artifacts land in `reports/runs/<timestamp>/`, with the summary and ranking created at the root of that run directory and each strategy’s own subdirectory containing its own run card and tear sheet.
- Chosen comparison policy: the ranking sorts by CAGR, Sharpe, Sortino, Calmar, and Profit Factor, while the summary explains the top-ranked baseline in deterministic terms for reproducible review.

## Phase 3.5

- Chosen optimization contract: `StrategyOptimizer.optimize(...)` performs deterministic, local-only parameter search over the registered strategy stack using exhaustive grid search, randomized search, and a graceful Optuna-backed Bayesian fallback when `optuna` is available.
- Chosen optimization objective policy: the engine scores candidate parameters against a configurable objective (`sharpe`, `sortino`, `cagr`, `calmar`, `profit_factor`) and then automatically performs a simple walk-forward in-sample versus out-of-sample comparison to surface overfitting gaps.
- Chosen output bundle: each optimization run writes `optimization_results.csv`, `best_parameters.json`, and `optimization_report.md` into the same timestamped `reports/runs/<timestamp>/` tree so the optimizer is fully integrated with the existing research-runner report contract.
