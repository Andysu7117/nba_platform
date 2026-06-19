"""Best-of-seven playoff series simulation using the 2-2-1-1-1 format.

``game_probability_func(home_team, away_team)`` must return the probability that
the **home** team wins a single game. The series simulator handles home-court
alternation; the probability function only ever sees who is at home.
"""
from __future__ import annotations

import random

# 1-indexed game -> which side hosts. The home-court team hosts games 1,2,5,7.
# True  means "home-court team hosts", False means "the other team hosts".
_HOMECOURT_HOSTS_GAME = {1: True, 2: True, 3: False, 4: False, 5: True, 6: False, 7: True}


def simulate_series(
    team_a,
    team_b,
    game_probability_func,
    homecourt_team,
    n_games: int = 7,
    rng: random.Random | None = None,
) -> str:
    """Simulate one best-of-seven series and return the winning team.

    Parameters
    ----------
    team_a, team_b:
        The two competing teams (any hashable identifiers).
    game_probability_func:
        ``f(home_team, away_team) -> P(home team wins)``.
    homecourt_team:
        Which of ``team_a``/``team_b`` holds home-court advantage (hosts games
        1, 2, 5, 7).
    n_games:
        Length of the series (default 7); ``wins_needed`` is ``n_games // 2 + 1``.
    rng:
        Optional ``random.Random`` for reproducible simulations.
    """
    rng = rng or random
    wins_needed = n_games // 2 + 1

    other_team = team_b if homecourt_team == team_a else team_a

    wins = {team_a: 0, team_b: 0}

    for game_no in range(1, n_games + 1):
        if _HOMECOURT_HOSTS_GAME.get(game_no, True):
            home, away = homecourt_team, other_team
        else:
            home, away = other_team, homecourt_team

        p_home = game_probability_func(home, away)
        winner = home if rng.random() < p_home else away
        wins[winner] += 1

        if wins[winner] >= wins_needed:
            return winner

    # Should be unreachable in a valid best-of format, but return current leader.
    return team_a if wins[team_a] >= wins[team_b] else team_b


def estimate_series_probability(
    team_a,
    team_b,
    game_probability_func,
    homecourt_team,
    n_simulations: int = 1000,
    rng: random.Random | None = None,
) -> dict:
    """Monte-Carlo estimate of each team's series-win probability.

    Returns a dict mapping each team to its estimated probability of winning the
    series; the two values sum to 1.
    """
    rng = rng or random
    counts = {team_a: 0, team_b: 0}

    for _ in range(n_simulations):
        winner = simulate_series(
            team_a, team_b, game_probability_func, homecourt_team, rng=rng
        )
        counts[winner] += 1

    total = max(n_simulations, 1)
    return {
        team_a: counts[team_a] / total,
        team_b: counts[team_b] / total,
    }
