# QuantDesk — Implementation Roadmap for GitHub Copilot

Companion to: `ARCHITECTURE.md`

Purpose: a file-level, phase-by-phase build spec — repository structure, files to create, interfaces, expected inputs/outputs, tests, and acceptance criteria — precise enough to drive Copilot one file at a time. Explicitly out of scope here: implementation code. Interfaces below are signatures/contracts only, describing shape and behavior, not logic.

## 0. How to Use This With Copilot

1. Add a `.github/copilot-instructions.md` to the repo so every inline suggestion and Copilot Chat session inherits the same conventions without repeating them per prompt.
2. Work one file at a time. For each file, give Copilot Chat the file’s row from the phase table below, its Interface, its Inputs/Outputs, and its Tests to write. Ask it to write the test file first (or alongside), then the implementation, then run the tests.
3. Do not let Copilot skip the “Tests to write” list — several of them (lookahead guards, kill-switch behavior, pre-trade check coverage) exist specifically to catch the failure modes this kind of project is prone to.
4. Keep this file and `ARCHITECTURE.md` in `docs/` so Copilot Chat can be pointed at them directly (`@workspace docs/IMPLEMENTATION_ROADMAP.md`) for context on later phases.
5. Commit after each file passes its own tests, not after each phase — smaller diffs, easier to bisect if something breaks later.

## 1. Global Conventions

### 1.1 Stack

- Python 3.12
- Dependency management via `pyproject.toml` (`pip install -e .[dev]`)
- Data: `pandas`, `numpy`
- Backtesting: `backtesting.py`, `vectorbt`
- Reporting: `quantstats`
- Broker: `ib_async`
- AI: Anthropic API (`anthropic` SDK)
- Schemas/config: `pydantic` v2, `pydantic-settings` for env-based config
- CLI: `typer`
- Testing: `pytest`, `pytest-cov`, `pytest-mock`
- Lint/format/type-check: `ruff`, `black`, `mypy`

### 1.2 Style Rules

- Every public function and class has a docstring (Google style) and full type hints.
- No bare `except:`.
- No `print()` outside the CLI layer — use logging.
- No secrets in code or notebooks. All credentials come from `.env` via `config/settings.py`, and `.env` is gitignored.
- Every module that touches money, orders, or the kill switch has at least 90% branch coverage; everything else targets at least 80% line coverage.

### 1.3 Testing Rules

- Unit tests never make live network calls (IBKR or Anthropic). External clients are always mocked in `tests/`.
- Tests that do require a live IBKR paper connection or a live Anthropic call are marked `@pytest.mark.manual` and excluded from CI by default.
- Test files mirror the source tree: `strategies/ma_crossover.py` → `tests/strategies/test_ma_crossover.py`.
- Every new interface gets a conformance test if it is one implementation of a shared abstract interface (`DataProvider`, `Strategy`, `BrokerConnector`) — one parametrized test that runs against every registered implementation.

### 1.4 Git / Process

- Conventional commits (`feat:`, `fix:`, `test:`, `docs:`).
- One `DECISIONS.md` entry per phase, written when the phase is judged done, not before — decisions are easier to state accurately in hindsight.
- Feature branch per phase, merged after its acceptance criteria are met.

### 1.5 `.github/copilot-instructions.md` (outline — write this in Phase 0)

Should state, in plain prose:
- the project’s purpose and non-goals (research platform, not an autonomous bot)
- the stack from §1.1
- the style rules from §1.2
- the rule that LLM output is advisory-only and every strategy must work with `memo=None`
- the rule that no order path may skip `pretrade_check`
- a pointer to this roadmap and the architecture doc for anything the instructions don’t cover

## 2. Full Repository Structure (end state, all phases)

