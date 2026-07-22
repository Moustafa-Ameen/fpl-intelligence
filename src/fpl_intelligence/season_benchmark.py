"""Permanent, realistic season benchmark for comparing FPL strategies.

This harness answers a directional research question: does a transfer strategy
score better than its previous version when evaluated under the same historical
season and FPL constraints? It is not a claim that the result is exactly what a
real manager would have scored.

The simulation uses starting-XI-only scoring, legal formations, basic autosubs,
free-transfer banking, hit costs, budget and club limits, and reports two captaincy
tracks: hindsight-optimal attribution and point-in-time realistic captain/vice
selection. Chips, injury/news reactions, exact intraweek price-change timing, and a
fully realistic human squad selection process are not simulated.

The strategy interface is deliberately small: a strategy receives the current
squad and only the data available before the target gameweek, then returns a
single legal transfer decision. New strategies can therefore use this harness
without changing scoring, transfer accounting, or result persistence.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
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
    resolve_active_lineup,
    score_gameweek,
    select_starting_xi,
    validate_squad,
)
from fpl_intelligence.step4_models import (
    FEATURE_COLUMNS,
    build_minutes_classifier,
    build_ridge_model,
    feature_columns_for_mode,
    fit_minutes_band_conditional_model,
    load_historical_player_gameweeks,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_PLAYER_GW_PATH = PROJECT_ROOT / "data" / "processed" / "historical_player_gw.csv"
BOOTSTRAP_PATH = PROJECT_ROOT / "data" / "raw" / "bootstrap-static.json"
HISTORY_PATH = PROJECT_ROOT / "data" / "processed" / "season_benchmark_history.csv"
HISTORICAL_MAX_FREE_TRANSFERS = {
    "2023-24": 2,
    "2024-25": 5,
    "2025-26": 5,
}
DEFAULT_BENCHMARK_SEASONS = ("2023-24", "2024-25")
DEFAULT_MODEL = "Ridge Regression"
DEFAULT_MODEL_VERSION = "local benchmark"
OPTIMIZER_VERSION = "m3.5-milp-v1"
HISTORY_COLUMNS = [
    "run_timestamp",
    "run_id",
    "commit_hash",
    "optimizer_version",
    "season",
    "strategy_name",
    "strategy_version",
    "model_name",
    "model_version",
    "variant_name",
    "total_points",
    "gross_points",
    "hindsight_total_points",
    "realistic_total_points",
    "realistic_gross_points",
    "captaincy_gap",
    "acceptance_result",
    "acceptance_reason",
    "transfers_made",
    "total_hit_cost",
    "max_free_transfers",
    "initial_bank",
    "final_bank",
    "validation_status",
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
    free_transfer_cap: int = FREE_TRANSFER_CAP
    future_predictions: dict[int, pd.DataFrame] = field(default_factory=dict)


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
    realistic_total_points: float
    realistic_gross_points: float
    realistic_captaincy_gap: float
    transfers_made: int
    total_hit_cost: int
    max_free_transfers: int
    initial_bank: float
    final_bank: float


@dataclass(frozen=True)
class RealisticCaptainScore:
    points: float
    raw_starter_points: float
    captain_id: int
    vice_captain_id: int
    captain_predicted_points: float
    vice_captain_predicted_points: float
    captain_actual_points: float
    vice_captain_actual_points: float
    vice_captain_fallback: bool
    starting_ids: tuple[int, ...]
    autosub_ids: tuple[int, ...]
    formation: str


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
    minutes_mode: str = "binary",
    feature_mode: str = "baseline",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Train and predict one target gameweek using an expanding time window."""

    if model_name not in MODEL_BUILDERS:
        raise ValueError(f"Unknown model {model_name!r}; choose from {', '.join(MODEL_BUILDERS)}")
    if minutes_mode not in {"binary", "conditional_bands"}:
        raise ValueError("minutes_mode must be 'binary' or 'conditional_bands'")
    feature_columns = feature_columns_for_mode(feature_mode)
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
        target["probability_0_minutes"] = 0.0
        target["probability_1_59_minutes"] = 0.0
        target["probability_60_plus_minutes_v2"] = 1.0
        target["predicted_minutes_band"] = 2
        target["minutes_model_mode"] = minutes_mode
        target["feature_mode"] = feature_mode
        target["expected_points_adjusted"] = target["predicted_points"]
        target["training_row_count"] = 0
        target["max_training_current_season_gameweek"] = None
        target["model"] = "Preseason heuristic"
        return target, training

    points_model: Pipeline = MODEL_BUILDERS[model_name](feature_columns)
    points_model.fit(training[feature_columns], training["next_gameweek_points"])

    target["predicted_points"] = points_model.predict(target[feature_columns])
    if minutes_mode == "binary":
        minutes_model = build_minutes_classifier(feature_columns)
        minutes_model.fit(training[feature_columns], (training["minutes"] >= 60).astype(int))
        target["probability_60_plus_minutes"] = minutes_model.predict_proba(
            target[feature_columns]
        )[:, 1]
        target["expected_points_adjusted"] = (
            target["predicted_points"] * target["probability_60_plus_minutes"]
        ).clip(lower=0.0)
    else:
        # This is intentionally independent benchmark logic: it fits its own
        # three-class model and band-specific point estimators for each target GW.
        minutes_band_model = fit_minutes_band_conditional_model(training, feature_columns)
        band_probabilities = minutes_band_model.predict_proba(target[feature_columns])
        target["probability_0_minutes"] = band_probabilities[:, 0]
        target["probability_1_59_minutes"] = band_probabilities[:, 1]
        target["probability_60_plus_minutes_v2"] = band_probabilities[:, 2]
        target["probability_60_plus_minutes"] = band_probabilities[:, 2]
        target["predicted_minutes_band"] = minutes_band_model.predict(target[feature_columns])
        target["expected_points_adjusted"] = minutes_band_model.predict_expected_points(
            target[feature_columns]
        ).clip(0.0)
    target["minutes_model_mode"] = minutes_mode
    target["feature_mode"] = feature_mode
    target["decision_price"] = target["price_before_deadline"].fillna(target["price"])
    target["training_row_count"] = len(training)
    current_training = training[training["season"] == season]
    target["max_training_current_season_gameweek"] = (
        None if current_training.empty else int(current_training["gameweek"].max())
    )
    target["model"] = model_name
    return target, training


