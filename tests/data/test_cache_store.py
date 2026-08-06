from __future__ import annotations

from pathlib import Path

import pandas as pd

from data.cache_store import CacheStore


def test_cache_round_trip_is_byte_identical(tmp_path: Path) -> None:
    store = CacheStore(base_dir=tmp_path)
    frame = pd.DataFrame({"close": [1.0, 2.0]}, index=pd.date_range("2024-01-01", periods=2, freq="D", name="date"))
    store.set("spy", frame)

    cached = store.get("spy")
    assert cached is not None
    assert cached.equals(frame)
    cached.to_parquet(tmp_path / "roundtrip.parquet")
