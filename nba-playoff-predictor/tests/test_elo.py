"""Tests for Elo feature construction."""
import pandas as pd

from src.features.elo import build_elo_features, expected_score


def test_expected_score_equal_ratings():
    # Equal ratings -> coin flip.
    assert abs(expected_score(1500, 1500) - 0.5) < 1e-9


def test_expected_score_higher_rating_favoured():
    # The stronger team should be favoured.
    assert expected_score(1600, 1500) > 0.5
    assert expected_score(1500, 1600) < 0.5


def test_build_elo_features_one_row_per_game():
    games = pd.DataFrame(
        {
            "GAME_ID": ["1", "2", "3"],
            "GAME_DATE": pd.to_datetime(["2023-01-01", "2023-01-03", "2023-01-05"]),
            "HOME_TEAM_ID": [10, 20, 10],
            "AWAY_TEAM_ID": [20, 10, 30],
            "HOME_WIN": [1, 0, 1],
        }
    )
    out = build_elo_features(games)

    assert len(out) == len(games)
    for col in ["GAME_ID", "HOME_ELO_BEFORE", "AWAY_ELO_BEFORE", "ELO_DIFF", "ELO_HOME_WIN_PROB"]:
        assert col in out.columns

    # First game: both teams start at 1500 so the diff is zero.
    first = out[out["GAME_ID"] == "1"].iloc[0]
    assert first["HOME_ELO_BEFORE"] == 1500.0
    assert first["AWAY_ELO_BEFORE"] == 1500.0
    assert first["ELO_DIFF"] == 0.0
