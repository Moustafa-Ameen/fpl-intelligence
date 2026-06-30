from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_PLAYER_GW_PATH = PROJECT_ROOT / "data" / "processed" / "historical_player_gw.csv"
PREDICTIONS_PATH = PROJECT_ROOT / "data" / "processed" / "step4_predictions.csv"
MODELS_DIR = PROJECT_ROOT / "models"
RIDGE_MODEL_PATH = MODELS_DIR / "ridge_points_model.joblib"
MINUTES_MODEL_PATH = MODELS_DIR / "logistic_minutes_model.joblib"

TRAIN_SEASONS = ["2023-24", "2024-25"]
TEST_SEASON = "2025-26"
NUMERIC_FEATURES = [
    "price",
    "minutes_last_3",
    "points_last_3",
    "opponent_strength",
    "selected_by_percent",
]
CATEGORICAL_FEATURES = ["position", "home_or_away"]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES


@dataclass(frozen=True)
class Step4Results:
    ridge_mae: float
    ridge_rmse: float
    baseline_mae: float
    baseline_rmse: float
    minutes_accuracy: float
    minutes_precision: float
    minutes_recall: float
    confusion: np.ndarray


def load_historical_player_gameweeks(path: Path = HISTORICAL_PLAYER_GW_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def build_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )


def build_ridge_model() -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            ("model", Ridge(alpha=1.0)),
        ]
    )


def build_minutes_classifier() -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            ("model", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )


