from api.chip_signals import generate_chip_alerts


def _gameweek(gameweek: int, bench_xp: float, *, difficulty: float = 3.0, risk_count: int = 0):
    return {
        "gameweek": gameweek,
        "bench": [
            {"projected_points": bench_xp / 4, "fixture_difficulty": difficulty}
            for _ in range(4)
        ],
        "starting_xi": [{"risk": index < risk_count} for index in range(11)],
    }


def test_elevated_bench_relative_to_own_baseline_triggers_bench_boost():
    history = [_gameweek(gameweek, 5.0, difficulty=3.0) for gameweek in range(1, 4)]
    target = _gameweek(4, 8.0, difficulty=2.0)

    result = generate_chip_alerts(history, target)

    assert result["status"] == "ready"
    assert [alert["chip"] for alert in result["alerts"]] == ["Bench Boost"]
    assert "8.0 points" in result["alerts"][0]["message"]
    assert "60% above" in result["alerts"][0]["message"]


def test_normal_squad_relative_to_own_baseline_has_no_alerts():
    history = [_gameweek(gameweek, 8.0, difficulty=2.0) for gameweek in range(1, 4)]
    target = _gameweek(4, 8.0, difficulty=2.0)

    result = generate_chip_alerts(history, target)

    assert result["status"] == "ready"
    assert result["alerts"] == []
    assert "Nothing to flag" in result["message"]


def test_chip_alerts_wait_for_minimum_rolling_history():
    history = [_gameweek(gameweek, 5.0) for gameweek in range(1, 3)]
    target = _gameweek(3, 10.0)

    result = generate_chip_alerts(history, target)

    assert result["status"] == "insufficient_data"
    assert result["alerts"] == []
    assert result["baseline"]["minimum_baseline_gameweeks"] == 3


def test_wildcard_signal_uses_squad_relative_risk_baseline():
    history = [_gameweek(gameweek, 5.0, risk_count=2) for gameweek in range(1, 4)]
    target = _gameweek(4, 5.0, risk_count=4)

    result = generate_chip_alerts(history, target)

    assert [alert["chip"] for alert in result["alerts"]] == ["Wildcard"]
    assert "4 of your starting XI" in result["alerts"][0]["message"]
