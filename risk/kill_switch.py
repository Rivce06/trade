"""Filesystem-based kill switch for QuantDesk risk governance."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


def is_halted(control_dir: str | Path = "control") -> bool:
    """Return `True` when the filesystem HALT file is present."""

    control_path = Path(control_dir)
    return (control_path / "HALT").exists()


def halt(reason: str, control_dir: str | Path = "control") -> None:
    """Write a HALT file that immediately blocks downstream execution."""

    control_path = Path(control_dir)
    control_path.mkdir(parents=True, exist_ok=True)
    halt_path = control_path / "HALT"
    halt_path.write_text(f"{reason} | {datetime.utcnow().isoformat()}Z")


def resume(control_dir: str | Path = "control") -> None:
    """Remove the HALT file, returning the system to a runnable state."""

    halt_path = Path(control_dir) / "HALT"
    if halt_path.exists():
        halt_path.unlink()
