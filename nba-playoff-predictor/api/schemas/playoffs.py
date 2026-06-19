"""Playoff-simulator request/response models."""
from __future__ import annotations

from pydantic import BaseModel, Field

from api.schemas.common import TeamRef


class SeedEntry(BaseModel):
    seed: int = Field(..., ge=1, le=8)
    abbr: str


class SimulateRequest(BaseModel):
    n_simulations: int = Field(default=2000, ge=100, le=20000)
    season: str | None = Field(default=None, description="Seed from this season; defaults to current")
    # Optional manual seeding; when omitted the server seeds from standings.
    east: list[SeedEntry] | None = None
    west: list[SeedEntry] | None = None


class SeriesResult(BaseModel):
    """One best-of-seven series in the representative bracket run."""

    higher: TeamRef
    lower: TeamRef
    higher_won: bool
    higher_wins: int
    lower_wins: int


class BracketColumn(BaseModel):
    label: str
    series: list[SeriesResult]


class ChampionshipOdd(BaseModel):
    team: TeamRef
    titles: int
    probability: float


class SimulateResponse(BaseModel):
    n_simulations: int
    champion: TeamRef
    runner_up: TeamRef
    final_higher_wins: int
    final_lower_wins: int
    columns: list[BracketColumn]
    odds: list[ChampionshipOdd]


class SeedsResponse(BaseModel):
    """Default seeding presented before a simulation is run."""

    east: list[TeamRef]
    west: list[TeamRef]
