"""Rolling pre-game team features.

The cardinal rule here is **no data leakage**: every feature describing a game
must be computable *before tip-off*. We therefore ``shift(1)`` each team's
series before taking a rolling mean, so the value attached to game *N* only ever
uses games ``1 .. N-1``.
"""
from __future__ import annotations

import pandas as pd

# Box-score stats we roll into "last-N" averages.
ROLLING_STATS: list[str] = [
    "PTS",
    "PLUS_MINUS",
    "FG_PCT",
    "FG3_PCT",
    "FT_PCT",
    "REB",
    "AST",
    "STL",
    "BLK",
    "TOV",
]


def add_rolling_team_features(
    team_games: pd.DataFrame,
    window: int = 10,
) -> pd.DataFrame:
    """Add shifted rolling-average, rest-day and back-to-back features.

    Parameters
    ----------
    team_games:
        One row per team per game (as returned by LeagueGameFinder), containing
        at least ``TEAM_ID``, ``GAME_DATE`` and the box-score stat columns.
    window:
        Rolling window length (default 10 -> ``*_LAST_10`` columns).

    Returns
    -------
    pd.DataFrame
        Copy of the input with added ``<STAT>_LAST_{window}`` columns plus
        ``REST_DAYS`` and ``IS_BACK_TO_BACK``.
    """
    df = team_games.copy()
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    df = df.sort_values(["TEAM_ID", "GAME_DATE"]).reset_index(drop=True)

    grouped = df.groupby("TEAM_ID", group_keys=False)

    for stat in ROLLING_STATS:
        if stat not in df.columns:
            # Some stats may be absent depending on the endpoint; skip safely.
            continue
        col = f"{stat}_LAST_{window}"
        # shift(1) first -> the current game is excluded from its own average.
        df[col] = grouped[stat].apply(
            lambda s: s.shift(1).rolling(window, min_periods=1).mean()
        )

    # Rest days = gap since the team's previous game. First game of the sample
    # for a team is NaN (handled downstream in the modelling imputation step).
    df["REST_DAYS"] = grouped["GAME_DATE"].apply(lambda s: s.diff().dt.days)

    # Back-to-back when there was exactly one calendar day between games.
    df["IS_BACK_TO_BACK"] = (df["REST_DAYS"] == 1).astype(int)

    return df
