# Phase M8.2 — Fixture Horizon and Scenario Layer

## Status

Implemented and verified. M8.3 chip-specific valuation has not started.

## Delivered

- Added `FixtureScenario`, a deterministic immutable contract for a 3-, 5-, or
  8-Gameweek planning horizon.
- Added canonical fixture normalization and SHA-256 fixture-data hashes.
- Added scenario IDs derived from season, cutoff, horizon, source, and fixture
  payload hash.
- Added fixture status classification for confirmed, uncertain, postponed, and
  rescheduled fixtures.
- Added team fixture counts, blank-Gameweek counts, and Double-Gameweek counts.
- Connected optional scenario metadata to the existing multi-Gameweek projection
  functions without changing their default output contract.
- Extended point-in-time future prediction requests to support every offset
  inside the 3/5/8 planning horizons. Chip-enabled benchmark runs request all
  offsets from 1 through 8 so an 8-Gameweek valuation is contiguous.
- Added per-Gameweek benchmark scenario IDs, fixture hashes, horizon, cutoff,
  and schedule-status counts to the persisted decision rows.
- Historical scenarios use raw fixture rows and deduplicate the two player/team
  perspectives into one fixture. This preserves genuine blanks and doubles.

## Verification

- Focused M8.2 tests: `7 passed`.
- Full pytest: `110 passed`.
- Ruff: clean.
- Historical fixture reconciliation: 80 unique fixtures across the first eight
  2023/24 Gameweeks, including the observed blank/double pattern.
- No-chip deterministic control remains unchanged: 2023/24 produced 2,320
  hindsight points and 2,119 realistic points, with 32 transfers and zero hits.

## Limitations carried forward

Historical raw files provide the final schedule but not timestamped fixture
snapshots. Historical fixtures therefore remain explicitly `uncertain` for
point-in-time certainty classification; this prevents the backtest from
claiming that a final schedule was known before the original deadline. Live
snapshots can provide confirmed, postponed, and rescheduled status when those
fields are available.

The chip planner still uses the provisional immediate-projection valuation.
Multi-Gameweek scenario data is now available for the next phase, but it is not
yet used to promote or select chips. M8.3 must implement and validate that
chip-specific valuation.
