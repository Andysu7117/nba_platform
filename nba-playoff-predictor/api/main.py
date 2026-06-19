"""FastAPI application entry point.

Run locally with::

    uvicorn api.main:app --reload

All resource routers are mounted under ``/api``. Interactive docs live at
``/api/docs``.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import API_PREFIX, CORS_ORIGINS
from api.routers import (
    meta,
    players,
    playoffs,
    predict,
    schedule,
    standings,
    teams,
)

app = FastAPI(
    title="NBA Platform API",
    description="Stats, predictions and playoff simulation for the NBA platform.",
    version="1.0.0",
    docs_url=f"{API_PREFIX}/docs",
    openapi_url=f"{API_PREFIX}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (meta, teams, standings, schedule, predict, playoffs, players):
    app.include_router(router.router, prefix=API_PREFIX)