```text
quantdesk/
├── .github/
│   └── copilot-instructions.md
├── config/
│   ├── __init__.py
│   └── settings.py
├── data/
│   ├── __init__.py
│   ├── schemas.py
│   ├── cache_store.py
│   ├── cache/                      # gitignored
│   └── providers/
│       ├── __init__.py
│       ├── base.py
│       ├── ibkr_provider.py
│       └── yfinance_provider.py
├── strategies/
│   ├── __init__.py
│   ├── base.py
│   ├── registry.py
│   ├── buy_and_hold.py
│   ├── ma_crossover.py
│   └── inverse_vol_blend.py
├── backtest/
│   ├── __init__.py
│   ├── schemas.py
│   ├── runner.py
│   ├── benchmarks.py
│   ├── run_card.py
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── backtesting_py_adapter.py
│   │   └── vectorbt_adapter.py
│   └── validation/
│       ├── __init__.py
│       ├── walk_forward.py
│       ├── monte_carlo.py
│       └── regime.py
├── risk/
│   ├── __init__.py
│   ├── schemas.py
│   ├── sizing.py
│   ├── regime_overlay.py
│   ├── pretrade_check.py
│   └── kill_switch.py
├── research_council/
│   ├── __init__.py
│   ├── schemas.py
│   ├── client.py
│   ├── debate.py
│   ├── memo_store.py
│   ├── analysts/
│   │   ├── __init__.py
│   │   ├── macro.py
│   │   ├── technical.py
│   │   └── sentiment.py
│   └── prompts/
│       ├── macro.md
│       ├── technical.md
│       ├── sentiment.md
│       └── debate.md
├── research/
│   ├── __init__.py
│   ├── schemas.py
│   ├── hypothesis_registry.py
│   ├── decision_log.py
│   └── hypotheses/                 # data, one .md per hypothesis
├── execution/
│   ├── __init__.py
│   ├── schemas.py
│   ├── order_queue.py
│   ├── audit_ledger.py
│   ├── staged/                     # gitignored, runtime state
│   └── connector/
│       ├── __init__.py
│       ├── base.py
│       └── ibkr_paper_connector.py
├── reports/
│   ├── runs/                       # gitignored per-run artifacts
│   └── memos/                      # research memo renders
├── control/
│   └── HALT                        # absent by default; presence = halted
├── notebooks/
│   ├── 00_ibkr_connectivity_check.ipynb
│   └── 01_first_backtest.ipynb
├── cli.py
├── pyproject.toml
├── .env.example
├── .gitignore
├── README.md
├── DECISIONS.md
└── tests/
    ├── conftest.py
    ├── data/
    ├── strategies/
    ├── backtest/
    ├── risk/
    ├── research_council/
    ├── research/
    └── execution/
```

## 3. Phase-by-Phase Build Spec

### Phase 0 — Foundation

Objective: a working, empty skeleton — settings load, IBKR paper connects, one trivial strategy runs end to end through a backtest and a tear sheet.

Files to create:

| File | Purpose |
| --- | --- |
| `pyproject.toml` | dependencies from §1.1, project metadata |
| `.env.example` | `IBKR_HOST`, `IBKR_PORT`, `IBKR_CLIENT_ID`, `ANTHROPIC_API_KEY` placeholders |
| `.gitignore` | `.env`, `data/cache/`, `reports/runs/`, `execution/staged/`, notebook checkpoints |
| `config/settings.py` | Settings (`pydantic BaseSettings`) + `get_settings()` |
| `README.md` | project purpose, quick start |
| `DECISIONS.md` | first entry: why this stack, why this layout |
| `notebooks/00_ibkr_connectivity_check.ipynb` | connect to IBKR paper, print account summary |
| `notebooks/01_first_backtest.ipynb` | pull SPY, buy-and-hold, `backtesting.py`, `quantstats` tear sheet |

Interfaces:

- `Settings`: fields `ibkr_host: str`, `ibkr_port: int`, `ibkr_client_id: int`, `anthropic_api_key: SecretStr`, `data_cache_dir: Path`, `control_dir: Path`. Required fields raise a validation error if missing, with a message naming the missing env var.
- `get_settings() -> Settings`: cached singleton (e.g. `functools.lru_cache`), so it’s read once per process.

Inputs / Outputs:

- Input: a populated `.env` file (not committed).
- Output: a `Settings` instance; downstream modules never read `os.environ` directly, only `get_settings()`.

Tests to write:

- `tests/test_settings.py`: loads from a fixture `.env`; missing required field raises with a clear message; defaults apply where declared.

Acceptance criteria:

