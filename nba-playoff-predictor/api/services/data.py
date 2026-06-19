"""Cached access to the heavy, slow-to-build data artifacts.

Building the modelling dataset and loading the model are expensive, so we memoise
them process-wide with ``lru_cache``. The cache is cleared on demand (e.g. after a
data refresh) via :func:`clear_caches`.
"""
from __future__ import annotations

from functools import lru_cache

import pandas as pd

from src.app_helpers import build_dataset_from_cache, load_cached_team_games
from src.config import DEFAULT_SEASONS
from src.features.build_game_dataset import make_game_rows
from src.models.predict import load_model, model_exists

#: The season the UI treats as "current" (most recent configured season).
CURRENT_SEASON: str = DEFAULT_SEASONS[-1]


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
