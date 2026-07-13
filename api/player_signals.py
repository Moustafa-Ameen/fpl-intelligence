"""Rule-based live player signals that sit on top of model output."""

from __future__ import annotations

import pandas as pd

# These are deliberately named thresholds so the live signal remains explainable.
# A 0.75 minutes-security floor represents a regular starter in this snapshot.
SAFE_MINUTES_SECURITY = 0.75
SAFE_ATTACKING_MINUTES_SECURITY = 0.85
SAFE_DEFCON_PEER_PERCENTILE = 0.75
RISKY_MINUTES_SECURITY = 0.60
RISKY_UPSIDE_SCORE = 0.45
RISKY_OWNERSHIP_PERCENT = 25.0
RISKY_PREMIUM_PRICE = 8.0
OUTFIELD_POSITIONS = {"DEF", "MID", "FWD"}


def _position_group(value: object) -> str:
    position = str(value or "").upper()
    aliases = {"GOALKEEPER": "GK", "DEFENDER": "DEF", "MIDFIELDER": "MID", "FORWARD": "FWD"}
    return aliases.get(position, position)


def add_safety_tiers(players: pd.DataFrame) -> pd.DataFrame:
    """Add a position-aware ``safety_tier`` to a live ranked player table.

    ``Safe`` requires reliable minutes plus either a top-quartile defensive
    contribution rate within the player's position or, for attacking players,
    a higher minutes-only floor. ``Risky`` is reserved for high-upside players
    with weak minutes security or expensive, highly-owned players without a
    proven nailed-on status. Neutral players are intentionally left untagged.
    """

    ranked = players.copy()
    ranked["position_group"] = ranked["position"].map(_position_group)
    for column in [
        "minutes_security",
        "defensive_contribution",
        "defensive_contribution_per_90",
        "captain_score",
        "transfer_score",
        "selected_by_percent",
        "price",
    ]:
        if column not in ranked:
            ranked[column] = 0.0
        ranked[column] = pd.to_numeric(ranked[column], errors="coerce").fillna(0.0)

    peer_percentile = (
        ranked.groupby("position_group")["defensive_contribution_per_90"]
        .rank(pct=True, method="average")
        .fillna(0.0)
    )
    has_defcon_signal = ranked["defensive_contribution_per_90"] > 0
    high_defcon = (
        ranked["position_group"].isin(OUTFIELD_POSITIONS)
        & has_defcon_signal
        & (peer_percentile >= SAFE_DEFCON_PEER_PERCENTILE)
    )
    high_minutes = ranked["minutes_security"] >= SAFE_MINUTES_SECURITY
    attacking_minutes = (
        ranked["position_group"].isin({"MID", "FWD"})
        & (ranked["minutes_security"] >= SAFE_ATTACKING_MINUTES_SECURITY)
    )
    safe = high_minutes & (high_defcon | attacking_minutes)

    upside = ranked[["captain_score", "transfer_score"]].max(axis=1)
    upside_risk = (upside >= RISKY_UPSIDE_SCORE) & (
        ranked["minutes_security"] < RISKY_MINUTES_SECURITY
    )
    premium_ownership_risk = (
        (ranked["selected_by_percent"] >= RISKY_OWNERSHIP_PERCENT)
        & (ranked["price"] >= RISKY_PREMIUM_PRICE)
        & (ranked["minutes_security"] < SAFE_MINUTES_SECURITY)
    )
    risky = ~safe & (upside_risk | premium_ownership_risk)
    ranked["safety_tier"] = ""
    ranked.loc[safe, "safety_tier"] = "Safe"
    ranked.loc[risky, "safety_tier"] = "Risky"
    return ranked.drop(columns=["position_group"])
