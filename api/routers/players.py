import unicodedata
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from api import data_service
from api.player_signals import add_safety_tiers

router = APIRouter(prefix="/api/players", tags=["players"])

PLAYER_COLUMN_MAP = {
    "element_id": "element_id",
    "player_name": "name",
    "web_name": "web_name",
    "team_name": "team",
    "team_code": "team_code",
    "position": "position",
    "price": "price",
    "total_points": "total_points",
    "points_per_game": "ppg",
    "form": "form",
    "minutes_security": "start_likelihood",
    "value_score": "value",
    "captain_score": "captain_score",
    "transfer_score": "transfer_score",
    "selected_by_percent": "selected_by_percent",
    "defensive_contribution": "defensive_contribution",
    "defensive_contribution_per_90": "defensive_contribution_per_90",
    "safety_tier": "safety_tier",
}

NUMERIC_COLUMNS = data_service.PLAYERS_RANKED_NUMERIC_COLUMNS

RECENT_FORM_WINDOW = 3


def _load_players() -> tuple[Any, list[str]]:
    dataframe = data_service.players()
    if dataframe.empty:
        return dataframe, []

    dataframe = _add_element_ids(dataframe)
    dataframe = _add_team_codes(dataframe)

    for column in NUMERIC_COLUMNS:
        if column in dataframe.columns:
            dataframe[column] = pd.to_numeric(
                dataframe[column].astype(str).str.rstrip("%"),
                errors="coerce",
            )
    existing_numeric_columns = [column for column in NUMERIC_COLUMNS if column in dataframe.columns]
    dataframe[existing_numeric_columns] = dataframe[existing_numeric_columns].fillna(0)
    dataframe = _add_historical_form_fallback(dataframe)
    dataframe = add_safety_tiers(dataframe)
    available_columns = list(dataframe.columns)
    missing = [column for column in PLAYER_COLUMN_MAP if column not in dataframe.columns]
    if missing:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "players_ranked.csv is missing required columns.",
                "missing_columns": missing,
                "available_columns": available_columns,
            },
        )
    return dataframe, available_columns


def _plain_player_columns(dataframe):
    output = dataframe.rename(columns=PLAYER_COLUMN_MAP)
    columns = [column for column in PLAYER_COLUMN_MAP.values() if column in output.columns]
    return output[columns]


def _add_team_codes(dataframe):
    if "team_code" in dataframe.columns:
        return dataframe

    bootstrap = data_service.bootstrap_static()
    teams = bootstrap.get("teams", [])
    code_by_name = {team.get("name"): team.get("code") for team in teams}
    code_by_short = {team.get("short_name"): team.get("code") for team in teams}
    dataframe["team_code"] = dataframe["team_name"].map(code_by_name)
    if "team_short_name" in dataframe.columns:
        dataframe["team_code"] = dataframe["team_code"].fillna(
            dataframe["team_short_name"].map(code_by_short)
        )
    dataframe["team_code"] = dataframe["team_code"].fillna(1).astype(int)
    return dataframe


def _add_element_ids(dataframe):
    if "element_id" in dataframe.columns:
        return dataframe

    bootstrap = data_service.bootstrap_static()
    teams = bootstrap.get("teams", [])
    team_by_id = {team.get("id"): team for team in teams}
    exact: dict[tuple[str, str], int] = {}
    name_only: dict[str, int | None] = {}

    for player in bootstrap.get("elements", []):
        team = team_by_id.get(player.get("team"), {})
        short = _normalize(team.get("short_name"))
        full_name = f"{player.get('first_name', '')} {player.get('second_name', '')}".strip()
        names = {_normalize(full_name), _normalize(player.get("web_name"))}
        for name in names:
            if not name:
                continue
            exact[(name, short)] = player.get("id")
            name_only[name] = player.get("id") if name not in name_only else None

    def lookup(row: pd.Series) -> int | None:
        row_names = [
            _normalize(row.get("player_name")),
            _normalize(row.get("web_name")),
        ]
        row_teams = [
            _normalize(row.get("team_short_name")),
            _normalize(row.get("team_name")),
        ]
        for row_name in row_names:
            for row_team in row_teams:
                found = exact.get((row_name, row_team))
                if found is not None:
                    return found
        for row_name in row_names:
            found = name_only.get(row_name)
            if found is not None:
                return found
        return None

    dataframe["element_id"] = dataframe.apply(lookup, axis=1)
    return dataframe


