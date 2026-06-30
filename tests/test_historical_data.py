import pandas as pd

from fpl_intelligence.historical_data import build_historical_player_gameweeks


def test_rolling_features_use_only_prior_gameweeks():
    gameweeks = pd.DataFrame(
        [
            {
                "season": "2024-25",
                "element": 1,
                "name": "Test Player",
                "GW": 1,
                "value": 50,
                "position": "MID",
                "team": "Arsenal",
                "opponent_team": 2,
                "was_home": True,
                "selected": 150,
                "minutes": 90,
                "total_points": 5,
            },
            {
                "season": "2024-25",
                "element": 1,
                "name": "Test Player",
                "GW": 1,
                "value": 50,
                "position": "MID",
                "team": "Arsenal",
                "opponent_team": 3,
                "was_home": False,
                "selected": 150,
                "minutes": 10,
                "total_points": 1,
            },
            {
                "season": "2024-25",
                "element": 1,
                "name": "Test Player",
                "GW": 2,
                "value": 51,
                "position": "MID",
                "team": "Arsenal",
                "opponent_team": 2,
                "was_home": False,
                "selected": 150,
                "minutes": 80,
                "total_points": 3,
            },
            {
                "season": "2024-25",
                "element": 1,
                "name": "Test Player",
                "GW": 3,
                "value": 52,
                "position": "MID",
                "team": "Arsenal",
                "opponent_team": 2,
                "was_home": True,
                "selected": 150,
                "minutes": 70,
                "total_points": 10,
            },
        ]
    )
    teams = pd.DataFrame(
        [
            {
                "season": "2024-25",
                "id": 2,
                "name": "Chelsea",
                "strength_overall_home": 1200,
                "strength_overall_away": 1100,
            },
            {
                "season": "2024-25",
                "id": 3,
                "name": "Spurs",
                "strength_overall_home": 1250,
                "strength_overall_away": 1150,
            }
        ]
    )

    historical = build_historical_player_gameweeks(gameweeks, teams)
    gw1 = historical[historical["gameweek"] == 1].iloc[0]
    gw3 = historical[historical["gameweek"] == 3].iloc[0]

    assert len(historical[historical["gameweek"] == 1]) == 1
    assert gw1["minutes_last_3"] == 0
    assert gw1["points_last_3"] == 0
    assert gw1["minutes"] == 100
    assert gw1["total_points"] == 6
    assert gw3["minutes_last_3"] == 180
    assert gw3["points_last_3"] == 9
    assert gw3["next_gameweek_points"] == 10
