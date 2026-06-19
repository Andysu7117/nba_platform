"""Conference standings / team stats."""
from __future__ import annotations

from fastapi import APIRouter, Query

from api.schemas.standings import StandingsResponse
from api.services import standings as standings_service

router = APIRouter(prefix="/standings", tags=["standings"])


@router.get("", response_model=StandingsResponse)
def get_standings(
    conference: str = Query("East", pattern="^(East|West|League|east|west|league)$"),
    season: str | None = Query(None, description="e.g. '2025-26'; defaults to current"),
) -> StandingsResponse:
    return standings_service.get_standings(conference, season)
