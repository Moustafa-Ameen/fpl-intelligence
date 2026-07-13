import pandas as pd

from fpl_intelligence.backtest_transfer_strategy import choose_transfer, validate_squad


def _squad_rows() -> list[dict[str, object]]:
    rows = []
    player_id = 1
    for position, count in [("GK", 2), ("DEF", 5), ("MID", 5), ("FWD", 3)]:
        for index in range(count):
            rows.append(
                {
                    "player_id": player_id,
                    "player_name": f"Player {player_id}",
                    "position": position,
                    "team": f"{position} Team {index + 1}",
                    "price": 5.0,
                }
            )
            player_id += 1
    return rows


def test_validate_squad_accepts_fpl_roster_shape_and_budget():
    squad = pd.DataFrame(_squad_rows())

    assert validate_squad(squad) == []


def test_validate_squad_reports_position_and_budget_violations():
    squad = pd.DataFrame(_squad_rows())
    squad.loc[0, "position"] = "DEF"
    squad.loc[1, "price"] = 100.0

    violations = validate_squad(squad)

    assert any("GK" in violation for violation in violations)
    assert any("above" in violation for violation in violations)


def test_choose_transfer_uses_adjusted_projection_and_budget():
    squad = pd.DataFrame(_squad_rows())
    incoming = {
        "player_id": 100,
        "player_name": "Upgrade",
        "position": "MID",
        "team": "New Team",
        "price": 5.5,
        "expected_points_adjusted": 6.0,
    }
    predictions = pd.concat(
        [
            squad.assign(expected_points_adjusted=1.0),
            pd.DataFrame([incoming]),
        ],
        ignore_index=True,
    )

    decision = choose_transfer(
        squad,
        predictions,
        bank=0.5,
        free_transfers=1,
        gain_threshold=2.0,
    )

    assert decision.made
    assert decision.incoming_id == 100
    assert decision.projected_gain == 5.0
    assert decision.hit_cost == 0


def test_choose_transfer_rejects_over_budget_move():
    squad = pd.DataFrame(_squad_rows())
    incoming = {
        "player_id": 100,
        "player_name": "Too Expensive",
        "position": "MID",
        "team": "New Team",
        "price": 6.0,
        "expected_points_adjusted": 8.0,
    }
    predictions = pd.concat(
        [
            squad.assign(expected_points_adjusted=1.0),
            pd.DataFrame([incoming]),
        ],
        ignore_index=True,
    )

    decision = choose_transfer(
        squad,
        predictions,
        bank=0.0,
        free_transfers=1,
        gain_threshold=2.0,
    )

    assert not decision.made
