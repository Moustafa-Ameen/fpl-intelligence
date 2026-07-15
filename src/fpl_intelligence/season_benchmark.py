"""Permanent, realistic season benchmark for comparing FPL strategies.

This harness answers a directional research question: does a transfer strategy
score better than its previous version when evaluated under the same historical
season and FPL constraints? It is not a claim that the result is exactly what a
real manager would have scored.

The simulation uses starting-XI-only scoring, legal formations, basic autosubs,
one captain doubled each gameweek, free-transfer banking, hit costs, budget and
club limits. Captaincy is intentionally hindsight-optimal so captaincy quality
is held constant while transfer or prediction changes are evaluated. Chips,
injury/news reactions, price-change timing, and a fully realistic human squad
selection process are not simulated.

The strategy interface is deliberately small: a strategy receives the current
squad and only the data available before the target gameweek, then returns a
single legal transfer decision. New strategies can therefore use this harness
without changing scoring, transfer accounting, or result persistence.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

import pandas as pd
from sklearn.pipeline import Pipeline

from fpl_intelligence.backtest_transfer_strategy import (
    DEFAULT_GAIN_THRESHOLD,
    FREE_TRANSFER_CAP,
    INITIAL_BUDGET,
    MODEL_BUILDERS,
    TransferDecision,
    build_initial_squad,
    build_preseason_scores,
    choose_transfer,
    score_gameweek,
    validate_squad,
)
from fpl_intelligence.step4_models import (
    FEATURE_COLUMNS,
    build_minutes_classifier,
    load_historical_player_gameweeks,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_PLAYER_GW_PATH = PROJECT_ROOT / "data" / "processed" / "historical_player_gw.csv"
BOOTSTRAP_PATH = PROJECT_ROOT / "data" / "raw" / "bootstrap-static.json"
HISTORY_PATH = PROJECT_ROOT / "data" / "processed" / "season_benchmark_history.csv"
DEFAULT_BENCHMARK_SEASONS = ("2023-24", "2024-25")
DEFAULT_MODEL = "Ridge Regression"
DEFAULT_MODEL_VERSION = "local benchmark"
HISTORY_COLUMNS = [
    "run_timestamp",
    "season",
    "strategy_name",
    "strategy_version",
    "model_name",
    "model_version",
    "total_points",
    "gross_points",
    "transfers_made",
    "total_hit_cost",
    "max_free_transfers",
    "initial_bank",
    "final_bank",
]


@dataclass(frozen=True)
class StrategyContext:
    season: str
    gameweek: int
    squad: pd.DataFrame
    predictions: pd.DataFrame
    bank: float
    free_transfers: int
    available_data: pd.DataFrame


class BenchmarkStrategy(Protocol):
    name: str
    version: str

    def decide(self, context: StrategyContext) -> TransferDecision:
        """Return a transfer decision using only ``context.available_data``."""


@dataclass(frozen=True)
class NoTransfersStrategy:
    name: str = "no-transfers"
    version: str = "v1"

    def decide(self, context: StrategyContext) -> TransferDecision:
        del context
        return _empty_decision()


@dataclass(frozen=True)
class DeterministicTransferStrategy:
    gain_threshold: float = DEFAULT_GAIN_THRESHOLD
    name: str = "deterministic-single-transfer"
    version: str = "v1"

    def decide(self, context: StrategyContext) -> TransferDecision:
        return choose_transfer(
            context.squad,
            context.predictions,
            bank=context.bank,
            free_transfers=context.free_transfers,
            gain_threshold=self.gain_threshold,
        )


@dataclass(frozen=True)
class SeasonBenchmarkResult:
    season: str
    strategy_name: str
    strategy_version: str
    model_name: str
    model_version: str
    rows: pd.DataFrame
    initial_squad: pd.DataFrame
    final_squad: pd.DataFrame
    total_points: float
    gross_points: float
    transfers_made: int
    total_hit_cost: int
    max_free_transfers: int
    initial_bank: float
    final_bank: float


def get_training_data_for_season(
    players: pd.DataFrame,
    season: str,
    gameweek: int,
    training_seasons: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Return rows available before a target gameweek and assert no leakage."""

    available_seasons = sorted(str(value) for value in players["season"].unique())
    allowed_seasons = list(
        training_seasons or [value for value in available_seasons if value < season]
    )
    training = players[
        players["season"].isin(allowed_seasons)
        | ((players["season"] == season) & (players["gameweek"] < gameweek))
    ].copy()

    current_training = training[training["season"] == season]
    if not current_training.empty:
        max_current_gameweek = int(current_training["gameweek"].max())
        assert max_current_gameweek < gameweek, (
            f"Lookahead detected: target {season} GW{gameweek} has current-season "
            f"training data through GW{max_current_gameweek}."
        )
    assert not (
        (training["season"] == season) & (training["gameweek"] >= gameweek)
    ).any(), "Training data contains target or future rows."
    return training


