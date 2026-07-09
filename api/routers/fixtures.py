import html
import re
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import APIRouter

from api import data_service, fpl_client

router = APIRouter(prefix="/api/fixtures", tags=["fixtures"])

PL_2026_27_FIXTURES_URL = (
    "https://www.premierleague.com/en/news/4675097/"
    "all-380-fixtures-for-202627-premier-league-season"
)

TEAM_SHORT_NAMES = {
    "AFC Bournemouth": "BOU",
    "Arsenal": "ARS",
    "Aston Villa": "AVL",
    "Brentford": "BRE",
    "Brighton & Hove Albion": "BHA",
    "Chelsea": "CHE",
    "Coventry City": "COV",
    "Crystal Palace": "CRY",
    "Everton": "EVE",
    "Fulham": "FUL",
    "Hull City": "HUL",
    "Ipswich Town": "IPS",
    "Leeds United": "LEE",
    "Liverpool": "LIV",
    "Manchester City": "MCI",
    "Manchester United": "MUN",
    "Newcastle United": "NEW",
    "Nottingham Forest": "NFO",
    "Sunderland": "SUN",
    "Tottenham Hotspur": "TOT",
}

TEAM_STRENGTH = {
    "ARS": 5,
    "MCI": 5,
    "LIV": 5,
    "CHE": 4,
    "MUN": 4,
    "NEW": 4,
    "TOT": 4,
    "AVL": 4,
    "BOU": 3,
    "BHA": 3,
    "BRE": 3,
    "CRY": 3,
    "EVE": 3,
    "FUL": 3,
    "LEE": 3,
    "NFO": 3,
    "SUN": 2,
    "IPS": 2,
    "HUL": 2,
    "COV": 2,
}

MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

_PL_2026_27_CACHE: list[dict[str, Any]] | None = None

FPL_FIXTURE_SOURCE = "FPL Fantasy API"
PL_RELEASE_SOURCE = "Official PL fixture release"
FPL_DIFFICULTY_SOURCE = "Official FPL FDR"
ESTIMATED_DIFFICULTY_SOURCE = "App-estimated difficulty"


async def fixture_source_state() -> dict[str, str]:
    fixture_rows = await fpl_client.get_fixtures()
    upcoming = [fixture for fixture in fixture_rows if not fixture.get("finished", False)]
    if upcoming:
        return {
            "source": FPL_FIXTURE_SOURCE,
            "season": _season_from_fpl_fixtures(upcoming),
            "difficulty_source": FPL_DIFFICULTY_SOURCE,
            "freshness": "live",
        }

    return {
        "source": PL_RELEASE_SOURCE,
        "season": "2026-27",
        "difficulty_source": ESTIMATED_DIFFICULTY_SOURCE,
        "freshness": "static official release",
    }


@router.get("")
async def fixtures() -> list[dict[str, Any]]:
    rows = await fpl_client.get_fixtures()
    bootstrap = data_service.bootstrap_static()
    teams_by_id = {team.get("id"): team for team in bootstrap.get("teams", [])}
    upcoming = [fixture for fixture in rows if not fixture.get("finished", False)]
    if not upcoming:
        return await _premier_league_2026_27_fixtures()

    source_meta = {
        "source": FPL_FIXTURE_SOURCE,
        "season": _season_from_fpl_fixtures(upcoming),
        "difficulty_source": FPL_DIFFICULTY_SOURCE,
    }
    return [
        {
            "id": fixture.get("id"),
            "team_h": fixture.get("team_h"),
            "team_a": fixture.get("team_a"),
            "team_h_name": teams_by_id.get(fixture.get("team_h"), {}).get("name"),
            "team_a_name": teams_by_id.get(fixture.get("team_a"), {}).get("name"),
            "team_h_short": teams_by_id.get(fixture.get("team_h"), {}).get("short_name"),
            "team_a_short": teams_by_id.get(fixture.get("team_a"), {}).get("short_name"),
            "team_h_score": fixture.get("team_h_score"),
            "team_a_score": fixture.get("team_a_score"),
            "event": fixture.get("event"),
            "kickoff_time": fixture.get("kickoff_time"),
            "started": fixture.get("started"),
            "finished": fixture.get("finished"),
            "minutes": fixture.get("minutes"),
            "team_h_difficulty": fixture.get("team_h_difficulty"),
            "team_a_difficulty": fixture.get("team_a_difficulty"),
            **source_meta,
        }
        for fixture in upcoming
    ]


