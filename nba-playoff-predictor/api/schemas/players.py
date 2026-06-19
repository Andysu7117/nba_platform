"""Player-stats response models."""
from __future__ import annotations

from pydantic import BaseModel


class PlayerRow(BaseModel):
    """A single player's per-game season line for the leaderboard table."""

    rank: int
    name: str
    team_abbr: str
    team_color: str
    position: str | None = None
    games_played: int
    minutes: float
    points: float
    rebounds: float
    assists: float
    steals: float
    blocks: float
    fg_pct: float
    fg3_pct: float
    ft_pct: float


class LeaderCard(BaseModel):
    """A 'league leader' summary card (points / rebounds / assists)."""

    category: str  # "POINTS" | "REBOUNDS" | "ASSISTS"
    unit: str  # "PPG" | "RPG" | "APG"
    name: str
    team_abbr: str
    team_color: str
    team_name: str
    value: float


class PlayersResponse(BaseModel):
    season: str
    available: bool
    message: str | None = None
    leaders: list[LeaderCard]
    rows: list[PlayerRow]
