from typing import Any

import httpx
from fastapi import HTTPException

BASE_URL = "https://fantasy.premierleague.com/api/"
TIMEOUT_SECONDS = 10.0
UNAVAILABLE_MESSAGE = "FPL data is temporarily unavailable. Try again shortly."


async def _get(path: str) -> Any:
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(path)
            response.raise_for_status()
    except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as exc:
        raise HTTPException(status_code=503, detail=UNAVAILABLE_MESSAGE) from exc

    return response.json()


async def get_bootstrap() -> dict[str, Any]:
    return await _get("bootstrap-static/")


async def get_fixtures() -> list[dict[str, Any]]:
    return await _get("fixtures/")


async def get_team(team_id: int) -> dict[str, Any]:
    return await _get(f"entry/{team_id}/")


async def get_team_picks(team_id: int, gw: int) -> dict[str, Any]:
    return await _get(f"entry/{team_id}/event/{gw}/picks/")


async def get_live_gw(gw: int) -> dict[str, Any]:
    return await _get(f"event/{gw}/live/")
