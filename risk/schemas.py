"""Schema definitions for risk checks and mandates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Mandate:
    """Active trading mandate used by pre-trade validation."""

    allowed_symbols: list[str]
    max_order_notional: float
    max_gross_exposure: float


@dataclass(frozen=True)
class ProposedOrder:
    """A proposed trade request before approval or execution."""

    symbol: str
    side: str
    quantity: int
    notional: float


@dataclass(frozen=True)
class CheckResult:
    """Boolean approval result plus human-readable reasons."""

    approved: bool
    reasons: list[str]
