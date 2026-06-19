"""Elo rating features for NBA games.

Elo gives a single, continuously-updated strength estimate per team. Crucially
for leakage-avoidance, the rating attached to a game is the rating *before* that
game is played; ratings are only updated after the result is known.
"""
from __future__ import annotations

import pandas as pd


def expected_score(rating_a: float, rating_b: float) -> float:
    """Elo expected score (win probability) for A against B.

    Returns ~0.5 when ratings are equal and increases as A's rating exceeds B's.
    """
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def build_elo_features(
    games: pd.DataFrame,
    k: float = 20.0,
    home_advantage: float = 65.0,
) -> pd.DataFrame:
    """Compute pre-game Elo features for a chronologically-ordered set of games.

    Parameters
    ----------
    games:
        One row per game with ``GAME_ID``, ``GAME_DATE``, ``HOME_TEAM_ID``,
        ``AWAY_TEAM_ID`` and ``HOME_WIN`` (1/0).
    k:
        Elo K-factor (update magnitude).
    home_advantage:
        Elo points added to the home team for the win-probability calculation.

    Returns
    -------
    pd.DataFrame
        One row per game with the pre-game Elo features:
        ``GAME_ID, HOME_ELO_BEFORE, AWAY_ELO_BEFORE, ELO_DIFF, ELO_HOME_WIN_PROB``.
    """
    games = games.sort_values("GAME_DATE").reset_index(drop=True)

    ratings: dict[int, float] = {}
    records: list[dict] = []

    def _get(team_id: int) -> float:
        # Every previously-unseen team starts at the standard 1500 baseline.
        return ratings.setdefault(team_id, 1500.0)

    for row in games.itertuples(index=False):
        home_id = row.HOME_TEAM_ID
        away_id = row.AWAY_TEAM_ID

        home_elo = _get(home_id)
        away_elo = _get(away_id)

        # Home-court advantage only nudges the win-probability estimate, not the
        # stored ratings themselves.
        home_win_prob = expected_score(home_elo + home_advantage, away_elo)

        records.append(
            {
                "GAME_ID": row.GAME_ID,
                "HOME_ELO_BEFORE": home_elo,
                "AWAY_ELO_BEFORE": away_elo,
                "ELO_DIFF": home_elo - away_elo,
                "ELO_HOME_WIN_PROB": home_win_prob,
            }
        )

        # ---- Update ratings *after* recording the pre-game snapshot ----------
        home_win = float(row.HOME_WIN)
        ratings[home_id] = home_elo + k * (home_win - home_win_prob)
        ratings[away_id] = away_elo + k * ((1.0 - home_win) - (1.0 - home_win_prob))

    return pd.DataFrame.from_records(records)
