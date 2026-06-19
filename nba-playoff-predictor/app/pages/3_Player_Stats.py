"""Player Stats page: game-by-game charts plus career season/totals tables."""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import plotly.express as px
import streamlit as st

from src.config import DEFAULT_SEASONS
from src.ingest.fetch_player_logs import (
    fetch_player_career,
    fetch_player_logs,
    find_player,
)

st.set_page_config(page_title="Player Stats", page_icon="📈", layout="wide")
st.title("📈 Player Stats")

STAT_OPTIONS = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "PLUS_MINUS", "MIN"]
SEASON_OPTIONS = list(reversed(DEFAULT_SEASONS)) + ["2018-19", "2017-18"]


@st.cache_data(show_spinner="Searching player...")
def _find(name: str):
    return find_player(name)


@st.cache_data(show_spinner="Fetching player game log...")
def _logs(player_id: int, season: str, season_type: str):
    return fetch_player_logs(player_id, season, season_type)


@st.cache_data(show_spinner="Fetching career stats...")
def _career(player_id: int, per_mode: str):
    return fetch_player_career(player_id, per_mode)


name = st.text_input("Search for a player", value="LeBron James")
if not name.strip():
    st.info("Type a player name to begin.")
    st.stop()

player = _find(name)
if player is None:
    st.error(f"No player found matching '{name}'. Try a different spelling.")
    st.stop()

st.subheader(player["full_name"])

tab_log, tab_career = st.tabs(["Game Log", "Career"])

# ---------------------------------------------------------------------------
# Game Log tab
# ---------------------------------------------------------------------------
with tab_log:
    col1, col2, col3 = st.columns(3)
    with col1:
        season = st.selectbox("Season", SEASON_OPTIONS, index=0)
    with col2:
        season_type = st.selectbox("Season type", ["Regular Season", "Playoffs"], index=0)
    with col3:
        stat = st.selectbox("Stat", STAT_OPTIONS, index=0)

    try:
        logs = _logs(int(player["id"]), season, season_type)
    except Exception as err:  # noqa: BLE001
        st.error(f"Could not fetch game logs (the NBA API may be unavailable): {err}")
        logs = None

    if logs is None:
        pass
    elif logs.empty:
        st.warning("No games found for this player/season/type.")
    elif stat not in logs.columns:
        st.warning(f"Stat '{stat}' is not available for this log.")
    else:
        # PlayerGameLog returns most-recent first; sort chronologically.
        logs = logs.sort_values("GAME_DATE").reset_index(drop=True)
        logs[f"{stat}_ROLL5"] = logs[stat].rolling(5, min_periods=1).mean()

        fig = px.line(
            logs,
            x="GAME_DATE",
            y=[stat, f"{stat}_ROLL5"],
            labels={"value": stat, "GAME_DATE": "Game date", "variable": "Series"},
            title=f"{player['full_name']} — {stat} per game ({season} {season_type})",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Solid line = per-game value · second line = rolling 5-game average.")

        show_cols = [c for c in ["GAME_DATE", "MATCHUP", "WL", *STAT_OPTIONS] if c in logs.columns]
        st.dataframe(
            logs[show_cols].sort_values("GAME_DATE", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

# ---------------------------------------------------------------------------
# Career tab
# ---------------------------------------------------------------------------
with tab_career:
    mode_label = st.radio(
        "View",
        ["Per Game", "Totals"],
        horizontal=True,
        help="Toggle between per-game averages and season/career totals.",
    )
    per_mode = "Totals" if mode_label == "Totals" else "PerGame"

    try:
        career = _career(int(player["id"]), per_mode)
    except Exception as err:  # noqa: BLE001
        st.error(f"Could not fetch career stats (the NBA API may be unavailable): {err}")
        career = None

    if career is not None:
        season_df = career["season"]
        career_df = career["career"]

        # Columns most users care about; fall back gracefully if absent.
        core = [
            "SEASON_ID", "TEAM_ABBREVIATION", "PLAYER_AGE", "GP", "GS", "MIN",
            "PTS", "REB", "AST", "STL", "BLK", "TOV",
            "FG_PCT", "FG3_PCT", "FT_PCT",
        ]

        st.markdown(f"**Season-by-season ({mode_label})**")
        if season_df is None or season_df.empty:
            st.info("No regular-season career data available for this player.")
        else:
            cols = [c for c in core if c in season_df.columns]
            st.dataframe(
                season_df[cols].sort_values("SEASON_ID", ascending=False),
                use_container_width=True,
                hide_index=True,
            )

        st.markdown(f"**Career ({mode_label})**")
        if career_df is None or career_df.empty:
            st.info("No career totals available.")
        else:
            cols = [c for c in core if c in career_df.columns]
            st.dataframe(career_df[cols], use_container_width=True, hide_index=True)

    st.caption("Regular-season career stats via nba_api PlayerCareerStats.")
