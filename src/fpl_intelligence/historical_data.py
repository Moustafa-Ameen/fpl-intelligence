from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_HISTORICAL_DIR = PROJECT_ROOT / "data" / "raw" / "historical"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
HISTORICAL_PLAYER_GW_PATH = PROCESSED_DATA_DIR / "historical_player_gw.csv"

SEASONS = ["2023-24", "2024-25", "2025-26"]

SOURCE_FILES = {
    season: {
        "merged_gw": RAW_HISTORICAL_DIR / season / "merged_gw.csv",
        "teams": RAW_HISTORICAL_DIR / season / "teams.csv",
    }
    for season in SEASONS
}

RELEVANT_COLUMN_EXPLANATIONS = {
    "season": "FPL season the row came from.",
    "player_id": "Vaastav/FPL player identifier from the element column.",
    "player_name": "Player name from Vaastav's per-gameweek row.",
    "gameweek": "The target gameweek being predicted.",
    "feature_cutoff_gameweek": "Last completed gameweek allowed in rolling features.",
    "price": "FPL price for the target gameweek, converted from value / 10.",
    "position": "FPL position abbreviation such as GK, DEF, MID, or FWD.",
    "team": "Player's team in that gameweek.",
    "opponent_team": "Opponent team name mapped from the opponent_team id.",
    "opponent_strength": "Opponent overall strength for the venue they are playing in.",
    "home_or_away": "H if the player is at home, A if away.",
    "selected_by_percent": "Estimated ownership percentage for that gameweek.",
    "minutes": "Actual minutes played in the target gameweek.",
    "total_points": "Actual FPL points scored in the target gameweek.",
    "minutes_last_3": "Sum of minutes from the player's previous three gameweeks only.",
    "points_last_3": "Sum of points from the player's previous three gameweeks only.",
    "prior_games_available_last_3": "Count of prior player-gameweek rows available in the window.",
    "next_gameweek_points": "Prediction target: actual total_points in the target gameweek.",
}


def combine_unique_text(values: pd.Series) -> str:
    unique_values = sorted(str(value) for value in values.dropna().unique())
    return "+".join(unique_values)


def combine_home_away(values: pd.Series) -> str:
    unique_values = sorted(str(value) for value in values.dropna().unique())
    if len(unique_values) == 1:
        return unique_values[0]

    return "M"


