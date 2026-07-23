# Phase M8.3 — Chip-Specific Valuation

## Status

Implemented as an experimental, provisional valuation layer. M8.4 beam search
has not started.

## Delivered

- Wildcard valuation uses a permanent 8-Gameweek horizon, including future
  squad value rather than only the activation Gameweek.
- Free Hit valuation uses a temporary 3-Gameweek comparison: the current
  temporary squad is scored while the retained squad supplies future value.
- Free Hit future opportunity cost is estimated from future legal squad upgrades,
  allowing Blank and Double Gameweek value to influence whether it is saved.
- Bench Boost adds the expected contribution of all four bench players and
  compares it with future bench opportunities.
- Triple Captain adds expected captain points and compares current value with
  future captain opportunities.
- Chip decisions now subtract deterministic uncertainty and future-opportunity
  guardrails from the raw expected gain before selection.
- Counterfactuals persist current points, horizon points, opportunity cost,
  uncertainty penalty, and rejection/selection reasons for every evaluated chip.
- Added the historical Assistant Manager scoring contract:
  `6 * wins + 3 * draws + team goals + 2 * clean sheets + table bonus`.
  It remains non-selectable in benchmark runs without manager projections.
- Future prediction requests are contiguous for offsets 1 through 8, so the
  Wildcard horizon does not skip Gameweeks.

## Verification

- Focused chip valuation tests: `22 passed`.
- Full pytest: `112 passed`.
- Ruff: clean.
- Synthetic Blank Gameweek test selects Free Hit when the temporary squad
  materially outperforms the retained squad while future retained-squad value
  is preserved.
- Historical 2023/24 diagnostic run completed with five legal chip decisions,
  persisted horizon/opportunity/uncertainty fields, and no runtime failures.

## Interpretation

This improves the decision objective and correctly makes Blank/Double Gameweek
structure affect chip valuation, but it is not production promotion. The
historical planner remains provisional and season-dependent. M8.4 must add the
complete deterministic beam-search state before further optimizer promotion.
