"""Fetch and cache team game logs from the NBA stats API.

Uses ``LeagueGameFinder`` which returns one row *per team per game*. Each
season is cached to its own parquet file so we never re-hit the NBA endpoints
unnecessarily, and so the app remains usable from cache if the API is down.
"""
from __future__ import annotations

import re
import time

import pandas as pd

from src.config import RAW_DATA_DIR
from src.ingest.cache import cache_dataframe, cache_exists, load_cached_dataframe


def _safe_filename(value: str) -> str:
    """Make a string safe to embed in a filename (e.g. 'Regular Season')."""
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())


def _cache_path(season: str, season_type: str):
    fname = f"team_games_{_safe_filename(season)}_{_safe_filename(season_type)}.parquet"
    return RAW_DATA_DIR / fname


def _fetch_from_api(season: str, season_type: str, max_retries: int = 3) -> pd.DataFrame:
    """Call LeagueGameFinder with polite retry/backoff.

    Imported lazily so the rest of the app (and the test suite) does not require
    network access or the nba_api package just to import this module.
    """
    from nba_api.stats.endpoints import leaguegamefinder

    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            finder = leaguegamefinder.LeagueGameFinder(
                season_nullable=season,
                season_type_nullable=season_type,
                league_id_nullable="00",  # NBA
                timeout=60,
            )
            df = finder.get_data_frames()[0]
            # Be polite to the NBA servers between successful calls.
            time.sleep(0.6)
            return df
        except Exception as err:  # noqa: BLE001 - we want to retry on any error
            last_err = err
            # Exponential-ish backoff: 1s, 2s, 4s ...
            time.sleep(2 ** (attempt - 1))

    raise RuntimeError(
        f"Failed to fetch team games for {season} ({season_type}) after "
        f"{max_retries} attempts. The NBA API may be unavailable. "
        f"Original error: {last_err}"
    )


def fetch_team_games(
    season: str,
    season_type: str = "Regular Season",
    force_refresh: bool = False,
) -> pd.DataFrame:
    """Return team game logs for one season, using a local cache when possible.

    Parameters
    ----------
    season:
        Season string, e.g. ``"2023-24"``.
    season_type:
        ``"Regular Season"`` or ``"Playoffs"``.
    force_refresh:
        If True, ignore any cache and re-fetch from the API.
    """
    path = _cache_path(season, season_type)

    if not force_refresh and cache_exists(path):
        return load_cached_dataframe(path)

    df = _fetch_from_api(season, season_type)

    # ---- Standardise columns -------------------------------------------------
    df = df.copy()
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    df["SEASON"] = season
    df["SEASON_TYPE"] = season_type

    cache_dataframe(df, path)
    return df


def fetch_multiple_seasons(
    seasons: list[str],
    season_type: str = "Regular Season",
) -> pd.DataFrame:
    """Fetch (and cache) several seasons and concatenate them.

    Seasons that fail to fetch *and* have no cache are skipped with a warning so
    one bad season does not sink the whole pipeline.
    """
    frames: list[pd.DataFrame] = []
    for season in seasons:
        try:
            frames.append(fetch_team_games(season, season_type))
        except Exception as err:  # noqa: BLE001
            print(f"[warn] Skipping season {season}: {err}")

    if not frames:
        raise RuntimeError(
            "No team-game data could be loaded for any requested season. "
            "Check your internet connection / the NBA API, or pre-populate "
            "the cache in data/raw/."
        )

    return pd.concat(frames, ignore_index=True)
