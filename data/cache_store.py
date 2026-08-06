"""Parquet-backed local cache for price history.

The cache stores a dataframe on disk for a requested key and reads it back
byte-for-byte stable for repeated fetches.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class CacheStore:
    """Simple key-value cache for market data frames."""

    def __init__(self, base_dir: str | Path = "data/cache") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        return self.base_dir / f"{key}.parquet"

    def get(self, key: str) -> pd.DataFrame | None:
        """Return a cached frame for `key`, or `None` if no cached file exists."""

        path = self._path_for(key)
        if not path.exists():
            return None
        return pd.read_parquet(path)

    def set(self, key: str, df: pd.DataFrame) -> None:
        """Persist a dataframe to the local cache under `key`."""

        path = self._path_for(key)
        df.to_parquet(path)
