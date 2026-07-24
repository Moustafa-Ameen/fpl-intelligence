# Phase M10 — Team, Fixture, and Calibrated Component Forecasting

## Status

M10 is in progress. The first implementation slice is complete and remains an
opt-in experimental candidate. It does not replace the accepted M8.6.1
chip-aware control, M3 xG/xA control, or the provisional M9 availability model.

## Implemented slice

- `team_forecast.py` provides a deterministic, shrunk Poisson-style team-goal
  model.
- Processed player rows are converted into fixture rows and duplicate player
  perspectives are collapsed before fitting.
- Fits are strictly point-in-time safe: only gameweeks earlier than the
  requested cutoff are used.
- Forecasts include expected home and away goals, result probabilities, clean
  sheet probabilities, fixture status, rules version, data cutoff, training
  match count, and model version.
- `calibration.py` provides binary Brier/log-loss diagnostics, reliability
  tables, Poisson MAE/RMSE/log-loss, central interval coverage, and an
  optional sparse-safe isotonic calibrator.
- Component projection models can be filtered by both BPS and DC rule regime;
  selected training regimes are retained in model metadata.
- A walk-forward evaluator produces season-level out-of-sample diagnostics.

## Focused validation

The new M10 tests pass, as do the relevant historical, fixture, rules, and
component regression tests. The existing accepted benchmark control was not
changed.

Walk-forward team-layer diagnostics on the current processed historical table:

| Season | Fixtures | Home goal MAE | Away goal MAE | Clean-sheet Brier | 80% interval coverage (home/away) |
|---|---:|---:|---:|---:|---:|
| 2023/24 | 390 | 1.123 | 1.001 | 0.156 | 89.7% / 91.3% |
| 2024/25 | 385 | 1.039 | 0.907 | 0.176 | 92.2% / 94.0% |
| 2025/26 | 385 | 0.993 | 0.875 | 0.187 | 93.8% / 92.5% |

These are model-quality diagnostics only. They are not FPL points totals and
do not establish that the team layer improves transfers, captaincy, or chips.
The fixture counts also need reconciliation against the canonical historical
fixture source before being used as a final acceptance artifact.

The temporary processed-table rebuild reconciled exactly at the persisted-file
level: 85,311 rows, identical per-season row counts, and an identical SHA-256
hash to the existing processed table. A direct pandas frame comparison was not
used as the acceptance criterion because CSV reloads can differ in in-memory
dtype/NA representation even when persisted bytes are identical.

Regression status after the shared component API change:

- Focused M10/component tests: pass.
- Full pytest: 141 passed.
- Full Ruff: clean.
- Accepted M8.6.1 control path: unchanged; M10 remains opt-in.

## Remaining M10 work

- Add calibrated (rather than unadjusted) uncertainty outputs to component
  projections without changing the accepted control.
- Extend regime-specific BPS/DC models with standalone scoring validation.
- Add player goal/assist involvement, set-piece/penalty-role, goalkeeper-save,
  and position-aware bonus interfaces.
- Connect team/fixture probabilities to candidate player components through an
  opt-in projection mode.
- Evaluate transfer, captaincy, and chip decision metrics walk-forward by
  season, with no aggregate masking.
- Run the decision-metric comparison and complete the M10 acceptance review.

M10 remains provisional until those downstream decision metrics are evaluated.
