---
phase: 01-routing-navigation-scaffold
plan: 02
subsystem: ui
tags: [next.js, navigation, scanner, routing]

# Dependency graph
requires: [01-01]
provides:
  - "Scanner table rows clickable with navigation to /pair-analysis"
  - "Scanner-to-analysis user journey (NAV-02)"
affects: [02-statistics-tab, 06-scanner-upgrade]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "useRouter click-to-navigate with query params on table rows"

key-files:
  created: []
  modified:
    - frontend/src/app/(dashboard)/scanner/page.tsx

key-decisions:
  - "Entire row is click target (no separate Analyze button) per D-04"

patterns-established:
  - "Scanner drill-down: router.push with asset1/asset2/timeframe query params"

requirements-completed: [NAV-02]

# Metrics
duration: 1min
completed: 2026-03-31
---

# Phase 01 Plan 02: Scanner Click-to-Navigate Summary

**Added onClick navigation to scanner table rows, routing to /pair-analysis with asset1, asset2, and timeframe query params**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-31T20:00:13Z
- **Completed:** 2026-03-31T20:01:18Z
- **Tasks:** 1 of 2 (Task 2 is human-verify checkpoint, pending)
- **Files modified:** 1

## Accomplishments
- Scanner table rows now have onClick handler with router.push to /pair-analysis
- Query params include asset1 (base symbol), asset2 (base symbol), and timeframe from scan state
- Cursor: pointer style added for visual affordance
- No separate "Analyze" button -- entire row is the click target per D-04
- Production build passes

## Task Commits

Each task was committed atomically:

1. **Task 1: Add click-to-navigate on scanner table rows** - `236922c` (feat)
2. **Task 2: Verify full navigation flow** - PENDING (checkpoint:human-verify)

## Files Created/Modified
- `frontend/src/app/(dashboard)/scanner/page.tsx` - Added useRouter import, router initialization, onClick handler with router.push, cursor: pointer style

## Decisions Made
- Entire row is click target (no separate Analyze button) per D-04 design decision

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None - no stubs introduced by this plan.

## Pending Checkpoint

**Task 2 (checkpoint:human-verify)** requires manual browser verification of the full navigation flow:
1. Sidebar shows Scanner + Pair Analysis under Research and Backtesting
2. Old routes (deep-dive, research, backtest, optimize, summary) return 404
3. Pair Analysis empty state works
4. Pair Analysis with pair selection works
5. Tab switching with URL persistence works
6. Tab state clears on pair change
7. Scanner drill-down navigates to pair-analysis with correct params
8. Browser back button returns to Scanner

This checkpoint requires both backend and frontend servers running with cached data.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Self-Check: PASSED

- Modified file exists: frontend/src/app/(dashboard)/scanner/page.tsx
- Commit 236922c verified in git log

---
*Phase: 01-routing-navigation-scaffold*
*Completed: 2026-03-31*