def _point_in_time_future_frame(
    players: pd.DataFrame,
    season: str,
    decision_gameweek: int,
    target_gameweek: int,
) -> pd.DataFrame:
    """Build future target features using only the decision-time snapshot."""

    target = players[
        (players["season"] == season) & (players["gameweek"] == target_gameweek)
    ].copy()
    if target.empty:
        return target

    snapshot = players[
        (players["season"] == season) & (players["gameweek"] == decision_gameweek)
    ].copy()
    if snapshot.empty:
        snapshot = players[
            (players["season"] == season) & (players["gameweek"] < decision_gameweek)
        ].copy()
    snapshot = snapshot.sort_values(["player_id", "gameweek"]).drop_duplicates(
        "player_id", keep="last"
    )
    known_ids = set(snapshot["player_id"].tolist())
    target = target[target["player_id"].isin(known_ids)].copy()
    if target.empty:
        return target

    safe = target.sort_values(["player_id", "gameweek"]).drop_duplicates(
        "player_id", keep="last"
    ).copy()
    snapshot_by_id = snapshot.set_index("player_id")
    safe_by_id = safe.set_index("player_id")

    # Fixture context is known from the published schedule. All player-state
    # features, prices, positions, and ownership remain frozen at decision time.
    for column in (
        "price",
        "price_before_deadline",
        "selected_by_percent",
        "selected_by_percent_before_deadline",
        "market_snapshot_available",
        "position",
        *[
            feature
            for feature in feature_columns_for_mode("xg_xa")
            if feature not in {"home_or_away", "opponent_strength", "position"}
        ],
    ):
        if column in snapshot_by_id.columns:
            safe_by_id[column] = snapshot_by_id[column].reindex(safe_by_id.index)

    safe = safe_by_id.reset_index()
    safe["decision_price"] = safe["price_before_deadline"].fillna(safe["price"])
    safe["as_of_gameweek"] = decision_gameweek
    safe["future_target_gameweek"] = target_gameweek
    return safe


