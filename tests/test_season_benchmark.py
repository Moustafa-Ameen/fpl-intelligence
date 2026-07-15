from pathlib import Path

import pandas as pd
import pytest

from fpl_intelligence.backtest_transfer_strategy import TransferDecision
from fpl_intelligence.season_benchmark import (
    DeterministicTransferStrategy,
    StrategyContext,
    _assert_transfer_budget,
    append_result_to_history,
    load_historical_player_gameweeks,
    run_season_benchmark,
)


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


def test_strategy_interface_applies_hit_cost_and_budget_rule():
    squad = pd.DataFrame(_squad_rows())
    incoming = {
        "player_id": 100,
        "player_name": "Upgrade",
        "position": "MID",
        "team": "New Team",
        "price": 5.0,
        "expected_points_adjusted": 7.0,
    }
    predictions = pd.concat(
        [squad.assign(expected_points_adjusted=1.0), pd.DataFrame([incoming])],
        ignore_index=True,
    )
    context = StrategyContext(
        season="2024-25",
        gameweek=2,
        squad=squad,
        predictions=predictions,
        bank=0.0,
        free_transfers=0,
        available_data=pd.DataFrame(),
    )

    decision = DeterministicTransferStrategy(gain_threshold=0.0).decide(context)

    assert decision.made
    assert decision.hit_cost == 4
    assert decision.incoming_price <= decision.outgoing_price + context.bank


def test_no_transfer_strategy_runs_a_complete_historical_season(tmp_path: Path):
    from fpl_intelligence.season_benchmark import NoTransfersStrategy

    players = load_historical_player_gameweeks()
    result = run_season_benchmark(
        players,
        "2023-24",
        NoTransfersStrategy(),
        model_version="test",
    )

    assert len(result.rows) == 38
    assert result.transfers_made == 0
    assert result.total_hit_cost == 0
    assert result.total_points > 0
    assert result.rows["max_training_current_season_gameweek"].dropna().max() == 37

    history_path = tmp_path / "season_benchmark_history.csv"
    assert append_result_to_history(result, history_path) is None
    previous = append_result_to_history(result, history_path)
    assert previous is not None
    assert len(pd.read_csv(history_path)) == 2


def test_invalid_transfer_decision_is_represented_explicitly():
    decision = TransferDecision(
        outgoing_id=1,
        incoming_id=2,
        outgoing_name="Out",
        incoming_name="In",
        projected_gain=5.0,
        net_projected_gain=1.0,
        hit_cost=4,
        outgoing_price=4.0,
        incoming_price=6.0,
    )

    with pytest.raises(AssertionError, match="exceeds"):
        _assert_transfer_budget(pd.DataFrame(_squad_rows()), decision, bank=0.0)
