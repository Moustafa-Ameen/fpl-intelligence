import pandas as pd
from api.player_signals import add_safety_tiers


def test_safety_tiers_are_position_aware_and_leave_neutral_players_untagged():
    players = pd.DataFrame(
        [
            {
                "player_name": "Safe Defender",
                "position": "Defender",
                "minutes_security": 0.90,
                "defensive_contribution_per_90": 8.0,
                "captain_score": 0.30,
                "transfer_score": 0.30,
                "selected_by_percent": 8.0,
                "price": 5.0,
            },
            {
                "player_name": "Peer Defender",
                "position": "Defender",
                "minutes_security": 0.80,
                "defensive_contribution_per_90": 4.0,
                "captain_score": 0.30,
                "transfer_score": 0.30,
                "selected_by_percent": 8.0,
                "price": 5.0,
            },
            {
                "player_name": "Lower Defender",
                "position": "Defender",
                "minutes_security": 0.80,
                "defensive_contribution_per_90": 3.0,
                "captain_score": 0.30,
                "transfer_score": 0.30,
                "selected_by_percent": 8.0,
                "price": 5.0,
            },
            {
                "player_name": "Lowest Defender",
                "position": "Defender",
                "minutes_security": 0.80,
                "defensive_contribution_per_90": 2.0,
                "captain_score": 0.30,
                "transfer_score": 0.30,
                "selected_by_percent": 8.0,
                "price": 5.0,
            },
            {
                "player_name": "Explosive Risk",
                "position": "Forward",
                "minutes_security": 0.45,
                "defensive_contribution_per_90": 1.0,
                "captain_score": 0.70,
                "transfer_score": 0.60,
                "selected_by_percent": 8.0,
                "price": 7.0,
            },
            {
                "player_name": "Neutral Midfielder",
                "position": "Midfielder",
                "minutes_security": 0.70,
                "defensive_contribution_per_90": 2.0,
                "captain_score": 0.25,
                "transfer_score": 0.25,
                "selected_by_percent": 8.0,
                "price": 6.0,
            },
        ]
    )

    tagged = add_safety_tiers(players).set_index("player_name")

    assert tagged.loc["Safe Defender", "safety_tier"] == "Safe"
    assert tagged.loc["Explosive Risk", "safety_tier"] == "Risky"
    assert tagged.loc["Neutral Midfielder", "safety_tier"] == ""
