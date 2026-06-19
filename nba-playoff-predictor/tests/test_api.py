"""Smoke tests for the FastAPI layer.

These exercise the routers against whatever data is cached locally. They assert
on contract/shape rather than exact values so they stay stable across data
refreshes, and skip gracefully when no data/model is present.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.services import data

client = TestClient(app)


def test_health() -> None:
    assert client.get("/api/health").json() == {"status": "ok"}


def test_teams_returns_all_30() -> None:
    teams = client.get("/api/teams").json()
    assert len(teams) == 30
    assert {t["conference"] for t in teams} == {"East", "West"}
    assert all(t["color"].startswith("#") for t in teams)


def test_meta_shape() -> None:
    meta = client.get("/api/meta").json()
    assert "current_season" in meta
    assert isinstance(meta["has_model"], bool)


@pytest.mark.skipif(data.all_team_games().empty, reason="no cached team games")
def test_standings_ranked_and_consistent() -> None:
    body = client.get("/api/standings?conference=East").json()
    rows = body["rows"]
    assert rows, "expected at least one standings row"
    # Ranks are 1..n in order.
    assert [r["rank"] for r in rows] == list(range(1, len(rows) + 1))
    # Win pct is monotonically non-increasing down the table.
    pcts = [r["win_pct"] for r in rows]
    assert pcts == sorted(pcts, reverse=True)


@pytest.mark.skipif(data.all_team_games().empty, reason="no cached team games")
def test_predict_probabilities_complementary() -> None:
    res = client.post("/api/predict", json={"home_abbr": "BOS", "away_abbr": "LAL"})
    assert res.status_code == 200
    body = res.json()
    assert abs(body["home_win_prob"] + body["away_win_prob"] - 1.0) < 1e-6
    assert body["predicted_winner"] in {"home", "away"}
    assert len(body["factors"]) == 4


def test_predict_rejects_same_team() -> None:
    res = client.post("/api/predict", json={"home_abbr": "BOS", "away_abbr": "BOS"})
    assert res.status_code == 400


def test_predict_unknown_team_404() -> None:
    res = client.post("/api/predict", json={"home_abbr": "ZZZ", "away_abbr": "LAL"})
    assert res.status_code == 404


@pytest.mark.skipif(
    data.modeling_dataset().empty or not data.has_model(),
    reason="needs model + dataset",
)
def test_simulate_returns_bracket_and_odds() -> None:
    res = client.post("/api/playoffs/simulate", json={"n_simulations": 200})
    assert res.status_code == 200
    body = res.json()
    assert len(body["columns"]) == 7
    assert body["champion"]["abbr"]
    total = sum(o["titles"] for o in body["odds"])
    assert total <= body["n_simulations"]
