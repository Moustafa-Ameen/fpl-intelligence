# Phase M9 — Availability, Minutes, and Role Intelligence

## Status

Implemented and evaluated. M9 remains **provisional/failed for production
promotion** because the availability-role candidate regressed in two of the
three chip-aware validation seasons. M10 must not promote or stack this
candidate automatically.

## Delivered

- Added `fpl_intelligence.availability` with a strict, source-attributed
  `AvailabilityEvent` contract.
- Enforced timezone-aware `published_at`, `observed_at`, and `expiry` values.
- Added point-in-time event filtering by publication, observation, and expiry.
- Added deterministic availability features with neutral missing-event values.
- Added an official FPL bootstrap adapter for status, chance of playing, news,
  and `news_added`.
- Carried raw historical `starts` through fixture aggregation and the
  processed player-gameweek table.
- Added prior-only role features:
  `starts_last_3`, `minutes_mean_last_5`, `minutes_std_last_5`,
  `zero_minutes_rate_last_5`, and `starts_rate_last_5`.
- Added selectable `availability_role` minutes mode without changing the
  binary control mode.
- Added start, substitute-appearance proxy, and 60+ minutes probabilities,
  plus expected minutes conditional on starting.
- Added point-in-time-safe future feature freezing and optional live event
  overlays for target predictions.
- Added benchmark CLI/history metadata for `minutes_mode`.
- Materialized M9 historical features once per benchmark run to avoid repeated
  full-table recomputation.

## Validation

Focused availability, historical-data, and M9 prediction tests passed. Ruff
passed. The complete regression suite passed:

```text
132 passed in 360.90s
```

The chip-aware candidate was run with deterministic transfers,
`beam_search`, realistic captaincy, and season-specific rules:

| Season | M8.6.1 realistic control | M9 availability-role | Change |
|---|---:|---:|---:|
| 2023/24 | 2,337 | 2,185 | -152 |
| 2024/25 | 2,489 | 2,401 | -88 |
| 2025/26 | 2,192 | 2,227 | +35 |

The M9 run persisted 38 decision rows per season, all chip counterfactuals,
rules versions, squad hashes, and data cutoffs in
`data/processed/m9_availability_role_history_decisions.csv`. It had zero
duplicate decision keys and zero current-season lookahead violations. Chip
counts were 5, 5, and 8 for 2023/24, 2024/25, and 2025/26 respectively.

## Acceptance decision

M9 passes its engineering and leakage gates, but fails the production
performance gate. It improves only the 2025/26 regime and causes material
regressions in 2023/24 and 2024/25. The accepted M8.6.1 chip-aware control
remains the production reference. The M9 candidate is retained for diagnosis,
not stacked into the live recommendation path.

Likely follow-up work belongs in a later rework rather than M10 promotion:

- Calibrate start/substitute/60+ probabilities by position and season.
- Separate injury availability from tactical rotation and role changes.
- Add held-out decision-metric diagnostics for transfer, captain, and chip
  actions before changing the model again.
- Investigate why the new role features alter historical transfer/chip choices
  negatively in the pre-DC/BPS regimes.

## M9 hit-policy rework

The confirmed rework added a separate `horizon_value` hit policy. It:

- Keeps the existing `current_gw` policy as the control.
- Generates legal hit branches with the official four-point cost.
- Ranks a bounded shortlist using full-XI and captain value across available
  future Gameweeks.
- Applies future incremental value only to hit branches with positive net
  horizon value.
- Persists `hit_policy`, `hit_selected`, `hit_cost`,
  `transfer_expected_horizon_gain`, and
  `transfer_expected_horizon_net_gain`.
- Leaves Wildcard/Free Hit transfer replacement and chip legality unchanged.

The synthetic hit test passes: a transfer with insufficient immediate value but
positive multi-Gameweek net value is considered and selected with a -4 cost.
The completed historical hit-policy runs selected zero hits in every season;
that is a result of the model's projected value and not because hit branches
were forbidden.

Completed realistic totals:

| Track | 2023/24 | 2024/25 | 2025/26 |
|---|---:|---:|---:|
| M8.6.1 control | 2,337 | 2,489 | 2,192 |
| M8 binary + horizon hit policy | 2,173 | 2,567 | 2,219 |
| M9 role + current hit policy | 2,185 | 2,401 | 2,227 |
| M9 role + horizon hit policy | 2,232 | 2,389 | not persisted |

The binary hit-policy track improved 2024/25 and 2025/26 but regressed
2023/24. The M9-plus-hit track improved 2023/24 versus M9-current but still
remained below the accepted M8 control, and regressed 2024/25. The
2025/26 M9-plus-hit run exceeded the benchmark runtime budget before its
append step, so no score is claimed for it.

The hit rework is therefore implemented and remains experimental. It is not
production-promoted, and the accepted M8.6.1 control remains the reference.