def train_gameweek_predictions(
    players: pd.DataFrame,
    season: str,
    gameweek: int,
    model_name: str = DEFAULT_MODEL,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Train and predict one target gameweek using an expanding time window."""

    if model_name not in MODEL_BUILDERS:
        raise ValueError(f"Unknown model {model_name!r}; choose from {', '.join(MODEL_BUILDERS)}")
    training = get_training_data_for_season(players, season, gameweek)
    target = players[(players["season"] == season) & (players["gameweek"] == gameweek)].copy()
    if target.empty:
        raise ValueError(f"No target rows for {season} GW{gameweek}")

    if training.empty:
        # The earliest available season has no prior season file. GW1 therefore
        # uses the same preseason heuristic as the initial squad, without future
        # match results or current-season minutes.
        preseason = build_preseason_scores(players, season=season, prior_season=None)
        projection = preseason.set_index("player_id")["preseason_value_score"]
        target["predicted_points"] = target["player_id"].map(projection).fillna(0.0)
        target["probability_60_plus_minutes"] = 0.5
        target["expected_points_adjusted"] = target["predicted_points"]
        target["training_row_count"] = 0
        target["max_training_current_season_gameweek"] = None
        target["model"] = "Preseason heuristic"
        return target, training

    minutes_model = build_minutes_classifier()
    minutes_model.fit(training[FEATURE_COLUMNS], (training["minutes"] >= 60).astype(int))
    points_model: Pipeline = MODEL_BUILDERS[model_name]()
    points_model.fit(training[FEATURE_COLUMNS], training["next_gameweek_points"])

    target["predicted_points"] = points_model.predict(target[FEATURE_COLUMNS])
    target["probability_60_plus_minutes"] = minutes_model.predict_proba(
        target[FEATURE_COLUMNS]
    )[:, 1]
    target["expected_points_adjusted"] = (
        target["predicted_points"] * target["probability_60_plus_minutes"]
    ).clip(lower=0.0)
    target["training_row_count"] = len(training)
    current_training = training[training["season"] == season]
    target["max_training_current_season_gameweek"] = (
        None if current_training.empty else int(current_training["gameweek"].max())
    )
    target["model"] = model_name
    return target, training


def run_season_benchmark(
    players: pd.DataFrame,
    season: str,
    strategy: BenchmarkStrategy,
    *,
    model_name: str = DEFAULT_MODEL,
    model_version: str = DEFAULT_MODEL_VERSION,
    max_free_transfers: int | None = None,
    verbose: bool = False,
    prediction_cache: dict[tuple[str, int, str], tuple[pd.DataFrame, pd.DataFrame]] | None = None,
) -> SeasonBenchmarkResult:
    """Run one strategy through every available gameweek in one season."""

    season_players = players[players["season"] == season].copy()
    gameweeks = sorted(int(value) for value in season_players["gameweek"].unique())
    if not gameweeks or gameweeks[0] != 1:
        raise ValueError(f"Expected {season} data starting at GW1")

    prior_season = _previous_season(players, season)
    initial_squad = build_initial_squad(
        players,
        season=season,
        prior_season=prior_season,
        minutes_floor=900 if prior_season else None,
    )
    squad = initial_squad.copy()
    initial_bank = round(INITIAL_BUDGET - float(squad["price"].sum()), 1)
    bank = initial_bank
    free_transfers = 1
    transfer_cap = max_free_transfers or load_max_free_transfers()
    rows: list[dict[str, Any]] = []
    gross_points = 0.0
    total_points = 0.0
    transfers_made = 0
    total_hit_cost = 0

    if verbose:
        print(f"Season benchmark: {season} | {strategy.name} {strategy.version}")
        print(f"- Model: {model_name} ({model_version})")
        print(f"- Free-transfer cap: {transfer_cap}; initial bank: GBP {initial_bank:.1f}m")

    for gameweek in gameweeks:
        cache_key = (season, gameweek, model_name)
        if prediction_cache is not None and cache_key in prediction_cache:
            target, available_data = prediction_cache[cache_key]
        else:
            target, available_data = train_gameweek_predictions(
                players,
                season,
                gameweek,
                model_name=model_name,
            )
            if prediction_cache is not None:
                prediction_cache[cache_key] = (target, available_data)
        prices = _latest_prices(players, season, gameweek)
        squad["price"] = squad["player_id"].map(prices).fillna(squad["price"])
        predictions = target.copy()
        bank_before = bank
        free_transfers_before = free_transfers
        decision = _empty_decision()
        if gameweek >= 2:
            context = StrategyContext(
                season=season,
                gameweek=gameweek,
                squad=squad.copy(),
                predictions=predictions.copy(),
                bank=bank,
                free_transfers=free_transfers,
                available_data=available_data.copy(),
            )
            decision = strategy.decide(context)
            if decision.made:
                _assert_transfer_budget(squad, decision, bank)
                squad = _apply_benchmark_transfer(squad, predictions, decision)
                bank = round(
                    bank + float(decision.outgoing_price) - float(decision.incoming_price),
                    1,
                )
                free_transfers = max(0, free_transfers - 1)
                transfers_made += 1
                total_hit_cost += decision.hit_cost

        projections = predictions.set_index("player_id")["expected_points_adjusted"].to_dict()
        score = score_gameweek(squad, target, projections)
        gross_points += score.points
        total_points += score.points - decision.hit_cost
        rows.append(
            {
                "season": season,
                "gameweek": gameweek,
                "strategy_name": strategy.name,
                "model": target["model"].iloc[0],
                "gross_points": score.points,
                "raw_starter_points": score.raw_starter_points,
                "hit_cost": decision.hit_cost,
                "net_points": score.points - decision.hit_cost,
                "cumulative_points": total_points,
                "captain_id": score.captain_id,
                "starting_ids": "+".join(str(value) for value in score.starting_ids),
                "autosub_ids": "+".join(str(value) for value in score.autosub_ids),
                "formation": score.formation,
                "transfers_made": int(decision.made),
                "outgoing": decision.outgoing_name,
                "incoming": decision.incoming_name,
                "projected_gain": round(decision.projected_gain, 3),
                "net_projected_gain": round(decision.net_projected_gain, 3),
                "bank_before": round(bank_before, 1),
                "free_transfers_before": free_transfers_before,
                "training_row_count": int(target["training_row_count"].iloc[0]),
                "max_training_current_season_gameweek": target[
                    "max_training_current_season_gameweek"
                ].iloc[0],
            }
        )
        free_transfers = min(transfer_cap, free_transfers + 1)
        if verbose:
            print(
                f"- GW{gameweek:02d}: {score.points:.1f} gross, captain {score.captain_id}, "
                f"hit -{decision.hit_cost}, bank GBP {bank:.1f}m"
            )

    result = SeasonBenchmarkResult(
        season=season,
        strategy_name=strategy.name,
        strategy_version=strategy.version,
        model_name=model_name,
        model_version=model_version,
        rows=pd.DataFrame(rows),
        initial_squad=initial_squad,
        final_squad=squad,
        total_points=round(total_points, 2),
        gross_points=round(gross_points, 2),
        transfers_made=transfers_made,
        total_hit_cost=total_hit_cost,
        max_free_transfers=transfer_cap,
        initial_bank=initial_bank,
        final_bank=round(bank, 1),
    )
    _assert_no_lookahead(result.rows, season)
    return result


def run_benchmark_suite(
    players: pd.DataFrame,
    seasons: Iterable[str] = DEFAULT_BENCHMARK_SEASONS,
    *,
    strategies: Sequence[BenchmarkStrategy] | None = None,
    model_name: str = DEFAULT_MODEL,
    model_version: str = DEFAULT_MODEL_VERSION,
    max_free_transfers: int | None = None,
    verbose: bool = False,
) -> list[SeasonBenchmarkResult]:
    selected_strategies = list(
        strategies
        or (NoTransfersStrategy(), DeterministicTransferStrategy())
    )
    prediction_cache: dict[tuple[str, int, str], tuple[pd.DataFrame, pd.DataFrame]] = {}
    return [
        run_season_benchmark(
            players,
            season,
            strategy,
            model_name=model_name,
            model_version=model_version,
            max_free_transfers=max_free_transfers,
            verbose=verbose,
            prediction_cache=prediction_cache,
        )
        for season in seasons
        for strategy in selected_strategies
    ]


def append_result_to_history(
    result: SeasonBenchmarkResult,
    history_path: Path = HISTORY_PATH,
) -> pd.Series | None:
    """Append one result and return the latest prior same-season strategy row."""

    previous = None
    if history_path.exists():
        history = pd.read_csv(history_path)
        matching = history[
            (history["season"] == result.season)
            & (history["strategy_name"] == result.strategy_name)
        ]
        if not matching.empty:
            previous = matching.iloc[-1]

    record = pd.DataFrame(
        [
            {
                "run_timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
                "season": result.season,
                "strategy_name": result.strategy_name,
                "strategy_version": result.strategy_version,
                "model_name": result.model_name,
                "model_version": result.model_version,
                "total_points": result.total_points,
                "gross_points": result.gross_points,
                "transfers_made": result.transfers_made,
                "total_hit_cost": result.total_hit_cost,
                "max_free_transfers": result.max_free_transfers,
                "initial_bank": result.initial_bank,
                "final_bank": result.final_bank,
            }
        ],
        columns=HISTORY_COLUMNS,
    )
    history_path.parent.mkdir(parents=True, exist_ok=True)
    record.to_csv(history_path, mode="a", header=not history_path.exists(), index=False)
    return previous


def print_result_summary(result: SeasonBenchmarkResult, previous: pd.Series | None = None) -> None:
    print(
        f"{result.season} | {result.strategy_name} {result.strategy_version}: "
        f"{result.total_points:.1f} pts; {result.transfers_made} transfers; "
        f"hits -{result.total_hit_cost}"
    )
    if previous is not None:
        previous_points = float(previous["total_points"])
        change = result.total_points - previous_points
        print(
            f"Previous run ({previous['run_timestamp']}): {previous_points:.1f} pts. "
            f"Change: {change:+.1f} pts"
        )


def load_max_free_transfers(path: Path = BOOTSTRAP_PATH) -> int:
    """Read the cached bootstrap rule, with the documented historical fallback."""

    try:
        with path.open(encoding="utf-8") as handle:
            bootstrap = json.load(handle)
        value = int(bootstrap.get("game_settings", {}).get("max_extra_free_transfers", 0))
        return value if value > 0 else FREE_TRANSFER_CAP
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return FREE_TRANSFER_CAP


def _previous_season(players: pd.DataFrame, season: str) -> str | None:
    seasons = sorted(str(value) for value in players["season"].unique())
    previous = [value for value in seasons if value < season]
    return previous[-1] if previous else None


def _latest_prices(players: pd.DataFrame, season: str, gameweek: int) -> dict[int, float]:
    rows = players[(players["season"] == season) & (players["gameweek"] <= gameweek)]
    latest = rows.sort_values(["player_id", "gameweek"]).drop_duplicates(
        "player_id", keep="last"
    )
    return {int(row.player_id): float(row.price) for row in latest.itertuples()}


def _assert_transfer_budget(
    squad: pd.DataFrame,
    decision: TransferDecision,
    bank: float,
) -> None:
    if not decision.made:
        return
    if decision.incoming_price is None or decision.outgoing_price is None:
        raise AssertionError("A transfer decision must include incoming and outgoing prices")
    if float(decision.incoming_price) > float(decision.outgoing_price) + bank + 1e-9:
        raise AssertionError("Transfer exceeds the player's sale price plus bank")
    outgoing = squad[squad["player_id"] == decision.outgoing_id]
    if outgoing.empty:
        raise AssertionError("Transfer decision names an outgoing player outside the squad")


def _apply_benchmark_transfer(
    squad: pd.DataFrame,
    predictions: pd.DataFrame,
    decision: TransferDecision,
) -> pd.DataFrame:
    """Apply a transfer after sale-price-plus-bank validation.

    Current player prices can push a squad's market value above the original
    budget after price rises. FPL's relevant transfer constraint is the incoming
    price against the outgoing sale price plus bank, so roster validation here
    checks shape and club limits without incorrectly reapplying the initial
    budget to current market values.
    """

    incoming = predictions[predictions["player_id"] == decision.incoming_id].iloc[0]
    updated = squad[squad["player_id"] != decision.outgoing_id].copy()
    updated = pd.concat([updated, pd.DataFrame([incoming])], ignore_index=True)
    violations = validate_squad(updated, budget=float("inf"))
    if violations:
        raise ValueError(f"Transfer produced an invalid squad: {'; '.join(violations)}")
    return updated


def _assert_no_lookahead(rows: pd.DataFrame, season: str) -> None:
    leakage = rows[
        rows["max_training_current_season_gameweek"].notna()
        & (
            pd.to_numeric(rows["max_training_current_season_gameweek"])
            >= pd.to_numeric(rows["gameweek"])
        )
    ]
    assert leakage.empty, (
        f"No-lookahead assertion failed for {season}: {leakage.to_dict('records')}"
    )


def _empty_decision() -> TransferDecision:
    return TransferDecision(None, None, None, None, 0.0, 0.0, 0, None, None)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the permanent FPL season benchmark.")
    parser.add_argument("--seasons", nargs="+", default=list(DEFAULT_BENCHMARK_SEASONS))
    parser.add_argument(
        "--strategy",
        choices=("all", "no-transfers", "deterministic-single-transfer"),
        default="all",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, choices=tuple(MODEL_BUILDERS))
    parser.add_argument("--model-version", default=DEFAULT_MODEL_VERSION)
    parser.add_argument("--history-path", type=Path, default=HISTORY_PATH)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    players = load_historical_player_gameweeks(HISTORICAL_PLAYER_GW_PATH)
    if args.strategy == "all":
        strategies = (NoTransfersStrategy(), DeterministicTransferStrategy())
    elif args.strategy == "no-transfers":
        strategies = (NoTransfersStrategy(),)
    else:
        strategies = (DeterministicTransferStrategy(),)

    results = run_benchmark_suite(
        players,
        seasons=args.seasons,
        strategies=strategies,
        model_name=args.model,
        model_version=args.model_version,
        verbose=args.verbose,
    )
    for result in results:
        previous = append_result_to_history(result, args.history_path)
        print_result_summary(result, previous)
    print(f"Appended benchmark history to {args.history_path}")


if __name__ == "__main__":
    main()
