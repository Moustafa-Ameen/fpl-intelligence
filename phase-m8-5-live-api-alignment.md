# Phase M8.5 — Live/API Chip Alignment

## Status

Implemented and regression-tested. The live chip recommendation endpoint now
uses the same deterministic beam-search decision engine as the benchmark.
M8.5 is not a production-performance promotion: the planner remains
experimental/provisional until the later multi-season decision-quality gates
pass. M9 has not started.

## Delivered

- Added a live adapter from bootstrap, team picks, bank, free transfers, chip
  history, rules manifests, and multi-gameweek projections into the typed
  benchmark decision state.
- Replaced the `/api/chip-tips` primary recommendation path's independent
  Bench Boost/Wildcard heuristic with `chip_mode="beam_search"`.
- Preserved the former squad-relative alerts as explanatory signals only; they
  no longer override the optimizer recommendation.
- Added live output for:
  - use/save decision;
  - chip key and slot;
  - target Gameweek;
  - immediate and horizon expected gain;
  - expected points with and without the chip;
  - uncertainty penalty and downside range;
  - confidence level;
  - ordinary-transfer interaction;
  - best projected future alternative;
  - remaining and used chips;
  - model version, rules version, payload hash, and data cutoff.
- Added projection-frame normalization, including stable player IDs, team IDs,
  FPL position normalization, price, expected points, and minutes probability.
- Added horizon-level expected-point fields to beam actions so live and
  benchmark consumers use the same current-versus-future accounting.
- Updated the frontend chip page to show the optimizer recommendation,
  uncertainty, confidence, transfer interaction, alternative opportunity, and
  provenance.

## Verification

- Focused backend/API/beam/chip suite: `52 passed`.
- Ruff: clean.
- Python diff check: clean; only normal Windows line-ending warnings remain.
- Frontend ESLint: clean.
- Frontend TypeScript: clean.
- Live recommendation tests cover chip-state reconstruction, position and
  projection normalization, use decisions, save decisions, horizon gains, and
  provenance metadata.

## Safety boundaries

- The endpoint remains recommendation-only; it never executes transfers or
  chips.
- The live planner only receives projections generated from the current live
  cutoff and does not use realized future points.
- Wildcard and Free Hit transfer interaction remains governed by the shared
  chip legality rules.
- The output is not a top-1% guarantee and does not promote the beam planner
  to production by itself.
