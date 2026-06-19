"""Prediction helpers, designed to be robust for Streamlit usage.

The model is persisted as a dict ``{"pipeline": ..., "features": [...]}`` so the
exact feature ordering travels with the estimator and prediction never depends
on column order at the call site.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import joblib

from src.config import MODEL_PATH
from src.models.train_game_model import get_feature_columns


def model_exists() -> bool:
    """True if a trained model file is present on disk."""
    return MODEL_PATH.exists()


def load_model() -> dict:
    """Load the persisted ``{"pipeline", "features"}`` bundle.

    Raises a friendly error if the model has not been trained yet.
    """
    if not model_exists():
        raise FileNotFoundError(
            "No trained model found. Run `python -m src.models.train_game_model` "
            "first to fetch data and train the model."
        )
    return joblib.load(MODEL_PATH)


def predict_from_feature_dict(features: dict, model: dict | None = None) -> float:
    """Return P(home win) for a single feature dictionary.

    Missing features are passed through as NaN and handled by the pipeline's
    imputer, which keeps this robust to partial inputs from the UI.
    """
    model = model or load_model()
    pipeline = model["pipeline"]
    cols = model.get("features") or get_feature_columns()

    row = {c: features.get(c, np.nan) for c in cols}
    X = pd.DataFrame([row], columns=cols)
    return float(pipeline.predict_proba(X)[:, 1][0])


def predict_home_win_probability(
    home_team_id: int,
    away_team_id: int,
    latest_features_df: pd.DataFrame,
    model: dict | None = None,
) -> float:
    """Predict P(home win) using prepared per-game feature rows.

    ``latest_features_df`` is expected to be a built modelling dataset (one row
    per game with all feature columns). We try, in order:

      1. An exact row already framed as ``home_team_id`` vs ``away_team_id``
         (most recent such game), and
      2. Otherwise, synthesise a feature row from each team's most recent game.
    """
    model = model or load_model()
    cols = model.get("features") or get_feature_columns()

    # 1. Exact existing matchup (home/away as requested) -> use its features.
    exact = latest_features_df[
        (latest_features_df["HOME_TEAM_ID"] == home_team_id)
        & (latest_features_df["AWAY_TEAM_ID"] == away_team_id)
    ]
    if not exact.empty:
        row = exact.sort_values("GAME_DATE").iloc[-1]
        feats = {c: row.get(c, np.nan) for c in cols}
        return predict_from_feature_dict(feats, model)

    # 2. Synthesise from each team's latest available game features.
    feats = build_matchup_features(home_team_id, away_team_id, latest_features_df)
    return predict_from_feature_dict(feats, model)


def _latest_team_side_features(
    team_id: int, dataset: pd.DataFrame
) -> dict[str, float]:
    """Pull a team's most recent rolling/rest/elo values, side-agnostic.

    Returns base feature names (without HOME_/AWAY_ prefix), e.g. ``PTS_LAST_10``.
    """
    games = dataset[
        (dataset["HOME_TEAM_ID"] == team_id) | (dataset["AWAY_TEAM_ID"] == team_id)
    ].sort_values("GAME_DATE")
    if games.empty:
        return {}

    last = games.iloc[-1]
    is_home = last["HOME_TEAM_ID"] == team_id
    prefix = "HOME_" if is_home else "AWAY_"

    bases = [
        "PLUS_MINUS_LAST_10",
        "PTS_LAST_10",
        "REB_LAST_10",
        "AST_LAST_10",
        "TOV_LAST_10",
        "REST_DAYS",
        "IS_BACK_TO_BACK",
    ]
    out: dict[str, float] = {}
    for base in bases:
        col = f"{prefix}{base}"
        out[base] = last.get(col, np.nan)

    # Carry this team's most recent pre-game Elo as an absolute strength proxy.
    out["ELO"] = last.get("HOME_ELO_BEFORE" if is_home else "AWAY_ELO_BEFORE", 1500.0)
    return out


def build_matchup_features(
    home_team_id: int,
    away_team_id: int,
    dataset: pd.DataFrame,
    home_advantage: float = 65.0,
) -> dict[str, float]:
    """Build a full feature dict for an arbitrary home/away matchup.

    Uses each team's latest available rolling features and Elo so the Game
    Predictor and Playoff Simulator can score *any* pairing, even one that has
    not actually occurred.
    """
    from src.features.elo import expected_score

    home = _latest_team_side_features(home_team_id, dataset)
    away = _latest_team_side_features(away_team_id, dataset)

    def g(d: dict, key: str, default: float = np.nan) -> float:
        return d.get(key, default)

    home_elo = g(home, "ELO", 1500.0)
    away_elo = g(away, "ELO", 1500.0)

    feats: dict[str, float] = {
        "ELO_DIFF": home_elo - away_elo,
        "ELO_HOME_WIN_PROB": expected_score(home_elo + home_advantage, away_elo),
        "HOME_PLUS_MINUS_LAST_10": g(home, "PLUS_MINUS_LAST_10"),
        "AWAY_PLUS_MINUS_LAST_10": g(away, "PLUS_MINUS_LAST_10"),
        "HOME_PTS_LAST_10": g(home, "PTS_LAST_10"),
        "AWAY_PTS_LAST_10": g(away, "PTS_LAST_10"),
        "HOME_REB_LAST_10": g(home, "REB_LAST_10"),
        "AWAY_REB_LAST_10": g(away, "REB_LAST_10"),
        "HOME_AST_LAST_10": g(home, "AST_LAST_10"),
        "AWAY_AST_LAST_10": g(away, "AST_LAST_10"),
        "HOME_TOV_LAST_10": g(home, "TOV_LAST_10"),
        "AWAY_TOV_LAST_10": g(away, "TOV_LAST_10"),
        "HOME_REST_DAYS": g(home, "REST_DAYS"),
        "AWAY_REST_DAYS": g(away, "REST_DAYS"),
        "HOME_IS_BACK_TO_BACK": g(home, "IS_BACK_TO_BACK"),
        "AWAY_IS_BACK_TO_BACK": g(away, "IS_BACK_TO_BACK"),
    }
    # Difference features.
    feats["PLUS_MINUS_DIFF_LAST_10"] = (
        feats["HOME_PLUS_MINUS_LAST_10"] - feats["AWAY_PLUS_MINUS_LAST_10"]
    )
    feats["PTS_DIFF_LAST_10"] = feats["HOME_PTS_LAST_10"] - feats["AWAY_PTS_LAST_10"]
    feats["REB_DIFF_LAST_10"] = feats["HOME_REB_LAST_10"] - feats["AWAY_REB_LAST_10"]
    feats["AST_DIFF_LAST_10"] = feats["HOME_AST_LAST_10"] - feats["AWAY_AST_LAST_10"]
    feats["TOV_DIFF_LAST_10"] = feats["HOME_TOV_LAST_10"] - feats["AWAY_TOV_LAST_10"]
    feats["REST_DIFF"] = feats["HOME_REST_DAYS"] - feats["AWAY_REST_DAYS"]
    return feats
