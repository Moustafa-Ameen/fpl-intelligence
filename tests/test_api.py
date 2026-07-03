import asyncio

from api.main import app
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
