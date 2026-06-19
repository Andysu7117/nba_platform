"""Player leaderboard."""
from __future__ import annotations

from fastapi import APIRouter, Query

from api.schemas.players import PlayersResponse
from api.services import players as players_service

router = APIRouter(prefix="/players", tags=["players"])


@router.get("", response_model=PlayersResponse)
def get_players(
    season: str | None = Query(None, description="e.g. '2025-26'; defaults to current"),
    min_games: int = Query(15, ge=0, le=82, description="Minimum games played filter"),
) -> PlayersResponse:
    return players_service.get_players(season, min_games)