def train_future_gameweek_predictions(
    players: pd.DataFrame,
    season: str,
    decision_gameweek: int,
    *,
    model_name: str = DEFAULT_MODEL,
    minutes_mode: str = "binary",
    feature_mode: str = "baseline",
    horizons: Sequence[int] = (1, 2),
) -> dict[int, pd.DataFrame]:
    """Forecast t+1/t+2 using only information available before gameweek t."""

    if any(horizon not in (1, 2) for horizon in horizons):
        raise ValueError("future horizons must be 1 or 2 gameweeks")
    if model_name not in MODEL_BUILDERS:
        raise ValueError(f"Unknown model {model_name!r}; choose from {', '.join(MODEL_BUILDERS)}")
    if minutes_mode not in {"binary", "conditional_bands"}:
        raise ValueError("minutes_mode must be 'binary' or 'conditional_bands'")
    feature_columns = feature_columns_for_mode(feature_mode)
    training = get_training_data_for_season(players, season, decision_gameweek)
    output: dict[int, pd.DataFrame] = {}

    points_model: Pipeline | None = None
    minutes_model: Pipeline | None = None
    minutes_band_model: Any | None = None
    if not training.empty:
        points_model = MODEL_BUILDERS[model_name](feature_columns)
        points_model.fit(training[feature_columns], training["next_gameweek_points"])
        if minutes_mode == "binary":
            minutes_model = build_minutes_classifier(feature_columns)
            minutes_model.fit(
                training[feature_columns], (training["minutes"] >= 60).astype(int)
            )
        else:
            minutes_band_model = fit_minutes_band_conditional_model(
                training, feature_columns
            )

    for horizon in horizons:
        target_gameweek = decision_gameweek + horizon
        target = _point_in_time_future_frame(
            players, season, decision_gameweek, target_gameweek
        )
        if target.empty:
            output[target_gameweek] = pd.DataFrame()
            continue

        if training.empty:
            preseason = build_preseason_scores(
                players, season=season, prior_season=None
            ).set_index("player_id")
            target["predicted_points"] = target["player_id"].map(
                preseason["preseason_value_score"]
            ).fillna(0.0)
            target["expected_points_adjusted"] = target["predicted_points"]
            target["probability_60_plus_minutes"] = 0.5
        else:
            assert points_model is not None
            target["predicted_points"] = points_model.predict(target[feature_columns])
            if minutes_mode == "binary":
                assert minutes_model is not None
                target["probability_60_plus_minutes"] = minutes_model.predict_proba(
                    target[feature_columns]
                )[:, 1]
                target["expected_points_adjusted"] = (
                    target["predicted_points"]
                    * target["probability_60_plus_minutes"]
                ).clip(lower=0.0)
            else:
                assert minutes_band_model is not None
                target["probability_60_plus_minutes"] = minutes_band_model.predict_proba(
                    target[feature_columns]
                )[:, 2]
                target["expected_points_adjusted"] = minutes_band_model.predict_expected_points(
                    target[feature_columns]
                ).clip(0.0)

        target["minutes_model_mode"] = minutes_mode
        target["feature_mode"] = feature_mode
        target["training_row_count"] = len(training)
        target["max_training_current_season_gameweek"] = (
            decision_gameweek - 1 if decision_gameweek > 1 else None
        )
        target["model"] = model_name if not training.empty else "Preseason heuristic"
        # Actual outcomes are deliberately excluded from the strategy-facing frame.
        output[target_gameweek] = target[
            [
                "player_id",
                "player_name",
                "position",
                "team",
                "price",
                "decision_price",
                "gameweek",
                "expected_points_adjusted",
                "predicted_points",
                "probability_60_plus_minutes",
                "minutes_model_mode",
                "feature_mode",
                "training_row_count",
                "max_training_current_season_gameweek",
                "as_of_gameweek",
                "future_target_gameweek",
            ]
        ].copy()
    return output


