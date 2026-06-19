"""Warm the league player-stats cache for the Player Stats page.

Run while online::

    python -m scripts.fetch_player_leaderboard
    python -m scripts.fetch_player_leaderboard --season 2024-25
"""
from __future__ import annotations

import argparse

from src.config import DEFAULT_SEASON_TYPE, DEFAULT_SEASONS
from src.ingest.fetch_league_player_stats import fetch_league_player_stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Cache league-wide per-game player stats.")
    parser.add_argument("--season", default=DEFAULT_SEASONS[-1], help="e.g. 2025-26")
    parser.add_argument("--season-type", default=DEFAULT_SEASON_TYPE)
    args = parser.parse_args()

    print(f"Fetching league player stats for {args.season} ({args.season_type}) ...")
    df = fetch_league_player_stats(args.season, args.season_type)
    print(f"Cached {len(df)} players.")


if __name__ == "__main__":
    main()
