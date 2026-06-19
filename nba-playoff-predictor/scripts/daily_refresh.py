"""Refresh the live data the platform depends on. Run daily from a scheduler.

Re-pulls the current season's team games (standings / records / predictions),
today's scoreboard, and the league player leaderboard — all from the NBA API,
bypassing the cache. Each step is best-effort: a failure is logged and the
others still run.

    python -m scripts.daily_refresh

Schedule it with cron (Linux/macOS) or Task Scheduler (Windows) to keep the
cached data current without restarting the API.
"""
from __future__ import annotations

import datetime as dt

from src.config import DEFAULT_SEASON_TYPE, DEFAULT_SEASONS

CURRENT_SEASON = DEFAULT_SEASONS[-1]


def _step(label: str, fn) -> None:
    try:
        fn()
        print(f"  [ok]   {label}")
    except Exception as err:  # noqa: BLE001
        print(f"  [skip] {label}: {err}")


def main() -> None:
    today = dt.date.today().isoformat()
    print(f"Daily refresh for {today} (season {CURRENT_SEASON}) ...")

    from src.ingest.fetch_league_player_stats import fetch_league_player_stats
    from src.ingest.fetch_scoreboard import fetch_scoreboard
    from src.ingest.fetch_team_games import fetch_team_games

    _step("team games", lambda: fetch_team_games(CURRENT_SEASON, DEFAULT_SEASON_TYPE, force_refresh=True))
    _step("today's scoreboard", lambda: fetch_scoreboard(today, force_refresh=True))
    _step("player leaderboard", lambda: fetch_league_player_stats(CURRENT_SEASON))

    print("Done. The running API picks up team-game changes within a day; "
          "restart it to force an immediate reload.")


if __name__ == "__main__":
    main()
