"""NBA Playoff Predictor - Streamlit home page."""
from __future__ import annotations

import pathlib
import sys

# Ensure the project root is importable when launched via `streamlit run`.
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.app_helpers import load_cached_team_games, load_saved_metrics
from src.models.predict import model_exists

st.set_page_config(page_title="NBA Playoff Predictor", page_icon="🏀", layout="wide")

st.title("🏀 NBA Playoff Predictor")

st.markdown(
    """
This app **predicts NBA regular-season game winners**, **simulates playoff
series and brackets**, and **visualises player and team statistics**.

It uses only **pre-game features** — Elo ratings, rolling last-10-game averages,
rest days, and back-to-back flags — with a **time-based train/test split** to
avoid data leakage. The baseline model is a logistic regression.

Use the pages in the sidebar:

- **Game Predictor** — pick a home and away team and get win probabilities.
- **Playoff Simulator** — build a 16-team bracket and simulate a champion.
- **Player Stats** — search a player; chart game logs and view career tables.
- **Team Stats** — explore cached team scoring and plus-minus trends.
- **Schedule** — any date's games: win % for upcoming, box scores for finals.
"""
)

st.divider()

# ---- Model status -----------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Model status")
    if model_exists():
        st.success("✅ A trained model is available.")
    else:
        st.warning("⚠️ No trained model found yet.")
        st.markdown(
            "Train one first:\n\n```bash\npython -m src.models.train_game_model\n```"
        )

with col2:
    st.subheader("Cached data")
    team_games = load_cached_team_games()
    if team_games.empty:
        st.info("No cached NBA data found in `data/raw/`. Training will fetch it.")
    else:
        n_games = team_games["GAME_ID"].nunique()
        seasons = ", ".join(sorted(team_games["SEASON"].dropna().unique()))
        st.metric("Cached team-game rows", f"{len(team_games):,}")
        st.caption(f"~{n_games:,} unique games · seasons: {seasons}")

# ---- Saved metrics ----------------------------------------------------------
st.divider()
st.subheader("Saved model metrics")

metrics = load_saved_metrics()
if metrics is None:
    st.info("Metrics will appear here after you train the model.")
else:
    m1, m2, m3 = st.columns(3)
    m1.metric("Accuracy", f"{metrics.get('accuracy', float('nan')):.3f}")
    m2.metric("Log loss", f"{metrics.get('log_loss', float('nan')):.3f}")
    m3.metric("Brier score", f"{metrics.get('brier_score', float('nan')):.3f}")
    if "n_train" in metrics:
        st.caption(
            f"Trained on {metrics['n_train']:,} games "
            f"(through {metrics.get('train_end_date', '?')}), tested on "
            f"{metrics['n_test']:,} games (from {metrics.get('test_start_date', '?')})."
        )

st.divider()
st.markdown(
    """
**Quick start**

1. Train the model (fetches NBA data and caches it locally):
   ```bash
   python -m src.models.train_game_model
   ```
2. Run the app:
   ```bash
   streamlit run app/Home.py
   ```

_This is a baseline model for educational use — **not betting advice**._
"""
)
