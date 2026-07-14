import asyncio
from typing import Any

from fastapi import APIRouter, Query

from api import data_service, fpl_client
from api.chip_signals import BASELINE_WINDOW, generate_chip_alerts
from api.routers.fixtures import fixture_source_state
from api.routers.fpl_live import (
    _current_gameweek_from_bootstrap,
    _detect_season_state,
    _next_gameweek_from_bootstrap,
    _season_label_from_bootstrap,
)
from api.routers.planner import _current_player_rows, _season_transition_message
from fpl_intelligence.multi_gw_projection import load_planner_models, project_players

router = APIRouter(prefix="/api", tags=["chips"])


@router.get("/chip-tips")
async def chip_tips(team_id: int | None = Query(default=None)) -> dict[str, Any]:
    if team_id is None:
        return {
            "status": "no_team",
            "team_id": None,
            "message": "Connect your FPL team to receive squad-relative chip timing tips.",
            "alerts": [],
        }

    bootstrap = await fpl_client.get_bootstrap()
    fixture_rows = await fpl_client.get_fixtures()
    fixture_state = await fixture_source_state(fixture_rows)
    season = _season_label_from_bootstrap(bootstrap)
    season_state = _detect_season_state(bootstrap, fixture_state)
    response_meta = {
        "team_id": team_id,
        "season_state": season_state,
        "fpl_api_season": season,
        "fixture_season": fixture_state.get("season", "unknown"),
        "difficulty_source": fixture_state.get("difficulty_source", "unknown"),
        "current_gw": _current_gameweek_from_bootstrap(bootstrap),
        "next_gw": _next_gameweek_from_bootstrap(bootstrap),
    }
    if season_state != "in_season":
        return {
            **response_meta,
            "status": "unavailable",
            "message": _season_transition_message(
                season,
                fixture_state.get("next_kickoff"),
            ),
            "alerts": [],
        }

    target_gameweek = (
        _next_gameweek_from_bootstrap(bootstrap)
        or _current_gameweek_from_bootstrap(bootstrap)
        or 1
    )
    completed_gameweeks = sorted(
        {
            int(event["id"])
            for event in bootstrap.get("events", [])
            if event.get("finished") and event.get("id") and int(event["id"]) < target_gameweek
        }
    )[-BASELINE_WINDOW:]
    if len(completed_gameweeks) < 3:
        return {
            **response_meta,
            "status": "insufficient_data",
            "baseline_gameweeks": len(completed_gameweeks),
            "minimum_baseline_gameweeks": 3,
            "message": (
                "Not enough gameweek history yet to establish your squad's normal "
                "baseline. Chip timing will appear after at least 3 completed gameweeks."
            ),
            "alerts": [],
        }

    squad_gameweek = max(1, target_gameweek - 1)
    team_picks, historical_pick_payloads = await asyncio.gather(
        fpl_client.get_team_picks(team_id, squad_gameweek),
        _historical_picks(team_id, completed_gameweeks),
    )

    try:
        models = load_planner_models()
    except FileNotFoundError as exc:
        return {
            **response_meta,
            "status": "unavailable",
            "message": f"Chip tips are unavailable until projection models are ready: {exc}",
            "alerts": [],
        }

    player_rows = _current_player_rows(bootstrap)
    projected_players = project_players(
        player_rows,
        fixture_rows,
        bootstrap.get("teams", []),
        max(1, target_gameweek - (BASELINE_WINDOW - 1)),
        8,
        models=models,
        history=data_service.historical_player_gw(),
    )
    projections_by_id = {
        player.get("element_id"): player
        for player in projected_players
        if player.get("element_id") is not None
    }
    player_by_id = {
        player.get("element_id"): player
        for player in player_rows
        if player.get("element_id") is not None
    }
    difficulty_by_team_gw = _difficulty_by_team_gw(fixture_rows)

    history_rows = []
    for gameweek, picks in historical_pick_payloads:
        if picks is None:
            continue
        history_rows.append(
            _build_gameweek_row(
                gameweek,
                picks.get("picks", []),
                player_by_id,
                projections_by_id,
                difficulty_by_team_gw,
            )
        )
    target_row = _build_gameweek_row(
        target_gameweek,
        team_picks.get("picks", []),
        player_by_id,
        projections_by_id,
        difficulty_by_team_gw,
    )
    signals = generate_chip_alerts(history_rows, target_row)
    return {
        **response_meta,
        **signals,
        "target_gameweek": target_gameweek,
        "baseline_gameweeks": completed_gameweeks,
        "model": "Gradient Boosting Regressor",
    }


async def _historical_picks(
    team_id: int,
    gameweeks: list[int],
) -> list[tuple[int, dict[str, Any] | None]]:
    payloads = await asyncio.gather(
        *(fpl_client.get_team_picks(team_id, gameweek) for gameweek in gameweeks),
        return_exceptions=True,
    )
    return [
        (gameweek, payload if isinstance(payload, dict) else None)
        for gameweek, payload in zip(gameweeks, payloads, strict=True)
    ]


def _build_gameweek_row(
    gameweek: int,
    picks: list[dict[str, Any]],
    player_by_id: dict[int, dict[str, Any]],
    projections_by_id: dict[int, dict[str, Any]],
    difficulty_by_team_gw: dict[tuple[int, int], list[float]],
) -> dict[str, Any]:
    starting_xi = []
    bench = []
    for index, pick in enumerate(picks):
        element_id = pick.get("element")
        player = player_by_id.get(element_id, {})
        projected = projections_by_id.get(element_id, {})
        projection = next(
            (
                row
                for row in projected.get("projections", [])
                if row.get("gameweek") == gameweek
            ),
            {},
        )
        difficulties = difficulty_by_team_gw.get((player.get("team_id"), gameweek), [])
        fixture_rows = projection.get("fixtures", [])
        start_likelihoods = [
            fixture.get("start_likelihood")
            for fixture in fixture_rows
            if fixture.get("start_likelihood") is not None
        ]
        player_row = {
            "projected_points": projection.get("projected_points", 0.0),
            "start_likelihood": (
                sum(start_likelihoods) / len(start_likelihoods)
                if start_likelihoods
                else player.get("start_likelihood")
            ),
            "fixture_difficulty": difficulties,
        }
        pick_order = int(pick.get("position") or index + 1)
        (starting_xi if pick_order <= 11 else bench).append(player_row)

    return {
        "gameweek": gameweek,
        "starting_xi": starting_xi,
        "bench": bench,
    }


def _difficulty_by_team_gw(
    fixtures: list[dict[str, Any]],
) -> dict[tuple[int, int], list[float]]:
    output: dict[tuple[int, int], list[float]] = {}
    for fixture in fixtures:
        gameweek = fixture.get("event")
        if gameweek is None:
            continue
        for team_key, difficulty_key in (
            ("team_h", "team_h_difficulty"),
            ("team_a", "team_a_difficulty"),
        ):
            team_id = fixture.get(team_key)
            difficulty = fixture.get(difficulty_key)
            if team_id is None or difficulty is None:
                continue
            output.setdefault((team_id, int(gameweek)), []).append(float(difficulty))
    return output
