"""Fetch and cache league-wide per-game player stats.

Powers the Player Stats leaderboard. Uses ``LeagueDashPlayerStats`` which returns
one row per player for a season; cached to parquet so the page works offline once
populated.
"""
from __future__ import annotations

import re
import time

import pandas as pd

from src.config import RAW_DATA_DIR
from src.ingest.cache import cache_dataframe, cache_exists, load_cached_dataframe


def _safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(value).strip())


def _cache_path(season: str, season_type: str, per_mode: str):
    return RAW_DATA_DIR / f"league_player_stats_{_safe(season)}_{_safe(season_type)}_{_safe(per_mode)}.parquet"


def fetch_league_player_stats(
    season: str,
    season_type: str = "Regular Season",
    per_mode: str = "PerGame",
    force_refresh: bool = False,
    max_retries: int = 3,
) -> pd.DataFrame:
    """Return one row per player for a season, cached by season/type/mode."""
    path = _cache_path(season, season_type, per_mode)
    if not force_refresh and cache_exists(path):
        return load_cached_dataframe(path)

    from nba_api.stats.endpoints import leaguedashplayerstats

    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            stats = leaguedashplayerstats.LeagueDashPlayerStats(
                season=season,
                season_type_all_star=season_type,
                per_mode_detailed=per_mode,
                timeout=60,
            )
            df = stats.get_data_frames()[0]
            time.sleep(0.6)
            break
        except Exception as err:  # noqa: BLE001
            last_err = err
            time.sleep(2 ** (attempt - 1))
    else:
        raise RuntimeError(
            f"Failed to fetch league player stats for {season} ({season_type}). "
            f"The NBA API may be unavailable. Original error: {last_err}"
        )

    df = df.copy()
    df["SEASON"] = season
    df["SEASON_TYPE"] = season_type
    cache_dataframe(df, path)
    return df


def load_cached_league_player_stats(
    season: str,
    season_type: str = "Regular Season",
    per_mode: str = "PerGame",
) -> pd.DataFrame | None:
    """Return the cached league player stats, or ``None`` if not cached yet."""
    path = _cache_path(season, season_type, per_mode)
    if not cache_exists(path):
        return None
    return load_cached_dataframe(path)
