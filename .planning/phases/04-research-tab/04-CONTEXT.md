# Phase 4: Research Tab - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the Research tab content inside the existing Pair Analysis page. Users can run any of the 8 research modules independently, view chart results with contextual takeaway callouts, and carry recommended parameters directly into the Backtest tab via "Apply to Backtest". This phase delivers RSRCH-01 through RSRCH-05.

</domain>

<decisions>
## Implementation Decisions

### Module Layout & Sections
- **D-01:** Use Mantine Accordion for the 8 research modules. Each module is a collapsible section with title and Run button visible in the accordion header (no need to expand first).
- **D-02:** Multiple modules can be expanded simultaneously (`multiple` prop on Accordion). Users can compare findings across modules.
- **D-03:** Modules are grouped under 3 labeled section headers:
  - **Pair Stability**: Rolling Stability, OOS Validation, Cointegration Method
  - **Parameter Tuning**: Lookback Window Sweep, Z-Score Threshold, Transaction Cost
  - **Method Comparison**: Spread Method, Timeframe Comparison
- **D-04:** Per-module Run buttons only — no "Run All" button. Matches RSRCH-01 ("run each independently") and avoids overwhelming the user with 8 simultaneous results.
- **D-05:** Run button is in the accordion header, visible when collapsed. Clicking Run on a collapsed section auto-expands it when results arrive.

### Apply to Backtest Mechanism
- **D-06:** Lift backtest parameter state to the pair-analysis page level. `page.tsx` holds `pendingBacktestParams` state via `useState<BacktestRequest | null>(null)`. Research tab receives `onApplyToBacktest` callback; Backtest tab receives `pendingParams` prop and `onParamsConsumed` callback.
- **D-07:** Clicking "Apply to Backtest" auto-switches to the Backtest tab with params pre-filled in the form. This resolves the STATE.md blocker about cross-tab state design.
- **D-08:** Apply does NOT auto-run the backtest — only pre-fills the form. User reviews and clicks Run manually, consistent with Phase 3 decision that backtests require explicit Run click.

### Chart Types
- **D-09:** Claude's discretion on chart type per module based on data structure. Appropriate types include: bar charts for comparisons (lookback sweep, spread methods), line charts for time series (rolling stability), grouped bars for paired data (OOS validation), heatmaps for 2D parameter sweeps (z-score thresholds), tables for categorical data (coint methods).

### Takeaway Callout Design
- **D-10:** Use Mantine Alert component for takeaway callouts, colored by severity: green (color="green"), yellow (color="yellow"), red (color="red"). Placed between the chart and the Apply to Backtest button within each accordion section.
- **D-11:** Takeaway text is rendered verbatim from the backend `takeaway.text` field — no frontend interpretation of the message content.

### Claude's Discretion
- Exact chart heights and sizing per module
- Chart configuration details (axis labels, hover tooltips, reference lines)
- Module ordering within each group
- Loading state skeleton design while module is computing
- Whether to show a "recommended" badge on the best result row/bar in charts
- How to handle modules where `recommended_backtest_params` is null (hide Apply button vs show disabled)
- Exact section header styling for the 3 groups

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frontend - Tab Location & Pattern
- `frontend/src/app/(dashboard)/pair-analysis/page.tsx` — Tab shell; will need `pendingBacktestParams` state added here for D-06
- `frontend/src/components/pair-analysis/StatisticsTab.tsx` — Established tab component pattern (useState, useEffect, PlotlyChart, Mantine layout)
- `frontend/src/components/pair-analysis/BacktestTab.tsx` — Needs `pendingParams` and `onParamsConsumed` props added for D-06/D-07

### API Client & Types
- `frontend/src/lib/api.ts` — All 8 research module functions and interfaces (lines 246-494, 699-811): `postLookbackSweep`, `postRollingStability`, `postOOSValidation`, `postTimeframeComparison`, `postSpreadMethodComparison`, `postZScoreThreshold`, `postTxCost`, `postCointMethodComparison`. Each response includes `takeaway: ResearchTakeawayPayload` and most include `recommended_backtest_params: BacktestRequest | null`.

### Backend API
- `api/routers/research.py` — All 8 research endpoints under `/api/research/`
- `api/schemas.py` — Pydantic response models for research modules

### Charts & Theme
- `frontend/src/components/charts/PlotlyChart.tsx` — Shared Plotly wrapper (dark theme, SSR-safe)
- `frontend/src/lib/theme.ts` — Mantine theme + `PLOTLY_DARK_TEMPLATE`

### State Management
- `frontend/src/contexts/PairContext.tsx` — Global pair selection (asset1, asset2, timeframe)

### Next.js Guide
- `frontend/AGENTS.md` — Read Next.js docs in `node_modules/next/dist/docs/` before writing code (breaking changes from training data)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PlotlyChart` wrapper: SSR-safe dynamic import, dark theme auto-merge, responsive sizing — all charts must use this
- `PairContext`: Provides `asset1`, `asset2`, `timeframe` needed for all research API calls
- All 8 research API functions already typed in `api.ts` with full request/response interfaces
- `ResearchTakeawayPayload` interface: `{ text: string; severity: 'green' | 'yellow' | 'red' }`
- Phase 2 stat card pattern: SimpleGrid + Paper + Badge with interpretive colors
- Phase 3 Alert pattern: Mantine Alert with color variants for warnings

### Established Patterns
- All pages/tabs are `'use client'` with `useState` for loading/error/data
- Click-triggered fetch for heavy compute (Phase 3 pattern) — each module Run button triggers its API call
- Tab content extracted to `components/pair-analysis/` directory
- Mantine `Container`, `Stack`, `Paper`, `Accordion`, `Alert`, `Badge`, `Button` for layout

### Integration Points
- Replace "Research — coming in Phase 4" placeholder in pair-analysis/page.tsx tab panel
- New component: `frontend/src/components/pair-analysis/ResearchTab.tsx`
- Modify `page.tsx`: Add `pendingBacktestParams` state and pass as props to Research and Backtest tabs
- Modify `BacktestTab.tsx`: Accept `pendingParams` prop, consume on mount/change to pre-fill form
- Tab switching: page.tsx needs programmatic tab change when Apply to Backtest is clicked (controlled Tabs value)

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

*Phase: 04-research-tab*
*Context gathered: 2026-04-02*