- `python -c "from config.settings import get_settings; print(get_settings())"` runs clean against a real `.env`.
- Notebook 00 connects to the IBKR paper account and prints net liquidation value.
- Notebook 01 runs SPY buy-and-hold through `backtesting.py` and renders a `quantstats` HTML tear sheet.
- `DECISIONS.md` has a Phase 0 entry.
- `pytest` passes with zero tests failing, zero live network calls.

### Phase 1 — Data Layer + Baseline Strategies

Objective: a swappable data source behind one interface, a local cache, and three baseline strategies behind one strategy interface.

Files to create:

| File | Purpose |
| --- | --- |
| `data/schemas.py` | `OHLCVBar`, `PriceFrame` validation helpers |
| `data/providers/base.py` | abstract `DataProvider` |
| `data/providers/ibkr_provider.py` | `ib_async`-backed implementation |
| `data/providers/yfinance_provider.py` | fallback implementation |
| `data/cache_store.py` | Parquet-backed cache read/write |
| `strategies/base.py` | abstract `Strategy` |
| `strategies/registry.py` | name → class lookup for the CLI |
| `strategies/buy_and_hold.py` | baseline 1 |
| `strategies/ma_crossover.py` | baseline 2 |
| `strategies/inverse_vol_blend.py` | baseline 3 (`SPY`/`GLD`) |

Interfaces:

- `DataProvider.get_history(symbol: str, start: date, end: date, interval: str = "1d") -> pd.DataFrame`
  - columns: `[open, high, low, close, volume]`
  - `DatetimeIndex` named `date`
  - the bar for date `D` must contain only information available by `D`’s close
- `DataProvider.get_multiple(symbols: list[str], start: date, end: date, interval: str = "1d") -> dict[str, pd.DataFrame]`
- `CacheStore.get(key: str) -> pd.DataFrame | None`
- `CacheStore.set(key: str, df: pd.DataFrame) -> None`
- `Strategy.name: str` (class attribute)
- `Strategy.required_symbols: list[str]` (class attribute)
- `Strategy.generate_weights(data: dict[str, pd.DataFrame], memo: "ResearchMemo | None" = None) -> pd.Series`
  - index: `(date, symbol)` `MultiIndex`
  - values: target weight, bounded per strategy’s declared range
  - must be point-in-time safe: weight for date `D` uses only data up to and including `D`

Inputs / Outputs:

- Input: `data = {"SPY": df_spy, "GLD": df_gld}`, each 2015-01-01 → 2026-01-01 daily bars.
- Output: `pd.Series` with `MultiIndex` `(date, symbol)`, e.g. `(2024-06-03, "SPY") → 0.6`, `(2024-06-03, "GLD") → 0.4`.

Tests to write:

- `tests/data/test_providers.py` — schema conformance for each provider, using a mocked client.
- `tests/data/test_cache_store.py` — write/read round-trip is byte-identical.
- `tests/data/test_lookahead_guard.py` — a provider never returns a bar dated after the requested end.
- `tests/strategies/test_interface_conformance.py` — parametrized over every registered strategy: output index type, value bounds, no NaN.
- `tests/strategies/test_buy_and_hold.py`, `test_ma_crossover.py`, `test_inverse_vol_blend.py` — behavior on small synthetic, hand-checkable data.

Acceptance criteria:

- All three strategies pass the conformance test.
- A repeated data pull for an already-cached range makes zero network calls (verified via a mock assertion).
- A data gap (e.g. a missing trading day) surfaces a logged warning, never a silent forward-fill.
- `quantdesk data pull --symbol SPY --start 2015-01-01` fetches and caches end to end.

### Phase 2 — Validation Engine

Objective: one backtest interface over both `backtesting.py` and `vectorbt`, plus walk-forward, Monte Carlo, regime segmentation, and reproducible run cards.

Files to create:

| File | Purpose |
| --- | --- |
| `backtest/schemas.py` | `BacktestConfig`, `BacktestResult`, `RunCard` |
| `backtest/runner.py` | `run_backtest(...)` |
| `backtest/adapters/backtesting_py_adapter.py` | wraps `backtesting.py` |
| `backtest/adapters/vectorbt_adapter.py` | wraps `vectorbt` |
| `backtest/benchmarks.py` | benchmark return series |
| `backtest/run_card.py` | writes `run_card.json` / `.md` |
| `backtest/validation/walk_forward.py` | rolling train/test splits |
| `backtest/validation/monte_carlo.py` | trade-sequence resampling |
| `backtest/validation/regime.py` | regime labeling |

