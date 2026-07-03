from typing import Any

from fastapi import APIRouter, Query

from api import data_service, fpl_client
from api.routers.predictions import BEST_MODEL

router = APIRouter(prefix="/api/fpl", tags=["fpl-live"])


def _current_gameweek_from_bootstrap(bootstrap: dict[str, Any]) -> int | None:
    events = bootstrap.get("events", [])
    current = next((event for event in events if event.get("is_current")), None)
    if current:
        return current.get("id")

    upcoming = next((event for event in events if event.get("is_next")), None)
    if upcoming:
        return upcoming.get("id")

    finished = [event.get("id") for event in events if event.get("finished") and event.get("id")]
    return max(finished, default=0) + 1 if finished else None


@router.get("/current-gw")
async def current_gameweek() -> dict[str, int | None]:
    bootstrap = await fpl_client.get_bootstrap()
    return {"current_gw": _current_gameweek_from_bootstrap(bootstrap)}


@router.get("/team/{team_id}")
async def team(team_id: int) -> dict[str, Any]:
    entry = await fpl_client.get_team(team_id)
    return {
        "team_name": entry.get("name"),
        "overall_rank": entry.get("summary_overall_rank"),
        "total_points": entry.get("summary_overall_points"),
        "bank_value": _money(entry.get("last_deadline_bank")),
        "current_gw_points": entry.get("summary_event_points"),
        "squad_value": _money(entry.get("last_deadline_value")),
        "free_transfers_available": entry.get("free_transfers"),
    }


@router.get("/team/{team_id}/squad")
async def squad(team_id: int, gw: int = Query(..., ge=1, le=38)) -> list[dict[str, Any]]:
    bootstrap = await fpl_client.get_bootstrap()
    picks = await fpl_client.get_team_picks(team_id, gw)

    players_by_id = {player["id"]: player for player in bootstrap.get("elements", [])}
    teams_by_id = {team["id"]: team for team in bootstrap.get("teams", [])}
    positions_by_id = {
        position["id"]: position for position in bootstrap.get("element_types", [])
    }
    predictions_by_name = _predictions_by_name(gw)

    squad_rows = []
    for pick in picks.get("picks", []):
        player = players_by_id.get(pick.get("element"), {})
        first_name = player.get("first_name", "")
        second_name = player.get("second_name", "")
        player_name = f"{first_name} {second_name}".strip() or player.get("web_name")
        predicted = predictions_by_name.get(player_name, {})
        team_row = teams_by_id.get(player.get("team"), {})
        position_row = positions_by_id.get(player.get("element_type"), {})

        squad_rows.append(
            {
                "name": player_name,
                "web_name": player.get("web_name") or player_name,
                "position": position_row.get("singular_name_short")
                or position_row.get("singular_name"),
                "team": team_row.get("short_name") or team_row.get("name"),
                "team_code": team_row.get("code"),
                "price": _money(player.get("now_cost")),
                "is_captain": pick.get("is_captain", False),
                "is_vice_captain": pick.get("is_vice_captain", False),
                "predicted_pts": predicted.get("predicted_points"),
                "start_likelihood": predicted.get("probability_60_plus_minutes"),
                "form": _float_or_none(player.get("form")),
            }
        )

    return squad_rows


def _predictions_by_name(gw: int) -> dict[str, dict[str, Any]]:
    predictions = data_service.backtest_predictions()
    if predictions.empty:
        return {}

    filtered = predictions[
        (predictions["gameweek"] == gw) & (predictions["model"] == BEST_MODEL)
    ].copy()
    return filtered.set_index("player_name").to_dict(orient="index")


def _money(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value) / 10, 1)


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)
