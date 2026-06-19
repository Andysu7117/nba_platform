"""Standings / team-stats response models."""
from __future__ import annotations

from pydantic import BaseModel

from api.schemas.common import TeamRef


class StandingRow(BaseModel):
    """One team's record and rating profile within a conference standings."""

    rank: int
    team: TeamRef
    wins: int
    losses: int
    win_pct: float
    games_back: float
    streak: str  # e.g. "W5" / "L1"
    last_10: str  # e.g. "9-1"
    off_rating: float  # points scored per game (ORTG proxy)
    def_rating: float  # points allowed per game (DRTG proxy)
    net_rating: float
    games_played: int


class StandingsResponse(BaseModel):
    conference: str  # "East" | "West" | "League"
    season: str
    rows: list[StandingRow]