def split_train_test(players: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = players[players["season"].isin(TRAIN_SEASONS)].copy()
    test = players[players["season"] == TEST_SEASON].copy()
    return train, test


def rmse(actual: pd.Series, predicted: np.ndarray | pd.Series) -> float:
    return float(np.sqrt(mean_squared_error(actual, predicted)))


def train_step4_models(
    players: pd.DataFrame,
) -> tuple[Pipeline, Pipeline, pd.DataFrame, Step4Results]:
    train, test = split_train_test(players)

    ridge_model = build_ridge_model()
    minutes_model = build_minutes_classifier()

    ridge_model.fit(train[FEATURE_COLUMNS], train["next_gameweek_points"])

    train_minutes_target = (train["minutes"] >= 60).astype(int)
    test_minutes_target = (test["minutes"] >= 60).astype(int)
    minutes_model.fit(train[FEATURE_COLUMNS], train_minutes_target)

    predictions = test.copy()
    predictions["predicted_points"] = ridge_model.predict(test[FEATURE_COLUMNS])
    predictions["naive_points_prediction"] = predictions["points_last_3"] / 3
    predictions["probability_60_plus_minutes"] = minutes_model.predict_proba(
        test[FEATURE_COLUMNS]
    )[:, 1]
    predictions["predicted_played_60_plus"] = minutes_model.predict(test[FEATURE_COLUMNS])
    predictions["actual_played_60_plus"] = test_minutes_target
    predictions["expected_points_adjusted"] = (
        predictions["predicted_points"] * predictions["probability_60_plus_minutes"]
    )

    results = Step4Results(
        ridge_mae=float(
            mean_absolute_error(
                test["next_gameweek_points"],
                predictions["predicted_points"],
            )
        ),
        ridge_rmse=rmse(test["next_gameweek_points"], predictions["predicted_points"]),
        baseline_mae=float(
            mean_absolute_error(
                test["next_gameweek_points"],
                predictions["naive_points_prediction"],
            )
        ),
        baseline_rmse=rmse(test["next_gameweek_points"], predictions["naive_points_prediction"]),
        minutes_accuracy=float(
            accuracy_score(test_minutes_target, predictions["predicted_played_60_plus"])
        ),
        minutes_precision=float(
            precision_score(
                test_minutes_target,
                predictions["predicted_played_60_plus"],
                zero_division=0,
            )
        ),
        minutes_recall=float(
            recall_score(
                test_minutes_target,
                predictions["predicted_played_60_plus"],
                zero_division=0,
            )
        ),
        confusion=confusion_matrix(test_minutes_target, predictions["predicted_played_60_plus"]),
    )

    return ridge_model, minutes_model, predictions, results


def save_artifacts(
    ridge_model: Pipeline,
    minutes_model: Pipeline,
    predictions: pd.DataFrame,
) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(ridge_model, RIDGE_MODEL_PATH)
    joblib.dump(minutes_model, MINUTES_MODEL_PATH)
    predictions.to_csv(PREDICTIONS_PATH, index=False)


def print_feature_set() -> None:
    print("Step 4 feature set:")
    print("- price: current gameweek FPL price; captures cost and market expectation.")
    print("- position: categorical FPL role, because scoring rules differ by position.")
    print("- minutes_last_3: prior 3-gameweek minutes only; captures recent playing time.")
    print("- points_last_3: prior 3-gameweek points only; captures recent FPL output.")
    print("- opponent_strength: venue-adjusted opponent strength from FPL team data.")
    print("- home_or_away: categorical fixture venue flag; H, A, or M for mixed/double GWs.")
    print("- selected_by_percent: estimated ownership percentage for that gameweek.")


def print_results(results: Step4Results) -> None:
    print("\nRidge Regression points model:")
    print(f"- Ridge MAE: {results.ridge_mae:.3f}")
    print(f"- Ridge RMSE: {results.ridge_rmse:.3f}")
    print(f"- Naive baseline MAE (points_last_3 / 3): {results.baseline_mae:.3f}")
    print(f"- Naive baseline RMSE (points_last_3 / 3): {results.baseline_rmse:.3f}")
    if results.ridge_mae < results.baseline_mae:
        print("- Ridge beats the naive baseline on MAE.")
    else:
        print("- Ridge does not beat the naive baseline on MAE.")

    print("\nLogistic Regression minutes classifier:")
    print(f"- Accuracy: {results.minutes_accuracy:.3f}")
    print(f"- Precision: {results.minutes_precision:.3f}")
    print(f"- Recall: {results.minutes_recall:.3f}")
    print("- Confusion matrix [[true_0_pred_0, true_0_pred_1], [true_1_pred_0, true_1_pred_1]]:")
    print(results.confusion)


def print_top_adjusted_predictions(predictions: pd.DataFrame, sample_gameweek: int = 10) -> None:
    sample = predictions[predictions["gameweek"] == sample_gameweek].copy()
    display_columns = [
        "player_name",
        "team",
        "position",
        "price",
        "opponent_team",
        "home_or_away",
        "minutes_last_3",
        "points_last_3",
        "predicted_points",
        "probability_60_plus_minutes",
        "expected_points_adjusted",
        "minutes",
        "next_gameweek_points",
    ]

    top_players = sample.sort_values("expected_points_adjusted", ascending=False).head(10)
    print(f"\nTop 10 by expected_points_adjusted for {TEST_SEASON} GW{sample_gameweek}:")
    print(top_players[display_columns].to_string(index=False))

    low_minutes = top_players[top_players["minutes_last_3"] == 0]
    print("\nSanity check:")
    if low_minutes.empty:
        print("- No top-10 adjusted pick had 0 minutes across the prior three gameweeks.")
    else:
        names = ", ".join(low_minutes["player_name"].tolist())
        print(f"- Prior-3-GW 0-minute players appeared in the top 10: {names}.")


def main() -> None:
    players = load_historical_player_gameweeks()

    print("Season-boundary check:")
    gw1 = players[players["gameweek"] == 1]
    boundary_max = gw1[
        ["prior_games_available_last_3", "minutes_last_3", "points_last_3"]
    ].max()
    print("- Rolling features reset by season and player_id.")
    print(f"- GW1 max prior_games_available_last_3: {boundary_max['prior_games_available_last_3']}")
    print(f"- GW1 max minutes_last_3: {boundary_max['minutes_last_3']}")
    print(f"- GW1 max points_last_3: {boundary_max['points_last_3']}")

    train, test = split_train_test(players)
    print("\nTrain/test split:")
    print(f"- Train seasons: {', '.join(TRAIN_SEASONS)} ({len(train):,} rows)")
    print(f"- Test season: {TEST_SEASON} ({len(test):,} rows)")

    print_feature_set()
    ridge_model, minutes_model, predictions, results = train_step4_models(players)
    print_results(results)
    print_top_adjusted_predictions(predictions)
    save_artifacts(ridge_model, minutes_model, predictions)

    print(f"\nSaved Ridge model to {RIDGE_MODEL_PATH}")
    print(f"Saved Logistic Regression minutes model to {MINUTES_MODEL_PATH}")
    print(f"Saved test predictions to {PREDICTIONS_PATH}")


if __name__ == "__main__":
    main()
