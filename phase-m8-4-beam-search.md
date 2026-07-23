# Phase M8.4 — Deterministic Beam-Search Planner

## Status

Implemented as an experimental planner. Runtime qualification passed and M8.5
live/API alignment is complete, but the planner is not promoted to production
or represented as top-1%-quality. M8.6 is the current repair and reconciliation
phase.

## Delivered

- Added `DecisionState` containing squad, XI, bench order, captain, vice,
  bank, free transfers, transfer hits, chip state, active chip, fixture
  scenario, rules version, score, and first action.
- Added deterministic beam search over no-transfer, legal transfer, and legal
  chip branches.
- Added Wildcard and Free Hit squad branches, Bench Boost, Triple Captain, and
  historical Assistant Manager gating.
- Added deterministic transfer candidate generation with no-transfer control,
  bank and club-limit checks, transfer-hit costs, and candidate pruning.
- Added stable beam tie-breaking and reproducible first-action selection.
- Added per-position candidate pruning that preserves current squad players
  before squad MILP construction.
- Added an experimental `chip_mode="beam_search"` benchmark path.

## Verification

- Focused beam/chip tests: `14 passed` after the benchmark adapter correction.
- Full pytest: `114 passed`.
- Ruff: clean.
- No-transfer and chip-control paths remain covered by the full regression
  suite.

## Runtime qualification

The initial implementation was too slow because every beam branch repeatedly
called the Pandas-based starting-XI optimizer. Profiling identified 520 such
calls in a single real Gameweek decision. The runtime fix added a fast
deterministic lineup evaluator for beam scoring, candidate pruning, and cached
chip-squad solves. A representative real Gameweek fell from approximately
65 seconds to 9.3 seconds.

Clean full-season beam runs then completed for both supported validation
seasons:

| Season | Runtime | Hindsight | Realistic | Transfers | Chips |
|---|---:|---:|---:|---:|---:|
| 2023/24 | 369.4 s | 2,583 | 2,313 | 33 | 5 |
| 2024/25 | 277.6 s | 2,653 | 2,443 | 34 | 5 |

The first post-optimization run exposed an adapter issue: the selected
`BeamAction` was not being copied into the benchmark's transfer and chip
accounting layer. That was corrected before these totals were accepted. The
resulting audit rows contain the selected chip, ordinary-transfer legality,
transfer application status, and expected chip gain.

This is a runtime and accounting correction, not a performance-promotion
result. M8.6 extends this implementation with horizon-aware Wildcard scoring,
opportunity-cost accounting, safer branch-specific caching, stronger future
candidate retention, and complete root counterfactuals.
