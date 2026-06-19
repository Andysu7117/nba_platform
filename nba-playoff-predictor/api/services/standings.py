"""Compute conference standings and rating profiles from cached team games.

We only have box-score totals, so "offensive/defensive rating" are reported as
points scored / allowed *per game* — a faithful, if simplified, proxy for the
per-100-possession ratings the UI labels them with. Opponent points come from
``PTS - PLUS_MINUS`` (a team's own points minus its margin).
"""
from __future__ import annotations

import pandas as pd

from api.reference import teams as team_ref
from api.schemas.common import TeamRef
from api.schemas.standings import StandingRow, StandingsResponse
from api.services import data


def _streak(wl_sorted: list[str]) -> str:
    """Current win/loss streak from a chronologically-ordered W/L list."""
    if not wl_sorted:
        return "—"
    last = wl_sorted[-1]
    count = 0
    for result in reversed(wl_sorted):
        if result == last:
            count += 1
        else:
            break
    return f"{last}{count}"


def _last_10(wl_sorted: list[str]) -> str:
    recent = wl_sorted[-10:]
    wins = sum(1 for r in recent if r == "W")
    return f"{wins}-{len(recent) - wins}"


def _team_ref(team_id: int, record: str) -> TeamRef:
    meta = team_ref.get_by_id(team_id)
    if meta is None:
        # Fall back to a neutral descriptor for any unmapped team id.
        return TeamRef(
            team_id=team_id, abbr="?", city="", name=str(team_id),
            conference="", color="#888888", record=record,
        )
    return TeamRef(
        team_id=meta.team_id, abbr=meta.abbr, city=meta.city, name=meta.name,
        conference=meta.conference, color=meta.color, record=record,
    )


def _compute_rows(season: str) -> list[dict]:
    """Per-team aggregates for a season, sorted by win pct (best first)."""
    df = data.team_games_for_season(season)
    if df.empty:
        return []

    df = df.sort_values("GAME_DATE")
    rows: list[dict] = []
    for team_id, grp in df.groupby("TEAM_ID"):
        wl = grp["WL"].tolist()
        wins = sum(1 for r in wl if r == "W")
        losses = sum(1 for r in wl if r == "L")
        played = wins + losses
        if played == 0:
            continue
        pts_for = float(grp["PTS"].mean())
        pts_against = float((grp["PTS"] - grp["PLUS_MINUS"]).mean())
        rows.append(
            {
                "team_id": int(team_id),
                "wins": wins,
                "losses": losses,
                "win_pct": wins / played,
                "off_rating": round(pts_for, 1),
                "def_rating": round(pts_against, 1),
                "net_rating": round(pts_for - pts_against, 1),
                "streak": _streak(wl),
                "last_10": _last_10(wl),
                "games_played": played,
            }
        )

    rows.sort(key=lambda r: (r["win_pct"], r["net_rating"]), reverse=True)
    return rows


def get_standings(conference: str, season: str | None = None) -> StandingsResponse:
    """Return ranked standings for ``East`` | ``West`` | ``League``."""
    season = season or data.CURRENT_SEASON
    conference = conference.title() if conference.lower() != "league" else "League"

    all_rows = _compute_rows(season)
    if conference != "League":
        all_rows = [
            r for r in all_rows
            if (m := team_ref.get_by_id(r["team_id"])) and m.conference == conference
        ]

    leader = all_rows[0] if all_rows else None
    out: list[StandingRow] = []
    for i, r in enumerate(all_rows):
        record = f"{r['wins']}-{r['losses']}"
        games_back = (
            0.0 if leader is None or i == 0
            else round(((leader["wins"] - r["wins"]) + (r["losses"] - leader["losses"])) / 2, 1)
        )
        out.append(
            StandingRow(
                rank=i + 1,
                team=_team_ref(r["team_id"], record),
                wins=r["wins"],
                losses=r["losses"],
                win_pct=round(r["win_pct"], 3),
                games_back=games_back,
                streak=r["streak"],
                last_10=r["last_10"],
                off_rating=r["off_rating"],
                def_rating=r["def_rating"],
                net_rating=r["net_rating"],
                games_played=r["games_played"],
            )
        )

    return StandingsResponse(conference=conference, season=season, rows=out)


def team_record_map(season: str | None = None) -> dict[int, str]:
    """``team_id -> 'W-L'`` for the season, for embedding in other responses."""
    season = season or data.CURRENT_SEASON
    return {r["team_id"]: f"{r['wins']}-{r['losses']}" for r in _compute_rows(season)}
