"""Playoff seeding and Monte-Carlo simulation."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas.playoffs import SeedsResponse, SimulateRequest, SimulateResponse
from api.services import playoffs as playoffs_service

router = APIRouter(prefix="/playoffs", tags=["playoffs"])


@router.get("/seeds", response_model=SeedsResponse)
def default_seeds() -> SeedsResponse:
    return playoffs_service.get_default_seeds()


@router.post("/simulate", response_model=SimulateResponse)
def simulate(req: SimulateRequest) -> SimulateResponse:
    try:
        return playoffs_service.simulate(req)
    except (KeyError, ValueError) as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