def load_historical_raw(seasons: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    selected_seasons = seasons or SEASONS
    gameweek_frames = []
    team_frames = []

    for season in selected_seasons:
        files = SOURCE_FILES[season]
        gameweeks = pd.read_csv(files["merged_gw"])
        teams = pd.read_csv(files["teams"])

        gameweeks["season"] = season
        teams["season"] = season

        gameweek_frames.append(gameweeks)
        team_frames.append(teams)

    return pd.concat(gameweek_frames, ignore_index=True), pd.concat(team_frames, ignore_index=True)


def print_raw_structure(gameweeks: pd.DataFrame) -> None:
    print("Raw Vaastav merged_gw.csv columns:")
    print(", ".join(gameweeks.columns))

    print("\nRelevant columns:")
    for column, explanation in RELEVANT_COLUMN_EXPLANATIONS.items():
        if column in {"feature_cutoff_gameweek", "price", "opponent_strength", "home_or_away"}:
            source_note = "derived"
        elif column == "player_id":
            source_note = "from element"
        elif column == "player_name":
            source_note = "from name"
        elif column == "gameweek":
            source_note = "from GW"
        elif column == "selected_by_percent":
            source_note = "derived from selected / estimated managers"
        elif column == "next_gameweek_points":
            source_note = "from total_points"
        else:
            source_note = "raw or rolling"
        print(f"- {column}: {explanation} ({source_note})")


def build_opponent_lookup(teams: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "season",
        "id",
        "name",
        "strength_overall_home",
        "strength_overall_away",
    ]
    return teams[columns].rename(
        columns={
            "id": "opponent_team_id",
            "name": "opponent_team",
        }
    )


def add_selected_by_percent(gameweeks: pd.DataFrame) -> pd.DataFrame:
    ranked = gameweeks.copy()
    estimated_managers = ranked.groupby(["season", "GW"])["selected"].transform("sum") / 15
    ranked["selected_by_percent"] = (ranked["selected"] / estimated_managers * 100).fillna(0)
    return ranked


def add_rolling_features(players: pd.DataFrame) -> pd.DataFrame:
    sorted_players = players.sort_values(["season", "player_id", "gameweek"]).copy()
    grouped = sorted_players.groupby(["season", "player_id"], group_keys=False)

    sorted_players["minutes_last_3"] = grouped["minutes"].transform(
        lambda series: series.shift(1).rolling(window=3, min_periods=1).sum()
    )
    sorted_players["points_last_3"] = grouped["total_points"].transform(
        lambda series: series.shift(1).rolling(window=3, min_periods=1).sum()
    )
    sorted_players["prior_games_available_last_3"] = grouped["total_points"].transform(
        lambda series: series.shift(1).rolling(window=3, min_periods=1).count()
    )

    columns_to_fill = ["minutes_last_3", "points_last_3", "prior_games_available_last_3"]
    sorted_players[columns_to_fill] = sorted_players[columns_to_fill].fillna(0)

    return sorted_players


def aggregate_fixture_rows_to_gameweeks(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    aggregated = (
        fixture_rows.groupby(["season", "player_id", "gameweek"], as_index=False)
        .agg(
            player_name=("player_name", "first"),
            feature_cutoff_gameweek=("feature_cutoff_gameweek", "first"),
            price=("price", "last"),
            position=("position", "first"),
            team=("team", "first"),
            opponent_team=("opponent_team", combine_unique_text),
            opponent_strength=("opponent_strength", "mean"),
            home_or_away=("home_or_away", combine_home_away),
            selected_by_percent=("selected_by_percent", "max"),
            minutes=("minutes", "sum"),
            total_points=("total_points", "sum"),
            next_gameweek_points=("next_gameweek_points", "sum"),
        )
        .sort_values(["season", "gameweek", "player_id"])
        .reset_index(drop=True)
    )
    return aggregated


def build_historical_player_gameweeks(gameweeks: pd.DataFrame, teams: pd.DataFrame) -> pd.DataFrame:
    source = add_selected_by_percent(gameweeks)
    source["opponent_team_id"] = source["opponent_team"]
    source = source.drop(columns=["opponent_team"])
    opponents = build_opponent_lookup(teams)

    merged = source.merge(
        opponents,
        left_on=["season", "opponent_team_id"],
        right_on=["season", "opponent_team_id"],
        how="left",
    )

    merged["player_id"] = merged["element"]
    merged["player_name"] = merged["name"]
    merged["gameweek"] = merged["GW"]
    merged["feature_cutoff_gameweek"] = merged["gameweek"] - 1
    merged["price"] = merged["value"] / 10
    merged["home_or_away"] = merged["was_home"].map({True: "H", False: "A"})
    merged["opponent_strength"] = merged.apply(
        lambda row: row["strength_overall_away"]
        if row["was_home"]
        else row["strength_overall_home"],
        axis=1,
    )
    merged["next_gameweek_points"] = merged["total_points"]

    columns = [
        "season",
        "player_id",
        "player_name",
        "gameweek",
        "feature_cutoff_gameweek",
        "price",
        "position",
        "team",
        "opponent_team",
        "opponent_strength",
        "home_or_away",
        "selected_by_percent",
        "minutes",
        "total_points",
        "next_gameweek_points",
    ]

    fixture_rows = merged[columns].copy()
    clean = aggregate_fixture_rows_to_gameweeks(fixture_rows)
    clean = add_rolling_features(clean)

    final_columns = [
        "season",
        "player_id",
        "player_name",
        "gameweek",
        "feature_cutoff_gameweek",
        "price",
        "position",
        "team",
        "opponent_team",
        "opponent_strength",
        "home_or_away",
        "selected_by_percent",
        "minutes_last_3",
        "points_last_3",
        "prior_games_available_last_3",
        "minutes",
        "total_points",
        "next_gameweek_points",
    ]
    return (
        clean[final_columns]
        .sort_values(["season", "gameweek", "player_id"])
        .reset_index(drop=True)
    )


def save_historical_player_gameweeks(
    players: pd.DataFrame,
    path: Path = HISTORICAL_PLAYER_GW_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    players.to_csv(path, index=False)


def print_sanity_checks(players: pd.DataFrame) -> None:
    print("\nSanity checks:")
    print(f"- Row count: {len(players):,}")
    print(
        "- Season/gameweek range: "
        f"{players['season'].min()} GW{players['gameweek'].min()} to "
        f"{players['season'].max()} GW{players['gameweek'].max()}"
    )
    print(
        "- Rolling window convention: raw fixture rows are first aggregated to one row per "
        "player-gameweek. For target gameweek N, minutes_last_3 and points_last_3 sum "
        "player-gameweeks N-3 through N-1 only; gameweek N is never included."
    )
    print(
        "- Early gameweeks: missing prior history is filled with 0, and "
        "prior_games_available_last_3 shows how much history existed."
    )
    print(
        "- Target mapping: each row's features are for the target gameweek shown; "
        "next_gameweek_points is the actual total_points in that target gameweek."
    )

    sample_columns = [
        "season",
        "player_id",
        "player_name",
        "gameweek",
        "feature_cutoff_gameweek",
        "minutes_last_3",
        "points_last_3",
        "minutes",
        "total_points",
        "next_gameweek_points",
    ]
    sample = players[
        (players["season"] == "2024-25") & (players["prior_games_available_last_3"] >= 3)
    ].head(5)
    print("\nSample rows with full 3-gameweek history:")
    print(sample[sample_columns].to_string(index=False))


def main() -> None:
    print("Historical source: vaastav/Fantasy-Premier-League")
    print("Pulled seasons: 2023-24, 2024-25, and 2025-26.")
    print(
        "Reason: 2025-26 is the most recent complete Vaastav season available locally for a clean "
        "future backtest; 2023-24 and 2024-25 add prior history for later "
        "chronological experiments."
    )

    gameweeks, teams = load_historical_raw()
    print_raw_structure(gameweeks)

    players = build_historical_player_gameweeks(gameweeks, teams)
    save_historical_player_gameweeks(players)
    print_sanity_checks(players)
    print(f"\nSaved historical player-gameweek table to {HISTORICAL_PLAYER_GW_PATH}")


if __name__ == "__main__":
    main()
