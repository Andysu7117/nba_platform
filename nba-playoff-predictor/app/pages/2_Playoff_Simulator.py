"""Playoff Simulator page: build a 16-team bracket and simulate a champion."""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from src.app_helpers import build_dataset_from_cache, get_team_options
from src.models.predict import (
    build_matchup_features,
    load_model,
    model_exists,
    predict_from_feature_dict,
)
from src.simulation.simulate_playoffs import simulate_playoffs

st.set_page_config(page_title="Playoff Simulator", page_icon="🏆", layout="wide")
st.title("🏆 Playoff Simulator")


@st.cache_data(show_spinner="Building dataset from cache...")
def _load_dataset():
    return build_dataset_from_cache()


if not model_exists():
    st.warning(
        "⚠️ No trained model found. Run `python -m src.models.train_game_model` first."
    )
    st.stop()

dataset = _load_dataset()
if dataset.empty:
    st.error("No cached NBA data found. Train the model (which fetches data) first.")
    st.stop()

teams = get_team_options(dataset)
team_names = list(teams.keys())
id_to_name = {v: k for k, v in teams.items()}

st.markdown(
    "Manually seed both conferences (1–8), choose a number of simulations, and "
    "the trained model will estimate each team's championship odds."
)


def _seed_picker(conf: str) -> dict[int, int]:
    """Render 8 seed selectboxes for a conference; return {seed: team_id}."""
    st.subheader(f"{conf} seeds")
    chosen: dict[int, int] = {}
    for seed in range(1, 9):
        # Default to distinct teams to avoid all-same initial selections.
        default_idx = (seed - 1 + (0 if conf == "East" else 8)) % len(team_names)
        name = st.selectbox(
            f"{conf} #{seed}",
            team_names,
            index=default_idx,
            key=f"{conf}_{seed}",
        )
        chosen[seed] = teams[name]
    return chosen


col_east, col_west = st.columns(2)
with col_east:
    east = _seed_picker("East")
with col_west:
    west = _seed_picker("West")

n_sims = st.select_slider("Number of simulations", options=[100, 500, 1000, 5000], value=1000)

if st.button("Simulate playoffs", type="primary"):
    model = load_model()

    # Memoise matchup probabilities: at most 16 teams -> few unique pairings.
    _prob_cache: dict[tuple[int, int], float] = {}

    def game_probability_func(home_id: int, away_id: int) -> float:
        key = (home_id, away_id)
        if key not in _prob_cache:
            feats = build_matchup_features(home_id, away_id, dataset)
            _prob_cache[key] = predict_from_feature_dict(feats, model)
        return _prob_cache[key]

    bracket = {"East": east, "West": west}

    with st.spinner(f"Running {n_sims:,} simulations..."):
        results = simulate_playoffs(bracket, game_probability_func, n_simulations=n_sims)

    total = results["n_simulations"]

    def _counts_to_df(counts: dict, label: str) -> pd.DataFrame:
        rows = [
            {"Team": id_to_name.get(tid, str(tid)), label: c / total}
            for tid, c in counts.items()
        ]
        df = pd.DataFrame(rows).sort_values(label, ascending=False)
        return df

    # ---- Championship odds ---------------------------------------------------
    st.subheader("🏆 Championship probability")
    champ_df = _counts_to_df(results["champion_counts"], "Championship %")
    champ_df_display = champ_df.copy()
    champ_df_display["Championship %"] = (champ_df_display["Championship %"] * 100).round(1)
    fig = px.bar(
        champ_df.head(16),
        x="Championship %",
        y="Team",
        orientation="h",
        title="Title odds",
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(champ_df_display, use_container_width=True, hide_index=True)

    # ---- Finals odds ---------------------------------------------------------
    st.subheader("🥈 Finals appearance probability")
    finals_df = _counts_to_df(results["finals_counts"], "Finals %")
    finals_df["Finals %"] = (finals_df["Finals %"] * 100).round(1)
    st.dataframe(finals_df, use_container_width=True, hide_index=True)

    # ---- Conference finals odds ---------------------------------------------
    st.subheader("Conference Finals appearance probability")
    cf_rows = [
        {
            "Team": id_to_name.get(tid, str(tid)),
            "Conf Finals %": round(adv["conf_finals"] / total * 100, 1),
        }
        for tid, adv in results["advancement"].items()
    ]
    cf_df = pd.DataFrame(cf_rows).sort_values("Conf Finals %", ascending=False)
    st.dataframe(cf_df, use_container_width=True, hide_index=True)

    st.caption("Educational baseline simulation — not betting advice.")