Interfaces:

- `run_backtest(strategy, data, config, engine="vectorbt") -> BacktestResult`
- `walk_forward_split(data, n_splits, train_ratio) -> list[tuple[pd.DataFrame, pd.DataFrame]]`
- `monte_carlo_resample(trade_returns, n_sims, method="bootstrap", seed=None) -> MonteCarloResult`
- `segment_by_regime(data, method="vix" | "realized_vol" | "trend") -> pd.Series`
- `write_run_card(result, hypothesis_id=None) -> Path`

Inputs / Outputs:

- Input to `run_backtest`: a `Strategy` instance, cached price data, `BacktestConfig(start, end, initial_capital, commission_bps, slippage_bps)`.
- Output: a `BacktestResult`, and on disk `reports/runs/<run_id>/run_card.json` + `run_card.md`.

Tests to write:

- `tests/backtest/test_runner.py` — a strategy that never trades yields 0% return and 0 drawdown; a hand-computable synthetic case matches expected metrics.
- `tests/backtest/test_walk_forward.py` — splits are chronological, non-overlapping, correct count/size.
- `tests/backtest/test_monte_carlo.py` — fixed seed is deterministic; resampled mean converges to the input mean as `n_sims` grows.
- `tests/backtest/test_regime.py` — an engineered volatility spike in synthetic data is correctly flagged.
- `tests/backtest/test_run_card.py` — JSON round-trip, all required fields present, markdown renders without error.
- `tests/backtest/test_no_lookahead.py` — a strategy deliberately fed future data is caught by an automated check, not silently accepted.

Acceptance criteria:

- The same strategy run through both adapters produces metrics within a documented tolerance; any expected divergence is written down.
- Every backtest run automatically writes a run card.
- `quantdesk backtest ma_crossover --walk-forward --monte-carlo` runs the full validation suite in one command.
- The Phase 2 test suite runs in CI in under 2 minutes on synthetic fixtures — no live data required.

### Phase 3 — Risk Management

Objective: every proposed order — simulated or real — passes through one non-bypassable pre-trade check, and a filesystem kill switch halts everything immediately.

Files to create:

| File | Purpose |
| --- | --- |
| `risk/schemas.py` | `Mandate`, `ProposedOrder`, `CheckResult` |
| `risk/sizing.py` | position/exposure caps |
| `risk/regime_overlay.py` | regime-based deleveraging |
| `risk/pretrade_check.py` | the one gate every order passes through |
| `risk/kill_switch.py` | halt / resume / check |

Interfaces:

- `apply_position_caps(weights, max_position, max_gross_exposure) -> pd.Series`
- `apply_regime_deleverage(weights, regime_labels, deleverage_map) -> pd.Series`
- `pretrade_check(order, mandate) -> CheckResult`
- `is_halted() -> bool`
- `halt(reason: str) -> None`
- `resume() -> None`

Inputs / Outputs:

- Input to `pretrade_check`: one `ProposedOrder` (symbol, side, quantity or notional) + the active `Mandate`.
- Output: `CheckResult`, always logged regardless of outcome — approvals and denials both leave a record.

Tests to write:

- `tests/risk/test_sizing.py` — boundary behavior exactly at `max_position` (pass) vs. `max_position + epsilon` (clipped).
- `tests/risk/test_regime_overlay.py` — deleverage applies only to the flagged regime, other periods untouched.
- `tests/risk/test_pretrade_check.py` — out-of-universe symbol denied with a clear reason; oversized order denied; halted state denies unconditionally, before any other check runs.
- `tests/risk/test_kill_switch.py` — `halt()` creates the file with reason + timestamp; `is_halted()` reflects it immediately; `resume()` removes it.

Acceptance criteria:

- No code path from strategy weights to an order exists that bypasses `pretrade_check` — verified by a repo-wide search/lint rule Copilot can check for (`connector.submit_order` and `stage_order` calls only appear downstream of a `pretrade_check` call).
- `run_backtest` also respects `is_halted()` when configured to, so kill-switch behavior is exercised in backtests before it ever matters live.
- `risk/pretrade_check.py` has at least 90% branch coverage.

### Phase 4 — Research Council

Objective: three analyst agents and a debate step producing a versioned research memo — advisory only, never a trade instruction, and never required (every strategy must still run with `memo=None`).

Files to create:

| File | Purpose |
| --- | --- |
| `research_council/schemas.py` | `MarketContext`, `AnalystReport`, `ResearchMemo` |
| `research_council/client.py` | Anthropic API wrapper |
| `research_council/analysts/macro.py` | `run_macro_analyst` |
| `research_council/analysts/technical.py` | `run_technical_analyst` |
| `research_council/analysts/sentiment.py` | `run_sentiment_analyst` |
| `research_council/debate.py` | `run_debate` |
| `research_council/memo_store.py` | save/load memos |
| `research_council/prompts/*.md` | one prompt template per role |

Interfaces:

- `MarketContext`
- `AnalystReport`
- `ResearchMemo`
- `run_macro_analyst(context) -> AnalystReport`
- `run_technical_analyst(context) -> AnalystReport`
- `run_sentiment_analyst(context) -> AnalystReport`
- `run_debate(reports) -> ResearchMemo`
- `save_memo(memo) -> Path`
- `load_memo(memo_id) -> ResearchMemo`

Inputs / Outputs:

- Input: a `MarketContext` for SPY on a given date.
- Output: `ResearchMemo` saved as `research/memos/<symbol>/<date>.json` + a rendered `.md` alongside it.

Tests to write:

- `tests/research_council/test_schemas.py` — malformed LLM output (e.g. confidence outside `[0,1]`) is rejected by validation.
- `tests/research_council/test_client.py` — mocked API; retry-on-failure and timeout handled without a real network call.
- `tests/research_council/test_analysts.py` — mocked client returning a fixed structured response → each analyst function returns a correctly typed `AnalystReport`.
- `tests/research_council/test_debate.py` — canned all-bullish input vs. mixed input; mixed input must not silently produce high confidence.
- `tests/research_council/test_memo_store.py` — save/load round-trip is lossless.

Acceptance criteria:

- Zero live network calls in the default `pytest` run — everything mocked.
- Every Phase 1 strategy still passes its tests with `memo=None`, proving the council is genuinely optional, not a hidden dependency.
- `quantdesk research SPY` produces a memo end to end against the real API when run manually (`@pytest.mark.manual`, not part of CI).
- Every research run logs token usage so cost stays visible.

### Phase 5 — Hypothesis Registry & Research Memory

Objective: every strategy idea is a file before it’s a backtest, every backtest links back to the idea that motivated it, and a decision log makes “what did we try and why” answerable from git history alone.

Files to create:

| File | Purpose |
| --- | --- |
| `research/schemas.py` | `Hypothesis`, `DecisionEntry` |
| `research/hypothesis_registry.py` | create / update / link / search |
| `research/decision_log.py` | append-only log writer |

Interfaces:

- `Hypothesis`: `id`, `title`, `statement`, `status`, `created_at`, `linked_run_ids`
- `create_hypothesis(title, statement) -> Hypothesis`
- `update_status(hypothesis_id, status) -> None`
- `link_backtest(hypothesis_id, run_id) -> None`
- `search(query, status=None) -> list[Hypothesis]`
- `DecisionEntry`: `date`, `summary`, `related_hypothesis_ids`, `related_run_ids`
- `append_decision(entry) -> None`

Inputs / Outputs:

- All state lives as plain files: `research/hypotheses/<id>.md` (frontmatter + prose) and `research/decision_log.md` (append-only).

Tests to write:

- `tests/research/test_hypothesis_registry.py` — create/update/link/search round-trip correctly against a temp directory.
- `tests/research/test_decision_log.py` — append never overwrites prior entries; file stays parseable after many appends.

Acceptance criteria:

- Every run card produced from a hypothesis-linked backtest has a non-null `hypothesis_id` resolving to a real file.
- `quantdesk hypothesis list --status active` and `quantdesk hypothesis show <id>` work end to end.
- Manual check: reviewing one week of simulated activity through `git log` + `research/` files alone is enough to reconstruct what was believed and tested, and when.

