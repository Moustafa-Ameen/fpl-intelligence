import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api import data_service, fpl_client
from api.routers.fixtures import fixture_source_state
from api.routers.fpl_live import (
    _current_gameweek_from_bootstrap,
    _detect_season_state,
    _next_gameweek_from_bootstrap,
    _season_label_from_bootstrap,
)
from fpl_intelligence.multi_gw_projection import (
    ALLOWED_HORIZONS,
    MODEL_NAME,
    load_planner_models,
    project_players,
)

router = APIRouter(prefix="/api/predictions", tags=["planner"])


@router.get("/planner")
async def planner(
    team_id: int | None = Query(default=None),
    horizon: int = Query(default=3, ge=1, le=8),
) -> dict[str, Any]:
    if team_id is None:
        raise HTTPException(
            status_code=400,
            detail="Connect your FPL team ID before using the multi-gameweek planner.",
        )
    if horizon not in ALLOWED_HORIZONS:
        raise HTTPException(status_code=400, detail="horizon must be one of 3, 5, or 8")

    bootstrap = await fpl_client.get_bootstrap()
    fixture_rows = await fpl_client.get_fixtures()
    fixture_state = await fixture_source_state(fixture_rows)
    season_state = _detect_season_state(bootstrap, fixture_state)
    if season_state != "in_season":
        return {
            "team_id": team_id,
            "season_state": season_state,
            "fpl_api_season": _season_label_from_bootstrap(bootstrap),
            "fixture_season": fixture_state.get("season", "unknown"),
            "next_season_start": fixture_state.get("next_kickoff"),
            "message": _season_transition_message(
                _season_label_from_bootstrap(bootstrap),
                fixture_state.get("next_kickoff"),
            ),
        }

    current_gameweek = _current_gameweek_from_bootstrap(bootstrap) or 1
    start_gameweek = _next_gameweek_from_bootstrap(bootstrap) or min(current_gameweek + 1, 38)
    squad_gameweek = max(1, start_gameweek - 1)
    team_entry, picks_payload = await asyncio.gather(
        fpl_client.get_team(team_id),
        fpl_client.get_team_picks(team_id, squad_gameweek),
    )
    history = data_service.historical_player_gw()

    try:
        models = load_planner_models()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    player_rows = _current_player_rows(bootstrap)
    if not player_rows:
        raise HTTPException(
            status_code=503,
            detail="FPL player data is unavailable for the planner.",
        )

    projected_players = project_players(
        player_rows,
        fixture_rows,
        bootstrap.get("teams", []),
        start_gameweek,
        horizon,
        models=models,
        history=history,
    )
    projections_by_id = {player["element_id"]: player for player in projected_players}
    squad = _squad_rows(picks_payload.get("picks", []), projections_by_id)
    if not squad:
        raise HTTPException(status_code=404, detail="No squad picks were available for this team.")

    gameweeks = list(range(start_gameweek, start_gameweek + horizon))
    baseline = []
    for gameweek in gameweeks:
        rows = [
            _projection_for_gameweek(player, gameweek)
            for player in squad
            if player["is_starter"]
        ]
        baseline.append(
            {
                "gameweek": gameweek,
                "projected_points": round(sum(row["projected_points"] for row in rows), 2),
                "blank_count": sum(1 for row in rows if row["blank"]),
                "double_count": sum(1 for row in rows if row["double"]),
            }
        )

    settings = bootstrap.get("game_settings", {})
    player_pool = [
        _pool_row(player, projections_by_id[player["element_id"]])
        for player in player_rows
        if player["element_id"] in projections_by_id
    ]

    return {
        "team_id": team_id,
        "season_state": season_state,
        "fpl_api_season": _season_label_from_bootstrap(bootstrap),
        "fixture_season": fixture_state.get("season", "unknown"),
        "start_gameweek": start_gameweek,
        "horizon": horizon,
        "squad_gameweek": squad_gameweek,
        "model": MODEL_NAME,
        "assumption": (
            "Projections assume current form and role continue; "
            "fixture context changes by gameweek."
        ),
        "bank_value": _money(team_entry.get("last_deadline_bank")),
        "free_transfers_available": int(team_entry.get("free_transfers") or 0),
        "max_extra_free_transfers": int(settings.get("max_extra_free_transfers") or 4),
        "baseline": baseline,
        "squad": squad,
        "player_pool": player_pool,
    }


