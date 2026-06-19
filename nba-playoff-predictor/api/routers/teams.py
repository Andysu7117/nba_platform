"""Team directory."""
from __future__ import annotations

from fastapi import APIRouter

from api.reference import teams as team_ref
from api.schemas.common import TeamRef
from api.services import standings

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=list[TeamRef])
def list_teams() -> list[TeamRef]:
    """All 30 teams with their current-season record where available."""
    records = standings.team_record_map()
    return [
        TeamRef(
            team_id=t.team_id, abbr=t.abbr, city=t.city, name=t.name,
            conference=t.conference, color=t.color, record=records.get(t.team_id),
        )
        for t in team_ref.all_teams()
    ]
