from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RAW_DIR = PROJECT_ROOT / "data" / "raw"

PLAYERS_RANKED_REQUIRED_COLUMNS = [
    "player_name",
    "team_name",
    "position",
    "price",
    "points_per_game",
    "form",
    "minutes_security",
    "value_score",
    "captain_score",
    "transfer_score",
]

PLAYERS_RANKED_NUMERIC_COLUMNS = [
    "price",
    "total_points",
    "points_per_game",
    "form",
    "minutes",
    "selected_by_percent",
    "value_score",
    "minutes_security",
    "ownership_risk",
    "captain_score",
    "transfer_score",
]


def processed_path(filename: str) -> Path:
    return PROCESSED_DIR / filename


@lru_cache(maxsize=1)
def load_players_ranked() -> pd.DataFrame:
    players = pd.read_csv(processed_path("players_ranked.csv"))
    missing_columns = [
        column for column in PLAYERS_RANKED_REQUIRED_COLUMNS if column not in players.columns
    ]
    if missing_columns:
        available = ", ".join(players.columns)
        missing = ", ".join(missing_columns)
        raise ValueError(
            f"players_ranked.csv is missing required columns: {missing}. "
            f"Available columns: {available}"
        )

    for column in PLAYERS_RANKED_NUMERIC_COLUMNS:
        if column in players.columns:
            players[column] = pd.to_numeric(players[column], errors="coerce").fillna(0)

    players["position"] = players["position"].astype(str).str.strip()
    return players


@lru_cache(maxsize=1)
def load_step6_predictions() -> pd.DataFrame:
    return pd.read_csv(processed_path("step6_backtest_predictions.csv"))


@lru_cache(maxsize=1)
def load_raw_accuracy() -> pd.DataFrame:
    return pd.read_csv(processed_path("step7_raw_accuracy.csv"))


@lru_cache(maxsize=1)
def load_adjusted_accuracy() -> pd.DataFrame:
    return pd.read_csv(processed_path("step7_adjusted_accuracy.csv"))


@lru_cache(maxsize=1)
def load_adjustment_impact() -> pd.DataFrame:
    return pd.read_csv(processed_path("step7_adjustment_impact.csv"))


@lru_cache(maxsize=1)
def load_top10_metrics() -> pd.DataFrame:
    return pd.read_csv(processed_path("step7_top10_metrics.csv"))


@lru_cache(maxsize=1)
def load_captaincy_backtest() -> pd.DataFrame:
    return pd.read_csv(processed_path("step7_captaincy_backtest.csv"))


@lru_cache(maxsize=1)
def load_step7_summary() -> str:
    return processed_path("step7_summary.txt").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def load_historical_player_gw() -> pd.DataFrame:
    return pd.read_csv(processed_path("historical_player_gw.csv"))


@lru_cache(maxsize=1)
def load_bootstrap() -> dict:
    bootstrap_path = RAW_DIR / "bootstrap-static.json"
    if not bootstrap_path.exists():
        return {}
    return json.loads(bootstrap_path.read_text(encoding="utf-8"))


def latest_prediction_gameweek(predictions: pd.DataFrame) -> int:
    return int(predictions["gameweek"].max())


def model_predictions_for_gameweek(
    predictions: pd.DataFrame,
    model: str,
    gameweek: int,
) -> pd.DataFrame:
    return predictions[
        (predictions["model"] == model) & (predictions["gameweek"] == gameweek)
    ].copy()


def default_model(predictions: pd.DataFrame) -> str:
    preferred = "Gradient Boosting Regressor"
    if preferred in set(predictions["model"]):
        return preferred
    return sorted(predictions["model"].unique())[0]


def get_demo_squad(predictions: pd.DataFrame, model: str, gameweek: int) -> pd.DataFrame:
    gw = model_predictions_for_gameweek(predictions, model, gameweek)
    formation = {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2}
    squad_parts = []
    for position, count in formation.items():
        position_players = gw[gw["position"] == position].sort_values(
            "expected_points_adjusted",
            ascending=False,
        )
        squad_parts.append(position_players.head(count))
    return pd.concat(squad_parts, ignore_index=True)


def get_transfer_suggestions(
    predictions: pd.DataFrame,
    ranked_players: pd.DataFrame,
    model: str,
    gameweek: int,
) -> pd.DataFrame:
    squad = get_demo_squad(predictions, model, gameweek)
    out_players = squad.sort_values(
        ["expected_points_adjusted", "opponent_strength"],
        ascending=[True, False],
    ).head(2)

    squad_names = set(squad["player_name"])
    in_pool = ranked_players[~ranked_players["player_name"].isin(squad_names)].copy()
    in_players = in_pool.sort_values("transfer_score", ascending=False).head(2)

    rows = []
    for (_, out_row), (_, in_row) in zip(
        out_players.iterrows(),
        in_players.iterrows(),
        strict=False,
    ):
        reason = "tough fixture" if out_row["opponent_strength"] >= 1250 else "rotation risk"
        net_gain = float(in_row["transfer_score"] - out_row["expected_points_adjusted"])
        rows.append(
            {
                "out_player": out_row["player_name"],
                "out_team": out_row["team"],
                "out_xp": out_row["expected_points_adjusted"],
                "reason": reason,
                "in_player": in_row["player_name"],
                "in_team": in_row["team_name"],
                "in_xp": in_row["transfer_score"],
                "in_price": in_row["price"],
                "net_gain": net_gain,
            }
        )
    return pd.DataFrame(rows)


