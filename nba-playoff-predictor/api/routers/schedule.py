"""Schedule, calendar counts and box scores."""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, HTTPException, Query

from api.schemas.schedule import (
    BoxScoreResponse,
    CalendarResponse,
    ScheduleResponse,
)
from api.services import schedule as schedule_service

router = APIRouter(tags=["schedule"])


def _parse_date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=f"Invalid date {value!r}; use YYYY-MM-DD.") from err


@router.get("/schedule", response_model=ScheduleResponse)
def get_schedule(date: str = Query(..., description="YYYY-MM-DD")) -> ScheduleResponse:
    return schedule_service.get_schedule(_parse_date(date))


@router.get("/schedule/calendar", response_model=CalendarResponse)
def get_calendar(
    start: str = Query(..., description="YYYY-MM-DD"),
    end: str = Query(..., description="YYYY-MM-DD"),
) -> CalendarResponse:
    s, e = _parse_date(start), _parse_date(end)
    if e < s:
        raise HTTPException(status_code=400, detail="`end` must be on or after `start`.")
    if (e - s).days > 60:
        raise HTTPException(status_code=400, detail="Range too large (max 60 days).")
    return schedule_service.get_calendar(s, e)


@router.get("/games/{game_id}/boxscore", response_model=BoxScoreResponse)
def get_box_score(game_id: str) -> BoxScoreResponse:
    return schedule_service.get_box_score(game_id)
