# Phase 2: Statistics Tab - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the Statistics tab content inside the existing Pair Analysis page. When a user selects a pair and opens the Statistics tab, they see cointegration metrics as stat cards and two time-series charts (spread + z-score) with configurable threshold lines. This phase delivers the first real data view in the Pair Analysis page — replacing the Phase 1 placeholder text.

</domain>

<decisions>
## Implementation Decisions

### Stat Cards
- **D-01:** Use a Mantine `SimpleGrid` with Paper cards in a 4-column row (collapses to 2x2 on smaller screens). Five cards total: p-value, half-life, hedge ratio, correlation, and cointegration score (0-100).
- **D-02:** Each card includes a colored `Badge` below the value with an interpretive label. Color coding: green for strong/good values, yellow for moderate, red for weak/concerning. Examples: p-value < 0.01 = green "Strong", p-value > 0.05 = red "Weak"; half-life < 20 = green "Fast", etc.
- **D-03:** Cointegration score (0-100) shown as a 5th card. The API already returns `cointegration_score` in `CointegrationResponse`.

### Z-Score Threshold Controls
- **D-04:** Use Mantine `Slider` components for entry and exit threshold values. Two sliders: one for entry threshold, one for exit threshold. Chart threshold lines update as the user drags.
- **D-05:** Thresholds are symmetric — entry slider draws lines at +value and -value, exit slider draws lines at +value and -value. Two sliders total, four lines drawn.

### Data Loading
- **D-06:** Auto-load cointegration data when the Statistics tab opens and a pair is selected. `useEffect` fires `postCointegration()` immediately. Show skeleton/loading state while fetching.
- **D-07:** Lookback period (`days_back`) is user-adjustable via a dropdown with presets (e.g., 90d, 180d, 365d, 730d).
- **D-08:** Changing the lookback dropdown auto-reloads data immediately (no separate refresh button needed).

### Chart Layout
- **D-09:** Two stacked charts with shared x-axis: spread chart on top, z-score chart below. Time axes aligned vertically.
- **D-10:** Charts are interactive — Plotly zoom (drag-select), pan, and reset-zoom supported.
- **D-11:** Hover tooltips enabled showing date + value on both charts.

### Claude's Discretion
- Exact slider range/step values for entry (e.g., 0.5-4.0) and exit (e.g., 0.0-2.0) thresholds
- Default values for entry (2.0) and exit (0.5) thresholds
- Default lookback period preset selection
- Skeleton loading component design
- Exact color thresholds for interpretive badges (what counts as "strong" vs "moderate")
- Whether to show `interpretation` text from the API response (already returned by backend)
- Chart height ratios (spread vs z-score)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frontend - Statistics Tab Location
- `frontend/src/app/(dashboard)/pair-analysis/page.tsx` — Existing tab shell with placeholder at line 96-98 to be replaced
- `frontend/src/contexts/PairContext.tsx` — Global pair selection (asset1, asset2, timeframe)

### API Client & Types
- `frontend/src/lib/api.ts` — `postCointegration()` function and `CointegrationResponse` interface (lines 75-124, 686-695). Returns p_value, hedge_ratio, half_life, correlation, cointegration_score, spread[], zscore[], timestamps[]

### Backend API
- `api/routers/analysis.py` — Cointegration endpoint implementation
- `api/schemas.py` — Pydantic response models

### Charts & Theme
- `frontend/src/components/charts/PlotlyChart.tsx` — Shared Plotly wrapper (dark theme, SSR-safe, dynamic import)
- `frontend/src/lib/theme.ts` — Mantine theme + `PLOTLY_DARK_TEMPLATE`

### Codebase Conventions
- `.planning/codebase/CONVENTIONS.md` — Naming, imports, component patterns

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PlotlyChart` wrapper: Handles SSR-safe dynamic import, dark theme auto-merge, responsive sizing. All charts must go through this.
- `PairContext`: Provides `asset1`, `asset2`, `timeframe` — all needed for the `postCointegration()` call.
- `postCointegration()` in `api.ts`: Already typed, returns everything needed for both stat cards and charts.
- `PLOTLY_DARK_TEMPLATE` in `theme.ts`: Must be used for chart consistency with Academy.

### Established Patterns
- All pages are `'use client'` with `useState` for loading/error/data
- Data fetching via `useEffect` with cleanup flag pattern
- Mantine `Container`, `Stack`, `Paper`, `SimpleGrid` for layout
- `Badge` component for colored labels

### Integration Points
- Replace `<Text c="dimmed">Statistics — coming in Phase 2</Text>` in `pair-analysis/page.tsx` line 97 with the new Statistics tab content component
- Component should be extracted to its own file (e.g., `frontend/src/components/pair-analysis/StatisticsTab.tsx`) to keep the page file manageable

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

*Phase: 02-statistics-tab*
*Context gathered: 2026-03-31*
