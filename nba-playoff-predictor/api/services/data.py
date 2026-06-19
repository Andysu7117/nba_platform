"""Cached access to the heavy, slow-to-build data artifacts.

Building the modelling dataset and loading the model are expensive, so we memoise
them process-wide with ``lru_cache``. The cache is cleared on demand (e.g. after a
data refresh) via :func:`clear_caches`.
"""
from __future__ import annotations

import datetime as dt
from functools import lru_cache

import pandas as pd

from src.app_helpers import build_dataset_from_cache, load_cached_team_games
from src.config import DEFAULT_SEASON_TYPE, DEFAULT_SEASONS
from src.features.build_game_dataset import make_game_rows
from src.models.predict import load_model, model_exists

#: The season the UI treats as "current" (most recent configured season).
CURRENT_SEASON: str = DEFAULT_SEASONS[-1]

#: Tracks the last calendar day we re-pulled the current season from the API,
#: so the auto-refresh runs at most once per day per process.
_last_refresh_day: dt.date | None = None


@lru_cache(maxsize=1)
def all_team_games() -> pd.DataFrame:
    """Every cached team-game row across all seasons (empty if none cached)."""
    return load_cached_team_games()


def team_games_for_season(season: str) -> pd.DataFrame:
    """The cached team-game rows for a single season."""
    df = all_team_games()
    if df.empty:
        return df
    return df[df["SEASON"] == season].copy()


@lru_cache(maxsize=1)
def game_rows() -> pd.DataFrame:
    """One row per game (home/away identity + final score), all seasons."""
    df = all_team_games()
    if df.empty:
        return df
    return make_game_rows(df)


@lru_cache(maxsize=1)
def modeling_dataset() -> pd.DataFrame:
    """The full feature dataset used by the predictor and simulator."""
    return build_dataset_from_cache()


@lru_cache(maxsize=1)
def get_model() -> dict | None:
    """The trained model bundle, or ``None`` when it has not been trained yet."""
    if not model_exists():
        return None
    return load_model()


def has_model() -> bool:
    return get_model() is not None


def clear_caches() -> None:
    """Drop all memoised artifacts (use after refreshing the underlying data)."""
    for fn in (all_team_games, game_rows, modeling_dataset, get_model):
        fn.cache_clear()


def ensure_fresh_current_season(force: bool = False) -> bool:
    """Re-pull the current season from the NBA API at most once per calendar day.

    Keeps standings, records and predictions current without re-fetching on every
    request. Best-effort: if the API is unreachable we keep the existing cache and
    simply try again the next day. Returns ``True`` when a refresh actually ran.
    """
    global _last_refresh_day
    today = dt.date.today()
    if not force and _last_refresh_day == today:
        return False
    # Mark the attempt up front so a transient failure doesn't retry all day.
    _last_refresh_day = today
    try:
        from src.ingest.fetch_team_games import fetch_team_games

        fetch_team_games(CURRENT_SEASON, DEFAULT_SEASON_TYPE, force_refresh=True)
        clear_caches()
        return True
    except Exception:  # noqa: BLE001 - offline / API down: keep stale cache
        return False
