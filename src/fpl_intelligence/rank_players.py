from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLAYERS_CURRENT_PATH = PROJECT_ROOT / "data" / "processed" / "players_current.csv"
PLAYERS_RANKED_PATH = PROJECT_ROOT / "data" / "processed" / "players_ranked.csv"

FORMULA_EXPLANATIONS = {
    "minutes_security": (
        "minutes / max_minutes_in_dataset, clipped to 0-1. This approximates how nailed-on a "
        "player has been across the season, but it cannot see recent rotation until Step 3 adds "
        "per-gameweek data."
    ),
    "ownership_risk": (
        "1 - selected_by_percent / 100. I treat low ownership as higher risk because differentials "
        "often carry uncertainty around minutes, role, team strength, or proven FPL output."
    ),
    "captain_score": (
        "0.50 * points_per_game_norm + 0.30 * form_norm + 0.20 * minutes_security. Captaincy "
        "prioritizes scoring rate, then current form, then reliable minutes."
    ),
    "transfer_score": (
        "0.70 * value_score_norm + 0.20 * form_norm - 0.10 * ownership_risk. Transfers prioritize "
        "value, reward form, and apply a small penalty for low-ownership risk."
    ),
}


def normalize(series: pd.Series) -> pd.Series:
    max_value = series.max()
    if pd.isna(max_value) or max_value == 0:
        return pd.Series(0.0, index=series.index)

    return series / max_value


def load_current_players(path: Path = PLAYERS_CURRENT_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def add_rule_based_scores(players: pd.DataFrame) -> pd.DataFrame:
    ranked = players.copy()

    max_minutes = ranked["minutes"].max()
    ranked["minutes_security"] = (ranked["minutes"] / max_minutes).clip(lower=0, upper=1)
    ranked["ownership_risk"] = (1 - ranked["selected_by_percent"] / 100).clip(lower=0, upper=1)

    points_per_game_norm = normalize(ranked["points_per_game"])
    form_norm = normalize(ranked["form"])
    value_score_norm = normalize(ranked["value_score"])

    ranked["captain_score"] = (
        0.50 * points_per_game_norm + 0.30 * form_norm + 0.20 * ranked["minutes_security"]
    )
    ranked["transfer_score"] = (
        0.70 * value_score_norm + 0.20 * form_norm - 0.10 * ranked["ownership_risk"]
    )

    return ranked


def save_ranked_players(players: pd.DataFrame, path: Path = PLAYERS_RANKED_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    players.to_csv(path, index=False)


def print_formula_explanations() -> None:
    print("Step 2 rule-based formulas:")
    for column, explanation in FORMULA_EXPLANATIONS.items():
        print(f"- {column}: {explanation}")


def print_top_rankings(players: pd.DataFrame, sort_column: str, limit: int = 10) -> None:
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
        "minutes_security",
        "ownership_risk",
        sort_column,
    ]
    top_players = players.sort_values(sort_column, ascending=False).head(limit)

    print(f"\nTop {limit} players by {sort_column}:")
    print(top_players[display_columns].to_string(index=False))


def find_sanity_warnings(players: pd.DataFrame) -> list[str]:
    warnings = []
    if players["form"].max() == 0:
        warnings.append(
            "All form values are 0 in the current API snapshot, so form does not affect today's "
            "captain_score or transfer_score rankings."
        )

    top_captains = players.sort_values("captain_score", ascending=False).head(10)
    low_minutes_captains = top_captains[top_captains["minutes_security"] < 0.50]
    if not low_minutes_captains.empty:
        names = ", ".join(low_minutes_captains["player_name"].tolist())
        warnings.append(f"Low-minutes players appear in the captain top 10: {names}.")

    top_transfers = players.sort_values("transfer_score", ascending=False).head(10)
    low_minutes_transfers = top_transfers[top_transfers["minutes_security"] < 0.50]
    if not low_minutes_transfers.empty:
        names = ", ".join(low_minutes_transfers["player_name"].tolist())
        warnings.append(
            f"Low-minutes players appear in the transfer top 10: {names}. This can happen because "
            "transfer_score is value-heavy."
        )

    return warnings


def main() -> None:
    players = load_current_players()
    ranked_players = add_rule_based_scores(players)

    print_formula_explanations()
    print_top_rankings(ranked_players, "captain_score")
    print_top_rankings(ranked_players, "transfer_score")

    warnings = find_sanity_warnings(ranked_players)
    print("\nSanity notes:")
    if warnings:
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("- No obvious low-minutes outliers appeared in the top 10 rankings.")

    save_ranked_players(ranked_players)
    print(f"\nSaved ranked player table to {PLAYERS_RANKED_PATH}")


if __name__ == "__main__":
    main()
