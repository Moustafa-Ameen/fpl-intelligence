from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import requests

FPL_BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def fetch_json(url: str) -> dict[str, Any]:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def save_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_players(bootstrap_data: dict[str, Any]) -> pd.DataFrame:
    players = pd.DataFrame(bootstrap_data["elements"])
    teams = pd.DataFrame(bootstrap_data["teams"])[["id", "name", "short_name"]]
    positions = pd.DataFrame(bootstrap_data["element_types"])[["id", "singular_name_short"]]

    players = players.merge(
        teams,
        left_on="team",
        right_on="id",
        how="left",
        suffixes=("", "_team"),
    )
    players = players.merge(
        positions,
        left_on="element_type",
        right_on="id",
        how="left",
        suffixes=("", "_position"),
    )

    players["price"] = players["now_cost"] / 10
    players["display_name"] = players["first_name"] + " " + players["second_name"]

    return players


def print_top_players(players: pd.DataFrame, limit: int = 10) -> None:
    columns = [
        "display_name",
        "name",
        "singular_name_short",
        "price",
        "total_points",
        "points_per_game",
        "form",
        "selected_by_percent",
    ]

    top_players = players.sort_values("total_points", ascending=False).head(limit)
    print(top_players[columns].to_string(index=False))


def main() -> None:
    bootstrap_data = fetch_json(FPL_BOOTSTRAP_URL)
    save_json(bootstrap_data, RAW_DATA_DIR / "bootstrap-static.json")

    players = load_players(bootstrap_data)
    print_top_players(players)


if __name__ == "__main__":
    main()
