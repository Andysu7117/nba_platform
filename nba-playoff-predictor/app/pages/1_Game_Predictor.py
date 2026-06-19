"""Game Predictor page: predict the winner of a single matchup."""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.app_helpers import build_dataset_from_cache, get_team_options
from src.models.predict import load_model, model_exists, predict_home_win_probability

st.set_page_config(page_title="Game Predictor", page_icon="🔮", layout="wide")
st.title("🔮 Game Predictor")


@st.cache_data(show_spinner="Building dataset from cache...")
def _load_dataset():
    return build_dataset_from_cache()


if not model_exists():
    st.warning(
        "⚠️ No trained model found. Run `python -m src.models.train_game_model` "
        "first, then reload this page."
    )
    st.stop()

dataset = _load_dataset()
if dataset.empty:
    st.error(
        "No cached NBA data found. Train the model (which fetches data) first: "
        "`python -m src.models.train_game_model`."
    )
    st.stop()

teams = get_team_options(dataset)
team_names = list(teams.keys())

st.markdown(
    "Pick a home and away team. The model uses each team's **latest available** "
    "pre-game features (Elo, last-10 rolling stats, rest) from cached data."
)

col1, col2 = st.columns(2)
with col1:
    home_name = st.selectbox("🏠 Home team", team_names, index=0)
with col2:
    default_away = 1 if len(team_names) > 1 else 0
    away_name = st.selectbox("✈️ Away team", team_names, index=default_away)

if home_name == away_name:
    st.info("Please pick two different teams.")
    st.stop()

if st.button("Predict winner", type="primary"):
    model = load_model()
    home_id = teams[home_name]
    away_id = teams[away_name]

    p_home = predict_home_win_probability(home_id, away_id, dataset, model=model)
    p_away = 1.0 - p_home

    c1, c2 = st.columns(2)
    c1.metric(f"🏠 {home_name} win prob", f"{p_home * 100:.1f}%")
    c2.metric(f"✈️ {away_name} win prob", f"{p_away * 100:.1f}%")

    winner = home_name if p_home >= 0.5 else away_name
    st.success(f"🏆 Predicted winner: **{winner}**")
    st.progress(p_home, text=f"Home win probability: {p_home * 100:.1f}%")

    st.caption(
        "Prediction based on latest cached team form, not the live roster. "
        "Educational baseline — not betting advice."
    )
