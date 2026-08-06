# QuantDesk Architecture

## Purpose

QuantDesk is a research-first, paper-trading-oriented systematic trading platform. Its goal is to let a user test hypotheses, evaluate strategy behavior, enforce risk gates, and optionally consult a research council before any paper or live execution approval.

This project is not an autonomous trading bot. All advisory outputs remain advisory-only, and every order path must still satisfy explicit pre-trade validation.

## High-Level Layers

1. Data Layer
   - Pulls market data through a provider abstraction.
   - Uses a cache to avoid repeated network requests.
   - Normalizes price data into validated OHLCV frames.

2. Strategy Layer
   - Exposes a common `Strategy` interface.
   - Produces point-in-time-safe target weights.
   - Remains usable even when no research memo is available.

3. Validation Layer
   - Runs backtests with a stable adapter interface.
   - Produces metrics, run cards, and statistical validation passes.
   - Attempts to catch lookahead misuse and confirm reproducibility.

4. Risk Layer
   - Applies position caps, regime overlays, and mandatory pre-trade checks.
   - Uses a filesystem kill switch to halt any new order path immediately.

5. Research Council Layer
   - Produces optional research memos from analyst prompts and debate synthesis.
   - Never becomes a hidden dependency of execution or strategy code.

6. Execution Layer
   - Stages orders for explicit approval.
   - Submits only through the paper broker connector.
   - Records an append-only audit trail.

## Core Design Principles

- Interfaces are small and explicit.
- Data and execution boundaries are cleanly separated.
- LLM-generated research is advisory-only.
- Governance is enforced in the risk and execution layers.
- Every operational path is testable without live broker or model calls.

## Data Flow

```text
Market Data -> Cache / Provider -> Strategy -> Backtest Engine
                                      \-> Risk / Pretrade Check -> Order Queue -> Broker Paper Connector
                                      \-> Research Council (optional memo)
```

## Notes

- `memo=None` must remain a valid execution path.
- `pretrade_check` is a mandatory gate on any order path.
- Validation and execution separation is deliberate: the platform may generate ideas and run simulations, but it must not bypass the explicit control path.