@router.get("/ticker")
async def ticker(range: int = 8) -> list[dict[str, Any]]:  # noqa: A002
    bootstrap = await fpl_client.get_bootstrap()
    fixture_rows = await fpl_client.get_fixtures()
    requested_range = min(max(range, 1), 8)

    teams = bootstrap.get("teams", [])
    team_by_id = {team["id"]: team for team in teams}
    upcoming = [
        fixture
        for fixture in fixture_rows
        if not fixture.get("finished", False) and fixture.get("event") is not None
    ]
    if not upcoming:
        return _ticker_from_named_fixtures(
            await _premier_league_2026_27_fixtures(),
            requested_range=requested_range,
        )

    source_meta = {
        "range": requested_range,
        "source": FPL_FIXTURE_SOURCE,
        "season": _season_from_fpl_fixtures(upcoming),
        "difficulty_source": FPL_DIFFICULTY_SOURCE,
    }
    next_gameweeks = sorted({fixture["event"] for fixture in upcoming})[:requested_range]

    grid = []
    for team in teams:
        team_id = team["id"]
        team_fixtures = []
        for fixture in upcoming:
            if fixture.get("event") not in next_gameweeks:
                continue
            if fixture.get("team_h") == team_id:
                opponent = team_by_id.get(fixture.get("team_a"), {})
                team_fixtures.append(
                    {
                        "gw": fixture.get("event"),
                        "opponent": opponent.get("short_name", opponent.get("name")),
                        "home": True,
                        "difficulty": fixture.get("team_h_difficulty"),
                    }
                )
            elif fixture.get("team_a") == team_id:
                opponent = team_by_id.get(fixture.get("team_h"), {})
                team_fixtures.append(
                    {
                        "gw": fixture.get("event"),
                        "opponent": opponent.get("short_name", opponent.get("name")),
                        "home": False,
                        "difficulty": fixture.get("team_a_difficulty"),
                    }
                )

        grid.append(
            {
                "team": team.get("name"),
                "team_short": team.get("short_name"),
                "fixtures": sorted(team_fixtures, key=lambda row: row["gw"]),
                **source_meta,
            }
        )

    return grid


def _season_from_fpl_fixtures(fixtures: list[dict[str, Any]]) -> str:
    kickoff_values = [
        fixture.get("kickoff_time")
        for fixture in fixtures
        if fixture.get("kickoff_time")
    ]
    if not kickoff_values:
        return "unknown"

    year = int(str(min(kickoff_values))[:4])
    return f"{year}-{str(year + 1)[-2:]}"


async def _premier_league_2026_27_fixtures() -> list[dict[str, Any]]:
    global _PL_2026_27_CACHE
    if _PL_2026_27_CACHE is not None:
        return _PL_2026_27_CACHE

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        response = await client.get(PL_2026_27_FIXTURES_URL)
        response.raise_for_status()

    _PL_2026_27_CACHE = _parse_premier_league_fixture_article(response.text)
    return _PL_2026_27_CACHE


def _parse_premier_league_fixture_article(source: str) -> list[dict[str, Any]]:
    paragraphs = re.findall(r"<p>(.*?)</p>", source, flags=re.DOTALL)
    fixtures: list[dict[str, Any]] = []
    current_date: tuple[int, int, int] | None = None

    for paragraph in paragraphs:
        lines = _clean_fixture_paragraph(paragraph)
        if not lines:
            continue

        parsed_date = _parse_article_date(lines[0])
        if parsed_date:
            current_date = parsed_date
            lines = lines[1:]

        if not current_date:
            continue

        for line in lines:
            fixture = _parse_fixture_line(line, current_date, len(fixtures))
            if fixture:
                fixtures.append(fixture)

    return fixtures


def _clean_fixture_paragraph(paragraph: str) -> list[str]:
    paragraph = re.sub(r"<br\s*/?>", "\n", paragraph)
    paragraph = re.sub(r"<[^>]+>", "", paragraph)
    paragraph = html.unescape(paragraph).replace("\xa0", " ")
    return [line.strip() for line in paragraph.splitlines() if line.strip()]


