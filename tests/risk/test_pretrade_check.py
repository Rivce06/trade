from __future__ import annotations

from pathlib import Path

import pandas as pd

from risk.kill_switch import halt, is_halted, resume
from risk.pretrade_check import pretrade_check
from risk.schemas import Mandate, ProposedOrder, CheckResult


def test_pretrade_check_rejects_out_of_universe_symbol_and_oversized_order(tmp_path: Path) -> None:
    mandate = Mandate(allowed_symbols=["SPY"], max_order_notional=1000.0, max_gross_exposure=1.0)
    order = ProposedOrder(symbol="QQQ", side="buy", quantity=10, notional=10000.0)
    result = pretrade_check(order, mandate)
    assert result.approved is False
    assert any("allowed_symbols" in reason for reason in result.reasons)

    oversized = ProposedOrder(symbol="SPY", side="buy", quantity=10, notional=5000.0)
    oversized_result = pretrade_check(oversized, mandate)
    assert oversized_result.approved is False


def test_pretrade_check_denies_when_halted(tmp_path: Path) -> None:
    control_dir = tmp_path / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    halt("manual stop", control_dir=control_dir)

    mandate = Mandate(allowed_symbols=["SPY"], max_order_notional=1000.0, max_gross_exposure=1.0)
    order = ProposedOrder(symbol="SPY", side="buy", quantity=1, notional=100.0)
    result = pretrade_check(order, mandate, control_dir=control_dir)
    assert result.approved is False
    assert any("halted" in reason.lower() for reason in result.reasons)

    resume(control_dir=control_dir)
    assert is_halted(control_dir=control_dir) is False
