"""Train the regular-season game-winner model.

Pipeline: median imputation -> standardisation -> logistic regression. We use a
**time-based** 80/20 split (earliest 80% train, latest 20% test) to mimic real
forecasting and avoid leaking future information into the past.

Run as a CLI to do the full fetch -> build -> train -> save cycle::

    python -m src.models.train_game_model
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import joblib

from src.config import (
    DEFAULT_SEASON_TYPE,
    DEFAULT_SEASONS,
    METRICS_PATH,
    MODEL_PATH,
)
from src.models.evaluate import evaluate_predictions


def get_feature_columns() -> list[str]:
    """Return the ordered list of model feature columns."""
    return [
        "ELO_DIFF",
        "ELO_HOME_WIN_PROB",
        "HOME_PLUS_MINUS_LAST_10",
        "AWAY_PLUS_MINUS_LAST_10",
        "PLUS_MINUS_DIFF_LAST_10",
        "HOME_PTS_LAST_10",
        "AWAY_PTS_LAST_10",
        "PTS_DIFF_LAST_10",
        "HOME_REB_LAST_10",
        "AWAY_REB_LAST_10",
        "REB_DIFF_LAST_10",
        "HOME_AST_LAST_10",
        "AWAY_AST_LAST_10",
        "AST_DIFF_LAST_10",
        "HOME_TOV_LAST_10",
        "AWAY_TOV_LAST_10",
        "TOV_DIFF_LAST_10",
        "HOME_REST_DAYS",
        "AWAY_REST_DAYS",
        "REST_DIFF",
        "HOME_IS_BACK_TO_BACK",
        "AWAY_IS_BACK_TO_BACK",
    ]


def _build_pipeline() -> Pipeline:
    """Construct the sklearn modelling pipeline."""
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000)),
        ]
    )


def train_model(dataset: pd.DataFrame) -> dict:
    """Train, evaluate and persist the model from a built modelling dataset.

    Returns the test-set metrics dict (also written to disk).
    """
    features = get_feature_columns()
    data = dataset.sort_values("GAME_DATE").reset_index(drop=True)

    X = data[features]
    y = data["HOME_WIN"].astype(int)

    # ---- Time-based split: first 80% train, final 20% test -------------------
    split_idx = int(len(data) * 0.8)
    if split_idx < 1 or split_idx >= len(data):
        raise ValueError(
            f"Not enough games ({len(data)}) to form a time-based train/test "
            "split. Fetch more seasons before training."
        )

    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    pipeline = _build_pipeline()
    pipeline.fit(X_train, y_train)

    test_prob = pipeline.predict_proba(X_test)[:, 1]
    metrics = evaluate_predictions(y_test.to_numpy(), test_prob)
    metrics["n_train"] = int(len(X_train))
    metrics["n_test"] = int(len(X_test))
    metrics["train_end_date"] = str(data["GAME_DATE"].iloc[split_idx - 1].date())
    metrics["test_start_date"] = str(data["GAME_DATE"].iloc[split_idx].date())

    # ---- Persist model + metrics ---------------------------------------------
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"pipeline": pipeline, "features": features},
        MODEL_PATH,
    )
    with open(METRICS_PATH, "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)

    return metrics


def _run_cli() -> None:
    """Full pipeline: fetch -> build dataset -> train -> save -> print."""
    # Imported here so the module imports cleanly without network deps.
    from src.features.build_game_dataset import build_modeling_dataset
    from src.ingest.fetch_team_games import fetch_multiple_seasons

    print(f"Fetching team games for seasons: {DEFAULT_SEASONS} ...")
    try:
        team_games = fetch_multiple_seasons(DEFAULT_SEASONS, DEFAULT_SEASON_TYPE)
    except Exception as err:  # noqa: BLE001
        print("\n[ERROR] Could not load NBA data.")
        print(f"        {err}")
        print(
            "\nTip: the NBA API can be slow or temporarily unavailable. "
            "Try again, or pre-populate data/raw/ with cached parquet files."
        )
        raise SystemExit(1)

    print(f"Loaded {len(team_games)} team-game rows. Building modelling dataset ...")
    dataset = build_modeling_dataset(team_games)
    print(f"Built dataset with {len(dataset)} games. Training model ...")

    metrics = train_model(dataset)

    print("\n=== Training complete ===")
    print(f"Model saved to:   {MODEL_PATH}")
    print(f"Metrics saved to: {METRICS_PATH}")
    print("\nTest-set metrics:")
    for key in ("accuracy", "log_loss", "brier_score"):
        print(f"  {key:12s}: {metrics[key]:.4f}")
    print(f"  train games : {metrics['n_train']}  (through {metrics['train_end_date']})")
    print(f"  test games  : {metrics['n_test']}  (from {metrics['test_start_date']})")


if __name__ == "__main__":
    _run_cli()
