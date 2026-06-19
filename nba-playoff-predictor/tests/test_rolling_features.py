"""Tests for leakage-safe rolling features."""
import numpy as np
import pandas as pd

from src.features.rolling_features import add_rolling_team_features


def _fake_team(points):
    return pd.DataFrame(
        {
            "TEAM_ID": [1] * len(points),
            "GAME_DATE": pd.to_datetime(
                [f"2023-01-0{i + 1}" for i in range(len(points))]
            ),
            "PTS": points,
        }
    )


def test_rolling_uses_shift_no_leakage():
    df = _fake_team([100, 110, 120])
    out = add_rolling_team_features(df, window=10).sort_values("GAME_DATE")
    rolled = out["PTS_LAST_10"].tolist()

    # Game 1: no prior games -> NaN.
    assert np.isnan(rolled[0])
    # Game 2: only game 1 counts -> 100.
    assert rolled[1] == 100.0
    # Game 3: games 1 and 2 -> mean(100, 110) = 105.
    assert rolled[2] == 105.0


def test_current_game_excluded_from_its_own_average():
    # If the current game leaked in, game 2's average would be mean(100,110)=105.
    df = _fake_team([100, 110, 120])
    out = add_rolling_team_features(df, window=10).sort_values("GAME_DATE")
    assert out["PTS_LAST_10"].tolist()[1] != 105.0


def test_rest_days_and_back_to_back():
    df = pd.DataFrame(
        {
            "TEAM_ID": [1, 1, 1],
            "GAME_DATE": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-05"]),
            "PTS": [100, 110, 120],
        }
    )
    out = add_rolling_team_features(df).sort_values("GAME_DATE").reset_index(drop=True)
    # Second game is a back-to-back (1 day rest).
    assert out.loc[1, "REST_DAYS"] == 1
    assert out.loc[1, "IS_BACK_TO_BACK"] == 1
    # Third game has 3 days rest, not a back-to-back.
    assert out.loc[2, "REST_DAYS"] == 3
    assert out.loc[2, "IS_BACK_TO_BACK"] == 0
