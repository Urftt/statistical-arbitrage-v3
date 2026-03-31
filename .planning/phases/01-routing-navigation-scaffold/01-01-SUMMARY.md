---
phase: 01-routing-navigation-scaffold
plan: 01
subsystem: ui
tags: [next.js, mantine, tabs, routing, react-context]

# Dependency graph
requires: []
provides:
  - "Restructured sidebar with Scanner + Pair Analysis navigation"
  - "Tabbed Pair Analysis page shell at /pair-analysis with URL-synced tabs"
  - "Deep linking support via URL params for pair and tab state"
affects: [02-statistics-tab, 03-backtest-tab, 04-research-tab, 05-optimize-tab, 06-scanner-upgrade]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "URL-synced tabs via useSearchParams + router.replace"
    - "React key remount on pair change for tab content isolation"
    - "Suspense boundary wrapping useSearchParams component"

key-files:
  created:
    - frontend/src/app/(dashboard)/pair-analysis/page.tsx
  modified:
    - frontend/src/components/layout/Sidebar.tsx

key-decisions:
  - "Used pathname.startsWith() for RESEARCH_ITEMS active state to support query params"
  - "Kept unused icon imports (IconAdjustments, IconChartHistogram, IconChartLine) removed per plan — only IconReportAnalytics removed"

patterns-established:
  - "URL tab sync: useSearchParams for reading, router.replace for writing tab state"
  - "Pair key remount: key={asset1-asset2} on Tabs to clear stale content on pair change"
  - "Deep linking: useEffect on mount to hydrate context from URL params"

requirements-completed: [NAV-01, NAV-03, NAV-04, NAV-05]

# Metrics
duration: 2min
completed: 2026-03-31
---

# Phase 01 Plan 01: Sidebar Restructure and Pair Analysis Tab Shell Summary

**Restructured sidebar to 2 items (Scanner + Pair Analysis) and created tabbed Pair Analysis page with URL-synced pill tabs, deep linking, and pair key remount**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-31T19:54:17Z
- **Completed:** 2026-03-31T19:56:27Z
- **Tasks:** 2
- **Files modified:** 7 (1 modified, 1 created, 5 deleted)

## Accomplishments
- Sidebar reduced from 6 research items to 2 (Scanner + Pair Analysis)
- Pair Analysis page at /pair-analysis with 4 pill-style tabs (Statistics, Research, Backtest, Optimize)
- Tab state synced to URL via useSearchParams, enabling deep linking and browser refresh persistence
- React key remount on pair change ensures stale tab content is cleared
- 5 old stub pages deleted (deep-dive, research, backtest, optimize, summary)

## Task Commits

Each task was committed atomically:

1. **Task 1: Restructure sidebar and delete old stub pages** - `c747c3f` (feat)
2. **Task 2: Create Pair Analysis page with tabbed interface** - `6e1f06a` (feat)

## Files Created/Modified
- `frontend/src/components/layout/Sidebar.tsx` - Reduced RESEARCH_ITEMS to 2 entries, changed active state to startsWith
- `frontend/src/app/(dashboard)/pair-analysis/page.tsx` - New tabbed Pair Analysis shell with URL sync
- `frontend/src/app/(dashboard)/deep-dive/page.tsx` - Deleted
- `frontend/src/app/(dashboard)/research/page.tsx` - Deleted
- `frontend/src/app/(dashboard)/backtest/page.tsx` - Deleted
- `frontend/src/app/(dashboard)/optimize/page.tsx` - Deleted
- `frontend/src/app/(dashboard)/summary/page.tsx` - Deleted

## Decisions Made
- Used pathname.startsWith() for RESEARCH_ITEMS NavLink active state so Pair Analysis stays highlighted with query params
- Removed all unused icon imports (IconAdjustments, IconChartHistogram, IconChartLine, IconReportAnalytics) from Sidebar since they are no longer used there; tab icons live in pair-analysis/page.tsx

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

| File | Line | Stub | Reason |
|------|------|------|--------|
| frontend/src/app/(dashboard)/pair-analysis/page.tsx | 99 | "Statistics — coming in Phase 2" | Intentional placeholder; Phase 02 will replace with Statistics tab content |
| frontend/src/app/(dashboard)/pair-analysis/page.tsx | 102 | "Research — coming in Phase 4" | Intentional placeholder; Phase 04 will replace with Research modules |
| frontend/src/app/(dashboard)/pair-analysis/page.tsx | 105 | "Backtest — coming in Phase 3" | Intentional placeholder; Phase 03 will replace with Backtest interface |
| frontend/src/app/(dashboard)/pair-analysis/page.tsx | 108 | "Optimize — coming in Phase 5" | Intentional placeholder; Phase 05 will replace with Optimize interface |

All stubs are intentional scaffold placeholders that will be replaced by their respective phases. The plan's goal (navigation skeleton) is fully achieved.

## Issues Encountered
- Pre-existing ESLint errors in academy components (hooks-of-rules violations, unused vars) — out of scope, not introduced by this plan

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Pair Analysis tab shell is ready to receive content from Phases 2-5
- Each phase will replace one "coming in Phase X" placeholder with actual tab content
- Scanner page unchanged, ready for Phase 6 upgrade

## Self-Check: PASSED

- All created files exist
- All deleted directories confirmed removed
- All commit hashes verified in git log

---
*Phase: 01-routing-navigation-scaffold*
*Completed: 2026-03-31*
