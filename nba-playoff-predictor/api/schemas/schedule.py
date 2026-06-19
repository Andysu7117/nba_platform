"""Schedule / scoreboard response models."""
from __future__ import annotations

from pydantic import BaseModel

from api.schemas.common import TeamRef


class GameSummary(BaseModel):
    """One game on a given date, with score and/or model win probabilities."""

    game_id: str
    date: str  # YYYY-MM-DD
    status: str  # "scheduled" | "live" | "final"
    status_text: str | None = None  # e.g. "7:00 pm ET" / "Q3 5:23" / "Final"
    home: TeamRef
    away: TeamRef
    home_score: int | None = None
    away_score: int | None = None
    home_win_prob: float | None = None  # model P(home win), 0..1
    away_win_prob: float | None = None
    winner: str | None = None  # "home" | "away" when final


class ScheduleResponse(BaseModel):
    date: str
    games: list[GameSummary]


class DayCount(BaseModel):
    date: str
    count: int


class CalendarResponse(BaseModel):
    days: list[DayCount]


# ---- Box score -------------------------------------------------------------


class BoxScorePlayer(BaseModel):
    name: str
    position: str | None = None
    minutes: str | None = None
    points: int | None = None
    rebounds: int | None = None
    assists: int | None = None
    plus_minus: str | None = None


class BoxScoreTeam(BaseModel):
    team: TeamRef
    score: int | None = None
    players: list[BoxScorePlayer]


class BoxScoreResponse(BaseModel):
    game_id: str
    status: str
    available: bool
    message: str | None = None
    home: BoxScoreTeam | None = None
    away: BoxScoreTeam | None = None
