import asyncio

import pandas as pd
from api.main import app
from api.routers import fpl_live
from api.routers import players as players_router
from api.routers import predictions as predictions_router
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


def test_players_form_falls_back_to_recent_history_when_snapshot_is_zero(monkeypatch):
    ranked_players = pd.DataFrame(
        [
            {
                "element_id": 1,
                "player_name": "Example Forward",
                "web_name": "Example",
                "team_name": "Arsenal",
                "team_code": 3,
                "position": "Forward",
                "price": 7.5,
                "total_points": 100,
                "points_per_game": 4.0,
                "form": 0.0,
                "minutes": 1000,
                "selected_by_percent": 10.0,
                "value_score": 13.3,
                "minutes_security": 0.8,
                "ownership_risk": 0.9,
                "captain_score": 0.5,
                "transfer_score": 0.4,
            }
        ]
    )
    history = pd.DataFrame(
        [
            {
                "season": "2025-26",
                "player_name": "Example Forward",
                "player_id": 1,
                "gameweek": 35,
                "total_points": 4,
            },
            {
                "season": "2025-26",
                "player_name": "Example Forward",
                "player_id": 1,
                "gameweek": 36,
                "total_points": 8,
            },
            {
                "season": "2025-26",
                "player_name": "Example Forward",
                "player_id": 1,
                "gameweek": 37,
                "total_points": 6,
            },
            {
                "season": "2025-26",
                "player_name": "Example Forward",
                "player_id": 1,
                "gameweek": 38,
                "total_points": 10,
            },
        ]
    )

    monkeypatch.setattr(players_router.data_service, "players", lambda: ranked_players.copy())
    monkeypatch.setattr(players_router.data_service, "historical_player_gw", lambda: history.copy())

    response = asyncio.run(_get("/api/players?sort_by=form&limit=1"))

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["form"] == 8.0


def test_form_fallback_diverges_from_season_ppg_in_both_directions(monkeypatch):
    ranked_players = pd.DataFrame(
        [
            {
                "element_id": 1,
                "player_name": "Out Of Form",
                "web_name": "Out",
                "team_name": "Arsenal",
                "team_code": 3,
                "position": "Forward",
                "price": 8.0,
                "total_points": 120,
                "points_per_game": 8.0,
                "form": 0.0,
                "minutes": 1200,
                "selected_by_percent": 10.0,
                "value_score": 15.0,
                "minutes_security": 0.9,
                "ownership_risk": 0.9,
                "captain_score": 0.8,
                "transfer_score": 0.5,
            },
            {
                "element_id": 2,
                "player_name": "In Form",
                "web_name": "In",
                "team_name": "Chelsea",
                "team_code": 8,
                "position": "Midfielder",
                "price": 6.0,
                "total_points": 45,
                "points_per_game": 3.0,
                "form": 0.0,
                "minutes": 900,
                "selected_by_percent": 10.0,
                "value_score": 7.5,
                "minutes_security": 0.9,
                "ownership_risk": 0.9,
                "captain_score": 0.5,
                "transfer_score": 0.6,
            },
        ]
    )
    history = pd.DataFrame(
        [
            {
                "season": "2025-26",
                "player_id": 1,
                "player_name": "Out Of Form",
                "gameweek": 36,
                "total_points": 2,
            },
            {
                "season": "2025-26",
                "player_id": 1,
                "player_name": "Out Of Form",
                "gameweek": 37,
                "total_points": 3,
            },
            {
                "season": "2025-26",
                "player_id": 1,
                "player_name": "Out Of Form",
                "gameweek": 38,
                "total_points": 1,
            },
            {
                "season": "2025-26",
                "player_id": 2,
                "player_name": "In Form",
                "gameweek": 36,
                "total_points": 7,
            },
            {
                "season": "2025-26",
                "player_id": 2,
                "player_name": "In Form",
                "gameweek": 37,
                "total_points": 8,
            },
            {
                "season": "2025-26",
                "player_id": 2,
                "player_name": "In Form",
                "gameweek": 38,
                "total_points": 6,
            },
        ]
    )

    monkeypatch.setattr(players_router.data_service, "players", lambda: ranked_players.copy())
    monkeypatch.setattr(players_router.data_service, "historical_player_gw", lambda: history.copy())

    response = asyncio.run(_get("/api/players?sort_by=name&limit=2"))

    assert response.status_code == 200
    by_name = {row["name"]: row for row in response.json()}
    assert by_name["Out Of Form"]["form"] == 2.0
    assert by_name["Out Of Form"]["form"] < by_name["Out Of Form"]["ppg"]
    assert by_name["In Form"]["form"] == 7.0
    assert by_name["In Form"]["form"] > by_name["In Form"]["ppg"]


def test_captaincy_predictions_use_ridge_regression_model():
    predictions = predictions_router.data_service.backtest_predictions()
    latest_gw = int(predictions["gameweek"].max())
    ridge_top = (
        predictions[
            (predictions["gameweek"] == latest_gw)
            & (predictions["model"] == predictions_router.CAPTAINCY_MODEL)
        ]
        .sort_values("expected_points_adjusted", ascending=False)
        .iloc[0]
    )

    response = asyncio.run(_get(f"/api/predictions/captaincy?gw={latest_gw}&limit=1"))

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["name"] == ridge_top["player_name"]
    assert predictions_router.CAPTAINCY_MODEL == "Ridge Regression"


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
