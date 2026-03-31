# Phase 1: Routing & Navigation Scaffold - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Restructure the frontend navigation from 6 separate research pages to 2 main pages (Scanner + Pair Analysis). Wire up scanner-to-analysis drill-down with pair selection flowing via URL params and PairContext. Build the Pair Analysis tabbed shell (Statistics, Research, Backtest, Optimize) with placeholder content in each tab. Tab content is built in later phases — this phase delivers only the navigation skeleton and tab container.

</domain>

<decisions>
## Implementation Decisions

### Sidebar Restructure
- **D-01:** Collapse the "Research & Backtesting" sidebar section to exactly 2 items: Scanner and Pair Analysis. Remove Pair Deep Dive, Research, Backtest, Optimize, and Summary entries.
- **D-02:** Pair Analysis sidebar item is a flat entry (no nested sub-items for individual tabs). Tab switching happens inside the page only.

### Scanner Drill-Down
- **D-03:** Clicking a scanner table row navigates to `/pair-analysis?asset1=ETH&asset2=BTC&timeframe=1h` via `router.push` with URL query params. The Pair Analysis page reads these params on mount and sets PairContext accordingly. This supports deep linking and bookmarking.
- **D-04:** The entire scanner table row is clickable (cursor: pointer on hover). No separate "Analyze" button.

### Tab Design & Behavior
- **D-05:** Use Mantine `Tabs` component with `variant="pills"` for the Pair Analysis page.
- **D-06:** Tab labels are: Statistics, Research, Backtest, Optimize (4 tabs, in that order).
- **D-07:** Use React `key={`${asset1}-${asset2}`}` on the tabs container to clear all tab state when the user switches pairs (NAV-05). This causes a full remount of tab content, automatically discarding stale results.

### URL Routing
- **D-08:** Pair Analysis page lives at `/pair-analysis` (new route). Old stub pages (`/deep-dive`, `/research`, `/backtest`, `/optimize`, `/summary`) are removed.
- **D-09:** Active tab is stored in the URL as a query param: `/pair-analysis?tab=backtest`. Tab state survives page refresh. Default tab is Statistics when no `tab` param is present.

### Claude's Discretion
- Whether to add icons to tab labels (Tabler icons matching the old sidebar items)
- Sidebar active state highlighting for Pair Analysis when on that route
- Whether to redirect old routes (/deep-dive, /research, etc.) or just remove them
- Pair Analysis page header design showing the currently selected pair

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frontend Layout & Navigation
- `frontend/src/components/layout/Sidebar.tsx` — Current sidebar structure to be restructured
- `frontend/src/components/layout/Header.tsx` — Header with pair selection dropdowns
- `frontend/src/app/(dashboard)/layout.tsx` — Dashboard shell (AppShell + PairProvider)

### State Management
- `frontend/src/contexts/PairContext.tsx` — Global pair selection context (asset1, asset2, timeframe, coins)

### Existing Pages (to be modified/removed)
- `frontend/src/app/(dashboard)/scanner/page.tsx` — Full scanner implementation, needs row click handler
- `frontend/src/app/(dashboard)/deep-dive/page.tsx` — Stub to be replaced
- `frontend/src/app/(dashboard)/research/page.tsx` — Stub to be removed
- `frontend/src/app/(dashboard)/backtest/page.tsx` — Stub to be removed
- `frontend/src/app/(dashboard)/optimize/page.tsx` — Stub to be removed
- `frontend/src/app/(dashboard)/summary/page.tsx` — Stub to be removed

### API Client
- `frontend/src/lib/api.ts` — Typed API client with all interfaces

### Theme & Charts
- `frontend/src/lib/theme.ts` — Mantine theme + Plotly dark template

### Codebase Conventions
- `.planning/codebase/CONVENTIONS.md` — Naming, imports, component patterns
- `.planning/codebase/STRUCTURE.md` — Where to add new code

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PairContext` (contexts/PairContext.tsx): Already provides global pair selection — drill-down sets these values
- `Sidebar` component: Uses Mantine `NavLink` with `Link` component and `usePathname()` for active state
- `Header` component: Already has pair selection dropdowns that will continue to work with PairContext
- `AppShell` layout: Dashboard shell with header (60px) and sidebar (260px) — no changes needed to the shell

### Established Patterns
- All pages are `'use client'` with `useState` for loading/error/data
- Mantine `Container`, `Stack`, `Paper`, `Title`, `Text` for page layout
- `usePathname()` for sidebar active state detection
- `next/link` for client-side navigation

### Integration Points
- New `/pair-analysis` route directory: `frontend/src/app/(dashboard)/pair-analysis/page.tsx`
- Sidebar.tsx: Replace RESEARCH_ITEMS array with 2 entries
- Scanner page.tsx: Add `onClick` handler to `Table.Tr` elements to navigate with `useRouter()`
- PairContext: May need a `setPair(asset1, asset2)` convenience method or the page reads URL params and calls setAsset1/setAsset2

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches within the decisions above.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-routing-navigation-scaffold*
*Context gathered: 2026-03-31*
