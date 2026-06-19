"""Playoff-simulator service.

Produces two things the UI needs from one request:

* **Championship odds** — a Monte-Carlo run (``simulate_playoffs`` in ``src``)
  over ``n_simulations`` brackets.
* **A representative bracket run** — one fully-played bracket whose individual
  series results drive the bracket visualisation.

Seeds default to the top eight of each conference's standings but can be
overridden by the client.
"""
from __future__ import annotations

import math
import random

from api.reference import teams as team_ref
from api.reference.teams import Team
from api.schemas.common import TeamRef
from api.schemas.playoffs import (
    BracketColumn,
    ChampionshipOdd,
    SeedEntry,
    SeedsResponse,
    SeriesResult,
    SimulateRequest,
    SimulateResponse,
)
from api.services import data, standings
from src.models.predict import build_matchup_features, predict_from_feature_dict
from src.simulation.simulate_playoffs import simulate_playoffs

_FIRST_ROUND_PAIRS = [(1, 8), (4, 5), (3, 6), (2, 7)]


def _team_ref(team: Team, records: dict[int, str]) -> TeamRef:
    return TeamRef(team_id=team.team_id, abbr=team.abbr, city=team.city, name=team.name,
                   conference=team.conference, color=team.color, record=records.get(team.team_id))


def _default_seed_ids(conference: str, season: str) -> dict[int, int]:
    rows = standings.get_standings(conference, season).rows[:8]
    return {i + 1: row.team.team_id for i, row in enumerate(rows)}


def get_default_seeds(season: str | None = None) -> SeedsResponse:
    season = season or data.CURRENT_SEASON
    records = standings.team_record_map(season)

    def refs(conf: str) -> list[TeamRef]:
        seeds = _default_seed_ids(conf, season)
        out = []
        for s in range(1, 9):
            meta = team_ref.get_by_id(seeds.get(s, 0))
            if meta:
                out.append(_team_ref(meta, records))
        return out

    return SeedsResponse(east=refs("East"), west=refs("West"))


def _seed_map(entries: list[SeedEntry] | None, conference: str, season: str) -> dict[int, int]:
    if not entries:
        return _default_seed_ids(conference, season)
    out: dict[int, int] = {}
    for e in entries:
        meta = team_ref.require_by_abbr(e.abbr)
        out[e.seed] = meta.team_id
    if len(out) != 8:
        raise ValueError(f"{conference} seeding must list all 8 seeds (got {len(out)}).")
    return out


def _make_prob_func(model: dict | None, dataset, net_by_id: dict[int, float]):
    """Return ``f(home_id, away_id) -> P(home win)`` with memoisation."""
    cache: dict[tuple[int, int], float] = {}

    def prob(home_id: int, away_id: int) -> float:
        key = (home_id, away_id)
        if key not in cache:
            if model is not None and not dataset.empty:
                feats = build_matchup_features(home_id, away_id, dataset)
                p = predict_from_feature_dict(feats, model)
            else:
                net = (net_by_id.get(home_id, 0.0) - net_by_id.get(away_id, 0.0)) + 2.6
                p = 1.0 / (1.0 + math.exp(-net / 4.6))
            cache[key] = min(0.95, max(0.05, float(p)))
        return cache[key]

    return prob


def _play_series(higher: tuple[int, int], lower: tuple[int, int], prob, rng) -> dict:
    """Play one best-of-7 (higher seed hosts 1,2,5,7); return result detail."""
    home_schedule = {1: True, 2: True, 3: False, 4: False, 5: True, 6: False, 7: True}
    wins = {higher[0]: 0, lower[0]: 0}
    for game in range(1, 8):
        if home_schedule[game]:
            home, away = higher[0], lower[0]
        else:
            home, away = lower[0], higher[0]
        p_home = prob(home, away)
        winner = home if rng.random() < p_home else away
        wins[winner] += 1
        if wins[winner] == 4:
            break
    higher_won = wins[higher[0]] >= 4
    return {
        "higher": higher, "lower": lower, "higher_won": higher_won,
        "higher_wins": wins[higher[0]], "lower_wins": wins[lower[0]],
    }


