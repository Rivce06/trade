from __future__ import annotations

from pathlib import Path

from risk.kill_switch import halt, is_halted, resume


def test_kill_switch_writes_reason_and_timestamp(tmp_path: Path) -> None:
    control_dir = tmp_path / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    halt("test stop", control_dir=control_dir)
    assert is_halted(control_dir=control_dir) is True

    resume(control_dir=control_dir)
    assert is_halted(control_dir=control_dir) is False