def train_realistic_captain_predictions(
    players: pd.DataFrame,
    season: str,
    gameweek: int,
) -> pd.DataFrame:
    """Train a fresh point-in-time Ridge model for captain selection."""

    training = get_training_data_for_season(players, season, gameweek)
    target = players[(players["season"] == season) & (players["gameweek"] == gameweek)].copy()
    if target.empty:
        raise ValueError(f"No target rows for {season} GW{gameweek}")

    current_training = training[training["season"] == season]
    max_current_gameweek = (
        None if current_training.empty else int(current_training["gameweek"].max())
    )
    if training.empty:
        # Only the earliest available season's GW1 can reach this fallback. It is
        # deterministic and pre-deadline by construction, but remains subject to
        # the benchmark's documented weak-GW1 heuristic limitation.
        preseason = build_preseason_scores(players, season=season, prior_season=None)
        projection = preseason.set_index("player_id")["preseason_value_score"]
        target["captain_predicted_points"] = target["player_id"].map(projection).fillna(0.0)
        target["captain_model"] = "Preseason captain fallback"
    else:
        model = build_ridge_model()
        model.fit(training[FEATURE_COLUMNS], training["next_gameweek_points"])
        target["captain_predicted_points"] = model.predict(target[FEATURE_COLUMNS])
        target["captain_model"] = "Ridge Regression"

    target["captain_training_row_count"] = len(training)
    target["captain_max_training_current_season_gameweek"] = max_current_gameweek
    return target


def score_realistic_gameweek(
    squad: pd.DataFrame,
    target: pd.DataFrame,
    projected_points: dict[int, float],
    captain_predictions: pd.DataFrame,
) -> RealisticCaptainScore:
    """Score with predicted captain/vice selection and real FPL fallback rules."""

    lineup = select_starting_xi(squad, projected_points)
    prediction_by_id = captain_predictions.set_index("player_id")[
        "captain_predicted_points"
    ].to_dict()
    predicted_order = sorted(
        lineup.starting_ids,
        key=lambda player_id: (float(prediction_by_id.get(player_id, 0.0)), -player_id),
        reverse=True,
    )
    captain_id, vice_captain_id = predicted_order[:2]
    active_ids, autosub_ids = resolve_active_lineup(squad, target, lineup)

    target_rows = target.drop_duplicates("player_id").set_index("player_id")
    minutes = target_rows["minutes"].to_dict()
    points = target_rows["next_gameweek_points"].to_dict()
    raw_starter_points = float(sum(float(points.get(player_id, 0)) for player_id in active_ids))
    captain_actual_points = float(points.get(captain_id, 0))
    vice_actual_points = float(points.get(vice_captain_id, 0))
    captain_played = float(minutes.get(captain_id, 0)) > 0
    vice_played = float(minutes.get(vice_captain_id, 0)) > 0

    if captain_played:
        bonus_points = captain_actual_points
        vice_captain_fallback = False
    elif vice_played:
        bonus_points = vice_actual_points
        vice_captain_fallback = True
    else:
        bonus_points = 0.0
        vice_captain_fallback = False

    return RealisticCaptainScore(
        points=raw_starter_points + bonus_points,
        raw_starter_points=raw_starter_points,
        captain_id=captain_id,
        vice_captain_id=vice_captain_id,
        captain_predicted_points=float(prediction_by_id.get(captain_id, 0.0)),
        vice_captain_predicted_points=float(prediction_by_id.get(vice_captain_id, 0.0)),
        captain_actual_points=captain_actual_points,
        vice_captain_actual_points=vice_actual_points,
        vice_captain_fallback=vice_captain_fallback,
        starting_ids=tuple(active_ids),
        autosub_ids=autosub_ids,
        formation=lineup.formation,
    )


