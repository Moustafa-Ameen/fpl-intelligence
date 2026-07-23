# Phase M7 — Component-Based Projection

## Status

Implemented and evaluated as a provisional ablation candidate. The existing
total-points projection remains the default control, and the M7 candidate is
not production-promoted.

## What changed

- Added raw component outcomes and strict prior-only component lags to the
  processed historical table.
- Added a component projection model that predicts scoring components with a
  shared multi-output Ridge model and converts them into expected FPL points.
- Applied position-aware scoring for goals, assists, clean sheets, saves,
  cards, own goals, penalties, goals conceded, bonus, and Defensive
  Contributions.
- Applied explicit BPS-regime matching with a visible prior-regime fallback
  when historical data for a future regime is unavailable.
- Added component projection to the point-in-time benchmark, future forecast
  path, realistic captaincy path, and ablation registry.
- Kept the control path, transfer logic, chips, optimizer, and minutes model
  unchanged.

## Evaluation

The same-run comparison against the accepted lagged xG/xA control produced:

| Season | Control realistic deterministic | M7 realistic deterministic | Delta |
|---|---:|---:|---:|
| 2023/24 | 2,139 | 2,094 | -45 |
| 2024/25 | 2,018 | 2,219 | +201 |

Aggregate improvement was +156, but the 2023/24 regression fails the
multi-season acceptance bar. M7 therefore remains `provisional / failed` and
must not replace the control.

## Verification

- Focused M7/data/ablation tests: passed.
- Full test suite before final diff review: 94 passed.
- Ruff: clean.
- Processed historical rows: 85,311, with component outcomes and lags present.
- Historical DC availability remains 2023/24 unavailable, 2024/25 unavailable,
  and 2025/26 available.
- Persisted benchmark-history SHA-256 remained unchanged.

## Follow-up

M7 should be revisited only with targeted diagnostics for the 2023/24
regression, calibration and component-specific error analysis, and a new
multi-season acceptance run. M8 must not begin until this result has been
reviewed.
