import asyncio

from api.main import app
from api.routers import fpl_live
from api.routers.fixtures import _ticker_from_named_fixtures
from httpx import ASGITransport, AsyncClient


async def _get(path: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


def test_health_returns_ok():
    response = asyncio.run(_get("/api/health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_players_returns_plain_english_fields():
    response = asyncio.run(_get("/api/players"))

    assert response.status_code == 200
    players = response.json()
    assert isinstance(players, list)
    assert len(players) > 0
    assert "name" in players[0]
    assert "element_id" in players[0]
    assert "player_name" not in players[0]


def test_captains_returns_ten_players():
    response = asyncio.run(_get("/api/players/captains"))

    assert response.status_code == 200
    assert len(response.json()) == 10


def test_transfers_includes_rotation_risk_boolean():
    response = asyncio.run(_get("/api/players/transfers"))

    assert response.status_code == 200
    transfers = response.json()
    assert len(transfers) > 0
    assert isinstance(transfers[0]["rotation_risk"], bool)


def test_fixture_ticker_rows_include_source_metadata():
    rows = _ticker_from_named_fixtures(
        [
            {
                "event": 1,
                "team_h_short": "ARS",
                "team_a_short": "CHE",
                "team_h_difficulty": 4,
                "team_a_difficulty": 5,
            }
        ],
        requested_range=3,
    )

    arsenal = next(row for row in rows if row["team_short"] == "ARS")
    assert arsenal["range"] == 3
    assert arsenal["source"] == "Official PL fixture release"
    assert arsenal["season"] == "2026-27"
    assert arsenal["difficulty_source"] == "App-estimated difficulty"
    assert arsenal["fixtures"][0]["opponent"] == "CHE"


def test_season_state_returns_central_source_metadata(monkeypatch):
    async def fake_bootstrap():
        return {
            "events": [
                {"id": 1, "deadline_time": "2025-08-15T17:30:00Z", "is_current": True},
                {"id": 2, "deadline_time": "2025-08-22T17:30:00Z", "is_next": True},
            ]
        }

    async def fake_fixture_source_state():
        return {
            "source": "Official PL fixture release",
            "season": "2026-27",
            "difficulty_source": "App-estimated difficulty",
            "freshness": "static official release",
        }

    monkeypatch.setattr(fpl_live.fpl_client, "get_bootstrap", fake_bootstrap)
    monkeypatch.setattr(fpl_live, "fixture_source_state", fake_fixture_source_state)

    response = asyncio.run(_get("/api/fpl/season-state"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["fpl_api_season"] == "2025-26"
    assert payload["fixture_source"] == "Official PL fixture release"
    assert payload["fixture_season"] == "2026-27"
    assert payload["difficulty_source"] == "App-estimated difficulty"
    assert payload["current_gw"] == 1
    assert payload["next_gw"] == 2


def test_backtest_accuracy_uses_plain_english_model_names():
    response = asyncio.run(_get("/api/backtest/accuracy"))

    assert response.status_code == 200
    payload = response.json()
    models = {row["model"] for row in payload}
    assert "FPL Intelligence (best)" in models
    assert "Gradient Boosting Regressor" not in models
    assert "Random Forest Regressor" not in models
    assert "Ridge Regression" not in models
    assert "Naive baseline" not in models
