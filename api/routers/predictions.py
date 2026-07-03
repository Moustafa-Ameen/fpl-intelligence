from typing import Any

import pandas as pd
from fastapi import APIRouter, Query

from api import data_service

router = APIRouter(prefix="/api/predictions", tags=["predictions"])

BEST_MODEL = "Gradient Boosting Regressor"
PREDICTION_COLUMNS = {
    "player_name": "name",
    "team": "team",
    "position": "position",
    "predicted_points": "predicted_pts",
    "probability_60_plus_minutes": "start_likelihood",
    "expected_points_adjusted": "adjusted_pts",
}


def _best_model_predictions(gw: int | None = None) -> pd.DataFrame:
    dataframe = data_service.backtest_predictions()
    if dataframe.empty:
        return dataframe

    dataframe = dataframe[dataframe["model"] == BEST_MODEL].copy()
    if gw is None:
        gw = int(dataframe["gameweek"].max())

    return dataframe[dataframe["gameweek"] == gw].copy()


@router.get("/captaincy")
def captaincy(gw: int | None = Query(default=None, ge=1, le=38)) -> list[dict[str, Any]]:
    dataframe = _best_model_predictions(gw)
    if dataframe.empty:
        return []

    output = dataframe.sort_values("expected_points_adjusted", ascending=False).head(10)
    output = output.rename(columns=PREDICTION_COLUMNS)
    return data_service.to_records(output[list(PREDICTION_COLUMNS.values())])


@router.get("/transfers")
def transfers() -> list[dict[str, Any]]:
    players = data_service.players()
    predictions = _best_model_predictions()
    if players.empty:
        return []

    players = players.sort_values("transfer_score", ascending=False).head(40).copy()
    if predictions.empty:
        players["predicted_pts"] = None
        players["adjusted_pts"] = None
        players["start_likelihood"] = players.get("minutes_security")
    else:
        prediction_columns = [
            "player_name",
            "predicted_points",
            "expected_points_adjusted",
            "probability_60_plus_minutes",
        ]
        latest_predictions = predictions[prediction_columns].drop_duplicates("player_name")
        players = players.merge(latest_predictions, on="player_name", how="left")
        players = players.rename(
            columns={
                "predicted_points": "predicted_pts",
                "expected_points_adjusted": "adjusted_pts",
                "probability_60_plus_minutes": "start_likelihood",
            }
        )

    players = players.rename(
        columns={
            "player_name": "name",
            "team_name": "team",
            "price": "price",
            "transfer_score": "transfer_score",
        }
    )
    columns = [
        "name",
        "team",
        "position",
        "price",
        "transfer_score",
        "predicted_pts",
        "adjusted_pts",
        "start_likelihood",
    ]
    return data_service.to_records(players[columns].head(20))