def run_season_benchmark(
    players: pd.DataFrame,
    season: str,
    strategy: BenchmarkStrategy,
    *,
    model_name: str = DEFAULT_MODEL,
    model_version: str = DEFAULT_MODEL_VERSION,
    max_free_transfers: int | None = None,
    verbose: bool = False,
    minutes_mode: str = "binary",
    feature_mode: str = "baseline",
    prediction_cache: dict[
        tuple[str, int, str, str, str], tuple[pd.DataFrame, pd.DataFrame]
    ] | None = None,
    captain_prediction_cache: dict[tuple[str, int], pd.DataFrame] | None = None,
    future_prediction_cache: dict[
        tuple[str, int, str, str, str], dict[int, pd.DataFrame]
    ] | None = None,
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
    transfer_cap = (
        max_free_transfers
        if max_free_transfers is not None
        else load_max_free_transfers(season=season)
    )
    rows: list[dict[str, Any]] = []
    gross_points = 0.0
    total_points = 0.0
    realistic_gross_points = 0.0
    realistic_total_points = 0.0
    transfers_made = 0
    total_hit_cost = 0

    if verbose:
        print(f"Season benchmark: {season} | {strategy.name} {strategy.version}")
        print(f"- Model: {model_name} ({model_version})")
        print(f"- Free-transfer cap: {transfer_cap}; initial bank: GBP {initial_bank:.1f}m")

    for gameweek in gameweeks:
        cache_key = (season, gameweek, model_name, minutes_mode, feature_mode)
        if prediction_cache is not None and cache_key in prediction_cache:
            target, available_data = prediction_cache[cache_key]
        else:
            target, available_data = train_gameweek_predictions(
                players,
                season,
                gameweek,
                model_name=model_name,
                minutes_mode=minutes_mode,
                feature_mode=feature_mode,
            )
            if prediction_cache is not None:
                prediction_cache[cache_key] = (target, available_data)
        if getattr(strategy, "requires_future_predictions", False):
            if future_prediction_cache is not None and cache_key in future_prediction_cache:
                future_predictions = future_prediction_cache[cache_key]
            else:
                future_predictions = train_future_gameweek_predictions(
                    players,
                    season,
                    gameweek,
                    model_name=model_name,
                    minutes_mode=minutes_mode,
                    feature_mode=feature_mode,
                )
                if future_prediction_cache is not None:
                    future_prediction_cache[cache_key] = future_predictions
        else:
            future_predictions = {}
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
                free_transfer_cap=transfer_cap,
                future_predictions={
                    target_gameweek: frame.copy()
                    for target_gameweek, frame in future_predictions.items()
                },
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
        captain_cache_key = (season, gameweek)
        if captain_prediction_cache is not None and captain_cache_key in captain_prediction_cache:
            captain_predictions = captain_prediction_cache[captain_cache_key]
        else:
            captain_predictions = train_realistic_captain_predictions(players, season, gameweek)
            if captain_prediction_cache is not None:
                captain_prediction_cache[captain_cache_key] = captain_predictions
        realistic_score = score_realistic_gameweek(
            squad,
            target,
            projections,
            captain_predictions,
        )
        gross_points += score.points
        total_points += score.points - decision.hit_cost
        realistic_gross_points += realistic_score.points
        realistic_total_points += realistic_score.points - decision.hit_cost
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
                "realistic_gross_points": realistic_score.points,
                "realistic_net_points": realistic_score.points - decision.hit_cost,
                "realistic_cumulative_points": realistic_total_points,
                "captain_id": score.captain_id,
                "realistic_captain_id": realistic_score.captain_id,
                "realistic_vice_captain_id": realistic_score.vice_captain_id,
                "realistic_captain_predicted_points": round(
                    realistic_score.captain_predicted_points, 4
                ),
                "realistic_vice_captain_predicted_points": round(
                    realistic_score.vice_captain_predicted_points, 4
                ),
                "realistic_captain_actual_points": realistic_score.captain_actual_points,
                "realistic_vice_captain_actual_points": realistic_score.vice_captain_actual_points,
                "realistic_vice_captain_fallback": realistic_score.vice_captain_fallback,
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
                "minutes_model_mode": target["minutes_model_mode"].iloc[0],
                "feature_mode": target["feature_mode"].iloc[0],
                "max_training_current_season_gameweek": target[
                    "max_training_current_season_gameweek"
                ].iloc[0],
                "captain_training_row_count": int(
                    captain_predictions["captain_training_row_count"].iloc[0]
                ),
                "captain_max_training_current_season_gameweek": captain_predictions[
                    "captain_max_training_current_season_gameweek"
                ].iloc[0],
            }
        )
        free_transfers = min(transfer_cap, free_transfers + 1)
        if verbose:
            print(
                f"- GW{gameweek:02d}: {score.points:.1f} gross, captain {score.captain_id}, "
                f"realistic {realistic_score.points:.1f} captain {realistic_score.captain_id}, "
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
        realistic_total_points=round(realistic_total_points, 2),
        realistic_gross_points=round(realistic_gross_points, 2),
        realistic_captaincy_gap=round(total_points - realistic_total_points, 2),
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
    minutes_mode: str = "binary",
    feature_mode: str = "baseline",
    verbose: bool = False,
) -> list[SeasonBenchmarkResult]:
    selected_strategies = list(
        strategies
        or (NoTransfersStrategy(), DeterministicTransferStrategy())
    )
    prediction_cache: dict[
        tuple[str, int, str, str, str], tuple[pd.DataFrame, pd.DataFrame]
    ] = {}
    captain_prediction_cache: dict[tuple[str, int], pd.DataFrame] = {}
    future_prediction_cache: dict[
        tuple[str, int, str, str, str], dict[int, pd.DataFrame]
    ] = {}
    return [
        run_season_benchmark(
            players,
            season,
            strategy,
            model_name=model_name,
            model_version=model_version,
            max_free_transfers=max_free_transfers,
            minutes_mode=minutes_mode,
            feature_mode=feature_mode,
            verbose=verbose,
            prediction_cache=prediction_cache,
            captain_prediction_cache=captain_prediction_cache,
            future_prediction_cache=future_prediction_cache,
        )
        for season in seasons
        for strategy in selected_strategies
    ]