### Phase 6 — Paper Execution Layer

Objective: a broker connector hardcoded to paper trading, an order queue that requires explicit human approval before anything is submitted, and an append-only audit trail.

Files to create:

| File | Purpose |
| --- | --- |
| `execution/schemas.py` | `ProposedOrder`, `AuditEvent`, `Fill` |
| `execution/connector/base.py` | abstract `BrokerConnector` |
| `execution/connector/ibkr_paper_connector.py` | `ib_async`-backed, paper-only |
| `execution/order_queue.py` | stage / list / approve / reject |
| `execution/audit_ledger.py` | append-only event log |

Interfaces:

- `BrokerConnector.is_paper: bool` (hardcoded True in `ibkr_paper_connector` — structural, not a config flag)
- `BrokerConnector.get_account_summary() -> AccountSummary`
- `BrokerConnector.submit_order(order: ProposedOrder) -> Fill | PendingOrder`
- `stage_order(order: ProposedOrder) -> str`
- `list_staged() -> list[ProposedOrder]`
- `approve(order_id: str) -> None`
- `reject(order_id: str, reason: str) -> None`
- `AuditEvent`: `event_type`, `order_id`, `timestamp`, `detail`
- `record(event: AuditEvent) -> None`

Inputs / Outputs:

- Input: risk-adjusted weights from Phase 3, converted to discrete orders (position value ÷ price).
- Output: `execution/audit_ledger.jsonl`, one line per event, append-only.

Tests to write:

- `tests/execution/test_order_queue.py` — stage → list → approve happy path; reject path confirms nothing was sent to the connector.
- `tests/execution/test_ibkr_paper_connector.py` — mocked `ib_async` client; `is_paper` is hardcoded `True` and cannot be flipped by config.
- `tests/execution/test_audit_ledger.py` — every staged/approved/rejected/filled/halted event is recorded; the module exposes no edit/delete method (test asserts the attempt raises `AttributeError`).
- `tests/execution/test_halt_blocks_execution.py` — with the kill switch active, `approve()` refuses even an already-staged order.

Acceptance criteria:

- Every order reaching `connector.submit_order` passed `pretrade_check` at approval time, no exceptions.
- The only path to IBKR is an explicit `approve()` call — no auto-approval path exists anywhere in the codebase.
- Manual, documented end-to-end test: stage a 1-share SPY order → approve → confirm the fill in the IBKR paper account → confirm all four audit events were recorded.
- The Phase 3 kill-switch test is re-verified here against the real connector mock.

### Phase 7 — Optional / Later

Objective: extend, don’t rebuild — anything here should slot into the interfaces already defined.

| Item | Notes |
| --- | --- |
| Second broker connector (e.g. Alpaca) | implement `BrokerConnector`; reuse the Phase 6 conformance tests as a checklist |
| Local reporting dashboard | start with a static HTML generator reading `reports/runs/*/run_card.json` — no new framework needed yet |
| CI/CD pipeline | GitLab CI: lint, type-check, unit tests, lookahead-guard tests on every push; nightly job re-running backtests against refreshed cached data |

## 4. Cross-Cutting Testing Summary

| Test type | Runs | Examples |
| --- | --- | --- |
| Unit (mocked externals) | every push, CI | all `tests/` files except `@pytest.mark.manual` |
| Conformance (parametrized over implementations) | every push, CI | `DataProvider`, `Strategy`, `BrokerConnector` |
| Manual / live | by hand, documented in PR description | real IBKR paper connection, real Anthropic call |
| Regression fixtures | every push, CI | synthetic OHLCV with known, hand-computable outcomes |

## 5. Definition of Done (applies to every phase)

- All listed files exist and pass their listed tests.
- `ruff`, `black --check`, and `mypy` are clean.
- No secrets committed; `.env` untouched by git.
- `DECISIONS.md` has an entry for the phase.
- Acceptance criteria checklist for the phase is fully checked, not partially.
- For phases 2, 3, 5, and 6: at least one run card / hypothesis / audit event exists in the repo as a worked example, not just passing tests.
