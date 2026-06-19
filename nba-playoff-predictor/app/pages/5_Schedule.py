"""Schedule / Current Season page.

Shows the games for a chosen date (defaults to today). For games that have not
been played yet, it shows each team's model-predicted win probability; for
finished games it shows the final score, expandable into a full box score.
"""
from __future__ import annotations

import datetime as _dt
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from src.app_helpers import build_dataset_from_cache
from src.ingest.fetch_scoreboard import (
    STATUS_FINAL,
    fetch_box_score,
    fetch_scoreboard,
)
from src.models.predict import load_model, model_exists, predict_home_win_probability

st.set_page_config(page_title="Schedule", page_icon="🗓️", layout="wide")
st.title("🗓️ Schedule & Predictions")


@st.cache_data(show_spinner="Building dataset from cache...")
def _load_dataset():
    return build_dataset_from_cache()


@st.cache_data(show_spinner="Loading scoreboard...")
def _scoreboard(date_str: str, force: bool):
    return fetch_scoreboard(date_str, force_refresh=force)


@st.cache_data(show_spinner="Loading box score...")
def _box_score(game_id: str):
    return fetch_box_score(game_id)


# ---- Controls ---------------------------------------------------------------
col_a, col_b = st.columns([3, 1])
with col_a:
    picked = st.date_input("Game date", value=_dt.date.today())
with col_b:
    st.write("")
    st.write("")
    refresh = st.button("🔄 Refresh live scores")

date_str = picked.strftime("%Y-%m-%d")

try:
    games = _scoreboard(date_str, refresh)
except Exception as err:  # noqa: BLE001
    st.error(f"Could not load the scoreboard (the NBA API may be unavailable): {err}")
    st.stop()

if games is None or games.empty:
    st.info(f"No NBA games found for {date_str}.")
    st.stop()

# ---- Model / dataset for predicting unplayed games --------------------------
dataset = _load_dataset()
have_model = model_exists() and not dataset.empty
model = load_model() if have_model else None
if not have_model:
    st.warning(
        "Predictions for upcoming games need a trained model and cached data. "
        "Run `python -m src.models.train_game_model` to enable them."
    )

st.caption(f"{len(games)} game(s) on {date_str}. Click a final game to see its box score.")


def _render_box_score(game_id: str, home_id: int, away_id: int,
                      home_name: str, away_name: str) -> None:
    """Render the two-team player box score inside an expander."""
    try:
        box = _box_score(str(game_id))
    except Exception as err:  # noqa: BLE001
        st.warning(f"Box score unavailable: {err}")
        return

    show_cols = [
        c for c in [
            "PLAYER_NAME", "START_POSITION", "MIN", "PTS", "REB", "AST",
            "STL", "BLK", "TO", "FG_PCT", "FG3M", "PLUS_MINUS",
        ] if c in box.columns
    ]
    for tid, tname in [(away_id, away_name), (home_id, home_name)]:
        st.markdown(f"**{tname}**")
        team_box = box[box["TEAM_ID"] == tid][show_cols]
        st.dataframe(team_box, use_container_width=True, hide_index=True)


for row in games.itertuples(index=False):
    home_name = getattr(row, "HOME_TEAM_NAME", "Home")
    away_name = getattr(row, "AWAY_TEAM_NAME", "Away")
    status_id = getattr(row, "GAME_STATUS_ID", None)
    status_text = getattr(row, "GAME_STATUS_TEXT", "")

    with st.container(border=True):
        is_final = status_id == STATUS_FINAL

        if is_final:
            home_pts = getattr(row, "HOME_PTS", None)
            away_pts = getattr(row, "AWAY_PTS", None)
            c1, c2 = st.columns([4, 1])
            with c1:
                away_won = (away_pts or 0) > (home_pts or 0)
                away_str = f"**{away_name} {int(away_pts)}**" if away_won else f"{away_name} {int(away_pts)}"
                home_str = f"**{home_name} {int(home_pts)}**" if not away_won else f"{home_name} {int(home_pts)}"
                st.markdown(f"{away_str}  &nbsp;@&nbsp;  {home_str}")
            with c2:
                st.caption("Final")
            with st.expander("📊 Box score"):
                _render_box_score(
                    getattr(row, "GAME_ID"),
                    getattr(row, "HOME_TEAM_ID"),
                    getattr(row, "AWAY_TEAM_ID"),
                    home_name,
                    away_name,
                )
        else:
            # Not played yet -> show predicted win probabilities.
            st.markdown(f"**{away_name}**  @  **{home_name}**  ·  _{status_text}_")
            if have_model:
                p_home = predict_home_win_probability(
                    getattr(row, "HOME_TEAM_ID"),
                    getattr(row, "AWAY_TEAM_ID"),
                    dataset,
                    model=model,
                )
                p_away = 1.0 - p_home
                pc1, pc2 = st.columns(2)
                pc1.metric(f"✈️ {away_name}", f"{p_away * 100:.1f}%")
                pc2.metric(f"🏠 {home_name}", f"{p_home * 100:.1f}%")
                st.progress(p_home, text=f"Home win probability: {p_home * 100:.1f}%")
            else:
                st.caption("Train the model to see win probabilities.")

st.caption("Educational baseline — not betting advice.")
