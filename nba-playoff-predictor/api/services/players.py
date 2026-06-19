"""Player-stats service: league-wide leaderboard + leader cards.

Reads cached league player stats when present; otherwise attempts a single live
fetch. If neither succeeds (offline, never populated) it returns an empty,
``available=False`` payload the UI renders as a friendly empty state.
"""
from __future__ import annotations

import pandas as pd

from api.reference import teams as team_ref
from api.schemas.players import (
    CareerRow,
    GameLogRow,
    LeaderCard,
    PlayerDetailResponse,
    PlayerRow,
    PlayerSearchResult,
    PlayersResponse,
)
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
                player_id=int(_num(getattr(r, "PLAYER_ID", 0))),
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


# ---- Individual player detail ----------------------------------------------


def search_players(query: str, limit: int = 10) -> list[PlayerSearchResult]:
    """Search the bundled static player list (works offline)."""
    from nba_api.stats.static import players as static_players

    query = (query or "").strip()
    if not query:
        return []
    matches = static_players.find_players_by_full_name(query)
    if not matches:
        lowered = query.lower()
        matches = [p for p in static_players.get_players() if lowered in p["full_name"].lower()]
    return [
        PlayerSearchResult(player_id=int(p["id"]), full_name=p["full_name"], is_active=p.get("is_active"))
        for p in matches[:limit]
    ]


def _player_name(player_id: int) -> str:
    from nba_api.stats.static import players as static_players

    p = static_players.find_player_by_id(player_id)
    return p["full_name"] if p else str(player_id)


def _opt(value) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 3)


def _game_log_rows(df: pd.DataFrame) -> list[GameLogRow]:
    rows: list[GameLogRow] = []
    df = df.sort_values("GAME_DATE", ascending=False)
    for r in df.itertuples(index=False):
        raw_date = getattr(r, "GAME_DATE", None)
        date = ""
        if raw_date is not None and not pd.isna(raw_date):
            date = pd.to_datetime(raw_date).date().isoformat()
        rows.append(
            GameLogRow(
                date=date,
                matchup=str(getattr(r, "MATCHUP", "") or ""),
                result=getattr(r, "WL", None),
                minutes=_opt(getattr(r, "MIN", None)),
                points=_opt(getattr(r, "PTS", None)),
                rebounds=_opt(getattr(r, "REB", None)),
                assists=_opt(getattr(r, "AST", None)),
                steals=_opt(getattr(r, "STL", None)),
                blocks=_opt(getattr(r, "BLK", None)),
                turnovers=_opt(getattr(r, "TOV", None)),
                fg_pct=_opt(getattr(r, "FG_PCT", None)),
                fg3_pct=_opt(getattr(r, "FG3_PCT", None)),
                ft_pct=_opt(getattr(r, "FT_PCT", None)),
                plus_minus=_opt(getattr(r, "PLUS_MINUS", None)),
            )
        )
    return rows


def _career_row(r) -> CareerRow:
    g = lambda attr: getattr(r, attr, None)  # noqa: E731
    return CareerRow(
        season_id=str(g("SEASON_ID") or "Career"),
        team_abbr=g("TEAM_ABBREVIATION"),
        games_played=_opt(g("GP")),
        minutes=_opt(g("MIN")),
        points=_opt(g("PTS")),
        rebounds=_opt(g("REB")),
        assists=_opt(g("AST")),
        steals=_opt(g("STL")),
        blocks=_opt(g("BLK")),
        turnovers=_opt(g("TOV")),
        fg_pct=_opt(g("FG_PCT")),
        fg3_pct=_opt(g("FG3_PCT")),
        ft_pct=_opt(g("FT_PCT")),
    )


def get_player_detail(
    player_id: int,
    season: str | None = None,
    season_type: str = "Regular Season",
    per_mode: str = "PerGame",
) -> PlayerDetailResponse:
    from src.ingest.fetch_player_logs import fetch_player_career, fetch_player_logs

    season = season or data.CURRENT_SEASON
    name = _player_name(player_id)
    base = dict(player_id=player_id, name=name, season=season, season_type=season_type, per_mode=per_mode)

    game_log: list[GameLogRow] = []
    log_msg: str | None = None
    try:
        logs = fetch_player_logs(player_id, season, season_type)
        game_log = _game_log_rows(logs) if logs is not None and not logs.empty else []
    except Exception as err:  # noqa: BLE001 - NBA API may be offline
        log_msg = f"Game log unavailable: {err}"

    career_season: list[CareerRow] = []
    career_total: CareerRow | None = None
    career_msg: str | None = None
    try:
        career = fetch_player_career(player_id, per_mode)
        season_df, career_df = career["season"], career["career"]
        if season_df is not None and not season_df.empty:
            career_season = [_career_row(r) for r in season_df.itertuples(index=False)]
        if career_df is not None and not career_df.empty:
            career_total = _career_row(next(career_df.itertuples(index=False)))
    except Exception as err:  # noqa: BLE001
        career_msg = f"Career stats unavailable: {err}"

    available = bool(game_log or career_season)
    message = None if available else (log_msg or career_msg or "No data available for this player.")
    return PlayerDetailResponse(
        **base, available=available, message=message,
        game_log=game_log, career_season=career_season, career_total=career_total,
    )
