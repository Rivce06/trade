# GitHub Copilot Instructions for QuantDesk

This repository is a research platform for systematic trading ideas, not an autonomous trading bot. The purpose of this codebase is to support backtesting, risk checks, research memo generation, and paper-execution workflows with explicit human oversight.

The stack for this project is:
- Python 3.12
- Dependency management via `pyproject.toml` and `pip install -e .[dev]`
- Data: `pandas`, `numpy`
- Backtesting: `backtesting.py`, `vectorbt`
- Reporting: `quantstats`
- Broker integration: `ib_async`
- AI integration: Anthropic via the `anthropic` SDK
- Schema / configuration: `pydantic` v2 and `pydantic-settings`
- CLI: `typer`
- Testing: `pytest`, `pytest-cov`, `pytest-mock`
- Lint / format / type-check: `ruff`, `black`, `mypy`

Follow the project style rules:
- Every public function and class needs a Google-style docstring and full type hints.
- Do not use bare `except:` blocks.
- Do not use `print()` outside the CLI layer; prefer logging.
- Never commit secrets. All credentials must come from `.env` through `config/settings.py`, and `.env` must remain gitignored.
- Every module that touches money, orders, or the kill switch must achieve at least 90% branch coverage; all other modules should target at least 80% line coverage.

Testing expectations:
- Unit tests must never make live network calls to IBKR or Anthropic. Mock those clients in `tests/`.
- Tests that require a live IBKR paper connection or a live Anthropic API should be marked with `@pytest.mark.manual` and excluded from CI by default.
- Test files should mirror the source tree structure.
- New interfaces should receive a conformance test if they are implementations of a shared abstract interface.

Important operational rules:
- LLM output is advisory-only. Every strategy must still work with `memo=None`.
- No order path may skip `pretrade_check`.
- Use the architecture and implementation roadmap in `docs/` for any guidance not covered here.

Before proposing implementation changes, prefer the repository’s documented conventions and current interfaces. Keep diffs small, test-driven, and reviewable.
