import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RAW_DIR = PROJECT_ROOT / "data" / "raw"

DATA_FILES = {
    "players": "players_ranked.csv",
    "backtest_predictions": "step6_backtest_predictions.csv",
    "raw_accuracy": "step7_raw_accuracy.csv",
    "adjusted_accuracy": "step7_adjusted_accuracy.csv",
    "captaincy_backtest": "step7_captaincy_backtest.csv",
    "top10_metrics": "step7_top10_metrics.csv",
    "historical_player_gw": "historical_player_gw.csv",
}


@lru_cache(maxsize=len(DATA_FILES))
def load_dataset(key: str) -> pd.DataFrame:
    filename = DATA_FILES.get(key)
    if filename is None:
        logging.warning("Unknown data key requested: %s", key)
        return pd.DataFrame()

    path = PROCESSED_DIR / filename
    if not path.exists():
        logging.warning("Processed data file is missing: %s", path)
        return pd.DataFrame()

    return pd.read_csv(path)


def to_records(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    if dataframe.empty:
        return []

    clean = dataframe.copy()
    clean = clean.where(pd.notna(clean), None)
    return clean.to_dict(orient="records")


def players() -> pd.DataFrame:
    return load_dataset("players").copy()


def backtest_predictions() -> pd.DataFrame:
    return load_dataset("backtest_predictions").copy()


def raw_accuracy() -> pd.DataFrame:
    return load_dataset("raw_accuracy").copy()


def adjusted_accuracy() -> pd.DataFrame:
    return load_dataset("adjusted_accuracy").copy()


def captaincy_backtest() -> pd.DataFrame:
    return load_dataset("captaincy_backtest").copy()


def top10_metrics() -> pd.DataFrame:
    return load_dataset("top10_metrics").copy()


def historical_player_gw() -> pd.DataFrame:
    return load_dataset("historical_player_gw").copy()


@lru_cache(maxsize=1)
def bootstrap_static() -> dict[str, Any]:
    path = RAW_DIR / "bootstrap-static.json"
    if not path.exists():
        logging.warning("Bootstrap data file is missing: %s", path)
        return {}

    with path.open(encoding="utf-8") as file:
        return json.load(file)
