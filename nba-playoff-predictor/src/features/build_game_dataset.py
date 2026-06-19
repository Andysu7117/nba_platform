"""Assemble the per-game modelling dataset from raw team game logs.

``LeagueGameFinder`` returns *two* rows per game (one for each team). We use the
``MATCHUP`` text to figure out which row is the home team (" vs. ") and which is
the away team (" @ "), then pivot to one row per game and attach rolling + Elo
features for both sides.
"""
from __future__ import annotations

import pandas as pd

from src.features.elo import build_elo_features
from src.features.rolling_features import ROLLING_STATS, add_rolling_team_features

# Rolling columns we carry across, prefixed HOME_/AWAY_ in the final dataset.
_ROLLING_FEATURE_BASES = [f"{stat}_LAST_10" for stat in ROLLING_STATS] + [
    "REST_DAYS",
    "IS_BACK_TO_BACK",
]


def _is_home(matchup: str) -> bool:
    """True if a MATCHUP string ('TEAM vs. OPP') denotes a home game."""
    return " vs. " in str(matchup)


def make_game_rows(team_games: pd.DataFrame) -> pd.DataFrame:
    """Collapse two-rows-per-game team logs into one row per game.

    Returns a DataFrame with identity/outcome columns:
    ``GAME_ID, GAME_DATE, SEASON, HOME_TEAM_ID, AWAY_TEAM_ID,
    HOME_TEAM_NAME, AWAY_TEAM_NAME, HOME_SCORE, AWAY_SCORE, HOME_WIN``.
    """
    df = team_games.copy()
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    df["IS_HOME"] = df["MATCHUP"].apply(_is_home)

    home = df[df["IS_HOME"]].copy()
    away = df[~df["IS_HOME"]].copy()

    home_cols = {
        "GAME_ID": "GAME_ID",
        "GAME_DATE": "GAME_DATE",
        "SEASON": "SEASON",
        "TEAM_ID": "HOME_TEAM_ID",
        "TEAM_NAME": "HOME_TEAM_NAME",
        "PTS": "HOME_SCORE",
    }
    away_cols = {
        "GAME_ID": "GAME_ID",
        "TEAM_ID": "AWAY_TEAM_ID",
        "TEAM_NAME": "AWAY_TEAM_NAME",
        "PTS": "AWAY_SCORE",
    }

    home_small = home[list(home_cols)].rename(columns=home_cols)
    away_small = away[list(away_cols)].rename(columns=away_cols)

    games = home_small.merge(away_small, on="GAME_ID", how="inner")
    games["HOME_WIN"] = (games["HOME_SCORE"] > games["AWAY_SCORE"]).astype(int)

    return games.sort_values("GAME_DATE").reset_index(drop=True)


def build_modeling_dataset(team_games: pd.DataFrame) -> pd.DataFrame:
    """Build the full per-game modelling dataset with features and target.

    Steps:
      1. Add team-game rolling features (shifted, leakage-safe).
      2. Collapse to one row per game (home/away identity + outcome).
      3. Merge home-side and away-side rolling features onto each game.
      4. Merge pre-game Elo features.
      5. Build home-minus-away difference features.
    """
    # 1. Rolling features at the team-game grain.
    team_feat = add_rolling_team_features(team_games, window=10)

    # 2. One row per game (identity + outcome).
    games = make_game_rows(team_games)

    # 3. Merge rolling features for each side using (GAME_ID, TEAM_ID).
    feat_cols = ["GAME_ID", "TEAM_ID"] + [
        c for c in _ROLLING_FEATURE_BASES if c in team_feat.columns
    ]
    team_feat_small = team_feat[feat_cols].copy()

    home_feat = team_feat_small.rename(
        columns={"TEAM_ID": "HOME_TEAM_ID", **{c: f"HOME_{c}" for c in _ROLLING_FEATURE_BASES}}
    )
    away_feat = team_feat_small.rename(
        columns={"TEAM_ID": "AWAY_TEAM_ID", **{c: f"AWAY_{c}" for c in _ROLLING_FEATURE_BASES}}
    )

    games = games.merge(home_feat, on=["GAME_ID", "HOME_TEAM_ID"], how="left")
    games = games.merge(away_feat, on=["GAME_ID", "AWAY_TEAM_ID"], how="left")

    # 4. Elo features.
    elo = build_elo_features(games)
    games = games.merge(elo, on="GAME_ID", how="left")

    # 5. Difference features (home minus away).
    games["PLUS_MINUS_DIFF_LAST_10"] = (
        games["HOME_PLUS_MINUS_LAST_10"] - games["AWAY_PLUS_MINUS_LAST_10"]
    )
    games["PTS_DIFF_LAST_10"] = games["HOME_PTS_LAST_10"] - games["AWAY_PTS_LAST_10"]
    games["REB_DIFF_LAST_10"] = games["HOME_REB_LAST_10"] - games["AWAY_REB_LAST_10"]
    games["AST_DIFF_LAST_10"] = games["HOME_AST_LAST_10"] - games["AWAY_AST_LAST_10"]
    games["TOV_DIFF_LAST_10"] = games["HOME_TOV_LAST_10"] - games["AWAY_TOV_LAST_10"]
    games["REST_DIFF"] = games["HOME_REST_DAYS"] - games["AWAY_REST_DAYS"]

    return games.sort_values("GAME_DATE").reset_index(drop=True)