def position_average_xp(squad: pd.DataFrame) -> pd.Series:
    return squad.groupby("position")["expected_points_adjusted"].transform("mean")


def build_fixture_ticker(historical: pd.DataFrame, team_limit: int = 20) -> pd.DataFrame:
    latest_season = historical["season"].max()
    season_data = historical[historical["season"] == latest_season].copy()
    fixture_gameweeks = sorted(season_data["gameweek"].unique())[-5:]

    rows = []
    for team in sorted(season_data["team"].dropna().unique())[:team_limit]:
        row = {"team": team}
        team_data = season_data[season_data["team"] == team]
        for gw in fixture_gameweeks:
            gw_data = team_data[team_data["gameweek"] == gw]
            if gw_data.empty:
                row[f"GW{gw}"] = np.nan
            else:
                row[f"GW{gw}"] = opponent_strength_to_fdr(gw_data["opponent_strength"].mean())
        rows.append(row)
    return pd.DataFrame(rows)


def opponent_strength_to_fdr(strength: float) -> int:
    if pd.isna(strength):
        return 3
    if strength < 1130:
        return 1
    if strength < 1210:
        return 2
    if strength < 1290:
        return 3
    if strength < 1370:
        return 4
    return 5


def get_price_change_estimates(players: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rising = players.sort_values(
        ["selected_by_percent", "form", "total_points"],
        ascending=False,
    ).head(5)
    falling = players.sort_values(
        ["selected_by_percent", "form", "total_points"],
        ascending=[True, True, True],
    ).head(3)
    return rising, falling


def get_differentials(predictions: pd.DataFrame, model: str, gameweek: int) -> pd.DataFrame:
    gw = model_predictions_for_gameweek(predictions, model, gameweek)
    return (
        gw[gw["selected_by_percent"] < 15]
        .sort_values("expected_points_adjusted", ascending=False)
        .head(3)
    )


def build_captaincy_timeseries(predictions: pd.DataFrame) -> pd.DataFrame:
    eval_predictions = predictions[predictions["gameweek"] >= 2].copy()
    rows = []

    for model, model_predictions in eval_predictions.groupby("model"):
        picks = (
            model_predictions.sort_values(
                ["gameweek", "expected_points_adjusted"],
                ascending=[True, False],
            )
            .groupby("gameweek")
            .head(1)
            .sort_values("gameweek")
        )
        for _, row in picks.iterrows():
            rows.append(
                {
                    "gameweek": row["gameweek"],
                    "strategy": f"{model} captain",
                    "captain_points": row["actual_points"] * 2,
                }
            )

    baseline_rows = eval_predictions[eval_predictions["model"] == "Naive baseline"].copy()
    most_owned = (
        baseline_rows.sort_values(["gameweek", "selected_by_percent"], ascending=[True, False])
        .groupby("gameweek")
        .head(1)
        .sort_values("gameweek")
    )
    for _, row in most_owned.iterrows():
        rows.append(
            {
                "gameweek": row["gameweek"],
                "strategy": "Always captain most-owned player",
                "captain_points": row["actual_points"] * 2,
            }
        )

    rolling_ppg = baseline_rows.copy()
    rolling_ppg["prior_points_per_available_game"] = np.where(
        rolling_ppg["prior_games_available_last_3"] > 0,
        rolling_ppg["points_last_3"] / rolling_ppg["prior_games_available_last_3"],
        -1,
    )
    highest_ppg = (
        rolling_ppg.sort_values(
            ["gameweek", "prior_points_per_available_game"],
            ascending=[True, False],
        )
        .groupby("gameweek")
        .head(1)
        .sort_values("gameweek")
    )
    for _, row in highest_ppg.iterrows():
        rows.append(
            {
                "gameweek": row["gameweek"],
                "strategy": "Always captain highest prior rolling PPG player",
                "captain_points": row["actual_points"] * 2,
            }
        )

    random_points = baseline_rows.groupby("gameweek")["actual_points"].mean().mul(2)
    for gameweek, points in random_points.items():
        rows.append(
            {
                "gameweek": gameweek,
                "strategy": "Random player average",
                "captain_points": points,
            }
        )

    timeline = pd.DataFrame(rows).sort_values(["strategy", "gameweek"])
    timeline["cumulative_captain_points"] = timeline.groupby("strategy")[
        "captain_points"
    ].cumsum()
    return timeline


def model_confidence(raw_accuracy: pd.DataFrame) -> str:
    naive = raw_accuracy[raw_accuracy["model"] == "Naive baseline"].iloc[0]
    best = raw_accuracy.sort_values("MAE").iloc[0]
    gap = naive["MAE"] - best["MAE"]
    if gap >= 0.05:
        return "High"
    if gap >= 0.02:
        return "Medium"
    return "Low"
