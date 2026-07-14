from api.chip_tracking import build_chip_status, filter_actionable_chip_alerts


def _bootstrap():
    return {
        "chips": [
            {"id": 1, "name": "wildcard", "start_event": 2, "stop_event": 19},
            {"id": 2, "name": "wildcard", "start_event": 20, "stop_event": 38},
            {"id": 3, "name": "freehit", "start_event": 2, "stop_event": 19},
            {"id": 4, "name": "bboost", "start_event": 1, "stop_event": 19},
        ]
    }


def test_chip_status_assigns_used_available_and_not_yet_available_slots():
    result = build_chip_status(
        _bootstrap(),
        {"chips": [{"name": "freehit", "event": 3}]},
        current_gameweek=5,
    )

    statuses = {row["key"]: row for row in result["chips"]}
    assert statuses["freehit-1"]["status"] == "used"
    assert statuses["freehit-1"]["used_gameweek"] == 3
    assert statuses["bboost-1"]["status"] == "available"
    assert statuses["wildcard-1"]["status"] == "available"
    assert statuses["wildcard-2"]["status"] == "not_yet_available"
    assert statuses["wildcard-2"]["available_from"] == 20


def test_chip_status_resets_history_during_preseason_transition():
    result = build_chip_status(
        _bootstrap(),
        {"chips": [{"name": "bboost", "event": 14}]},
        current_gameweek=38,
        season_state="season_ended_preseason",
    )

    assert result["season_reset"] is True
    assert all(row["status"] != "used" for row in result["chips"])
    assert result["chips"][0]["status"] in {"available", "not_yet_available"}


def test_chip_alerts_skip_used_or_closed_chip_slots():
    status = build_chip_status(
        _bootstrap(),
        {"chips": [{"name": "bboost", "event": 14}]},
        current_gameweek=20,
    )
    alerts = filter_actionable_chip_alerts(
        [
            {"chip": "Bench Boost", "message": "Use it now"},
            {"chip": "Wildcard", "message": "Rebuild now"},
        ],
        status,
    )

    assert [alert["chip"] for alert in alerts] == ["Wildcard"]
