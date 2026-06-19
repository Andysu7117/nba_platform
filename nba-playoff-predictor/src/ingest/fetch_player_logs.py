"""Fetch and cache individual player game logs from the NBA stats API."""
from __future__ import annotations

import re
import time

import pandas as pd

from src.config import RAW_DATA_DIR
from src.ingest.cache import cache_dataframe, cache_exists, load_cached_dataframe


def _safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(value).strip())


def find_player(name: str) -> dict | None:
    """Return the best static-player match for ``name`` or None if not found.

    Uses ``nba_api.stats.static.players`` which ships a bundled player list, so
    this works offline.
    """
    from nba_api.stats.static import players

    name = name.strip()
    if not name:
        return None

    matches = players.find_players_by_full_name(name)
    if matches:
        return matches[0]

    # Fall back to a loose contains-match across the full player list.
    lowered = name.lower()
    for player in players.get_players():
        if lowered in player["full_name"].lower():
            return player
    return None


def _cache_path(player_id: int, season: str, season_type: str):
    fname = (
        f"player_log_{player_id}_{_safe_filename(season)}_"
        f"{_safe_filename(season_type)}.parquet"
    )
    return RAW_DATA_DIR / fname


def fetch_player_logs(
    player_id: int,
    season: str,
    season_type: str = "Regular Season",
    force_refresh: bool = False,
    max_retries: int = 3,
) -> pd.DataFrame:
    """Return a player's game log for a season, cached by id/season/type."""
    path = _cache_path(player_id, season, season_type)

    if not force_refresh and cache_exists(path):
        return load_cached_dataframe(path)

    from nba_api.stats.endpoints import playergamelog

    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            log = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=season,
                season_type_all_star=season_type,
                timeout=60,
            )
            df = log.get_data_frames()[0]
            time.sleep(0.6)
            break
        except Exception as err:  # noqa: BLE001
            last_err = err
            time.sleep(2 ** (attempt - 1))
    else:
        raise RuntimeError(
            f"Failed to fetch player logs for player {player_id} "
            f"({season}, {season_type}). The NBA API may be unavailable. "
            f"Original error: {last_err}"
        )

    df = df.copy()
    if "GAME_DATE" in df.columns:
        # PlayerGameLog dates look like 'OCT 25, 2023'.
        df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], format="%b %d, %Y", errors="coerce")
    df["SEASON"] = season
    df["SEASON_TYPE"] = season_type

    cache_dataframe(df, path)
    return df


def fetch_player_career(
    player_id: int,
    per_mode: str = "PerGame",
    force_refresh: bool = False,
    max_retries: int = 3,
) -> dict[str, pd.DataFrame]:
    """Return a player's season-by-season and career-total regular-season stats.

    Parameters
    ----------
    per_mode:
        ``"PerGame"`` or ``"Totals"`` — the page toggles between the two.

    Returns
    -------
    dict with keys ``"season"`` (one row per season played) and ``"career"``
    (a single career-totals row). Both are cached by ``player_id`` + ``per_mode``.
    """
    per_mode = "Totals" if per_mode.lower() == "totals" else "PerGame"
    season_path = RAW_DATA_DIR / f"player_career_season_{player_id}_{per_mode}.parquet"
    career_path = RAW_DATA_DIR / f"player_career_total_{player_id}_{per_mode}.parquet"

    if not force_refresh and cache_exists(season_path) and cache_exists(career_path):
        return {
            "season": load_cached_dataframe(season_path),
            "career": load_cached_dataframe(career_path),
        }

    from nba_api.stats.endpoints import playercareerstats

    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            career = playercareerstats.PlayerCareerStats(
                player_id=player_id,
                per_mode36=per_mode,
                timeout=60,
            )
            season_df = career.season_totals_regular_season.get_data_frame()
            career_df = career.career_totals_regular_season.get_data_frame()
            time.sleep(0.6)
            break
        except Exception as err:  # noqa: BLE001
            last_err = err
            time.sleep(2 ** (attempt - 1))
    else:
        raise RuntimeError(
            f"Failed to fetch career stats for player {player_id}. The NBA API "
            f"may be unavailable. Original error: {last_err}"
        )

    cache_dataframe(season_df, season_path)
    cache_dataframe(career_df, career_path)
    return {"season": season_df, "career": career_df}
