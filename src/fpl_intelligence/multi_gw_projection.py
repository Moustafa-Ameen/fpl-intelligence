"""Multi-gameweek projections for the guided transfer planner.

The planner holds each player's current rolling minutes/points features and
ownership constant across the horizon. Fixture opponent, venue, and opponent
strength are refreshed for every target gameweek. This is an intentional
near-term planning simplification: projections assume current form and role
continue, while fixture context changes week by week.
"""

from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from fpl_intelligence.fixture_scenarios import FixtureScenario
from fpl_intelligence.step4_models import MINUTES_BAND_MODEL_PATH, MINUTES_MODEL_PATH
from fpl_intelligence.step5_model_comparison import GRADIENT_BOOSTING_MODEL_PATH

ALLOWED_HORIZONS = (3, 5, 8)
MODEL_NAME = "Gradient Boosting Regressor"
RECENT_WINDOW = 3


@lru_cache(maxsize=1)
def load_planner_models():
    """Load the points model and the newest available minutes model artifact."""
    missing = (
        [str(GRADIENT_BOOSTING_MODEL_PATH)]
        if not Path(GRADIENT_BOOSTING_MODEL_PATH).exists()
        else []
    )
    if not Path(MINUTES_BAND_MODEL_PATH).exists() and not Path(MINUTES_MODEL_PATH).exists():
        missing.append(str(MINUTES_BAND_MODEL_PATH))
    if missing:
        raise FileNotFoundError(f"Planner model artifacts are missing: {', '.join(missing)}")

    minutes_path = (
        MINUTES_BAND_MODEL_PATH
        if Path(MINUTES_BAND_MODEL_PATH).exists()
        else MINUTES_MODEL_PATH
    )
    return joblib.load(GRADIENT_BOOSTING_MODEL_PATH), joblib.load(minutes_path)


def project_player(
    player_id_or_name: int | str,
    start_gameweek: int,
    horizon_length: int,
    players: Iterable[dict[str, Any]],
    fixtures: Iterable[dict[str, Any]],
    teams: Iterable[dict[str, Any]],
    models=None,
    history: pd.DataFrame | None = None,
    fixture_scenario: FixtureScenario | None = None,
) -> list[dict[str, Any]]:
    """Return per-gameweek projections for one player.

    ``players`` contains current player records, ``fixtures`` contains FPL
    fixture rows, and ``teams`` contains bootstrap team strength metadata.
    Blank gameweeks return zero; two fixtures in the same gameweek are summed.
    """
    if horizon_length not in ALLOWED_HORIZONS:
        raise ValueError(f"horizon_length must be one of {ALLOWED_HORIZONS}")

    player_rows = list(players)
    player = _find_player(player_id_or_name, player_rows)
    return _project_row(
        player,
        start_gameweek,
        horizon_length,
        list(fixtures),
        list(teams),
        models=models,
        history=history,
        fixture_scenario=fixture_scenario,
    )


