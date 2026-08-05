"""Schema helpers for OHLCV market data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass(frozen=True)
class OHLCVBar:
    """Single normalized OHLCV bar."""

    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float


PriceFrame = pd.DataFrame


def validate_ohlcv_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize an OHLCV frame to the project contract.

    Args:
        frame: Raw market data frame.

    Returns:
        pd.DataFrame: A normalized frame with lowercase columns and a
        `date`-named DatetimeIndex.
    """

    required = {"open", "high", "low", "close", "volume"}
    normalized = frame.copy()
    normalized.columns = [col.lower() for col in normalized.columns]
    missing = required.difference(normalized.columns)
    if missing:
        raise ValueError(f"Missing required OHLCV columns: {sorted(missing)}")

    normalized = normalized.sort_index()
    normalized.index.name = "date"
    return normalized
