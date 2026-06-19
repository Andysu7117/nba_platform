"""Canonical NBA team metadata.

The NBA stats feeds give us ``TEAM_ID``, ``TEAM_ABBREVIATION`` and a combined
``TEAM_NAME`` ("Boston Celtics") but not the conference, the city/nickname split
or a brand colour — all of which the UI needs. We keep that here, keyed by the
stable three-letter abbreviation, and join it onto the live data by ``team_id``.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Team:
    """Immutable descriptor for one franchise."""

    team_id: int
    abbr: str
    city: str
    name: str
    conference: str  # "East" | "West"
    color: str  # primary brand colour (hex)

    @property
    def full_name(self) -> str:
        return f"{self.city} {self.name}"


# Ordered roughly by conference then alphabetically; ``team_id`` values match the
# NBA stats API (and the cached parquet files).
_TEAMS: tuple[Team, ...] = (
    # ---- Eastern Conference ------------------------------------------------
    Team(1610612737, "ATL", "Atlanta", "Hawks", "East", "#E03A3E"),
    Team(1610612738, "BOS", "Boston", "Celtics", "East", "#1B7A43"),
    Team(1610612751, "BKN", "Brooklyn", "Nets", "East", "#2E2E2E"),
    Team(1610612766, "CHA", "Charlotte", "Hornets", "East", "#1D1160"),
    Team(1610612741, "CHI", "Chicago", "Bulls", "East", "#CE1141"),
    Team(1610612739, "CLE", "Cleveland", "Cavaliers", "East", "#860038"),
    Team(1610612765, "DET", "Detroit", "Pistons", "East", "#C8102E"),
    Team(1610612754, "IND", "Indiana", "Pacers", "East", "#13294B"),
    Team(1610612748, "MIA", "Miami", "Heat", "East", "#98002E"),
    Team(1610612749, "MIL", "Milwaukee", "Bucks", "East", "#00471B"),
    Team(1610612752, "NYK", "New York", "Knicks", "East", "#1D428A"),
    Team(1610612753, "ORL", "Orlando", "Magic", "East", "#0B77C2"),
    Team(1610612755, "PHI", "Philadelphia", "76ers", "East", "#1D5FB6"),
    Team(1610612761, "TOR", "Toronto", "Raptors", "East", "#CE1141"),
    Team(1610612764, "WAS", "Washington", "Wizards", "East", "#002B5C"),
    # ---- Western Conference ------------------------------------------------
    Team(1610612742, "DAL", "Dallas", "Mavericks", "West", "#0053BC"),
    Team(1610612743, "DEN", "Denver", "Nuggets", "West", "#0E2240"),
    Team(1610612744, "GSW", "Golden State", "Warriors", "West", "#1D428A"),
    Team(1610612745, "HOU", "Houston", "Rockets", "West", "#CE1141"),
    Team(1610612746, "LAC", "LA", "Clippers", "West", "#C8102E"),
    Team(1610612747, "LAL", "Los Angeles", "Lakers", "West", "#552583"),
    Team(1610612763, "MEM", "Memphis", "Grizzlies", "West", "#5D76A9"),
    Team(1610612750, "MIN", "Minnesota", "Timberwolves", "West", "#236192"),
    Team(1610612740, "NOP", "New Orleans", "Pelicans", "West", "#0C2340"),
    Team(1610612760, "OKC", "Oklahoma City", "Thunder", "West", "#007AC1"),
    Team(1610612756, "PHX", "Phoenix", "Suns", "West", "#5B2B82"),
    Team(1610612757, "POR", "Portland", "Trail Blazers", "West", "#E03A3E"),
    Team(1610612758, "SAC", "Sacramento", "Kings", "West", "#5A2D81"),
    Team(1610612759, "SAS", "San Antonio", "Spurs", "West", "#1A1A1A"),
    Team(1610612762, "UTA", "Utah", "Jazz", "West", "#002B5C"),
)

TEAMS_BY_ID: dict[int, Team] = {t.team_id: t for t in _TEAMS}
TEAMS_BY_ABBR: dict[str, Team] = {t.abbr: t for t in _TEAMS}


def all_teams() -> list[Team]:
    """Return every team, ordered East then West, alphabetically within each."""
    return list(_TEAMS)


def get_by_id(team_id: int) -> Team | None:
    return TEAMS_BY_ID.get(int(team_id))


def get_by_abbr(abbr: str) -> Team | None:
    return TEAMS_BY_ABBR.get(abbr.upper())


def require_by_abbr(abbr: str) -> Team:
    team = get_by_abbr(abbr)
    if team is None:
        raise KeyError(f"Unknown team abbreviation: {abbr!r}")
    return team
