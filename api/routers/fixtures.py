from typing import Any

from fastapi import APIRouter

from api import data_service, fpl_client

router = APIRouter(prefix="/api/fixtures", tags=["fixtures"])


@router.get("")
async def fixtures() -> list[dict[str, Any]]:
    rows = await fpl_client.get_fixtures()
    bootstrap = data_service.bootstrap_static()
    teams_by_id = {team.get("id"): team for team in bootstrap.get("teams", [])}
    upcoming = [fixture for fixture in rows if not fixture.get("finished", False)]
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
        }
        for fixture in upcoming
    ]


@router.get("/ticker")
async def ticker() -> list[dict[str, Any]]:
    bootstrap = await fpl_client.get_bootstrap()
    fixture_rows = await fpl_client.get_fixtures()

    teams = bootstrap.get("teams", [])
    team_by_id = {team["id"]: team for team in teams}
    upcoming = [
        fixture
        for fixture in fixture_rows
        if not fixture.get("finished", False) and fixture.get("event") is not None
    ]
    next_gameweeks = sorted({fixture["event"] for fixture in upcoming})[:5]

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
            }
        )

    return grid
