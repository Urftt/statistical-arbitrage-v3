---
phase: 03-backtest-tab
plan: 02
subsystem: ui
tags: [react, plotly, typescript, charts, backtest]

# Dependency graph
requires:
  - phase: 03-backtest-tab plan 01
    provides: BacktestTab component with parameter form, metrics, trade log, chart placeholders, cointData state
  - phase: 02-statistics-tab
    provides: PlotlyChart usage patterns, buildZScoreShapes function pattern
provides:
  - Four Plotly charts in BacktestTab (equity curve, drawdown, z-score with markers, spread with markers)
  - Chart helper functions (MARKER_MAP, computeDrawdown, buildZScoreShapes, buildPositionShapes, buildSignalTraces)
affects: [04-research-tab (Apply-to-Backtest cross-tab)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Position background shading via Plotly rect shapes on equity curve
    - Trade marker overlays using MARKER_MAP constant with signal_type filtering
    - Timestamp matching between ISO-string signals and epoch-ms cointegration data
    - Graceful chart degradation when cointData is null

key-files:
  created: []
  modified:
    - frontend/src/components/pair-analysis/BacktestTab.tsx

key-decisions:
  - "Used separate buildZScoreMarkerTraces and buildSpreadMarkerTraces functions -- z-score uses zscore_at_signal directly, spread needs timestamp-based lookup"
  - "Axis titles use object form { text: '...' } for Plotly v3 compatibility (string form deprecated)"

patterns-established:
  - "MARKER_MAP constant: centralized signal type to marker symbol/color mapping for reuse across chart types"
  - "Position shading: iterate equity_curve position transitions, emit rect shapes with layer='below'"

requirements-completed: [BT-03, BT-04, BT-05]

# Metrics
duration: 3min
completed: 2026-04-01
---

# Phase 3 Plan 02: Backtest Charts Summary

**Four Plotly charts with equity curve position shading, drawdown fill, z-score threshold lines with trade markers, and spread with timestamp-matched trade markers**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-01T21:51:42Z
- **Completed:** 2026-04-01T21:55:00Z
- **Tasks:** 1 of 2 (Task 2 is human-verify checkpoint)
- **Files modified:** 1

## Accomplishments
- Added 4 Plotly charts to BacktestTab replacing placeholder text: equity curve (280px), drawdown (180px), z-score (300px), spread (260px)
- Built 6 pure helper functions outside component: MARKER_MAP, computeDrawdown, buildZScoreShapes, buildPositionShapes, buildZScoreMarkerTraces, buildSpreadMarkerTraces
- Graceful degradation for z-score and spread charts when cointegration data unavailable
- TypeScript builds clean, all chart data wired to real API response fields

## Task Commits

Each task was committed atomically:

1. **Task 1: Add four Plotly charts to BacktestTab results section** - `2772c36` (feat)

## Files Created/Modified
- `frontend/src/components/pair-analysis/BacktestTab.tsx` - Added PlotlyChart import, 6 chart helper functions, replaced 4 chart placeholders with actual Plotly charts

## Decisions Made
- Used object form for yaxis titles (`{ text: '...' }`) instead of string -- Plotly v3 deprecates string titles, and TypeScript type checking rejects them
- Split signal trace builders into two functions (buildZScoreMarkerTraces, buildSpreadMarkerTraces) because z-score uses zscore_at_signal directly while spread requires timestamp-based lookup

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plotly v3 axis title type mismatch**
- **Found during:** Task 1 (TypeScript build verification)
- **Issue:** Plan specified `yaxis: { title: 'EUR' }` but Plotly v3 types require `title: { text: '...' }` object form
- **Fix:** Changed all 4 chart yaxis titles to use object form
- **Files modified:** frontend/src/components/pair-analysis/BacktestTab.tsx
- **Verification:** `npm run build` passes clean
- **Committed in:** 2772c36 (part of task commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor type fix for Plotly v3 compatibility. No scope creep.

## Known Stubs

None -- all 4 chart placeholders from Plan 01 have been replaced with functional PlotlyChart components.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Complete BacktestTab with all UI elements: parameter form, metric cards, 4 charts, trade log, warnings, accordion
- Task 2 (human-verify checkpoint) pending -- visual verification of complete tab with real API data
- Ready for Phase 4 (Research tab) after verification passes

## Self-Check: PASSED

- BacktestTab.tsx: FOUND
- Commit 2772c36: FOUND
- All 20 acceptance criteria: PASSED
- TypeScript build: PASSED

---
*Phase: 03-backtest-tab*
*Completed: 2026-04-01*
