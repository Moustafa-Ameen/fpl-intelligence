"""Live chip availability derived from the FPL account history and bootstrap."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

CHIP_LABELS = {
    "wildcard": "Wildcard",
    "freehit": "Free Hit",
    "bboost": "Bench Boost",
    "3xc": "Triple Captain",
}


def build_chip_status(
    bootstrap: Mapping[str, Any],
    history: Mapping[str, Any] | None,
    current_gameweek: int,
    *,
    season_state: str = "in_season",
) -> dict[str, Any]:
    """Combine bootstrap chip windows with the team's current-season usage.

    The FPL history endpoint is deliberately ignored when the app is in a
    season-transition state. Chip usage resets with a new season, while the
    bootstrap definitions still provide the next season's window boundaries.
    """

    definitions = _chip_definitions(bootstrap)
    effective_gameweek = current_gameweek if season_state == "in_season" else 1
    used_by_key = _assign_used_chips(
        definitions,
        history.get("chips", []) if season_state == "in_season" and history else [],
    )
    rows = []
    for definition in definitions:
        key = definition["key"]
        used_gameweek = used_by_key.get(key)
        if used_gameweek is not None:
            status = "used"
        elif effective_gameweek < definition["start_event"]:
            status = "not_yet_available"
        elif effective_gameweek > definition["stop_event"]:
            status = "expired"
        else:
            status = "available"
        rows.append(
            {
                **definition,
                "status": status,
                "used_gameweek": used_gameweek,
                "available_from": (
                    definition["start_event"] if status == "not_yet_available" else None
                ),
            }
        )

    return {
        "status": "ready",
        "season_state": season_state,
        "current_gameweek": effective_gameweek,
        "season_reset": season_state != "in_season",
        "message": (
            "Chip usage is live from your FPL account."
            if season_state == "in_season"
            else "Chip usage has been reset for the upcoming season."
        ),
        "chips": rows,
    }


def filter_actionable_chip_alerts(
    alerts: Sequence[Mapping[str, Any]],
    chip_status: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Keep AI alerts actionable against the user's live chip inventory."""

    chips = chip_status.get("chips", [])
    output = []
    for alert in alerts:
        chip_type = _chip_type_from_label(str(alert.get("chip", "")))
        matching = [chip for chip in chips if chip.get("chip_type") == chip_type]
        available = [chip for chip in matching if chip.get("status") == "available"]
        if matching and not available:
            continue
        updated = dict(alert)
        used_count = sum(1 for chip in matching if chip.get("status") == "used")
        if used_count:
            updated["message"] = (
                f"{alert.get('message', '')} One {CHIP_LABELS.get(chip_type, 'chip')} "
                "slot has already been used; this signal applies to the remaining slot."
            )
        output.append(updated)
    return output


def _chip_definitions(bootstrap: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = [
        chip
        for chip in bootstrap.get("chips", [])
        if _chip_type(chip.get("name"))
        and _integer(chip.get("start_event")) is not None
        and _integer(chip.get("stop_event")) is not None
    ]
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for chip in raw:
        grouped.setdefault(_chip_type(chip.get("name")), []).append(chip)

    definitions = []
    for chip_type, group in grouped.items():
        ordered = sorted(
            group,
            key=lambda chip: (
                _integer(chip.get("start_event")) or 0,
                _integer(chip.get("id")) or 0,
            ),
        )
        multiple_windows = len(ordered) > 1
        for index, chip in enumerate(ordered, start=1):
            start_event = _integer(chip.get("start_event")) or 1
            stop_event = _integer(chip.get("stop_event")) or 38
            window = "first half" if index == 1 and multiple_windows else "second half"
            suffix = f" {index}" if multiple_windows else ""
            definitions.append(
                {
                    "key": f"{chip_type}-{index}",
                    "chip_type": chip_type,
                    "name": f"{CHIP_LABELS[chip_type]}{suffix}",
                    "subtitle": (
                        f"{window} · GW {start_event}-{stop_event}"
                        if multiple_windows
                        else f"GW {start_event}-{stop_event}"
                    ),
                    "definition_id": chip.get("id"),
                    "number": index,
                    "start_event": start_event,
                    "stop_event": stop_event,
                    "chip_type_definition": chip.get("chip_type"),
                }
            )
    return sorted(
        definitions,
        key=lambda row: (row["start_event"], row["chip_type"], row["number"]),
    )


def _assign_used_chips(
    definitions: Sequence[Mapping[str, Any]],
    played_chips: Sequence[Mapping[str, Any]],
) -> dict[str, int]:
    assignments: dict[str, int] = {}
    for played in sorted(played_chips, key=lambda row: _integer(row.get("event")) or 0):
        chip_type = _chip_type(played.get("name"))
        gameweek = _integer(played.get("event"))
        if not chip_type or gameweek is None:
            continue
        candidates = [
            definition
            for definition in definitions
            if definition["chip_type"] == chip_type
            and definition["key"] not in assignments
            and definition["start_event"] <= gameweek <= definition["stop_event"]
        ]
        if not candidates:
            continue
        assignments[candidates[0]["key"]] = gameweek
    return assignments


def _chip_type(value: Any) -> str:
    normalized = str(value or "").strip().casefold().replace("_", "")
    return normalized if normalized in CHIP_LABELS else ""


def _chip_type_from_label(value: str) -> str:
    normalized = value.casefold()
    for chip_type, label in CHIP_LABELS.items():
        if label.casefold() in normalized:
            return chip_type
    return ""


def _integer(value: Any) -> int | None:
    try:
        return int(value) if value is not None and value != "" else None
    except (TypeError, ValueError):
        return None
