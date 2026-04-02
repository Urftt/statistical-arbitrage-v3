# Phase 5: Optimize Tab - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the Optimize tab content inside the existing Pair Analysis page. Users configure a 2-axis grid search by selecting which two strategy parameters to sweep and their ranges, run the search and inspect a heatmap of results, view the best parameter combination, then validate stability through walk-forward analysis. This phase delivers OPT-01 through OPT-05.

</domain>

<decisions>
## Implementation Decisions

### Axis Configuration
- **D-01:** Two Mantine Select dropdowns ("Parameter 1" and "Parameter 2") listing sweepable params: entry_threshold, exit_threshold, lookback_window, stop_loss, position_size. Below each dropdown, 3 NumberInput fields for min/max/step with sensible defaults per parameter.
- **D-02:** Base strategy parameters come from whatever the user currently has set in the Backtest tab's parameter form. If no backtest has been run yet, fall back to `DEFAULT_STRATEGY_PARAMETERS`. This requires lifting or sharing backtest param state from BacktestTab (similar to Phase 4's `pendingBacktestParams` pattern).
- **D-03:** The 2 selected sweep axes override their corresponding values in the base strategy. All non-swept parameters stay at their base values.

### Heatmap Visualization
- **D-04:** Heatmap uses Plotly hover tooltip only (no click action). Tooltip shows: parameter values, Sharpe, total P&L, win rate, and trade count for the hovered cell.
- **D-05:** Best cell is highlighted with a star annotation on the heatmap.
- **D-06:** A Select dropdown above the heatmap lets the user switch the coloring metric between Sharpe ratio, total P&L, win rate, and max drawdown. Re-colors the heatmap client-side without re-running the search (data already available from GridSearchResponse cells).
- **D-07:** Best cell summary displayed as a highlighted Paper card ABOVE the heatmap. Shows: best parameter values, Sharpe, P&L, robustness score with a Badge (e.g., Strong/Moderate/Weak). Includes an "Apply to Backtest" button.

### Page Layout & Flow
- **D-08:** Shared axis configuration section at the top of the tab (two dropdowns + range inputs). Below it, two Run buttons side-by-side: "Run Grid Search" and "Run Walk-Forward". Both use the same axes and base params.
- **D-09:** Grid Search results section appears below the buttons: best cell card, then heatmap, then warnings/honest reporting (Accordion, collapsed by default, matching Phase 3 pattern).
- **D-10:** Walk-Forward results section appears below Grid Search results. Walk-forward-specific controls (fold count NumberInput + train % Slider) are inline above the fold table results, with defaults of 5 folds and 60% train.
- **D-11:** Walk-forward fold table shows per-fold: fold index, train Sharpe, test Sharpe, train trade count, test trade count, status. Below the table: aggregate train/test Sharpe and a stability verdict Badge (Stable = green, Moderate = yellow, Fragile = red).
- **D-12:** Both grid search and walk-forward run on explicit button click only (no auto-load), consistent with Phase 3 heavy compute pattern.

### Apply to Backtest
- **D-13:** Both grid search best cell card and walk-forward results get an "Apply to Backtest" button. Reuses Phase 4's `pendingBacktestParams` / `onApplyToBacktest` mechanism — sets params and switches to the Backtest tab.
- **D-14:** Walk-forward Apply button only appears when verdict is "stable" or "moderate" (API only returns recommended params for those). For "fragile" verdict, no Apply button — the results are warning-only.

### Warning Presentation
- **D-15:** Grid search warnings (from `GridSearchResponse.warnings`) displayed as Mantine Alert banners between the Run buttons and the results, matching Phase 3 three-tier warning pattern.
- **D-16:** Walk-forward warnings displayed similarly above walk-forward results.
- **D-17:** Honest reporting footers (grid search and walk-forward each have their own) in collapsible Accordion sections at the bottom of their respective result areas.

