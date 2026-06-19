"""API settings, configurable via environment variables."""
from __future__ import annotations

import os

# Comma-separated list of allowed CORS origins for the frontend dev/prod hosts.
_DEFAULT_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"

CORS_ORIGINS: list[str] = [
    o.strip() for o in os.getenv("NBA_CORS_ORIGINS", _DEFAULT_ORIGINS).split(",") if o.strip()
]

API_PREFIX: str = "/api"
