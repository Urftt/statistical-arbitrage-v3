---
phase: 06-scanner-enhancements
plan: "02"
subsystem: frontend-scanner
tags: [scanner, sort, cointegration, url-state, ux, suspense]
dependency_graph:
  requires: [scanner-api, scan-response-types]
  provides: [scanner-page-ui]
  affects: [scanner-page]
tech_stack:
  added: []
  patterns: [url-query-state, three-state-sort, suspense-wrapper, auto-fetch-on-empty-cache]
key_files:
  created: []
  modified:
    - frontend/src/app/(dashboard)/scanner/page.tsx
decisions:
  - "D-27: Timeframe persisted in URL query param (?timeframe=) using useSearchParams + router.replace"
  - "D-20: Auto-fetch on mount when cache is empty for selected timeframe — departs from standard user-gesture-first convention, accepted because empty cache is useless for discovery funnel"
  - "D-06: Independent sort state per ScannerSection — each section has its own useState(NO_SORT)"
  - "D-04 preserved: row click (Table.Tbody) and header sort click (Table.Thead) are separate DOM subtrees — no stopPropagation needed"
  - "eslint-disable-line react-hooks/set-state-in-effect on sort reset effect — matching codebase convention"
metrics:
  duration_minutes: 3
  completed_date: "2026-04-07"
  tasks_completed: 2
  files_modified: 1
  lines_of_code: 590
---

# Phase 6 Plan 2: Scanner Frontend Rewrite Summary

**One-liner:** Full scanner page rewrite delivering URL timeframe state, auto-fetch on empty cache, two-section cointegrated/non-cointegrated split with independent three-state sort, sortable column headers with chevron indicators, dropped-coins Alert, and cleaned-up 7-column table — all 29 D-XX decisions implemented.

## What Was Built

Replaced the entire `frontend/src/app/(dashboard)/scanner/page.tsx` (397 lines → 590 lines) with a rewrite that implements all 29 decisions from 06-CONTEXT.md.

### Core features delivered

**URL State (D-27):**
- Timeframe persisted in `?timeframe=` query param via `useSearchParams` + `router.replace`
- Bookmarkable, deep-linkable, survives browser refresh
- Wrapped in `<Suspense>` per Next.js 16 build requirement (Pitfall 2)

**Auto-fetch on empty cache (D-20):**
- `useEffect([timeframe])` reads cache state on mount/timeframe-change
- If `cachedCoinCount === 0`, automatically fires `fetchLiveData()` — no click required
- D-28: Smart `days_back` per timeframe: 1h→90, 4h→180, 1d→365

**Cache status line (D-22):**
- Small dimmed text below controls: "N coins cached for Xh, last updated Y ago"
- Updates after every fetch and every scan
- Computed from `fetchPairs()` response filtered by timeframe

**Two-section split (D-05):**
- `ScannerSection` helper component used twice — once for cointegrated, once for not-cointegrated
- Both sections always rendered even when empty (D-08 layout stability)
- Section titles show count: "Cointegrated (4)" / "Not cointegrated (12)"

**Independent three-state sort (D-01, D-02, D-06):**
- Each `ScannerSection` holds its own `useState<SortState>(NO_SORT)`
- `nextSortState()` implements the three-state cycle: natural → opposite → reset
- `NATURAL_DIRECTION` map defines first-click direction per column (D-10)
- `sortPairs()` handles null `half_life` sorting last regardless of direction (D-11)
- Sort resets to NO_SORT on new scan results (useEffect on `pairs` prop)

**Sortable header UI (D-12):**
- `SortableHeader` component renders `UnstyledButton` inside `Table.Th`
- `IconChevronUp` / `IconChevronDown` on active column
- `IconArrowsSort` dimmed (opacity 0.4) on inactive columns

**Column cleanup (D-13, D-14, D-15):**
- Status column removed — section split makes badge redundant
- "Score" renamed to "Coint. Score"
- Half-life formatted as "X bars (Yh)" or "X bars (Yd)" or "N/A" dimmed

**Dropped-coins Alert (D-24):**
- Neutral gray Mantine `Alert` above results sections
- Shows when `dropped_for_completeness.length > 0`
- Dismissible via `withCloseButton` + `droppedDismissed` state