def _add_historical_form_fallback(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Fill an empty API form snapshot from the player's latest three GWs.

    The FPL API's form field is sometimes empty early in a season or in a
    stale local snapshot. It must remain a short-term metric, so this fallback
    deliberately uses only the latest three rows for each player in the latest
    season. Season totals are never used to derive form.
    """
    if "form" not in dataframe.columns or dataframe["form"].max() > 0:
        return dataframe

    history = data_service.historical_player_gw()
    if history.empty or "total_points" not in history.columns or "season" not in history.columns:
        return dataframe

    latest_season = history["season"].dropna().max()
    season_history = history[history["season"] == latest_season].copy()
    if season_history.empty:
        return dataframe

    season_history["gameweek"] = pd.to_numeric(season_history["gameweek"], errors="coerce")
    season_history["total_points"] = pd.to_numeric(
        season_history["total_points"], errors="coerce"
    )
    season_history = season_history.dropna(subset=["gameweek", "total_points"])
    if season_history.empty:
        return dataframe

    # Tail per player rather than filtering from one global latest GW. This
    # preserves a player's latest available history when a fixture is missed.
    recent = season_history.sort_values("gameweek")
    recent_by_id: dict[Any, float] = {}
    if "player_id" in recent.columns:
        recent_by_id = (
            recent.dropna(subset=["player_id"])
            .groupby("player_id", sort=False)
            .tail(RECENT_FORM_WINDOW)
            .groupby("player_id")["total_points"]
            .mean()
            .to_dict()
        )

    recent_by_name: dict[str, float] = {}
    if "player_name" in recent.columns:
        recent["player_key"] = recent["player_name"].map(_normalize)
        recent_by_name = (
            recent[recent["player_key"] != ""]
            .groupby("player_key", sort=False)
            .tail(RECENT_FORM_WINDOW)
            .groupby("player_key")["total_points"]
            .mean()
            .to_dict()
        )

    current_ids = pd.to_numeric(dataframe["element_id"], errors="coerce")
    form = current_ids.map(recent_by_id)
    names = dataframe["player_name"].map(_normalize)
    form = form.fillna(names.map(recent_by_name))
    dataframe["form"] = form.fillna(0.0)
    return dataframe


def _normalize(value: Any) -> str:
    text = str(value or "").strip().casefold()
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def _captain_reasoning(row: pd.Series, rank: int) -> str:
    if rank == 1:
        return "Highest predicted score"
    if row.get("minutes_security", 0) > 0.9 and row.get("form", 0) > 7:
        return "Nailed starter, red-hot form"
    if row.get("minutes_security", 0) > 0.9:
        return "Near-certain starter"
    if row.get("form", 0) > 7:
        return "Excellent recent form"
    return "Strong overall metrics"


@router.get("")
def get_players(
    position: str | None = Query(default=None),
    sort_by: str = Query(default="captain_score"),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[dict[str, Any]]:
    dataframe, _ = _load_players()
    if dataframe.empty:
        return []

    if position:
        dataframe = dataframe[dataframe["position"].str.casefold() == position.casefold()]

    output = _plain_player_columns(dataframe)
    if sort_by not in output.columns:
        raise HTTPException(
            status_code=400,
            detail=f"sort_by must be one of: {', '.join(output.columns)}",
        )

    output = output.sort_values(sort_by, ascending=False).head(limit)
    return data_service.to_records(output)


@router.get("/captains")
def captains() -> list[dict[str, Any]]:
    dataframe, _ = _load_players()
    if dataframe.empty:
        return []

    ranked = dataframe.sort_values("captain_score", ascending=False).head(10).copy()
    ranked["reasoning"] = [
        _captain_reasoning(row, index + 1) for index, (_, row) in enumerate(ranked.iterrows())
    ]
    output = _plain_player_columns(ranked)
    output["reasoning"] = ranked["reasoning"].values
    return data_service.to_records(output)


@router.get("/transfers")
def transfers() -> list[dict[str, Any]]:
    dataframe, _ = _load_players()
    if dataframe.empty:
        return []

    dataframe["rotation_risk"] = dataframe["minutes_security"] < 0.4
    output = dataframe.sort_values("transfer_score", ascending=False).head(20)
    output = _plain_player_columns(output)
    output["rotation_risk"] = dataframe.loc[output.index, "rotation_risk"].astype(bool)
    return data_service.to_records(output)


@router.get("/differentials")
def differentials() -> list[dict[str, Any]]:
    dataframe, _ = _load_players()
    if dataframe.empty:
        return []

    output = dataframe[dataframe["selected_by_percent"] < 15]
    output = _plain_player_columns(output.sort_values("captain_score", ascending=False).head(10))
    return data_service.to_records(output)


@router.get("/{name}/history")
def player_history(name: str) -> list[dict[str, Any]]:
    history = data_service.historical_player_gw()
    if history.empty:
        return []

    needle = name.casefold()
    filtered = history[
        (history["season"] == "2025-26")
        & (history["player_name"].astype(str).str.casefold().str.contains(needle, na=False))
    ].copy()
    if filtered.empty:
        return []

    filtered = filtered.sort_values("gameweek").tail(10)
    output = filtered.rename(columns={"gameweek": "gw"})
    output = output.rename(columns={"player_id": "element_id"})
    columns = ["element_id", "gw", "price", "total_points", "minutes", "selected_by_percent"]
    return data_service.to_records(output[columns])
