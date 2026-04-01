# Phase 3: Backtest Tab - Context

**Gathered:** 2026-04-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the Backtest tab content inside the existing Pair Analysis page. Users configure strategy parameters via sliders, click "Run Backtest", and see results: metric summary cards, equity curve, drawdown chart, z-score/spread charts with trade markers, a trade log table, and honest reporting. This phase delivers BT-01 through BT-10, UX-02, and UX-04.

</domain>

<decisions>
## Implementation Decisions

### Parameter Form Design
- **D-01:** All 7 strategy parameters use Mantine Slider components, consistent with Phase 2 z-score threshold sliders. Each slider shows a label and current value.
- **D-02:** Sliders are grouped into 3 labeled sections: **Signal** (lookback window, entry threshold, exit threshold), **Risk Management** (stop-loss, position size), and **Execution** (initial capital, transaction fee).
- **D-03:** Parameter form stays always visible above results — no collapsing. Users can tweak and re-run immediately.
- **D-04:** Two buttons below the form: primary "Run Backtest" button and secondary "Reset to Defaults" button. Reset restores all sliders to `DEFAULT_STRATEGY_PARAMETERS` values from `api.ts`.
- **D-05:** Backtest does NOT auto-load on mount (unlike Statistics tab). User must click "Run Backtest" explicitly — per PROJECT.md "explicit run button for heavier compute".

### Results Layout
- **D-06:** Results appear below the parameter form in this vertical order: (1) metric cards, (2) equity curve chart, (3) drawdown chart, (4) z-score chart with trade markers, (5) spread chart with trade markers, (6) trade log table, (7) collapsible Assumptions & Limitations section.
- **D-07:** 6 metric cards in a Mantine SimpleGrid row: Sharpe Ratio, Max Drawdown %, Win Rate, Total P&L (EUR), Total Trades, Final Equity. Use Paper + colored Badge pattern from Phase 2 stat cards. Remaining API metrics (Sortino, profit factor, avg trade return, avg holding period) available in expandable detail or tooltip — Claude's discretion.
- **D-08:** Results section includes a "generated for [PAIR]" context label (UX-04) to prevent misattribution.

### Signal Overlay
- **D-09:** Trade entry/exit markers appear on BOTH the z-score chart and the spread chart. Z-score chart also shows entry/exit threshold horizontal lines (like Phase 2).
- **D-10:** Marker style: up-pointing triangles for entries (green = long, red = short), down-pointing triangles for exits. Stop-losses get an X marker. Standard trading chart convention.

### Warning Presentation
- **D-11:** Preflight warnings (data quality) appear as Mantine Alert banners between the Run button and results. Yellow for warnings, red for blockers. Blockers prevent results from rendering — only the blocker alert shows.
- **D-12:** Overfitting warnings (Sharpe > 3.0, too few trades, etc.) appear as a yellow Mantine Alert positioned between the metric cards and the first chart. Persistent, not dismissable. Lists each flag with explanation.
- **D-13:** Assumptions & Limitations section (BT-09) uses Mantine Accordion/Collapse at the very bottom of results. Collapsed by default. Shows execution model, fee model, data basis, assumptions[], and limitations[] from the HonestReportingFooter.

### Claude's Discretion
- Exact slider min/max/step ranges for each parameter
- Default slider values (use `DEFAULT_STRATEGY_PARAMETERS` from api.ts)
- Chart heights and relative sizing
- Trade log table columns and sorting (API provides: trade_id, direction, entry/exit timestamps, prices, net_pnl, return_pct, exit_reason, bars_held, equity_after_trade)
- How secondary metrics (Sortino, profit factor, etc.) are accessible beyond the 6 main cards
- Badge color thresholds for metric cards (e.g., what Sharpe is "good" vs "poor")
- Loading state skeleton design during backtest computation
- Whether drawdown chart uses filled area or line

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frontend - Tab Location & Pattern
- `frontend/src/app/(dashboard)/pair-analysis/page.tsx` — Tab shell with placeholder to replace
- `frontend/src/components/pair-analysis/StatisticsTab.tsx` — Established tab component pattern (useState, useEffect, PlotlyChart, Mantine layout)

### API Client & Types
- `frontend/src/lib/api.ts` — `postBacktest()` function (line ~700+), `BacktestRequest`, `BacktestResponse`, `StrategyParametersPayload`, `DEFAULT_STRATEGY_PARAMETERS`, all result interfaces (MetricSummaryPayload, EquityCurvePointPayload, SignalOverlayPointPayload, TradeLogEntryPayload, DataQualityReportPayload, EngineWarningPayload, HonestReportingFooterPayload)

### Backend API
- `api/routers/backtest.py` — POST /api/backtest endpoint implementation
- `api/schemas.py` — Pydantic request/response models for backtest

### Backend Engine (reference only)
- `src/statistical_arbitrage/backtesting/engine.py` — `run_backtest()` function, BacktestResult model
- `src/statistical_arbitrage/backtesting/preflight.py` — Data quality checks, blocker/warning codes and messages

### Charts & Theme
- `frontend/src/components/charts/PlotlyChart.tsx` — Shared Plotly wrapper (dark theme, SSR-safe)
- `frontend/src/lib/theme.ts` — Mantine theme + `PLOTLY_DARK_TEMPLATE`

### State Management
- `frontend/src/contexts/PairContext.tsx` — Global pair selection (asset1, asset2, timeframe)

### Codebase Conventions
- `.planning/codebase/CONVENTIONS.md` — Naming, imports, component patterns

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PlotlyChart` wrapper: SSR-safe dynamic import, dark theme auto-merge, responsive sizing — all charts must use this
- `PairContext`: Provides `asset1`, `asset2`, `timeframe` needed for `postBacktest()` call
- `postBacktest()` in `api.ts`: Already typed with full request/response interfaces
- `DEFAULT_STRATEGY_PARAMETERS` in `api.ts`: Pre-defined defaults for all 7 slider values
- `StatisticsTab.tsx`: Template for the component pattern — useState loading/error/data, useEffect with cleanup, Mantine layout
- Phase 2 Slider pattern: Mantine Slider with label and value display for z-score thresholds
- Phase 2 stat card pattern: SimpleGrid + Paper + Badge with interpretive colors

### Established Patterns
- All pages/tabs are `'use client'` with `useState` for loading/error/data
- Data fetching via `useEffect` with cancellation flag (`let cancelled = false`)
- Tab content extracted to `components/pair-analysis/` directory
- Mantine `Container`, `Stack`, `Paper`, `SimpleGrid`, `Alert`, `Badge` for layout
- Charts go through PlotlyChart wrapper with dark template

### Integration Points
- Replace "Backtest — coming in Phase 3" placeholder in pair-analysis/page.tsx tab panel
- New component: `frontend/src/components/pair-analysis/BacktestTab.tsx`
- Imports: `usePairContext()`, `postBacktest()`, `DEFAULT_STRATEGY_PARAMETERS`, `PlotlyChart`

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

*Phase: 03-backtest-tab*
*Context gathered: 2026-04-01*
