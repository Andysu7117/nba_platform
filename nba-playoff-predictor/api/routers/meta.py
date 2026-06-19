"""Health, model status and dataset metadata."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from src.app_helpers import load_saved_metrics
from src.config import DEFAULT_SEASONS

from api.schemas.common import ModelStatus
from api.services import data, schedule

router = APIRouter(tags=["meta"])


class AppMeta(BaseModel):
    current_season: str
    latest_date: str | None
    has_model: bool
    has_data: bool


class SeasonsResponse(BaseModel):
    current: str
    seasons: list[str]  # newest first


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/seasons", response_model=SeasonsResponse)
def seasons() -> SeasonsResponse:
    """Selectable seasons, newest first."""
    return SeasonsResponse(current=data.CURRENT_SEASON, seasons=list(reversed(DEFAULT_SEASONS)))


@router.get("/meta", response_model=AppMeta)
def app_meta() -> AppMeta:
    latest = schedule.latest_game_date()
    return AppMeta(
        current_season=data.CURRENT_SEASON,
        latest_date=latest.isoformat() if latest else None,
        has_model=data.has_model(),
        has_data=not data.all_team_games().empty,
    )


@router.get("/meta/model", response_model=ModelStatus)
def model_status() -> ModelStatus:
    metrics = load_saved_metrics()
    if metrics is None:
        return ModelStatus(trained=data.has_model())
    return ModelStatus(
        trained=data.has_model(),
        accuracy=metrics.get("accuracy"),
        log_loss=metrics.get("log_loss"),
        brier_score=metrics.get("brier_score"),
        n_train=metrics.get("n_train"),
        n_test=metrics.get("n_test"),
        train_end_date=metrics.get("train_end_date"),
        test_start_date=metrics.get("test_start_date"),
    )
