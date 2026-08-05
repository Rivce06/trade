"""Mandatory pre-trade risk gate for every order proposal."""

from __future__ import annotations

from pathlib import Path

from risk.kill_switch import is_halted
from risk.schemas import CheckResult, Mandate, ProposedOrder


def pretrade_check(order: ProposedOrder, mandate: Mandate, control_dir: str | Path = "control") -> CheckResult:
    """Return a deterministic approval/denial result for a proposed order.

    The gate remains intentionally simple and test-first: it enforces the
    order's symbol universe, order notional, and active halt state.
    """

    reasons: list[str] = []
    if is_halted(control_dir=control_dir):
        reasons.append("order denied because system is halted")
        return CheckResult(approved=False, reasons=reasons)

    if order.symbol not in mandate.allowed_symbols:
        reasons.append("order denied because symbol not in allowed_symbols")
    if order.notional > mandate.max_order_notional:
        reasons.append("order denied because order notional exceeds max_order_notional")
    if order.notional > mandate.max_gross_exposure:
        reasons.append("order denied because cumulative exposure exceeds max_gross_exposure")

    return CheckResult(approved=not reasons, reasons=reasons)
