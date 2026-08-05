"""Benchmark helpers for validation runs."""

from __future__ import annotations

import pandas as pd


def benchmark_return_series(data: pd.DataFrame) -> pd.Series:
    """Return a simple benchmark series from closing prices."""

    return data["close"].pct_change().dropna()
