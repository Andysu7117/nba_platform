"""Primitive, widely-reused response models."""
from __future__ import annotations

from pydantic import BaseModel, Field


class TeamRef(BaseModel):
    """A lightweight team descriptor embedded in many responses."""

    team_id: int
    abbr: str
    city: str
    name: str
    conference: str
    color: str
    record: str | None = Field(default=None, description="e.g. '48-12' when known")


class ModelStatus(BaseModel):
    """Training status surfaced to the dashboard."""

    trained: bool
    accuracy: float | None = None
    log_loss: float | None = None
    brier_score: float | None = None
    n_train: int | None = None
    n_test: int | None = None
    train_end_date: str | None = None
    test_start_date: str | None = None
