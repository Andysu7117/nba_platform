"""Tests for playoff series simulation."""
import random

from src.simulation.simulate_series import (
    estimate_series_probability,
    simulate_series,
)


def test_dominant_home_team_produces_valid_winner():
    # Probability function: the home team always wins.
    def always_home_wins(home, away):
        return 1.0

    # With home court for A, A hosts games 1,2,5,7 and B hosts 3,4,6.
    # A wins games 1,2,5 (3 wins) and B wins 3,4 -> game 5 makes A reach 3,
    # continue: A also wins game 5; B wins 3,4; A needs 4 -> wins 1,2,5,7.
    winner = simulate_series("A", "B", always_home_wins, homecourt_team="A")
    assert winner in ("A", "B")
    # A hosts 4 games (1,2,5,7) and always wins at home -> A takes the series.
    assert winner == "A"


def test_estimate_series_probabilities_sum_to_one():
    rng = random.Random(42)

    def coin_flip(home, away):
        return 0.5

    probs = estimate_series_probability(
        "A", "B", coin_flip, homecourt_team="A", n_simulations=500, rng=rng
    )
    assert set(probs) == {"A", "B"}
    assert abs(sum(probs.values()) - 1.0) < 1e-9
    # With even games, both teams should have non-trivial chances.
    assert 0.2 < probs["A"] < 0.8


def test_homecourt_advantage_helps():
    rng = random.Random(7)

    # Home team wins 70% of games -> the team with home court should win
    # the series more often than not.
    def home_edge(home, away):
        return 0.7

    probs = estimate_series_probability(
        "A", "B", home_edge, homecourt_team="A", n_simulations=2000, rng=rng
    )
    assert probs["A"] > 0.5