def _parse_article_date(line: str) -> tuple[int, int, int] | None:
    match = re.search(
        r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+"
        r"(?P<day>\d{1,2})\s+(?P<month>[A-Za-z]+)(?:\s+(?P<year>\d{4}))?",
        line,
    )
    if not match:
        return None

    month_name = match.group("month")
    month = MONTHS.get(month_name)
    if not month:
        return None

    year = int(match.group("year") or (2027 if month <= 5 else 2026))
    return year, month, int(match.group("day"))


def _parse_fixture_line(
    line: str,
    fixture_date: tuple[int, int, int],
    fixture_index: int,
) -> dict[str, Any] | None:
    if " v " not in line or line.startswith("*"):
        return None

    time_match = re.match(r"(?P<time>\d{1,2}:\d{2})\s+", line)
    kickoff = time_match.group("time") if time_match else "15:00"
    line = re.sub(r"^\d{1,2}:\d{2}\s+", "", line)
    line = re.sub(r"\s*\([^)]*\)\**$", "", line).rstrip("*").strip()
    try:
        home_name, away_name = [part.strip() for part in line.split(" v ", 1)]
    except ValueError:
        return None

    home_short = TEAM_SHORT_NAMES.get(home_name)
    away_short = TEAM_SHORT_NAMES.get(away_name)
    if not home_short or not away_short:
        return None

    year, month, day = fixture_date
    hour, minute = [int(part) for part in kickoff.split(":")]
    kickoff_time = (
        datetime(year, month, day, hour, minute, tzinfo=UTC)
        .isoformat()
        .replace("+00:00", "Z")
    )
    fixture_id = fixture_index + 1

    return {
        "id": fixture_id,
        "team_h": fixture_id * 2 - 1,
        "team_a": fixture_id * 2,
        "team_h_name": home_name,
        "team_a_name": away_name,
        "team_h_short": home_short,
        "team_a_short": away_short,
        "team_h_score": None,
        "team_a_score": None,
        "event": fixture_index // 10 + 1,
        "kickoff_time": kickoff_time,
        "started": False,
        "finished": False,
        "minutes": 0,
        "team_h_difficulty": _difficulty_against(away_short, is_home=True),
        "team_a_difficulty": _difficulty_against(home_short, is_home=False),
        "source": PL_RELEASE_SOURCE,
        "season": "2026-27",
        "difficulty_source": ESTIMATED_DIFFICULTY_SOURCE,
    }


def _difficulty_against(opponent_short: str, *, is_home: bool) -> int:
    base = TEAM_STRENGTH.get(opponent_short, 3)
    return min(5, max(1, base + (0 if is_home else 1)))


def _ticker_from_named_fixtures(
    fixtures: list[dict[str, Any]],
    requested_range: int = 8,
) -> list[dict[str, Any]]:
    teams = [
        {"name": name, "short_name": short}
        for name, short in sorted(TEAM_SHORT_NAMES.items(), key=lambda row: row[1])
    ]
    next_gameweeks = sorted({fixture["event"] for fixture in fixtures})[:requested_range]
    source_meta = {
        "range": requested_range,
        "source": PL_RELEASE_SOURCE,
        "season": "2026-27",
        "difficulty_source": ESTIMATED_DIFFICULTY_SOURCE,
    }
    grid = []

    for team in teams:
        team_short = team["short_name"]
        team_fixtures = []
        for fixture in fixtures:
            if fixture.get("event") not in next_gameweeks:
                continue
            if fixture.get("team_h_short") == team_short:
                team_fixtures.append(
                    {
                        "gw": fixture.get("event"),
                        "opponent": fixture.get("team_a_short"),
                        "home": True,
                        "difficulty": fixture.get("team_h_difficulty"),
                    }
                )
            elif fixture.get("team_a_short") == team_short:
                team_fixtures.append(
                    {
                        "gw": fixture.get("event"),
                        "opponent": fixture.get("team_h_short"),
                        "home": False,
                        "difficulty": fixture.get("team_a_difficulty"),
                    }
                )

        grid.append(
            {
                "team": team["name"],
                "team_short": team_short,
                "fixtures": sorted(team_fixtures, key=lambda row: row["gw"]),
                **source_meta,
            }
        )

    return grid
