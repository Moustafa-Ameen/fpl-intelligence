# Phase M8.6 — Beam Correctness and Horizon Valuation

## Status

Implemented and regression-tested. The existing beam architecture was repaired
without introducing the later production MILP/CP-SAT optimizer. The beam is
still experimental and provisional; M9 has not started.

## Delivered

- Wildcard squad construction now aggregates available future projections over
  a six-Gameweek permanent-chip horizon.
- Free Hit, Bench Boost, and Triple Captain valuation retain their shorter
  chip-specific horizons.
- Future Bench Boost and Triple Captain opportunity value is explicitly
  deducted from the current branch score when relevant.
- Chip-squad cache keys now include the branch squad signature, preventing a
  different beam branch from reusing an incompatible squad solution.
- Candidate pruning retains current-squad players, current leaders, future
  leaders, and high-ownership candidates by position.
- Beam lineup scoring no longer repeatedly slices Pandas frames for every
  branch; it uses indexed iteration and cached projection maps.
- Horizon and opportunity-cost metadata is calculated for the root action while
  deeper beam states avoid redundant audit recomputation.
- Every legal root chip branch is exposed through `last_counterfactuals` and
  persisted by the benchmark and live/API adapter.
- The live API now exposes the same root counterfactual fields as the
  benchmark.

## Verification

- Focused beam/recommendation tests: `23 passed` including the full-enumeration
  small-pool pruning oracle.
- Full Python suite: `122 passed`.
- Ruff: clean.
- `git diff --check`: clean apart from normal Windows line-ending warnings.
- Representative real Gameweek runtime: reduced from approximately 65 seconds
  before M8.6 optimization to 24.1 seconds.
- 2023/24 beam run: 412.8 seconds, 2,611 hindsight points and 2,337 realistic
  points.
- 2024/25 beam run: 393.5 seconds, 2,709 hindsight points and 2,489 realistic
  points.
- No-chip controls remained unchanged: 2,119 realistic points in 2023/24 and
  1,903 in 2024/25.

## M8.6.1 Persistence Verification

The canonical multi-season ablation runner now forwards `chip_mode` to each
variant and persists both season summaries and per-Gameweek decision rows. The
decision-row writer also normalizes the season and strategy keys for synthetic
or historical result frames, so a persisted summary cannot silently lack its
audit companion.

Verification at commit `8b69e8a842c62918d541879b3dcf6c837a8d759e`:

- 2023/24 beam track: 2,337 realistic points, 34 transfers, five chips.
- 2024/25 beam track: 2,489 realistic points, 30 transfers, five chips.
- Two persisted chip-aware summary rows and 76 persisted decision rows.
- All 76 decision rows contain counterfactual payloads.
- No duplicate run/season/strategy/Gameweek decision keys.
- No-chip controls still reconcile to 2,119 and 1,903 realistic points.
- Persistence-focused and regression tests pass; Ruff is clean.

### Explicit 2025/26 validation

The 2025/26 season was then run as an explicit deterministic-transfer beam
track using its season-specific rules manifest. The persisted result was:

- 2,378 hindsight points and 2,192 realistic points.
- 32 transfers, no hits, and all eight legal chips used.
- 38 decision rows with no duplicate Gameweeks or missing counterfactuals.
- First-half chip slots used in GW1-GW4 and second-half slots in GW20-GW23.
- No chip used in both GW19 and GW20, and no point-in-time lookahead violations.
- Rules version `2025-26-m6-v3-chips_v3_double_set_2025_26-bps_v1_2025_26`.

The 2025/26 contract reflects the official two-set, eight-chip season, the
2025/26 Defensive Contributions rules, and the separate 2025/26 BPS regime.

## Acceptance interpretation

The correctness and runtime gates pass. The performance-promotion gate does
not pass automatically: the beam remains provisional until later validation
shows repeatable realistic decision-quality improvement across seasons without
severe seasonal or Blank/Double Gameweek regression.

M11 remains a separate future phase. It will build the exact production
optimizer only after M9 and M10 improve the availability and projection inputs
and only for gaps that remain after this beam repair.
