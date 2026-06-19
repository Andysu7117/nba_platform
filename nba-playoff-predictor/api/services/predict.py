"""Game-predictor service: model win probability + projected score + factors."""
from __future__ import annotations

import math

from api.reference import teams as team_ref
from api.reference.teams import Team
from api.schemas.common import TeamRef
from api.schemas.predict import PredictFactor, PredictResponse
from api.services import data, standings
from src.models.predict import predict_home_win_probability


def _team_ref(team: Team, record: str | None) -> TeamRef:
    return TeamRef(
        team_id=team.team_id, abbr=team.abbr, city=team.city, name=team.name,
        conference=team.conference, color=team.color, record=record,
    )


def _stats_by_id(season: str) -> dict[int, dict]:
    """Map ``team_id`` to its rating/record profile for the season."""
    out: dict[int, dict] = {}
    for row in standings.get_standings("League", season).rows:
        out[row.team.team_id] = {
            "off": row.off_rating,
            "def": row.def_rating,
            "net": row.net_rating,
            "win_pct": row.win_pct,
            "record": row.team.record,
        }
    return out


def _fallback_prob(home: dict, away: dict) -> float:
    """Rating-based logistic used when the trained model is unavailable."""
    net = (home["net"] - away["net"]) + 2.6  # +2.6 ≈ home-court edge
    return 1.0 / (1.0 + math.exp(-net / 4.6))


def predict_matchup(home_abbr: str, away_abbr: str) -> PredictResponse:
    home = team_ref.require_by_abbr(home_abbr)
    away = team_ref.require_by_abbr(away_abbr)
    if home.team_id == away.team_id:
        raise ValueError("Home and away teams must be different.")

    season = data.CURRENT_SEASON
    stats = _stats_by_id(season)
    # Neutral defaults keep the endpoint working even with no cached games.
    default = {"off": 113.0, "def": 113.0, "net": 0.0, "win_pct": 0.5, "record": None}
    hs = stats.get(home.team_id, default)
    as_ = stats.get(away.team_id, default)

    model = data.get_model()
    dataset = data.modeling_dataset()
    if model is not None and not dataset.empty:
        p_home = predict_home_win_probability(home.team_id, away.team_id, dataset, model=model)
    else:
        p_home = _fallback_prob(hs, as_)
    p_home = min(0.99, max(0.01, float(p_home)))

    # Projected score: blend each team's scoring with the opponent's defence,
    # plus a small home-court nudge.
    proj_home = round((hs["off"] + as_["def"]) / 2 + 1.5)
    proj_away = round((as_["off"] + hs["def"]) / 2 - 1.0)

    factors = [
        PredictFactor(label="Offensive Rating", away_value=as_["off"], home_value=hs["off"], higher_is_better=True),
        PredictFactor(label="Defensive Rating", away_value=as_["def"], home_value=hs["def"], higher_is_better=False),
        PredictFactor(label="Net Rating", away_value=as_["net"], home_value=hs["net"], higher_is_better=True),
        PredictFactor(
            label="Win %",
            away_value=round(as_["win_pct"] * 100, 1),
            home_value=round(hs["win_pct"] * 100, 1),
            higher_is_better=True,
        ),
    ]

    return PredictResponse(
        home=_team_ref(home, hs["record"]),
        away=_team_ref(away, as_["record"]),
        home_win_prob=round(p_home, 4),
        away_win_prob=round(1 - p_home, 4),
        predicted_winner="home" if p_home >= 0.5 else "away",
        projected_home_score=int(proj_home),
        projected_away_score=int(proj_away),
        factors=factors,
    )
