"""Squad-relative chip timing signals.

The functions in this module deliberately accept plain dictionaries so the
signal logic can be tested without a live FPL season or model artifacts.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

BASELINE_WINDOW = 5
MIN_BASELINE_GAMEWEEKS = 3
BENCH_BOOST_RELATIVE_THRESHOLD = 0.40
WILDCARD_RISK_RELATIVE_THRESHOLD = 0.50
GOOD_FIXTURE_DIFFICULTY = 3.0
RISKY_START_LIKELIHOOD = 0.60
DIFFICULT_FIXTURE = 4.0


def calculate_bench_baseline(
    gameweeks: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Summarise the squad's normal bench output over its recent window."""

    summaries = [_bench_summary(row) for row in gameweeks]
    summaries = [summary for summary in summaries if summary["bench_xp"] is not None]
    summaries = sorted(summaries, key=lambda row: row["gameweek"])[-BASELINE_WINDOW:]
    values = [summary["bench_xp"] for summary in summaries]
    fixture_values = [
        summary["fixture_difficulty"]
        for summary in summaries
        if summary["fixture_difficulty"] is not None
    ]
    average = _average(values)
    good_fixture_values = [
        summary["good_fixture_rate"]
        for summary in summaries
        if summary["good_fixture_rate"] is not None
    ]
    return {
        "ready": len(summaries) >= MIN_BASELINE_GAMEWEEKS,
        "available_gameweeks": len(summaries),
        "window": [summary["gameweek"] for summary in summaries],
        "bench_xp_average": round(average, 2) if average is not None else None,
        "fixture_difficulty_average": (
            round(_average(fixture_values), 2) if fixture_values else None
        ),
        "good_fixture_rate_average": (
            round(_average(good_fixture_values), 3) if good_fixture_values else None
        ),
    }


