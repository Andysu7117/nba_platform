"""Schedule service: games by date (with model win probabilities) + box scores.

Games are sourced from the cached team-game logs, which carry real matchups and
final scores, so the Current Season view works fully offline. Per-game win
probabilities come from the trained model when available. Detailed box scores are
fetched live from the NBA API and degrade gracefully when it is unreachable.
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
from src.models.predict import predict_home_win_probability


def _team_ref(team_id: int, records: dict[int, str]) -> TeamRef:
    meta = team_ref.get_by_id(team_id)
    record = records.get(int(team_id))
    if meta is None:
        return TeamRef(team_id=int(team_id), abbr="?", city="", name=str(team_id),
                       conference="", color="#888888", record=record)
    return TeamRef(team_id=meta.team_id, abbr=meta.abbr, city=meta.city, name=meta.name,
                   conference=meta.conference, color=meta.color, record=record)


def _games_on(date: dt.date) -> pd.DataFrame:
    rows = data.game_rows()
    if rows.empty:
        return rows
    mask = pd.to_datetime(rows["GAME_DATE"]).dt.date == date
    return rows[mask].sort_values("GAME_ID")


def get_schedule(date: dt.date) -> ScheduleResponse:
    games_df = _games_on(date)
    if games_df.empty:
        return ScheduleResponse(date=date.isoformat(), games=[])

    season = games_df["SEASON"].iloc[0]
    records = standings.team_record_map(season)
    model = data.get_model()
    dataset = data.modeling_dataset()
    can_predict = model is not None and not dataset.empty

    summaries: list[GameSummary] = []
    for row in games_df.itertuples(index=False):
        home_id, away_id = int(row.HOME_TEAM_ID), int(row.AWAY_TEAM_ID)
        home_score, away_score = int(row.HOME_SCORE), int(row.AWAY_SCORE)
        p_home = None
        if can_predict:
            try:
                p_home = round(
                    float(predict_home_win_probability(home_id, away_id, dataset, model=model)), 4
                )
            except Exception:  # noqa: BLE001 - prediction is best-effort
                p_home = None
        summaries.append(
            GameSummary(
                game_id=str(row.GAME_ID),
                date=date.isoformat(),
                status="final",
                home=_team_ref(home_id, records),
                away=_team_ref(away_id, records),
                home_score=home_score,
                away_score=away_score,
                home_win_prob=p_home,
                away_win_prob=None if p_home is None else round(1 - p_home, 4),
                winner="home" if home_score > away_score else "away",
            )
        )
    return ScheduleResponse(date=date.isoformat(), games=summaries)


def get_calendar(start: dt.date, end: dt.date) -> CalendarResponse:
    """Per-day game counts across an inclusive date range (for the week strip)."""
    rows = data.game_rows()
    counts: dict[str, int] = {}
    if not rows.empty:
        dates = pd.to_datetime(rows["GAME_DATE"]).dt.date
        window = rows[(dates >= start) & (dates <= end)]
        grouped = pd.to_datetime(window["GAME_DATE"]).dt.date.value_counts()
        counts = {d.isoformat(): int(c) for d, c in grouped.items()}

    days: list[DayCount] = []
    cur = start
    while cur <= end:
        days.append(DayCount(date=cur.isoformat(), count=counts.get(cur.isoformat(), 0)))
        cur += dt.timedelta(days=1)
    return CalendarResponse(days=days)


def latest_game_date() -> dt.date | None:
    """The most recent date with cached games (used as the UI's default 'today')."""
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
    # Locate the game in the cache to recover the two teams and final score.
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
        # The NBA API has no per-player box score for this game id.
        return BoxScoreResponse(
            game_id=str(game_id), status="final", available=False,
            message="Player box score is not available for this game.",
            home=(_box_empty(home_id, home_score, records) if home_id else None),
            away=(_box_empty(away_id, away_score, records) if away_id else None),
        )

    if home_id is None:
        # Game not in local cache; infer teams from the box score itself.
        ids = [int(t) for t in box_df["TEAM_ID"].unique()[:2]]
        home_id, away_id = (ids + [None, None])[:2]

    return BoxScoreResponse(
        game_id=str(game_id), status="final", available=True,
        home=_box_team(box_df, home_id, home_score, records),
        away=_box_team(box_df, away_id, away_score, records),
    )


def _box_empty(team_id: int, score: int | None, records: dict[int, str]) -> BoxScoreTeam:
    return BoxScoreTeam(team=_team_ref(team_id, records), score=score, players=[])
