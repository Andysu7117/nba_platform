"""Full 16-team playoff bracket simulation.

The bracket is supplied explicitly (seeds 1-8 for East and West) so the MVP can
let users pick teams manually in Streamlit rather than depending on live
standings. Home-court advantage in every round goes to the higher seed.
"""
from __future__ import annotations

import random
from collections import defaultdict

from src.simulation.simulate_series import simulate_series

# Standard NBA first-round seed pairings within a conference.
_FIRST_ROUND_PAIRS = [(1, 8), (4, 5), (3, 6), (2, 7)]


def _higher_seed(team_seed_a: tuple, team_seed_b: tuple) -> tuple:
    """Given two (team, seed) tuples, return the one with the better (lower) seed."""
    return team_seed_a if team_seed_a[1] <= team_seed_b[1] else team_seed_b


def _play(matchup_a: tuple, matchup_b: tuple, prob_func, rng) -> tuple:
    """Play a series between two (team, seed) tuples; return the winner tuple.

    Home-court (hosting games 1,2,5,7) goes to the higher seed.
    """
    team_a, _ = matchup_a
    team_b, _ = matchup_b
    homecourt = _higher_seed(matchup_a, matchup_b)
    winner_team = simulate_series(
        team_a, team_b, prob_func, homecourt_team=homecourt[0], rng=rng
    )
    # Preserve the winner's seed for downstream home-court decisions.
    return matchup_a if winner_team == team_a else matchup_b


def _simulate_conference(seeds: dict, prob_func, rng, advancement: dict) -> tuple:
    """Simulate one conference; return the (team, seed) conference champion.

    ``advancement`` is mutated in place to tally how far each team got.
    """
    # Round 1.
    semifinalists = []
    for high, low in _FIRST_ROUND_PAIRS:
        winner = _play((seeds[high], high), (seeds[low], low), prob_func, rng)
        advancement[winner[0]]["round_2"] += 1
        semifinalists.append(winner)

    # Conference semifinals: bracket order (1/8 vs 4/5), (3/6 vs 2/7).
    cf_a = _play(semifinalists[0], semifinalists[1], prob_func, rng)
    cf_b = _play(semifinalists[2], semifinalists[3], prob_func, rng)
    advancement[cf_a[0]]["conf_finals"] += 1
    advancement[cf_b[0]]["conf_finals"] += 1

    # Conference finals.
    champ = _play(cf_a, cf_b, prob_func, rng)
    advancement[champ[0]]["finals"] += 1
    return champ


def simulate_playoffs(
    bracket: dict,
    game_probability_func,
    n_simulations: int = 1000,
    rng: random.Random | None = None,
) -> dict:
    """Monte-Carlo simulate the full playoffs.

    Parameters
    ----------
    bracket:
        ``{"East": {1: team_id, ..., 8: team_id}, "West": {1: ..., 8: ...}}``.
    game_probability_func:
        ``f(home_team, away_team) -> P(home wins)``.
    n_simulations:
        Number of bracket simulations.

    Returns
    -------
    dict with keys:
        ``champion_counts``  - team -> number of titles won
        ``finals_counts``    - team -> number of Finals appearances
        ``advancement``      - team -> {round_2, conf_finals, finals, champion}
        ``n_simulations``    - echoed back for probability normalisation
    """
    rng = rng or random
    champion_counts: dict = defaultdict(int)
    finals_counts: dict = defaultdict(int)
    advancement: dict = defaultdict(
        lambda: {"round_2": 0, "conf_finals": 0, "finals": 0, "champion": 0}
    )

    for _ in range(n_simulations):
        east_champ = _simulate_conference(bracket["East"], game_probability_func, rng, advancement)
        west_champ = _simulate_conference(bracket["West"], game_probability_func, rng, advancement)

        finals_counts[east_champ[0]] += 1
        finals_counts[west_champ[0]] += 1

        # NBA Finals: higher seed gets home court (ties -> East by convention).
        champ = _play(east_champ, west_champ, game_probability_func, rng)
        champion_counts[champ[0]] += 1
        advancement[champ[0]]["champion"] += 1

    return {
        "champion_counts": dict(champion_counts),
        "finals_counts": dict(finals_counts),
        "advancement": {k: dict(v) for k, v in advancement.items()},
        "n_simulations": n_simulations,
    }
