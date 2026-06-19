"""Shared helpers for the Streamlit pages.

Kept free of any ``streamlit`` import so it can also be used from scripts/tests.
The Streamlit pages wrap these in ``st.cache_data`` for performance.
"""
from __future__ import annotations

import glob
import json

import pandas as pd

from src.config import METRICS_PATH, RAW_DATA_DIR
from src.features.build_game_dataset import build_modeling_dataset


def list_cached_team_game_files() -> list[str]:
    """Return paths of all cached team-game parquet files."""
    return sorted(glob.glob(str(RAW_DATA_DIR / "team_games_*.parquet")))


def load_cached_team_games() -> pd.DataFrame:
    """Load and concatenate all cached team-game files.

    Returns an empty DataFrame if no cache exists (so the UI can show a helpful
    message instead of crashing).
    """
    files = list_cached_team_game_files()
    if not files:
        return pd.DataFrame()
    frames = [pd.read_parquet(f) for f in files]
    df = pd.concat(frames, ignore_index=True)
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    return df


def build_dataset_from_cache() -> pd.DataFrame:
    """Build the modelling dataset from whatever is in the local cache."""
    team_games = load_cached_team_games()
    if team_games.empty:
        return pd.DataFrame()
    return build_modeling_dataset(team_games)


def get_team_options(dataset: pd.DataFrame) -> dict[str, int]:
    """Return a ``{team_name: team_id}`` mapping from a built dataset."""
    if dataset.empty:
        return {}
    home = dataset[["HOME_TEAM_ID", "HOME_TEAM_NAME"]].rename(
        columns={"HOME_TEAM_ID": "TEAM_ID", "HOME_TEAM_NAME": "TEAM_NAME"}
    )
    away = dataset[["AWAY_TEAM_ID", "AWAY_TEAM_NAME"]].rename(
        columns={"AWAY_TEAM_ID": "TEAM_ID", "AWAY_TEAM_NAME": "TEAM_NAME"}
    )
    teams = pd.concat([home, away], ignore_index=True).drop_duplicates("TEAM_ID")
    teams = teams.sort_values("TEAM_NAME")
    return {row.TEAM_NAME: int(row.TEAM_ID) for row in teams.itertuples(index=False)}


def load_saved_metrics() -> dict | None:
    """Return the saved model metrics dict, or None if not present."""
    if not METRICS_PATH.exists():
        return None
    with open(METRICS_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)
