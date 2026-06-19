"""Player-stats response models."""
from __future__ import annotations

from pydantic import BaseModel


class PlayerRow(BaseModel):
    """A single player's per-game season line for the leaderboard table."""

    rank: int
    player_id: int
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


# ---- Individual player detail ----------------------------------------------


class PlayerSearchResult(BaseModel):
    player_id: int
    full_name: str
    is_active: bool | None = None


class GameLogRow(BaseModel):
    date: str  # YYYY-MM-DD
    matchup: str
    result: str | None = None  # "W" | "L"
    minutes: float | None = None
    points: float | None = None
    rebounds: float | None = None
    assists: float | None = None
    steals: float | None = None
    blocks: float | None = None
    turnovers: float | None = None
    fg_pct: float | None = None
    fg3_pct: float | None = None
    ft_pct: float | None = None
    plus_minus: float | None = None


class CareerRow(BaseModel):
    season_id: str
    team_abbr: str | None = None
    games_played: float | None = None
    minutes: float | None = None
    points: float | None = None
    rebounds: float | None = None
    assists: float | None = None
    steals: float | None = None
    blocks: float | None = None
    turnovers: float | None = None
    fg_pct: float | None = None
    fg3_pct: float | None = None
    ft_pct: float | None = None


class PlayerDetailResponse(BaseModel):
    player_id: int
    name: str
    season: str
    season_type: str
    per_mode: str
    available: bool
    message: str | None = None
    game_log: list[GameLogRow]
    career_season: list[CareerRow]
    career_total: CareerRow | None = None
