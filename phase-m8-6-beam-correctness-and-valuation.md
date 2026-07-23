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

## Acceptance interpretation

The correctness and runtime gates pass. The performance-promotion gate does
not pass automatically: the beam remains provisional until later validation
shows repeatable realistic decision-quality improvement across seasons without
severe seasonal or Blank/Double Gameweek regression.

M11 remains a separate future phase. It will build the exact production
optimizer only after M9 and M10 improve the availability and projection inputs
and only for gaps that remain after this beam repair.