def calculate_squad_health_baseline(
    gameweeks: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Summarise the squad's normal starting-XI risk count."""

    summaries = [_health_summary(row) for row in gameweeks]
    summaries = [summary for summary in summaries if summary["risk_count"] is not None]
    summaries = sorted(summaries, key=lambda row: row["gameweek"])[-BASELINE_WINDOW:]
    values = [summary["risk_count"] for summary in summaries]
    average = _average(values)
    return {
        "ready": len(summaries) >= MIN_BASELINE_GAMEWEEKS,
        "available_gameweeks": len(summaries),
        "window": [summary["gameweek"] for summary in summaries],
        "risk_count_average": round(average, 2) if average is not None else None,
    }


def generate_chip_alerts(
    gameweeks: Sequence[Mapping[str, Any]],
    target_gameweek: Mapping[str, Any],
) -> dict[str, Any]:
    """Generate personalized Bench Boost and Wildcard timing alerts.

    The minimum of three completed gameweeks avoids treating one unusual
    opening-week squad as a meaningful personal baseline. Bench Boost needs a
    40% uplift over that baseline; Wildcard uses a 50% relative uplift in the
    squad's own recent risk count. Both thresholds are relative to this squad,
    so they do not privilege expensive or cheap squads.
    """

    bench_baseline = calculate_bench_baseline(gameweeks)
    health_baseline = calculate_squad_health_baseline(gameweeks)
    baseline_ready = bench_baseline["ready"] and health_baseline["ready"]
    metadata = {
        "baseline_gameweeks": min(
            bench_baseline["available_gameweeks"],
            health_baseline["available_gameweeks"],
        ),
        "minimum_baseline_gameweeks": MIN_BASELINE_GAMEWEEKS,
        "bench": bench_baseline,
        "squad_health": health_baseline,
    }
    if not baseline_ready:
        return {
            "status": "insufficient_data",
            "message": (
                "Not enough gameweek history yet to establish your squad's normal "
                f"baseline. At least {MIN_BASELINE_GAMEWEEKS} gameweeks are needed."
            ),
            "alerts": [],
            "baseline": metadata,
        }

    target_bench = _bench_summary(target_gameweek)
    target_health = _health_summary(target_gameweek)
    if target_bench["bench_xp"] is None or target_health["risk_count"] is None:
        return {
            "status": "insufficient_data",
            "message": "The current squad projection is incomplete, so chip timing is unavailable.",
            "alerts": [],
            "baseline": metadata,
        }

    alerts: list[dict[str, Any]] = []
    bench_average = bench_baseline["bench_xp_average"]
    bench_relative = _relative_difference(target_bench["bench_xp"], bench_average)
    fixture_support = _fixture_support(target_bench, bench_baseline)
    if bench_relative >= BENCH_BOOST_RELATIVE_THRESHOLD and fixture_support["supported"]:
        fixture_context = fixture_support["message"]
        alerts.append(
            {
                "chip": "Bench Boost",
                "key": "bench_boost",
                "message": (
                    f"Your bench projects {target_bench['bench_xp']:.1f} points this week, "
                    f"{bench_relative * 100:.0f}% above its usual {bench_average:.1f}-point "
                    f"baseline, {fixture_context}"
                ),
                "strength_percent": round(bench_relative * 100, 1),
                "metrics": {
                    "target_bench_xp": round(target_bench["bench_xp"], 2),
                    "baseline_bench_xp": round(bench_average, 2),
                    "relative_change": round(bench_relative, 4),
                    "fixture_support": fixture_support["supported"],
                },
            }
        )

    risk_average = health_baseline["risk_count_average"]
    risk_relative = _relative_difference(target_health["risk_count"], risk_average)
    if (
        target_health["risk_count"] > risk_average
        and risk_relative >= WILDCARD_RISK_RELATIVE_THRESHOLD
    ):
        alerts.append(
            {
                "chip": "Wildcard",
                "key": "wildcard",
                "message": (
                    f"{target_health['risk_count']} of your starting XI carry rotation, "
                    f"minutes, or fixture risk this week versus your recent average of "
                    f"{risk_average:.1f}; that is {risk_relative * 100:.0f}% above normal."
                ),
                "strength_percent": round(risk_relative * 100, 1),
                "metrics": {
                    "target_risk_count": target_health["risk_count"],
                    "baseline_risk_count": round(risk_average, 2),
                    "relative_change": round(risk_relative, 4),
                },
            }
        )

    return {
        "status": "ready",
        "message": (
            "Nothing to flag right now. Your squad does not have a relative chip "
            "signal for this gameweek."
            if not alerts
            else f"{len(alerts)} personalized chip timing signal(s) found."
        ),
        "alerts": alerts,
        "baseline": {
            **metadata,
            "target_gameweek": target_gameweek.get("gameweek"),
            "target": {
                "bench_xp": round(target_bench["bench_xp"], 2),
                "risk_count": target_health["risk_count"],
            },
        },
    }


def _bench_summary(row: Mapping[str, Any]) -> dict[str, Any]:
    players = _players(row, "bench", "bench_players")
    bench_xp = _number_from_keys(row, "bench_xp", "bench_expected_points")
    if bench_xp is None and players:
        points = [
            _number_from_keys(player, "projected_points", "projected_pts", "xp", "xP")
            for player in players
        ]
        points = [point for point in points if point is not None]
        bench_xp = sum(points) if points else None

    difficulties = _difficulties(row, "bench_fixture_difficulty", "bench_average_difficulty")
    if not difficulties:
        difficulties = [difficulty for player in players for difficulty in _difficulties(player)]
    average_difficulty = _average(difficulties)
    good_rate = (
        sum(difficulty <= GOOD_FIXTURE_DIFFICULTY for difficulty in difficulties)
        / len(difficulties)
        if difficulties
        else None
    )
    return {
        "gameweek": _gameweek(row),
        "bench_xp": bench_xp,
        "fixture_difficulty": average_difficulty,
        "good_fixture_rate": good_rate,
    }


def _health_summary(row: Mapping[str, Any]) -> dict[str, Any]:
    players = _players(row, "starting_xi", "starters", "starting")
    if "risk_count" in row:
        risk_count = int(row["risk_count"] or 0)
    elif players:
        risk_count = sum(_is_risky(player) for player in players)
    else:
        risk_count = None
    return {"gameweek": _gameweek(row), "risk_count": risk_count}


def _players(row: Mapping[str, Any], *keys: str) -> list[Mapping[str, Any]]:
    for key in keys:
        value = row.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return [item for item in value if isinstance(item, Mapping)]
    return []


def _difficulties(row: Mapping[str, Any], *keys: str) -> list[float]:
    values: list[Any] = []
    for key in (*keys, "fixture_difficulty", "difficulty"):
        value = row.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            values.extend(value)
        elif value is not None:
            values.append(value)
    fixtures = row.get("fixtures")
    if isinstance(fixtures, Sequence) and not isinstance(fixtures, (str, bytes)):
        values.extend(
            fixture.get("difficulty")
            for fixture in fixtures
            if isinstance(fixture, Mapping) and fixture.get("difficulty") is not None
        )
    return [number for value in values if (number := _number(value)) is not None]


def _is_risky(player: Mapping[str, Any]) -> bool:
    for key in ("rotation_risk", "injury_risk", "difficult_fixture", "risk"):
        if player.get(key) is True:
            return True
    likelihood = _number_from_keys(player, "start_likelihood", "minutes_security")
    if likelihood is not None and likelihood < RISKY_START_LIKELIHOOD:
        return True
    difficulties = _difficulties(player)
    return any(difficulty >= DIFFICULT_FIXTURE for difficulty in difficulties)


def _fixture_support(target: Mapping[str, Any], baseline: Mapping[str, Any]) -> dict[str, Any]:
    target_difficulty = target.get("fixture_difficulty")
    baseline_difficulty = baseline.get("fixture_difficulty_average")
    target_good_rate = target.get("good_fixture_rate")
    baseline_good_rate = baseline.get("good_fixture_rate_average")
    if target_difficulty is None or baseline_difficulty is None:
        return {
            "supported": True,
            "message": "with no fixture downgrade in the available data.",
        }
    supported = target_difficulty <= baseline_difficulty or (
        target_good_rate is not None
        and baseline_good_rate is not None
        and target_good_rate >= baseline_good_rate
    )
    if target_difficulty <= baseline_difficulty:
        message = (
            f"its average fixture difficulty is {target_difficulty:.1f} versus "
            f"your usual {baseline_difficulty:.1f}"
        )
    elif supported:
        message = "its share of good fixtures is at least as strong as usual"
    else:
        message = "its fixture run does not support a Bench Boost"
    return {"supported": supported, "message": f"and {message}."}


def _gameweek(row: Mapping[str, Any]) -> int:
    value = _number(row.get("gameweek"))
    return int(value or 0)


def _number_from_keys(row: Mapping[str, Any], *keys: str) -> float | None:
    for key in keys:
        number = _number(row.get(key))
        if number is not None:
            return number
    return None


def _number(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _average(values: Sequence[float | int]) -> float | None:
    return sum(values) / len(values) if values else None


def _relative_difference(value: float, baseline: float) -> float:
    return max(0.0, (value - baseline) / max(abs(baseline), 1.0))
