"""Lightweight local caching helpers built on parquet.

These functions centralise all read/write-to-disk logic so the rest of the
ingestion code can stay agnostic about the storage format.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def cache_exists(path: str | Path) -> bool:
    """Return True if a cache file exists at ``path``."""
    return Path(path).exists()


def cache_dataframe(df: pd.DataFrame, path: str | Path) -> Path:
    """Write ``df`` to ``path`` as parquet, creating parent dirs if needed.

    Falls back to CSV only if parquet writing fails for any reason (e.g. a
    missing parquet engine), so the app degrades gracefully.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(path, index=False)
    except Exception:  # pragma: no cover - defensive fallback
        csv_path = path.with_suffix(".csv")
        df.to_csv(csv_path, index=False)
        return csv_path
    return path


def load_cached_dataframe(path: str | Path) -> pd.DataFrame:
    """Load a cached DataFrame previously written by :func:`cache_dataframe`."""
    path = Path(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    return pd.read_parquet(path)
