from fpl_intelligence.fetch_fpl import load_players


def test_load_players_adds_display_columns():
    bootstrap_data = {
        "elements": [
            {
                "id": 1,
                "first_name": "Mohamed",
                "second_name": "Salah",
                "team": 1,
                "element_type": 3,
                "now_cost": 140,
            }
        ],
        "teams": [{"id": 1, "name": "Liverpool", "short_name": "LIV"}],
        "element_types": [{"id": 3, "singular_name_short": "MID"}],
    }

    players = load_players(bootstrap_data)

    assert players.loc[0, "display_name"] == "Mohamed Salah"
    assert players.loc[0, "name"] == "Liverpool"
    assert players.loc[0, "singular_name_short"] == "MID"
    assert players.loc[0, "price"] == 14.0