def project_players(
    players: Iterable[dict[str, Any]],
    fixtures: Iterable[dict[str, Any]],
    teams: Iterable[dict[str, Any]],
    start_gameweek: int,
    horizon_length: int,
    models=None,
    history: pd.DataFrame | None = None,
    fixture_scenario: FixtureScenario | None = None,
) -> list[dict[str, Any]]:
    """Project all supplied players over a 3, 5, or 8 gameweek horizon."""
    if horizon_length not in ALLOWED_HORIZONS:
        raise ValueError(f"horizon_length must be one of {ALLOWED_HORIZONS}")

    player_rows = list(players)
    fixture_rows = (
        list(fixture_scenario.fixtures)
        if fixture_scenario is not None
        else list(fixtures)
    )
    team_by_id = {team.get("id"): team for team in teams}
    points_model, minutes_model = models or load_planner_models()
    baselines = _recent_baselines(history)
    projections = [{**player, "projections": []} for player in player_rows]

    # Batch each GW's fixture rows so the sklearn preprocessing pipeline runs
    # a few times per GW instead of once for every player-fixture pair.
    for gameweek in range(start_gameweek, start_gameweek + horizon_length):
        pending: list[tuple[int, dict[str, Any], dict[str, Any]]] = []
        fixture_groups: dict[int, list[dict[str, Any]]] = {}
        for index, player in enumerate(player_rows):
            player_fixtures = _fixtures_for_player(player, gameweek, fixture_rows, team_by_id)
            if not player_fixtures:
                projections[index]["projections"].append(
                    _gameweek_metadata(
                        {
                            "gameweek": gameweek,
                            "projected_points": 0.0,
                            "blank": True,
                            "double": False,
                            "fixtures": [],
                        },
                        fixture_scenario,
                    )
                )
                continue

            player_id = player.get("element_id", player.get("id"))
            baseline = (
                baselines.get(player_id)
                or baselines.get(_normalise(player.get("name")))
                or {}
            )
            fixture_groups[index] = []
            for fixture in player_fixtures:
                fixture_groups[index].append(fixture)
                pending.append((index, _feature_row(player, fixture, baseline), fixture))

        if not pending:
            continue

        feature_frame = pd.DataFrame([item[1] for item in pending])
        predicted_points, projected_points, start_likelihoods = _projected_values(
            points_model, minutes_model, feature_frame
        )
        fixture_results: dict[int, list[dict[str, Any]]] = {index: [] for index in fixture_groups}
        for pending_item, predicted, projected, start_likelihood in zip(
            pending, predicted_points, projected_points, start_likelihoods, strict=True
        ):
            index, _, fixture = pending_item
            predicted_value = max(0.0, float(predicted))
            projected_value = max(0.0, float(projected))
            start_value = max(0.0, min(1.0, float(start_likelihood)))
            fixture_results[index].append(
                {
                    "opponent": fixture["opponent"],
                    "opponent_name": fixture["opponent_name"],
                    "home": fixture["home"],
                    "opponent_strength": fixture["opponent_strength"],
                    "predicted_points": round(predicted_value, 2),
                    "start_likelihood": round(start_value, 4),
                    "projected_points": round(projected_value, 2),
                    **_fixture_metadata(fixture),
                }
            )

        for index, fixture_projections in fixture_results.items():
            projections[index]["projections"].append(
                _gameweek_metadata(
                    {
                        "gameweek": gameweek,
                        "projected_points": round(
                            sum(fixture["projected_points"] for fixture in fixture_projections), 2
                        ),
                        "blank": False,
                        "double": len(fixture_projections) > 1,
                        "fixtures": fixture_projections,
                    },
                    fixture_scenario,
                )
            )

    return projections


