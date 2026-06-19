"""Player leaderboard, search and individual detail."""
from __future__ import annotations

from fastapi import APIRouter, Query

from api.schemas.players import PlayerDetailResponse, PlayerSearchResult, PlayersResponse
from api.services import players as players_service

router = APIRouter(prefix="/players", tags=["players"])


@router.get("", response_model=PlayersResponse)
def get_players(
    season: str | None = Query(None, description="e.g. '2025-26'; defaults to current"),
    min_games: int = Query(15, ge=0, le=82, description="Minimum games played filter"),
) -> PlayersResponse:
    return players_service.get_players(season, min_games)


@router.get("/search", response_model=list[PlayerSearchResult])
def search_players(q: str = Query(..., min_length=1, description="Player name query")) -> list[PlayerSearchResult]:
    return players_service.search_players(q)


@router.get("/{player_id}", response_model=PlayerDetailResponse)
def player_detail(
    player_id: int,
    season: str | None = Query(None, description="e.g. '2025-26'; defaults to current"),
    season_type: str = Query("Regular Season", pattern="^(Regular Season|Playoffs)$"),
    per_mode: str = Query("PerGame", pattern="^(PerGame|Totals)$"),
) -> PlayerDetailResponse:
    return players_service.get_player_detail(player_id, season, season_type, per_mode)
