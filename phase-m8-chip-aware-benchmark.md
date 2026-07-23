# Phase M8 — Chip-Aware Benchmark and Baseline Planner

## Status

M8.1 control hardening, M8.2 fixture horizon/scenario work, M8.3
chip-specific valuation, M8.4 runtime hardening, M8.5 live/API alignment, and
M8.6 beam repair are implemented and verified. The planner remains
experimental and provisional. M9 has not started.
The chip planner remains experimental and provisional.

## Delivered

- Added `chip_simulation.py` with typed chip definitions, chip state, legality,
  half-season inventory handling, one-chip-per-gameweek enforcement, and the
  2026/27 GW19/GW20 Free Hit restriction.
- Implemented exact score effects for Wildcard/Free Hit squad transitions,
  Bench Boost bench inclusion, and Triple Captain multiplication.
- Added a deterministic projection-only baseline planner behind
  `chip_mode="baseline_planner"`.
- Preserved `chip_mode="none"` as the benchmark control and added a CLI switch.
- Added per-gameweek chip decisions, remaining inventory, expected gain,
  realized gain, rules version, and chip-aware totals to benchmark outputs.
- Corrected chip/transfer ordering: Bench Boost and Triple Captain use the
  post-transfer squad, while Wildcard and Free Hit replace ordinary transfer
  accounting. Free Hit restores the prior squad, bank, and free-transfer state.
- Added explicit per-Gameweek chip counterfactuals with selected/rejected
  status and reasons, plus a companion decision-history CSV.
- Added season-level chip fields to persisted benchmark history.
- Added team-goal, opponent-goal, and clean-sheet context to the historical
  processing path without zero-filling missing historical scores.
- Added deterministic 3/5/8-Gameweek fixture scenarios, fixture hashes, blank /
  double summaries, and explicit schedule-status metadata. See
  `phase-m8-2-fixture-horizon-scenario.md`.
- Added chip-specific 3/8-Gameweek valuations, future opportunity costs,
  uncertainty penalties, and permanent-versus-temporary squad comparisons. See
  `phase-m8-3-chip-specific-valuation.md`.
- Added an experimental complete-state deterministic beam-search planner with
  transfer/chip branches and candidate pruning. See
  `phase-m8-4-beam-search.md`.
- Hardened beam runtime with a fast lineup evaluator, bounded candidate
  pruning, and cached chip-squad solves. Full-season runs completed in 369.4
  seconds for 2023/24 and 277.6 seconds for 2024/25. The benchmark adapter was
  also corrected so selected beam transfers and chips are reflected in the
  persisted accounting rows.
- Aligned `/api/chip-tips` and the frontend chip page with the shared
  deterministic beam-search engine. The live response now includes the
  recommendation, horizon gain, downside range, confidence, future
  alternative, inventory, rules version, and data cutoff. See
  `phase-m8-5-live-api-alignment.md`.
- Repaired the beam's permanent-chip and branch-accounting gaps. Wildcard
  squads now use available multi-Gameweek projections, future Bench Boost and
  Triple Captain opportunity value is explicit, chip-squad caches include the
  branch squad signature, future high-value candidates are retained, and every
  legal root chip branch is persisted as a counterfactual. See
  `phase-m8-6-beam-correctness-and-valuation.md`.

## Verification

- Focused M8.1 tests: `20 passed`.
- Full pytest after M8.1 changes: `102 passed`.
- Ruff: clean.
- Dry-run historical rebuild: `85,311` rows across 2023/24, 2024/25, and
  2025/26; the rebuilt temporary table had 102 columns and preserved all
  season row counts.
- No-chip control remained chip-free and reproducible. For 2023/24, the
  default and explicit no-chip runs both produced 2,047 hindsight and 1,833
  realistic points with identical rows.
- Four-track comparison: the deterministic-transfer no-chip controls produced
  2,119 realistic points in 2023/24 and 1,903 in 2024/25. Its chip-enabled
  track produced 1,595 and 2,446 respectively, with ordinary transfers
  correctly coexisting with Bench Boost/Triple Captain and being suppressed
  for Wildcard/Free Hit.
- M8.6 reconciliation runs: deterministic-transfer no-chip controls produced
  2,119 realistic points in 2023/24 and 1,903 in 2024/25. The repaired beam
  produced 2,337 and 2,489 realistic points respectively, with 34 and 30
  transfers and five chips in each season. These remain provisional results,
  not production-promotion evidence.

## Interpretation

The M8 mechanics, reconciliation, and beam implementation gates pass. The
beam remains provisional: its decisions are season-dependent, its production
quality has not been established, and the chip-aware totals must not be used
to claim top-1% performance. M9 remains blocked until the M8.6 review is
accepted.
