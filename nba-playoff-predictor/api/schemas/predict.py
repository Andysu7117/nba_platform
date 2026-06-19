"""Game-predictor request/response models."""
from __future__ import annotations

from pydantic import BaseModel, Field

from api.schemas.common import TeamRef


class PredictRequest(BaseModel):
    home_abbr: str = Field(..., description="Home team abbreviation, e.g. 'BOS'")
    away_abbr: str = Field(..., description="Away team abbreviation, e.g. 'LAL'")


class PredictFactor(BaseModel):
    """A single comparison row in the 'key factors' breakdown."""

    label: str
    away_value: float
    home_value: float
    higher_is_better: bool


class PredictResponse(BaseModel):
    home: TeamRef
    away: TeamRef
    home_win_prob: float
    away_win_prob: float
    predicted_winner: str  # "home" | "away"
    projected_home_score: int
    projected_away_score: int
    factors: list[PredictFactor]
