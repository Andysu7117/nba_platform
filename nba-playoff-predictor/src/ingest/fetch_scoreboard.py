"""Fetch and cache the daily scoreboard and per-game box scores.

Powers the Schedule / Current Season page: a date's games with live status,
final scores, and (for finished games) traditional box scores.
"""
from __future__ import annotations

import time

import pandas as pd

from src.config import RAW_DATA_DIR
from src.ingest.cache import cache_dataframe, cache_exists, load_cached_dataframe

# NBA game-status ids: 1 = scheduled (not started), 2 = in progress, 3 = final.
STATUS_SCHEDULED = 1
STATUS_LIVE = 2
STATUS_FINAL = 3


def _scoreboard_cache_path(date_str: str):
    return RAW_DATA_DIR / f"scoreboard_{date_str}.parquet"


def _boxscore_cache_path(game_id: str):
    return RAW_DATA_DIR / f"boxscore_{game_id}.parquet"


def _normalise_scoreboard(header: pd.DataFrame, line: pd.DataFrame) -> pd.DataFrame:
    """Combine ScoreboardV2 GameHeader + LineScore into one row per game."""
    gh = header[
        [
            "GAME_ID",
            "GAME_STATUS_ID",
            "GAME_STATUS_TEXT",
            "HOME_TEAM_ID",
            "VISITOR_TEAM_ID",
            "GAME_DATE_EST",
        ]
    ].copy()
    # The two endpoints can disagree on key dtypes (object vs int), which breaks
    # the merges below. Normalise the join keys first.
    gh["GAME_ID"] = gh["GAME_ID"].astype(str)
    gh["HOME_TEAM_ID"] = pd.to_numeric(gh["HOME_TEAM_ID"], errors="coerce").astype("Int64")
    gh["VISITOR_TEAM_ID"] = pd.to_numeric(gh["VISITOR_TEAM_ID"], errors="coerce").astype("Int64")

    ls = line.copy()
    ls["GAME_ID"] = ls["GAME_ID"].astype(str)
    ls["TEAM_ID"] = pd.to_numeric(ls["TEAM_ID"], errors="coerce").astype("Int64")
    ls["FULL_NAME"] = (
        ls["TEAM_CITY_NAME"].fillna("").str.strip()
        + " "
        + ls["TEAM_NAME"].fillna("").str.strip()
    ).str.strip()
    ls_small = ls[["GAME_ID", "TEAM_ID", "FULL_NAME", "TEAM_ABBREVIATION", "PTS"]]

    # GameHeader occasionally leaves a side's team id null for upcoming games;
    # the LineScore still lists both teams, so backfill the missing side there.
    teams_by_game = ls.groupby("GAME_ID")["TEAM_ID"].apply(
        lambda s: [t for t in s.tolist() if pd.notna(t)]
    ).to_dict()

    def _backfill(row: pd.Series) -> pd.Series:
        ids = teams_by_game.get(row["GAME_ID"], [])
        home, visitor = row["HOME_TEAM_ID"], row["VISITOR_TEAM_ID"]
        if pd.isna(home) and pd.notna(visitor):
            home = next((t for t in ids if t != visitor), home)
        if pd.isna(visitor) and pd.notna(home):
            visitor = next((t for t in ids if t != home), visitor)
        return pd.Series({"HOME_TEAM_ID": home, "VISITOR_TEAM_ID": visitor})

    gh[["HOME_TEAM_ID", "VISITOR_TEAM_ID"]] = gh.apply(_backfill, axis=1)

    home = ls_small.rename(
        columns={
            "TEAM_ID": "HOME_TEAM_ID",
            "FULL_NAME": "HOME_TEAM_NAME",
            "TEAM_ABBREVIATION": "HOME_ABBR",
            "PTS": "HOME_PTS",
        }
    )
    away = ls_small.rename(
        columns={
            "TEAM_ID": "VISITOR_TEAM_ID",
            "FULL_NAME": "AWAY_TEAM_NAME",
            "TEAM_ABBREVIATION": "AWAY_ABBR",
            "PTS": "AWAY_PTS",
        }
    )

    games = gh.merge(home, on=["GAME_ID", "HOME_TEAM_ID"], how="left")
    games = games.merge(away, on=["GAME_ID", "VISITOR_TEAM_ID"], how="left")
    games = games.rename(columns={"VISITOR_TEAM_ID": "AWAY_TEAM_ID"})
    return games.reset_index(drop=True)


def _fetch_scoreboard_api(date_str: str, max_retries: int = 3) -> pd.DataFrame:
    from nba_api.stats.endpoints import scoreboardv2

    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            sb = scoreboardv2.ScoreboardV2(game_date=date_str, timeout=60)
            header = sb.game_header.get_data_frame()
            line = sb.line_score.get_data_frame()
            time.sleep(0.6)
            if header.empty:
                # No games that day -> return an empty, correctly-typed frame.
                return pd.DataFrame(
                    columns=[
                        "GAME_ID", "GAME_STATUS_ID", "GAME_STATUS_TEXT",
                        "HOME_TEAM_ID", "AWAY_TEAM_ID", "GAME_DATE_EST",
                        "HOME_TEAM_NAME", "HOME_ABBR", "HOME_PTS",
                        "AWAY_TEAM_NAME", "AWAY_ABBR", "AWAY_PTS",
                    ]
                )
            return _normalise_scoreboard(header, line)
        except Exception as err:  # noqa: BLE001
            last_err = err
            time.sleep(2 ** (attempt - 1))

    raise RuntimeError(
        f"Failed to fetch the scoreboard for {date_str}. The NBA API may be "
        f"unavailable. Original error: {last_err}"
    )


def fetch_scoreboard(date_str: str, force_refresh: bool = False) -> pd.DataFrame:
    """Return one-row-per-game scoreboard for ``date_str`` (``YYYY-MM-DD``).

    Strategy: a cached scoreboard is returned immediately for responsiveness;
    callers can pass ``force_refresh=True`` (a UI "Refresh" button) to pull live
    scores. If a live fetch fails, we fall back to any cache so the page still
    works when the API is down.
    """
    path = _scoreboard_cache_path(date_str)

    if not force_refresh and cache_exists(path):
        return load_cached_dataframe(path)

    try:
        df = _fetch_scoreboard_api(date_str)
    except Exception:
        if cache_exists(path):
            return load_cached_dataframe(path)
        raise

    cache_dataframe(df, path)
    return df


def fetch_box_score(game_id: str, force_refresh: bool = False, max_retries: int = 3) -> pd.DataFrame:
    """Return the traditional player box score for a finished game (cached).

    Final box scores never change, so this cache is permanent once written.
    """
    game_id = str(game_id)
    path = _boxscore_cache_path(game_id)

    if not force_refresh and cache_exists(path):
        return load_cached_dataframe(path)

    from nba_api.stats.endpoints import boxscoretraditionalv2

    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            bs = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id, timeout=60)
            players = bs.player_stats.get_data_frame()
            time.sleep(0.6)
            cache_dataframe(players, path)
            return players
        except Exception as err:  # noqa: BLE001
            last_err = err
            time.sleep(2 ** (attempt - 1))

    raise RuntimeError(
        f"Failed to fetch the box score for game {game_id}. The NBA API may be "
        f"unavailable. Original error: {last_err}"
    )
