"""Player-stats service: league-wide leaderboard + leader cards.

Reads cached league player stats when present; otherwise attempts a single live
fetch. If neither succeeds (offline, never populated) it returns an empty,
``available=False`` payload the UI renders as a friendly empty state.
"""
from __future__ import annotations

import pandas as pd

from api.reference import teams as team_ref
from api.schemas.players import LeaderCard, PlayerRow, PlayersResponse
from api.services import data

_NEUTRAL_COLOR = "#888888"


def _color_for(abbr: str) -> str:
    meta = team_ref.get_by_abbr(abbr)
    return meta.color if meta else _NEUTRAL_COLOR


def _pct(value) -> float:
    """NBA percentages arrive as 0..1; present them as 0..100."""
    if value is None or pd.isna(value):
        return 0.0
    return round(float(value) * 100, 1)


def _num(value, default: float = 0.0) -> float:
    if value is None or pd.isna(value):
        return default
    return float(value)


def _load_stats(season: str) -> pd.DataFrame | None:
    from src.ingest.fetch_league_player_stats import (
        fetch_league_player_stats,
        load_cached_league_player_stats,
    )

    cached = load_cached_league_player_stats(season)
    if cached is not None and not cached.empty:
        return cached
    try:
        df = fetch_league_player_stats(season)
        return df if not df.empty else None
    except Exception:  # noqa: BLE001 - offline / API down
        return None


def get_players(season: str | None = None, min_games: int = 15) -> PlayersResponse:
    season = season or data.CURRENT_SEASON
    df = _load_stats(season)
    if df is None or df.empty:
        return PlayersResponse(
            season=season, available=False, leaders=[], rows=[],
            message="Player leaderboard not cached. Populate it with "
                    "`python -m scripts.fetch_player_leaderboard` while online.",
        )

    df = df.copy()
    if "GP" in df.columns:
        df = df[df["GP"] >= min_games]

    rows: list[PlayerRow] = []
    records = df.sort_values("PTS", ascending=False) if "PTS" in df.columns else df
    for i, r in enumerate(records.itertuples(index=False)):
        abbr = getattr(r, "TEAM_ABBREVIATION", "?")
        rows.append(
            PlayerRow(
                rank=i + 1,
                name=getattr(r, "PLAYER_NAME", "—"),
                team_abbr=abbr,
                team_color=_color_for(abbr),
                position=None,
                games_played=int(_num(getattr(r, "GP", 0))),
                minutes=round(_num(getattr(r, "MIN", 0)), 1),
                points=round(_num(getattr(r, "PTS", 0)), 1),
                rebounds=round(_num(getattr(r, "REB", 0)), 1),
                assists=round(_num(getattr(r, "AST", 0)), 1),
                steals=round(_num(getattr(r, "STL", 0)), 1),
                blocks=round(_num(getattr(r, "BLK", 0)), 1),
                fg_pct=_pct(getattr(r, "FG_PCT", 0)),
                fg3_pct=_pct(getattr(r, "FG3_PCT", 0)),
                ft_pct=_pct(getattr(r, "FT_PCT", 0)),
            )
        )

    leaders = [
        _leader_card(rows, "points", "POINTS", "PPG"),
        _leader_card(rows, "rebounds", "REBOUNDS", "RPG"),
        _leader_card(rows, "assists", "ASSISTS", "APG"),
    ]
    leaders = [l for l in leaders if l is not None]

    return PlayersResponse(season=season, available=True, leaders=leaders, rows=rows)


def _leader_card(rows: list[PlayerRow], attr: str, category: str, unit: str) -> LeaderCard | None:
    if not rows:
        return None
    top = max(rows, key=lambda r: getattr(r, attr))
    meta = team_ref.get_by_abbr(top.team_abbr)
    team_name = meta.full_name if meta else top.team_abbr
    return LeaderCard(
        category=category, unit=unit, name=top.name, team_abbr=top.team_abbr,
        team_color=top.team_color, team_name=team_name, value=getattr(top, attr),
    )
