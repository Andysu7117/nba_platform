"""Schedule service: live games by date (with model win probabilities) + box scores.

Games come from the NBA **scoreboard** endpoint so the view reflects real
scheduled / live / final games for any date. Today's scoreboard is always
re-fetched (scores change through the day); past dates are served from cache
(finals never change) unless an explicit refresh is requested. Per-game win
probabilities come from the trained model. Detailed box scores are fetched live
and degrade gracefully when the NBA API is unreachable.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from api.reference import teams as team_ref
from api.schemas.common import TeamRef
from api.schemas.schedule import (
    BoxScorePlayer,
    BoxScoreResponse,
    BoxScoreTeam,
    CalendarResponse,
    DayCount,
    GameSummary,
    ScheduleResponse,
)
from api.services import data, standings
from src.ingest.fetch_scoreboard import (
    STATUS_FINAL,
    STATUS_LIVE,
    fetch_scoreboard,
)
from src.models.predict import predict_home_win_probability

_STATUS_MAP = {1: "scheduled", STATUS_LIVE: "live", STATUS_FINAL: "final"}


def _today() -> dt.date:
    return dt.date.today()


def season_for_date(date: dt.date) -> str:
    """The NBA season string ('2025-26') that a calendar date falls in."""
    # Seasons start in October; Jan–Sep belong to the season that began the prior year.
    start_year = date.year if date.month >= 10 else date.year - 1
    return f"{start_year}-{(start_year + 1) % 100:02d}"


def _team_ref(team_id: int, records: dict[int, str]) -> TeamRef:
    meta = team_ref.get_by_id(team_id)
    record = records.get(int(team_id))
    if meta is None:
        return TeamRef(team_id=int(team_id), abbr="?", city="", name=str(team_id),
                       conference="", color="#888888", record=record)
    return TeamRef(team_id=meta.team_id, abbr=meta.abbr, city=meta.city, name=meta.name,
                   conference=meta.conference, color=meta.color, record=record)


def _opt_int(value) -> int | None:
    if value is None or pd.isna(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _fetch_day(date: dt.date, refresh: bool) -> pd.DataFrame:
    """Fetch a single day's scoreboard, always refreshing today's live data."""
    force = refresh or date == _today()
    return fetch_scoreboard(date.isoformat(), force_refresh=force)


def get_schedule(date: dt.date, refresh: bool = False) -> ScheduleResponse:
    # Keep the current season's standings/records/predictions current (once/day).
    data.ensure_fresh_current_season()

    games_df = _fetch_day(date, refresh)
    if games_df is None or games_df.empty:
        return ScheduleResponse(date=date.isoformat(), games=[])

    records = standings.team_record_map(season_for_date(date))
    model = data.get_model()
    dataset = data.modeling_dataset()
    can_predict = model is not None and not dataset.empty

    summaries: list[GameSummary] = []
    for row in games_df.itertuples(index=False):
        home_id, away_id = _opt_int(getattr(row, "HOME_TEAM_ID", None)), _opt_int(getattr(row, "AWAY_TEAM_ID", None))
        if home_id is None or away_id is None:
            continue  # skip non-standard entries (e.g. all-star) with no team ids
        status = _STATUS_MAP.get(_opt_int(getattr(row, "GAME_STATUS_ID", 1)) or 1, "scheduled")
        home_score, away_score = _opt_int(getattr(row, "HOME_PTS", None)), _opt_int(getattr(row, "AWAY_PTS", None))

        p_home = None
        if can_predict:
            try:
                p_home = round(float(predict_home_win_probability(home_id, away_id, dataset, model=model)), 4)
            except Exception:  # noqa: BLE001 - prediction is best-effort
                p_home = None

        winner = None
        if status == "final" and home_score is not None and away_score is not None:
            winner = "home" if home_score > away_score else "away"

        summaries.append(
            GameSummary(
                game_id=str(row.GAME_ID),
                date=date.isoformat(),
                status=status,
                status_text=getattr(row, "GAME_STATUS_TEXT", None) or None,
                home=_team_ref(home_id, records),
                away=_team_ref(away_id, records),
                home_score=home_score,
                away_score=away_score,
                home_win_prob=p_home,
                away_win_prob=None if p_home is None else round(1 - p_home, 4),
                winner=winner,
            )
        )
    return ScheduleResponse(date=date.isoformat(), games=summaries)


def get_calendar(start: dt.date, end: dt.date) -> CalendarResponse:
    """Per-day game counts across an inclusive range (for the week strip)."""
    days: list[DayCount] = []
    cur = start
    while cur <= end:
        try:
            df = _fetch_day(cur, refresh=False)
            count = 0 if df is None else int(len(df))
        except Exception:  # noqa: BLE001 - one bad day shouldn't sink the strip
            count = 0
        days.append(DayCount(date=cur.isoformat(), count=count))
        cur += dt.timedelta(days=1)
    return CalendarResponse(days=days)


def latest_game_date() -> dt.date | None:
    """Most recent date with cached *completed* games (used for app metadata)."""
    rows = data.game_rows()
    if rows.empty:
        return None
    return pd.to_datetime(rows["GAME_DATE"]).max().date()


# ---- Box score -------------------------------------------------------------


def _box_team(box_df: pd.DataFrame, team_id: int, score: int | None,
              records: dict[int, str]) -> BoxScoreTeam:
    sub = box_df[box_df["TEAM_ID"] == team_id].copy()
    if "PTS" in sub.columns:
        sub = sub.sort_values("PTS", ascending=False, na_position="last")
    players: list[BoxScorePlayer] = []
    for r in sub.head(8).itertuples(index=False):
        def _int(attr: str) -> int | None:
            val = getattr(r, attr, None)
            return None if val is None or pd.isna(val) else int(val)

        pm = getattr(r, "PLUS_MINUS", None)
        players.append(
            BoxScorePlayer(
                name=getattr(r, "PLAYER_NAME", "—"),
                position=getattr(r, "START_POSITION", None) or None,
                minutes=str(getattr(r, "MIN", "") or "") or None,
                points=_int("PTS"),
                rebounds=_int("REB"),
                assists=_int("AST"),
                plus_minus=None if pm is None or pd.isna(pm) else f"{int(pm):+d}",
            )
        )
    return BoxScoreTeam(team=_team_ref(team_id, records), score=score, players=players)


def get_box_score(game_id: str) -> BoxScoreResponse:
    # Locate the game in the cached completed games to recover teams/score.
    rows = data.game_rows()
    match = rows[rows["GAME_ID"].astype(str) == str(game_id)] if not rows.empty else rows
    home_id = away_id = None
    home_score = away_score = None
    season = data.CURRENT_SEASON
    if not match.empty:
        g = match.iloc[0]
        home_id, away_id = int(g["HOME_TEAM_ID"]), int(g["AWAY_TEAM_ID"])
        home_score, away_score = int(g["HOME_SCORE"]), int(g["AWAY_SCORE"])
        season = g["SEASON"]

    records = standings.team_record_map(season)

    try:
        from src.ingest.fetch_scoreboard import fetch_box_score

        box_df = fetch_box_score(str(game_id))
    except Exception as err:  # noqa: BLE001 - NBA API may be offline
        return BoxScoreResponse(
            game_id=str(game_id), status="final", available=False,
            message=f"Player box score unavailable (NBA API offline): {err}",
            home=(_box_empty(home_id, home_score, records) if home_id else None),
            away=(_box_empty(away_id, away_score, records) if away_id else None),
        )

    if box_df.empty:
        return BoxScoreResponse(
            game_id=str(game_id), status="final", available=False,
            message="Player box score is not available for this game yet.",
            home=(_box_empty(home_id, home_score, records) if home_id else None),
            away=(_box_empty(away_id, away_score, records) if away_id else None),
        )

    if home_id is None:
        ids = [int(t) for t in box_df["TEAM_ID"].unique()[:2]]
        home_id, away_id = (ids + [None, None])[:2]

    return BoxScoreResponse(
        game_id=str(game_id), status="final", available=True,
        home=_box_team(box_df, home_id, home_score, records),
        away=_box_team(box_df, away_id, away_score, records),
    )


def _box_empty(team_id: int, score: int | None, records: dict[int, str]) -> BoxScoreTeam:
    return BoxScoreTeam(team=_team_ref(team_id, records), score=score, players=[])
