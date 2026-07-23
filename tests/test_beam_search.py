import pandas as pd

from fpl_intelligence.beam_search import (
    DeterministicBeamPlanner,
    _aggregate_horizon_predictions,
    _future_opportunity_cost,
    _prune_candidates,
    generate_transfer_options,
)
from fpl_intelligence.chip_simulation import (
    ChipState,
    apply_chip,
    build_chip_squad,
    chip_definitions,
)
from fpl_intelligence.season_rules import build_historical_season_rules


def _squad() -> pd.DataFrame:
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
                    "expected_points_adjusted": 1.0,
                    "probability_60_plus_minutes": 1.0,
                }
            )
            player_id += 1
    return pd.DataFrame(rows)


def test_transfer_branch_generation_is_legal_and_includes_control():
    squad = _squad()
    upgrade = squad.iloc[[5]].copy()
    upgrade["player_id"] = 100
    upgrade["player_name"] = "Upgrade"
    upgrade["team"] = "New Team"
    upgrade["expected_points_adjusted"] = 8.0
    predictions = pd.concat([squad, upgrade], ignore_index=True)

    options = generate_transfer_options(
        squad,
        predictions,
        bank=0.0,
        free_transfers=1,
        max_options=4,
    )

    assert options[0].made is False
    assert any(option.incoming_id == 100 for option in options)
    assert all(option.hit_cost == 0 for option in options if option.made)


def test_beam_search_is_reproducible_for_identical_inputs():
    squad = _squad()
    upgrade = squad.iloc[[5]].copy()
    upgrade["player_id"] = 100
    upgrade["player_name"] = "Upgrade"
    upgrade["team"] = "New Team"
    upgrade["expected_points_adjusted"] = 8.0
    predictions = pd.concat([squad, upgrade], ignore_index=True)
    rules = build_historical_season_rules("2025-26")
    chip_state = ChipState(
        season="2025-26",
        rules_version=rules.rules_version,
        remaining=(),
    )
    planner = DeterministicBeamPlanner(beam_width=4, horizon=2, max_transfers=4)

    first = planner.decide(
        gameweek=2,
        squad=squad,
        bank=0.0,
        free_transfers=1,
        chip_state=chip_state,
        predictions=predictions,
        future_predictions={3: predictions.copy()},
        rules=rules,
    )
    second = planner.decide(
        gameweek=2,
        squad=squad,
        bank=0.0,
        free_transfers=1,
        chip_state=chip_state,
        predictions=predictions,
        future_predictions={3: predictions.copy()},
        rules=rules,
    )

    assert first.transfer == second.transfer
    assert first.chip == second.chip
    assert first.reason == second.reason


def test_wildcard_horizon_aggregation_values_future_fixture_swing():
    current = _squad().copy()
    future_player = current.iloc[[5]].copy()
    future_player["player_id"] = 100
    future_player["player_name"] = "Future Swing"
    current.loc[current["player_id"] == 6, "expected_points_adjusted"] = 1.0
    future_player["expected_points_adjusted"] = 8.0
    current_predictions = pd.concat([current, future_player], ignore_index=True)
    future = future_player.copy()
    future["expected_points_adjusted"] = 12.0

    aggregated = _aggregate_horizon_predictions(
        current_predictions,
        {2: future, 3: future},
        minimum_gameweeks=3,
    )

    future_value = float(
        aggregated.loc[aggregated["player_id"] == 100, "expected_points_adjusted"].iloc[0]
    )
    current_value = float(
        aggregated.loc[aggregated["player_id"] == 6, "expected_points_adjusted"].iloc[0]
    )
    assert future_value == 32.0
    assert current_value == 1.0


def test_candidate_pruning_retains_future_fixture_swing():
    squad = _squad()
    current = squad.copy()
    current["expected_points_adjusted"] = 1.0
    future_player = current.iloc[[5]].copy()
    future_player["player_id"] = 100
    future_player["player_name"] = "Future Swing"
    future_player["expected_points_adjusted"] = 15.0
    predictions = pd.concat([current, future_player], ignore_index=True)

    retained = _prune_candidates(
        predictions,
        squad,
        future_predictions={2: future_player},
        per_position=1,
    )

    assert 100 in set(retained["player_id"])


def test_pruned_wildcard_pool_matches_full_small_pool_oracle():
    squad = _squad()
    predictions = squad.copy()
    future_player = squad.iloc[[5]].copy()
    future_player["player_id"] = 100
    future_player["player_name"] = "Future Swing"
    future_player["expected_points_adjusted"] = 15.0
    predictions = pd.concat([predictions, future_player], ignore_index=True)
    future = {2: future_player}
    full_pool = _aggregate_horizon_predictions(predictions, future, minimum_gameweeks=2)
    pruned_pool = _aggregate_horizon_predictions(
        _prune_candidates(
            predictions,
            squad,
            future_predictions=future,
            per_position=1,
        ),
        future,
        minimum_gameweeks=2,
    )

    full_solution = build_chip_squad(full_pool, budget=75.0)
    pruned_solution = build_chip_squad(pruned_pool, budget=75.0)
    full_score = float(full_solution["expected_points_adjusted"].sum())
    pruned_score = float(pruned_solution["expected_points_adjusted"].sum())

    assert pruned_score == full_score


def test_future_opportunity_cost_is_not_silently_zero():
    rules = build_historical_season_rules("2025-26")
    definitions = {chip.key: chip for chip in chip_definitions(rules)}
    state = ChipState(
        season=rules.season,
        rules_version=rules.rules_version,
        remaining=("bboost:1", "3xc:1"),
    )
    current_chip_state = apply_chip(state, definitions["bboost:1"], 1, rules)
    squad = _squad()
    current = squad.copy()
    current["expected_points_adjusted"] = 1.0
    future = squad.copy()
    future["expected_points_adjusted"] = 1.0
    future.loc[future["player_id"] == 6, "expected_points_adjusted"] = 12.0

    cost = _future_opportunity_cost(
        state,
        chip=definitions["bboost:1"],
        future={2: future},
        retained_squad=squad,
        next_chip_state=current_chip_state,
        rules=rules,
        current_expected_gain=0.0,
    )

    assert cost > 0.0


def test_beam_exposes_one_counterfactual_per_legal_chip():
    squad = _squad()
    predictions = squad.copy()
    rules = build_historical_season_rules("2025-26")
    planner = DeterministicBeamPlanner(beam_width=2, horizon=1, max_transfers=2)
    planner.decide(
        gameweek=2,
        squad=squad,
        bank=25.0,
        free_transfers=1,
        chip_state=ChipState(
            season=rules.season,
            rules_version=rules.rules_version,
            remaining=tuple(chip.key for chip in chip_definitions(rules)),
        ),
        predictions=predictions,
        future_predictions={},
        rules=rules,
    )
    keys = {
        candidate.chip.key if candidate.chip else "none"
        for candidate in planner.last_counterfactuals
    }
    assert "none" in keys
    assert "wildcard:1" in keys
    assert "freehit:1" in keys
    assert "bboost:1" in keys
    assert "3xc:1" in keys
