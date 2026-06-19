"""Project-wide configuration constants and directory setup.

All paths are resolved relative to the project root so the app works
regardless of the current working directory it is launched from.
"""
from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# config.py lives in <project_root>/src/, so the project root is two levels up.
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]

DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
MODEL_DIR: Path = PROJECT_ROOT / "models"

DB_PATH: Path = DATA_DIR / "nba.duckdb"
MODEL_PATH: Path = MODEL_DIR / "game_win_model.joblib"
METRICS_PATH: Path = MODEL_DIR / "game_win_model_metrics.json"

# ---------------------------------------------------------------------------
# Data defaults
# ---------------------------------------------------------------------------
DEFAULT_SEASONS: list[str] = ["2019-20", "2020-21","2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]
DEFAULT_SEASON_TYPE: str = "Regular Season"

# Rolling-feature window used across feature engineering.
ROLLING_WINDOW: int = 10


def ensure_directories() -> None:
    """Create all project data/model directories if they do not yet exist."""
    for directory in (DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, MODEL_DIR):
        directory.mkdir(parents=True, exist_ok=True)


# Create directories automatically on import so downstream code can assume
# they exist.
ensure_directories()