def _project_row(
    player: dict[str, Any],
    start_gameweek: int,
    horizon_length: int,
    fixtures: list[dict[str, Any]],
    teams: list[dict[str, Any]],
    models=None,
    history: pd.DataFrame | None = None,
    fixture_scenario: FixtureScenario | None = None,
) -> list[dict[str, Any]]:
    points_model, minutes_model = models or load_planner_models()
    projection_fixtures = (
        list(fixture_scenario.fixtures)
        if fixture_scenario is not None
        else fixtures
    )
    team_by_id = {team.get("id"): team for team in teams}
    baselines = _recent_baselines(history)
    player_id = player.get("element_id", player.get("id"))
    baseline = baselines.get(player_id) or baselines.get(_normalise(player.get("name"))) or {}

    output = []
    for gameweek in range(start_gameweek, start_gameweek + horizon_length):
        player_fixtures = _fixtures_for_player(
            player, gameweek, projection_fixtures, team_by_id
        )
        if not player_fixtures:
            output.append(
                _gameweek_metadata(
                    {
                        "gameweek": gameweek,
                        "projected_points": 0.0,
                        "blank": True,
                        "double": False,
                        "fixtures": [],
                    },
                    fixture_scenario,
                )
            )
            continue

        fixture_projections = []
        for fixture in player_fixtures:
            features = _feature_row(player, fixture, baseline)
            feature_frame = pd.DataFrame([features])
            predicted_points, projected_points, start_likelihood = _projected_values(
                points_model, minutes_model, feature_frame
            )
            predicted_points = max(0.0, float(predicted_points[0]))
            projected_points = max(0.0, float(projected_points[0]))
            start_likelihood = float(start_likelihood[0])
            start_likelihood = max(0.0, min(1.0, start_likelihood))
            fixture_projections.append(
                {
                    "opponent": fixture["opponent"],
                    "opponent_name": fixture["opponent_name"],
                    "home": fixture["home"],
                    "opponent_strength": fixture["opponent_strength"],
                    "predicted_points": round(predicted_points, 2),
                    "start_likelihood": round(start_likelihood, 4),
                    "projected_points": round(projected_points, 2),
                    **_fixture_metadata(fixture),
                }
            )

        output.append(
            _gameweek_metadata(
                {
                    "gameweek": gameweek,
                    "projected_points": round(
                        sum(fixture["projected_points"] for fixture in fixture_projections), 2
                    ),
                    "blank": False,
                    "double": len(fixture_projections) > 1,
                    "fixtures": fixture_projections,
                },
                fixture_scenario,
            )
        )

    return output


def _projected_values(points_model: Any, minutes_model: Any, features: pd.DataFrame):
    """Return raw points, adjusted points, and 60+ likelihood.

    The fallback keeps pre-M2 binary artifacts usable.  New M2 artifacts expose
    ``predict_expected_points`` and therefore calculate the full three-band
    conditional expectation.
    """
    predicted_points = points_model.predict(features)
    if hasattr(minutes_model, "predict_expected_points"):
        projected_points = minutes_model.predict_expected_points(features)
        start_likelihoods = np.asarray(minutes_model.predict_proba(features))[:, 2]
    else:
        start_likelihoods = np.asarray(minutes_model.predict_proba(features))[:, 1]
        projected_points = predicted_points * start_likelihoods
    return predicted_points, projected_points, start_likelihoods


def _feature_row(
    player: dict[str, Any], fixture: dict[str, Any], baseline: dict[str, Any]
) -> dict[str, Any]:
    return {
        # Live bootstrap values are fetched before the upcoming deadline, so they
        # already represent the model's pre-deadline market features. Historical
        # rows use the explicitly lagged equivalents built in historical_data.py.
        "price_before_deadline": _number(
            player.get("price_before_deadline", player.get("price"))
        ),
        "minutes_last_3": _number(player.get("minutes_last_3", baseline.get("minutes_last_3", 0))),
        "points_last_3": _number(player.get("points_last_3", baseline.get("points_last_3", 0))),
        "opponent_strength": _number(fixture.get("opponent_strength")),
        "selected_by_percent_before_deadline": _number(
            player.get("selected_by_percent_before_deadline", player.get("selected_by_percent"))
        ),
        "market_snapshot_available": _number(player.get("market_snapshot_available", 1)),
        "position": _position_code(player.get("position")),
        "home_or_away": "H" if fixture.get("home") else "A",
    }


