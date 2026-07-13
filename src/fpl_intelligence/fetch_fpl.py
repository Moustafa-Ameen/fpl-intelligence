from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import requests

FPL_BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
BOOTSTRAP_PATH = RAW_DATA_DIR / "bootstrap-static.json"
PLAYERS_CURRENT_PATH = PROCESSED_DATA_DIR / "players_current.csv"

TOP_LEVEL_KEY_DESCRIPTIONS = {
    "chips": "FPL chip definitions such as wildcard, bench boost, free hit, and triple captain.",
    "events": "Gameweek metadata, including deadlines, status, and highest-scoring player ids.",
    "game_settings": "Global game rules and limits such as squad size and league settings.",
    "game_config": "Scoring rules and configurable settings used by the FPL game.",
    "phases": "Season phases used by FPL for overall and monthly periods.",
    "teams": "Premier League teams, ids, names, strengths, and fixture difficulty fields.",
    "total_players": "Total number of registered FPL managers.",
    "element_stats": "Definitions for player statistic fields shown by FPL.",
    "element_types": "Position definitions: goalkeeper, defender, midfielder, and forward.",
    "elements": "Player records, including prices, points, form, minutes, ownership, and team ids.",
}

COLUMN_EXPLANATIONS = {
    "player_name": "Full player name built from first_name and second_name.",
    "web_name": "Short display name used by FPL.",
    "team_name": "Human-readable club name mapped from the player's team id.",
    "team_short_name": "Three-letter club abbreviation mapped from the player's team id.",
    "position": "Human-readable FPL position mapped from the player's element_type id.",
    "price": "Current FPL price converted from now_cost, where 105 becomes 10.5.",
    "total_points": "Total FPL points the player has scored in the current dataset.",
    "points_per_game": "Average FPL points per appearance as reported by FPL.",
    "form": "Recent form value as reported by FPL.",
    "minutes": "Total Premier League minutes played in the current dataset.",
    "selected_by_percent": "Percentage of FPL managers currently owning the player.",
    "value_score": "Simple value metric: total_points divided by current price.",
    "defensive_contribution": (
        "Season-total FPL points awarded for meeting the defensive contribution threshold."
    ),
    "defensive_contribution_per_90": (
        "Defensive actions per 90 minutes: clearances, blocks, interceptions, tackles, and "
        "recoveries combined under the current FPL Defensive Contributions rule."
    ),
}


def fetch_json(url: str) -> dict[str, Any]:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def save_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_bootstrap_data(path: Path = BOOTSTRAP_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def describe_bootstrap_structure(bootstrap_data: dict[str, Any]) -> list[str]:
    descriptions = []
    for key, value in bootstrap_data.items():
        description = TOP_LEVEL_KEY_DESCRIPTIONS.get(key, "No description available yet.")
        if isinstance(value, list):
            shape = f"list with {len(value)} records"
        elif isinstance(value, dict):
            shape = f"dictionary with {len(value)} keys"
        else:
            shape = type(value).__name__

        descriptions.append(f"- {key}: {shape}. {description}")

    return descriptions


def load_players(bootstrap_data: dict[str, Any]) -> pd.DataFrame:
    players = pd.DataFrame(bootstrap_data["elements"])
    teams = pd.DataFrame(bootstrap_data["teams"])[["id", "name", "short_name"]].rename(
        columns={
            "id": "team_id",
            "name": "team_name",
            "short_name": "team_short_name",
        }
    )
    positions = pd.DataFrame(bootstrap_data["element_types"])[["id", "singular_name"]].rename(
        columns={
            "id": "position_id",
            "singular_name": "position",
        }
    )

    players = players.merge(
        teams,
        left_on="team",
        right_on="team_id",
        how="left",
    )
    players = players.merge(
        positions,
        left_on="element_type",
        right_on="position_id",
        how="left",
    )

    players["price"] = players["now_cost"] / 10
    players["player_name"] = players["first_name"] + " " + players["second_name"]
    players["points_per_game"] = pd.to_numeric(players["points_per_game"], errors="coerce")
    players["form"] = pd.to_numeric(players["form"], errors="coerce")
    players["selected_by_percent"] = pd.to_numeric(players["selected_by_percent"], errors="coerce")
    for column in ["defensive_contribution", "defensive_contribution_per_90"]:
        if column in players:
            players[column] = pd.to_numeric(players[column], errors="coerce").fillna(0.0)
        else:
            players[column] = 0.0
    players["value_score"] = players["total_points"] / players["price"]

    columns = list(COLUMN_EXPLANATIONS)
    return players[columns].sort_values("total_points", ascending=False).reset_index(drop=True)


def save_players(players: pd.DataFrame, path: Path = PLAYERS_CURRENT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    players.to_csv(path, index=False)


def print_column_explanations() -> None:
    print("\nClean player table columns:")
    for column, explanation in COLUMN_EXPLANATIONS.items():
        print(f"- {column}: {explanation}")


def print_top_players(players: pd.DataFrame, sort_column: str, limit: int = 10) -> None:
    display_columns = [
        "player_name",
        "team_name",
        "position",
        "price",
        "total_points",
        "points_per_game",
        "form",
        "minutes",
        "selected_by_percent",
        "value_score",
    ]

    top_players = players.sort_values(sort_column, ascending=False).head(limit)
    print(f"\nTop {limit} players by {sort_column}:")
    print(top_players[display_columns].to_string(index=False))


def main() -> None:
    bootstrap_data = load_bootstrap_data()

    print("bootstrap-static top-level structure:")
    for line in describe_bootstrap_structure(bootstrap_data):
        print(line)

    players = load_players(bootstrap_data)
    print_column_explanations()
    print_top_players(players, "value_score")
    print_top_players(players, "total_points")
    save_players(players)
    print(f"\nSaved cleaned player table to {PLAYERS_CURRENT_PATH}")


if __name__ == "__main__":
    main()
