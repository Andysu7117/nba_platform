"""Team Stats page: visualise cached team scoring and plus-minus trends."""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import plotly.express as px
import streamlit as st

from src.app_helpers import load_cached_team_games

st.set_page_config(page_title="Team Stats", page_icon="📊", layout="wide")
st.title("📊 Team Stats")


@st.cache_data(show_spinner="Loading cached team games...")
def _load():
    return load_cached_team_games()


team_games = _load()
if team_games.empty:
    st.error(
        "No cached team data found in `data/raw/`. Run "
        "`python -m src.models.train_game_model` to fetch and cache data."
    )
    st.stop()

team_names = sorted(team_games["TEAM_NAME"].dropna().unique())
seasons = sorted(team_games["SEASON"].dropna().unique())

col1, col2 = st.columns(2)
with col1:
    team = st.selectbox("Team", team_names)
with col2:
    season = st.selectbox("Season", list(reversed(seasons)))

df = team_games[
    (team_games["TEAM_NAME"] == team) & (team_games["SEASON"] == season)
].copy()

if df.empty:
    st.warning("No games for that team/season in the cache.")
    st.stop()

df = df.sort_values("GAME_DATE").reset_index(drop=True)
df["GAME_NUMBER"] = range(1, len(df) + 1)
df["PTS_ROLL10"] = df["PTS"].rolling(10, min_periods=1).mean()
if "PLUS_MINUS" in df.columns:
    df["PLUS_MINUS_ROLL10"] = df["PLUS_MINUS"].rolling(10, min_periods=1).mean()

st.subheader(f"{team} — {season}")

# Points by game.
fig_pts = px.bar(df, x="GAME_DATE", y="PTS", title="Points by game")
st.plotly_chart(fig_pts, use_container_width=True)

# Plus-minus by game.
if "PLUS_MINUS" in df.columns:
    fig_pm = px.bar(
        df,
        x="GAME_DATE",
        y="PLUS_MINUS",
        title="Plus-minus by game",
        color="PLUS_MINUS",
        color_continuous_scale="RdYlGn",
    )
    st.plotly_chart(fig_pm, use_container_width=True)

# Rolling last-10 lines.
fig_roll = px.line(
    df,
    x="GAME_DATE",
    y=[c for c in ["PTS_ROLL10", "PLUS_MINUS_ROLL10"] if c in df.columns],
    labels={"value": "Rolling avg", "variable": "Metric", "GAME_DATE": "Game date"},
    title="Rolling last-10 averages",
)
st.plotly_chart(fig_roll, use_container_width=True)

show_cols = [
    c
    for c in ["GAME_DATE", "MATCHUP", "WL", "PTS", "PLUS_MINUS", "REB", "AST", "TOV"]
    if c in df.columns
]
st.dataframe(
    df[show_cols].sort_values("GAME_DATE", ascending=False),
    use_container_width=True,
    hide_index=True,
)