def append_result_to_history(
    result: SeasonBenchmarkResult,
    history_path: Path = HISTORY_PATH,
    validation_status: str = "provisional",
    variant_name: str = "baseline",
    acceptance_result: str = "not_evaluated",
    acceptance_reason: str = "",
    *,
    run_id: str | None = None,
    commit_hash: str = "unavailable",
    optimizer_version: str = OPTIMIZER_VERSION,
) -> pd.Series | None:
    """Append one result and return the latest prior same-season strategy row."""

    run_id = run_id or uuid.uuid4().hex
    if not str(run_id).strip():
        raise ValueError("run_id must be a non-empty identifier")
    key_columns = ("run_id", "variant_name", "season", "strategy_name")
    previous = None
    if history_path.exists():
        history = pd.read_csv(history_path)
        for column in HISTORY_COLUMNS:
            if column not in history.columns:
                if column == "variant_name":
                    history[column] = "baseline"
                elif column in {"commit_hash", "optimizer_version", "acceptance_reason"}:
                    history[column] = ""
                elif column == "validation_status":
                    history[column] = "provisional"
                elif column == "acceptance_result":
                    history[column] = "not_evaluated"
                else:
                    history[column] = pd.NA
        history = history[HISTORY_COLUMNS]
        populated_run_ids = history["run_id"].notna() & history["run_id"].astype(str).ne("")
        if history.loc[populated_run_ids].duplicated(list(key_columns), keep=False).any():
            raise ValueError("History contains duplicate run/variant/season/strategy rows")
        matching = history[
            (history["season"] == result.season)
            & (history["strategy_name"] == result.strategy_name)
            & (history["variant_name"] == variant_name)
        ]
        if not matching.empty:
            previous = matching.iloc[-1]
    else:
        history = pd.DataFrame(columns=HISTORY_COLUMNS)

    record = pd.DataFrame(
        [
            {
                "run_timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
                "run_id": run_id,
                "commit_hash": commit_hash,
                "optimizer_version": optimizer_version,
                "season": result.season,
                "strategy_name": result.strategy_name,
                "strategy_version": result.strategy_version,
                "model_name": result.model_name,
                "model_version": result.model_version,
                "variant_name": variant_name,
                "total_points": result.total_points,
                "gross_points": result.gross_points,
                "hindsight_total_points": result.total_points,
                "realistic_total_points": result.realistic_total_points,
                "realistic_gross_points": result.realistic_gross_points,
                "captaincy_gap": result.realistic_captaincy_gap,
                "acceptance_result": acceptance_result,
                "acceptance_reason": acceptance_reason,
                "transfers_made": result.transfers_made,
                "total_hit_cost": result.total_hit_cost,
                "max_free_transfers": result.max_free_transfers,
                "initial_bank": result.initial_bank,
                "final_bank": result.final_bank,
                "validation_status": validation_status,
            }
        ],
        columns=HISTORY_COLUMNS,
    )
    key = pd.DataFrame(
        [{
            "run_id": run_id,
            "variant_name": variant_name,
            "season": result.season,
            "strategy_name": result.strategy_name,
        }]
    )
    if pd.concat([history[list(key_columns)], key], ignore_index=True).duplicated(
        list(key_columns), keep=False
    ).any():
        raise ValueError("History row would duplicate run/variant/season/strategy")
    history_path.parent.mkdir(parents=True, exist_ok=True)
    pd.concat([history, record], ignore_index=True)[HISTORY_COLUMNS].to_csv(
        history_path, index=False
    )
    return previous