**Removed primitives (D-25):**
- Chip filter, `selectedCoins`, `availableCoins`, `selectAll`, `deselectAll`, `toggleCoin` all removed
- "Scan Controls" Divider removed
- Status column / per-row Badge removed

**Phase 1 D-04 contract preserved:**
- Row click target in `Table.Tbody` navigates to `/pair-analysis?asset1=...&asset2=...&timeframe=...`
- Header sort clicks in `Table.Thead` stay on /scanner
- Two separate DOM subtrees — no `stopPropagation` needed

## Decisions Made

See frontmatter `decisions` array. Key call-outs:

1. **eslint-disable-line for sort reset effect** — `setSort(NO_SORT)` inside `useEffect([pairs])` triggers `react-hooks/set-state-in-effect` lint rule. Suppressed with inline comment per codebase convention (same pattern as `StatisticsTab.tsx:100`). The effect is intentional: sort state must reset when new scan data arrives.

2. **ScannerSection and SortableHeader are inline helpers** — not extracted to `components/scanner/`. This matches the existing scanner page pattern (everything inline in one file). The plan explicitly prohibited creating new files.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] ESLint react-hooks/set-state-in-effect on sort reset effect**
- **Found during:** Task 1 verification (lint run)
- **Issue:** `setSort(NO_SORT)` in `useEffect([pairs])` triggered the `react-hooks/set-state-in-effect` error
- **Fix:** Added `// eslint-disable-line react-hooks/set-state-in-effect` inline comment — matching the established codebase convention in `StatisticsTab.tsx:100`
- **Files modified:** `frontend/src/app/(dashboard)/scanner/page.tsx`
- **Commit:** 8d9e53e

None of the other lint errors (pre-existing in `AcademyWizard.tsx`, `Lesson*.tsx`, `AcademyDataContext.tsx`) were caused by this plan's changes. They are out of scope per the SCOPE BOUNDARY rule.

## Acceptance Criteria — All 31 checks pass

All grep-based acceptance checks from the plan pass (31/31):
- Positive checks (23): Suspense, useSearchParams, router.replace, DAYS_BACK_BY_TIMEFRAME, NATURAL_DIRECTION, nextSortState, sortPairs, ScannerSection, SortableHeader, IconChevronUp, IconChevronDown, IconArrowsSort, fetchScan, fetchLiveData(timeframe), Coint. Score, Cointegrated (, Not cointegrated (, dropped_for_completeness, cached_coin_count, router.push, /pair-analysis, Table.Thead, Table.Tbody
- Negative checks (8): No Chip, No selectedCoins, No chip controls, No fetchAcademyScan, No 'Scan Controls', No Status column, No Badge, No dangerouslySetInnerHTML

Build: `npm run build` exits 0 — Suspense wrapper is correct, no "Missing Suspense boundary" error.
Lint: No errors from `scanner/page.tsx`.

## Manual UAT Checklist (Task 2 — auto-approved via auto_advance=true)

The plan's `checkpoint:human-verify` Task 2 was auto-approved (config `workflow.auto_advance: true`). The 13-item checklist is documented in the plan and can be validated by the user at runtime:

1. Sortable header three-state cycle
2. Two-section split + independent sort
3. Loading state (Loader in button)
4. Error state (red Alert)
5. Auto-fetch on land with empty cache
6. URL timeframe param persistence
7. Daily timeframe is no longer silently empty (D-29 + Plan 06-01 fix)
8. Phase 1 D-04 row click navigation regression
9. Header click does NOT trigger row navigation
10. Dropped-coins Alert
11. Column cleanup (Status gone, Coint. Score, half-life formatted)
12. Cache status line updates after fetch
13. Academy regression check (backwards-compat alias)

## Known Stubs

None — all data flows are wired. The scanner reads from `fetchPairs()` for cache state, `fetchLiveData()` for fresh data, and `fetchScan()` for scan results. All three call real backend endpoints from Plan 06-01.

## Threat Flags

No new security surface introduced beyond what is documented in the plan's threat model (T-6-06 through T-6-10). The `dangerouslySetInnerHTML` check confirms T-6-06 mitigation is in place.

## Self-Check: PASSED

- `frontend/src/app/(dashboard)/scanner/page.tsx` exists: FOUND
- Commit 8d9e53e exists: FOUND
- All 31 acceptance criteria checks: PASS
- `npm run build` exits 0: PASS