def _higher(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
    return a if a[1] <= b[1] else b


def _lower(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
    return b if a[1] <= b[1] else a


def _run_conference(seed_ids: dict[int, int], prob, rng) -> dict:
    """Play one conference; return r1/semis/final series detail + champion tuple."""
    seeds = {s: (tid, s) for s, tid in seed_ids.items()}
    r1 = [_play_series(seeds[h], seeds[l], prob, rng) for h, l in _FIRST_ROUND_PAIRS]
    r1_winners = [(r["higher"] if r["higher_won"] else r["lower"]) for r in r1]
    semis = [
        _play_series(_higher(r1_winners[0], r1_winners[1]), _lower(r1_winners[0], r1_winners[1]), prob, rng),
        _play_series(_higher(r1_winners[2], r1_winners[3]), _lower(r1_winners[2], r1_winners[3]), prob, rng),
    ]
    semi_winners = [(s["higher"] if s["higher_won"] else s["lower"]) for s in semis]
    final = _play_series(_higher(semi_winners[0], semi_winners[1]), _lower(semi_winners[0], semi_winners[1]), prob, rng)
    champ = final["higher"] if final["higher_won"] else final["lower"]
    return {"r1": r1, "semis": semis, "final": final, "champion": champ}


def _series_ref(detail: dict, records: dict[int, str]) -> SeriesResult:
    higher = team_ref.get_by_id(detail["higher"][0])
    lower = team_ref.get_by_id(detail["lower"][0])
    return SeriesResult(
        higher=_team_ref(higher, records),
        lower=_team_ref(lower, records),
        higher_won=detail["higher_won"],
        higher_wins=detail["higher_wins"],
        lower_wins=detail["lower_wins"],
    )


def simulate(req: SimulateRequest) -> SimulateResponse:
    season = data.CURRENT_SEASON
    records = standings.team_record_map(season)
    east_ids = _seed_map(req.east, "East", season)
    west_ids = _seed_map(req.west, "West", season)

    model = data.get_model()
    dataset = data.modeling_dataset()
    net_by_id = {row.team.team_id: row.net_rating
                 for row in standings.get_standings("League", season).rows}
    prob = _make_prob_func(model, dataset, net_by_id)

    # ---- Championship odds over many brackets --------------------------------
    odds_raw = simulate_playoffs({"East": east_ids, "West": west_ids}, prob, n_simulations=req.n_simulations)
    total = odds_raw["n_simulations"]
    odds: list[ChampionshipOdd] = []
    for team_id, titles in sorted(odds_raw["champion_counts"].items(), key=lambda kv: kv[1], reverse=True):
        meta = team_ref.get_by_id(team_id)
        if meta is None or titles == 0:
            continue
        odds.append(ChampionshipOdd(team=_team_ref(meta, records), titles=titles,
                                    probability=round(titles / total, 4)))

    # ---- One representative bracket run for the visualisation ----------------
    rng = random.Random()
    east = _run_conference(east_ids, prob, rng)
    west = _run_conference(west_ids, prob, rng)
    final = _play_series(_higher(east["champion"], west["champion"]),
                         _lower(east["champion"], west["champion"]), prob, rng)
    champion_tuple = final["higher"] if final["higher_won"] else final["lower"]
    runner_tuple = final["lower"] if final["higher_won"] else final["higher"]

    columns = [
        BracketColumn(label="EAST R1", series=[_series_ref(s, records) for s in east["r1"]]),
        BracketColumn(label="E. SEMIS", series=[_series_ref(s, records) for s in east["semis"]]),
        BracketColumn(label="E. FINAL", series=[_series_ref(east["final"], records)]),
        BracketColumn(label="FINALS", series=[_series_ref(final, records)]),
        BracketColumn(label="W. FINAL", series=[_series_ref(west["final"], records)]),
        BracketColumn(label="W. SEMIS", series=[_series_ref(s, records) for s in west["semis"]]),
        BracketColumn(label="WEST R1", series=[_series_ref(s, records) for s in west["r1"]]),
    ]

    return SimulateResponse(
        n_simulations=total,
        champion=_team_ref(team_ref.get_by_id(champion_tuple[0]), records),
        runner_up=_team_ref(team_ref.get_by_id(runner_tuple[0]), records),
        final_higher_wins=final["higher_wins"],
        final_lower_wins=final["lower_wins"],
        columns=columns,
        odds=odds,
    )