def get_git_commit() -> str:
    """Return the current commit when available without making metadata fatal."""

    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError:
        return "unavailable"
    commit = completed.stdout.strip()
    return commit if completed.returncode == 0 and commit else "unavailable"


def print_result_summary(result: SeasonBenchmarkResult, previous: pd.Series | None = None) -> None:
    print(
        f"{result.season} | {result.strategy_name} {result.strategy_version}: "
        f"{result.total_points:.1f} pts; {result.transfers_made} transfers; "
        f"hits -{result.total_hit_cost}"
    )
    print(
        f"  Hindsight captaincy: {result.total_points:.1f} pts | "
        f"Realistic captaincy: {result.realistic_total_points:.1f} pts | "
        f"Gap: {result.realistic_captaincy_gap:+.1f} pts"
    )
    if previous is not None:
        previous_points = float(previous["total_points"])
        change = result.total_points - previous_points
        print(
            f"Previous run ({previous['run_timestamp']}): {previous_points:.1f} pts. "
            f"Change: {change:+.1f} pts"
        )


def load_max_free_transfers(
    season: str | None = None,
    path: Path = BOOTSTRAP_PATH,
) -> int:
    """Return the rule-versioned historical cap or the current cached fallback."""

    if season in HISTORICAL_MAX_FREE_TRANSFERS:
        return HISTORICAL_MAX_FREE_TRANSFERS[season]

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
    cutoff = gameweek if gameweek == 1 else gameweek - 1
    rows = players[(players["season"] == season) & (players["gameweek"] <= cutoff)]
    latest = rows.sort_values(["player_id", "gameweek"]).drop_duplicates(
        "player_id", keep="last"
    )
    return {int(row.player_id): float(row.price) for row in latest.itertuples()}


def _decision_price(row: pd.Series) -> float:
    value = row.get("decision_price")
    if value is not None and pd.notna(value):
        return float(value)
    return float(row["price"])


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
    incoming = incoming.copy()
    incoming["price"] = _decision_price(incoming)
    updated = squad[squad["player_id"] != decision.outgoing_id].copy()
    updated = pd.concat([updated, pd.DataFrame([incoming])], ignore_index=True)
    violations = validate_squad(updated, budget=float("inf"))
    if violations:
        raise ValueError(f"Transfer produced an invalid squad: {'; '.join(violations)}")
    return updated


def _assert_no_lookahead(rows: pd.DataFrame, season: str) -> None:
    for training_column in (
        "max_training_current_season_gameweek",
        "captain_max_training_current_season_gameweek",
    ):
        leakage = rows[
            rows[training_column].notna()
            & (
                pd.to_numeric(rows[training_column])
                >= pd.to_numeric(rows["gameweek"])
            )
        ]
        assert leakage.empty, (
            f"No-lookahead assertion failed for {season} ({training_column}): "
            f"{leakage.to_dict('records')}"
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
    run_id = uuid.uuid4().hex
    commit_hash = get_git_commit()
    for result in results:
        previous = append_result_to_history(
            result,
            args.history_path,
            run_id=run_id,
            commit_hash=commit_hash,
        )
        print_result_summary(result, previous)
    print(f"Appended benchmark history to {args.history_path}")


if __name__ == "__main__":
    main()