def _fixtures_for_player(
    player: dict[str, Any],
    gameweek: int,
    fixtures: list[dict[str, Any]],
    team_by_id: dict[Any, dict[str, Any]],
) -> list[dict[str, Any]]:
    team_id = player.get("team_id", player.get("team"))
    rows = []
    for fixture in fixtures:
        if fixture.get("event") != gameweek:
            continue

        if fixture.get("team_h") == team_id:
            opponent_id = fixture.get("team_a")
            opponent = team_by_id.get(opponent_id, {})
            rows.append(
                {
                    "fixture_id": fixture.get("fixture_id", fixture.get("id")),
                    "opponent": opponent.get("short_name") or fixture.get("team_a_short", "-"),
                    "opponent_name": opponent.get("name") or fixture.get("team_a_name", "Unknown"),
                    "home": True,
                    "opponent_strength": fixture.get(
                        "opponent_strength", opponent.get("strength_overall_away", 0)
                    ),
                    **_fixture_metadata(fixture),
                }
            )
        elif fixture.get("team_a") == team_id:
            opponent_id = fixture.get("team_h")
            opponent = team_by_id.get(opponent_id, {})
            rows.append(
                {
                    "fixture_id": fixture.get("fixture_id", fixture.get("id")),
                    "opponent": opponent.get("short_name") or fixture.get("team_h_short", "-"),
                    "opponent_name": opponent.get("name") or fixture.get("team_h_name", "Unknown"),
                    "home": False,
                    "opponent_strength": fixture.get(
                        "opponent_strength", opponent.get("strength_overall_home", 0)
                    ),
                    **_fixture_metadata(fixture),
                }
            )

    return rows


def _fixture_metadata(fixture: dict[str, Any]) -> dict[str, Any]:
    keys = ("status", "confirmed", "postponed", "rescheduled")
    return {key: fixture[key] for key in keys if key in fixture}


def _gameweek_metadata(
    row: dict[str, Any], fixture_scenario: FixtureScenario | None
) -> dict[str, Any]:
    if fixture_scenario is None:
        return row
    return {**row, **fixture_scenario.metadata()}


def _recent_baselines(history: pd.DataFrame | None) -> dict[Any, dict[str, float]]:
    if history is None or history.empty:
        return {}

    required = {"season", "gameweek", "total_points", "minutes"}
    if not required.issubset(history.columns):
        return {}

    current = history.copy()
    current["gameweek"] = pd.to_numeric(current["gameweek"], errors="coerce")
    current["total_points"] = pd.to_numeric(current["total_points"], errors="coerce")
    current["minutes"] = pd.to_numeric(current["minutes"], errors="coerce")
    current = current.dropna(subset=["season", "gameweek", "total_points", "minutes"])
    if current.empty:
        return {}

    current = current[current["season"] == current["season"].max()].sort_values("gameweek")
    output: dict[Any, dict[str, float]] = {}
    if "player_id" in current.columns:
        recent = (
            current.dropna(subset=["player_id"])
            .groupby("player_id", sort=False)
            .tail(RECENT_WINDOW)
        )
        for player_id, rows in recent.groupby("player_id"):
            output[player_id] = {
                "minutes_last_3": float(rows["minutes"].sum()),
                "points_last_3": float(rows["total_points"].sum()),
            }

    if "player_name" in current.columns:
        current["player_key"] = current["player_name"].map(_normalise)
        recent = (
            current[current["player_key"] != ""]
            .groupby("player_key", sort=False)
            .tail(RECENT_WINDOW)
        )
        for player_name, rows in recent.groupby("player_key"):
            output[player_name] = {
                "minutes_last_3": float(rows["minutes"].sum()),
                "points_last_3": float(rows["total_points"].sum()),
            }

    return output


def _find_player(player_id_or_name: int | str, players: list[dict[str, Any]]) -> dict[str, Any]:
    if isinstance(player_id_or_name, int):
        match = next(
            (
                player
                for player in players
                if player.get("element_id", player.get("id")) == player_id_or_name
            ),
            None,
        )
    else:
        key = _normalise(player_id_or_name)
        match = next((player for player in players if _normalise(player.get("name")) == key), None)

    if match is None:
        raise KeyError(f"Player not found: {player_id_or_name}")
    return match


def _position_code(position: Any) -> str:
    return {
        "Goalkeeper": "GK",
        "GKP": "GK",
        "Defender": "DEF",
        "Midfielder": "MID",
        "Forward": "FWD",
    }.get(str(position), str(position))


def _normalise(value: Any) -> str:
    return str(value or "").strip().casefold()


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