### Claude's Discretion
- Exact min/max/step defaults per sweepable parameter
- Chart height and color scale for heatmap
- Heatmap cell annotation format (show values on cells or not)
- Star/marker style for best cell highlight
- Loading state skeleton design during grid search / walk-forward computation
- Robustness score badge thresholds and labels
- Fold table column widths and styling
- Walk-forward index-to-timestamp mapping strategy (STATE.md blocker — API returns bar indices, need readable date display)
- Whether to show execution time for grid search / walk-forward

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frontend - Tab Location & Pattern
- `frontend/src/app/(dashboard)/pair-analysis/page.tsx` — Tab shell with "Optimize — coming in Phase 5" placeholder to replace; holds `pendingBacktestParams` state from Phase 4
- `frontend/src/components/pair-analysis/StatisticsTab.tsx` — Established tab component pattern (useState, useEffect, PlotlyChart, Mantine layout)
- `frontend/src/components/pair-analysis/BacktestTab.tsx` — Has `pendingParams`/`onParamsConsumed` props and current parameter form state needed for base strategy

### API Client & Types
- `frontend/src/lib/api.ts` — `postGridSearch()` (line ~813), `postWalkForward()` (line ~826), `GridSearchRequest`, `GridSearchResponse`, `GridSearchCellPayload`, `WalkForwardRequest`, `WalkForwardResponse`, `WalkForwardFoldPayload`, `ParameterAxisPayload`, `DEFAULT_STRATEGY_PARAMETERS`, `StrategyParametersPayload`, `BacktestRequest`

### Backend API
- `api/routers/optimization.py` — POST /api/optimization/grid-search and POST /api/optimization/walk-forward endpoint implementations
- `api/schemas.py` — Pydantic request/response models for optimization

### Backend Engine (reference only)
- `src/statistical_arbitrage/backtesting/optimization.py` — `run_grid_search()` function
- `src/statistical_arbitrage/backtesting/walkforward.py` — `run_walk_forward()` function
- `src/statistical_arbitrage/backtesting/models.py` — `ParameterAxis`, `GridSearchResult`, `WalkForwardResult` domain models

### Charts & Theme
- `frontend/src/components/charts/PlotlyChart.tsx` — Shared Plotly wrapper (dark theme, SSR-safe)
- `frontend/src/lib/theme.ts` — Mantine theme + `PLOTLY_DARK_TEMPLATE`

### State Management
- `frontend/src/contexts/PairContext.tsx` — Global pair selection (asset1, asset2, timeframe)

### Next.js Guide
- `frontend/AGENTS.md` — Read Next.js docs in `node_modules/next/dist/docs/` before writing code (breaking changes from training data)

### Codebase Conventions
- `.planning/codebase/CONVENTIONS.md` — Naming, imports, component patterns

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PlotlyChart` wrapper: SSR-safe dynamic import, dark theme auto-merge, responsive sizing — all charts must use this
- `PairContext`: Provides `asset1`, `asset2`, `timeframe` needed for both optimization API calls
- `postGridSearch()` and `postWalkForward()` in `api.ts`: Already typed with full request/response interfaces
- `DEFAULT_STRATEGY_PARAMETERS` in `api.ts`: Pre-defined defaults for all 7 parameter values
- `pendingBacktestParams` state already on page.tsx from Phase 4 — Apply to Backtest mechanism ready
- Phase 3 Alert/Badge pattern for warnings and metrics
- Phase 3 Accordion pattern for collapsible honest reporting sections
- Phase 4 Accordion pattern for grouped sections

### Established Patterns
- All pages/tabs are `'use client'` with `useState` for loading/error/data
- Click-triggered fetch for heavy compute (Phase 3 pattern)
- Tab content extracted to `components/pair-analysis/` directory
- Mantine `Container`, `Stack`, `Paper`, `SimpleGrid`, `Alert`, `Badge`, `Button`, `Select`, `NumberInput`, `Slider` for layout
- Charts go through PlotlyChart wrapper with dark template

### Integration Points
- Replace "Optimize — coming in Phase 5" placeholder in pair-analysis/page.tsx tab panel (line ~120)
- New component: `frontend/src/components/pair-analysis/OptimizeTab.tsx`
- Imports: `usePairContext()`, `postGridSearch()`, `postWalkForward()`, `DEFAULT_STRATEGY_PARAMETERS`, `PlotlyChart`
- Need access to current Backtest tab parameter values for base strategy — may need to lift backtest param state to page level or read from BacktestTab via callback

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

*Phase: 05-optimize-tab*
*Context gathered: 2026-04-02*