def _season_transition_message(season: str, next_season_start: str | None) -> str:
    if next_season_start:
        start_date = next_season_start[:10]
        return (
            f"The {season} season has ended. Gameweek projections for the next season "
            f"will be available once the new season begins and enough gameweeks have "
            f"been played to establish rolling form data. Season starts {start_date}."
        )
    return (
        f"The {season} season has ended. Gameweek projections for the next season will be "
        "available once official fixtures and enough rolling form data exist."
    )


def _current_player_rows(bootstrap: dict[str, Any]) -> list[dict[str, Any]]:
    ranked = data_service.players()
    ranked_by_name = {
        _normalise(row.get("player_name")): row
        for row in ranked.to_dict(orient="records")
        if row.get("player_name")
    }
    teams_by_id = {team.get("id"): team for team in bootstrap.get("teams", [])}
    positions_by_id = {
        position.get("id"): position for position in bootstrap.get("element_types", [])
    }
    rows = []
    for player in bootstrap.get("elements", []):
        team = teams_by_id.get(player.get("team"), {})
        position = positions_by_id.get(player.get("element_type"), {})
        name = f"{player.get('first_name', '')} {player.get('second_name', '')}".strip()
        name = name or player.get("web_name") or "Unknown player"
        rank = ranked_by_name.get(_normalise(name), {})
        rows.append(
            {
                "element_id": player.get("id"),
                "name": name,
                "web_name": player.get("web_name") or name,
                "team_id": player.get("team"),
                "team": team.get("short_name") or team.get("name"),
                "team_code": team.get("code"),
                "position": position.get("singular_name_short") or position.get("singular_name"),
                "price": _money(player.get("now_cost")),
                "selected_by_percent": _number(
                    player.get("selected_by_percent", rank.get("selected_by_percent"))
                ),
                "start_likelihood": _number(rank.get("minutes_security")),
            }
        )
    return rows


def _squad_rows(
    picks: list[dict[str, Any]], projections_by_id: dict[int, dict[str, Any]]
) -> list[dict[str, Any]]:
    rows = []
    for index, pick in enumerate(picks):
        player = projections_by_id.get(pick.get("element"))
        if player is None:
            continue
        pick_order = int(pick.get("position") or index + 1)
        rows.append(
            {
                **_pool_row(player, player),
                "pick_order": pick_order,
                "is_starter": pick_order <= 11,
                "is_captain": bool(pick.get("is_captain")),
                "is_vice_captain": bool(pick.get("is_vice_captain")),
            }
        )
    return sorted(rows, key=lambda row: row["pick_order"])


def _pool_row(player: dict[str, Any], projected: dict[str, Any]) -> dict[str, Any]:
    return {
        "element_id": player.get("element_id"),
        "name": player.get("name"),
        "web_name": player.get("web_name"),
        "team": player.get("team"),
        "team_code": player.get("team_code"),
        "position": player.get("position"),
        "price": player.get("price"),
        "start_likelihood": player.get("start_likelihood"),
        "projections": projected.get("projections", []),
    }


def _projection_for_gameweek(player: dict[str, Any], gameweek: int) -> dict[str, Any]:
    return next(
        (projection for projection in player["projections"] if projection["gameweek"] == gameweek),
        {"projected_points": 0.0, "blank": True, "double": False},
    )


def _money(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value) / 10, 1)


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _normalise(value: Any) -> str:
    return str(value or "").strip().casefold()
