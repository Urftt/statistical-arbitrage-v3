# Project Research Summary

**Project:** Statistical Arbitrage v3 — Research & Backtesting Frontend
**Domain:** Interactive financial backtesting UI on top of an existing FastAPI + Next.js application
**Researched:** 2026-03-31
**Confidence:** HIGH

## Executive Summary

This milestone adds a research and backtesting frontend to an already-functional backend. The stack is locked in from Phase 1 (Next.js 16, React 19, Mantine v8, Plotly.js, FastAPI) and no new framework decisions are required. The primary engineering task is building a four-tab Pair Analysis page (Statistics, Research, Backtest, Optimize) that correctly integrates with the existing API, alongside enhancing the scanner page with a drill-down action. All backend computation is complete — every metric, recommendation, and warning is already returned by the API. The frontend's job is to surface these faithfully without adding its own interpretation.

The recommended architecture is a single-page shell with four lazy-loaded tab components, each owning its own fetch lifecycle. Tab results are local state; only the selected pair is global via the existing `PairContext`. Expensive computations (backtest, grid search, walk-forward, each research module) must sit behind explicit "Run" buttons — never triggered by form changes. The scanner-to-pair-analysis navigation flow is the primary user journey and must work end-to-end before any tab is built.

The key risk is not technical complexity but UX integrity: the backend already provides honest, education-aware data (in-sample labels, overfitting warnings, look-ahead-bias disclosures, honest reporting footers). If the UI buries or ignores these, the platform becomes a tool that teaches bad habits instead of good ones. Every pitfall identified in research comes down to the same pattern — surfacing backend signals prominently rather than hiding them for a cleaner-looking result.

---

## Key Findings

### Recommended Stack

The core stack requires no changes. Two small supporting libraries are worth adding: `use-debounce` (^10.1.1) for lightweight preview debouncing on cheap operations, and `mantine-datatable` (^8.3.13) for the sortable grid-search results table in the Optimize tab. Both are Mantine v8 and React 19 compatible.

Within the existing stack, four patterns are non-negotiable: use `Slider.onChangeEnd` (not `onChange`) for parameter controls that could trigger API calls; use `keepMounted={false}` on the four-tab `Tabs` component for lazy per-tab data loading; use `uirevision` in Plotly layouts to preserve zoom state across backtest re-runs; and use `useTransition` from React 19 to model the "Run" button's loading state.

**Core technologies:**
- Mantine `Tabs` with `keepMounted={false}`: tab switching without re-fetching data — lazy per-tab activation
- Mantine `Slider` + `onChangeEnd`: parameter tuning without hammering the API on every drag pixel
- Mantine `NumberInput` + `clampBehavior="strict"`: bounds-validated parameter entry paired with Sliders
- Plotly subplots via `yaxis.domain`: stacked equity + drawdown charts with linked zoom/pan at no extra cost
- Plotly `type: 'heatmap'` with `colorscale: 'RdYlGn'`: grid search parameter heatmap, already within Plotly's comfortable render range at 500 cells
- `mantine-datatable` ^8.3.13: sortable backtest results table — saves significant implementation time over native `Table`
- `use-debounce` ^10.1.1: `useDebouncedCallback` for lightweight previews only; not a substitute for Run buttons

### Expected Features

The backend API already returns all data required for every feature. Priority is determined by the user journey, not backend readiness.

**Must have (table stakes):**
- Pair Scanner sortable table (p-value, cointegration badge, half-life, correlation) — users cannot find pairs without this
- Click-to-pair-analysis navigation — every screener expects browse-then-drill; a dead-end scanner is unusable
- Statistics tab: spread chart, z-score chart with threshold lines, cointegration stat cards — canonical pair trading visualization
- Backtest tab: parameter controls, Run button, equity curve, trade log, metric cards (Sharpe, drawdown, win rate, P&L) — the core backtesting loop
- Loading state on all heavy operations — scans, backtests, grid searches take 1–60 seconds; no feedback looks like a crash
- Error state handling — API returns 404 (no cached data) and structured errors that need human-readable display

**Should have (differentiators — all unique to this platform):**
- Research tab with 8 modules, each showing a contextual `takeaway` callout — no other retail tool does this
- Research-to-backtest "Apply" button that pre-fills Backtest tab from recommended params — unique workflow
- Overfitting warning banners (`warnings` array from API) displayed inline before metrics — rare in consumer tools
- Data quality preflight display before backtest metrics — makes limitations visible, not hidden
- Honest reporting footer (`footer.limitations`) as a collapsible section — builds user trust
- Grid search parameter heatmap with robustness score — standard in quantitative tools, absent in most web apps
- Walk-forward stability verdict badge (Stable / Moderate / Fragile) — more actionable than raw fold tables
- Trade entry/exit markers overlaid on the spread/z-score chart — not just equity curve
- Rolling cointegration stability chart (p-value over time) — absent from consumer tools

**Defer (v2+):**
- Summary/dashboard page comparing multiple pairs (explicitly deferred in PROJECT.md)
- Export backtest results as JSON
- Persist named parameter presets per pair
- Real-time scanner auto-refresh (API rate limits make continuous polling expensive)
- Mobile layout (explicitly deferred)
- 3D+ parameter grid axes (combinatorial explosion; 2-axis heatmap is the right model)

### Architecture Approach

The Pair Analysis page is a tabbed shell at `/pair-analysis` that reads `{ asset1, asset2, timeframe }` from the existing `PairContext`. Each of the four tab components owns its own `{ data, loading, error }` state and clears it when the pair changes. No new context providers are needed. Statistics tab auto-fetches on activation; Research tab uses per-module Run buttons; Backtest and Optimize tabs use explicit Run buttons. `api.ts` is already fully typed — tab components import fetch functions directly. `PlotlyChart` stays generic; data transformation (API response → Plotly traces) happens inside each tab, not inside the chart wrapper.

**Major components (new):**
1. `app/(dashboard)/pair-analysis/page.tsx` — tabbed shell; owns tab state and pair-change invalidation
2. `components/pair-analysis/StatisticsTab.tsx` — fetch-on-activate: cointegration stats + spread + z-score charts
3. `components/pair-analysis/ResearchTab.tsx` — 8 accordion sections, each with independent Run button and lazy chart mount
4. `components/pair-analysis/BacktestTab.tsx` — parameter form + Run button + equity curve + trade log + metric cards
5. `components/pair-analysis/OptimizeTab.tsx` — axis configuration + grid search heatmap + walk-forward fold table
6. `components/pair-analysis/RunButton.tsx` — shared "run / loading / error" button (Backtest and Optimize share this pattern)
7. `components/pair-analysis/MetricCard.tsx` — shared stat card for Sharpe, drawdown, win rate, P&L

**Build order:** routing scaffold → Statistics tab → Backtest tab → Research tab → Optimize tab → Scanner enhancements. Each step validates the core pattern before building on top of it.

### Critical Pitfalls

1. **UI freeze during heavy computation** — Wire loading state (disabled Run button + spinner) before connecting any computation endpoint. Grid search can run for 60 seconds; zero visual feedback = users think it crashed and click again, creating duplicate requests. Use `execution_time_ms` from the response to show completion time.

2. **Stale results after pair change** — Every tab component needs a `useEffect` keyed on the selected pair that clears result state. Without this, a user switching from BTC/ETH to SOL/ADA sees BTC/ETH metrics labeled with the new pair. Always display the pair used to generate results in the results header, not just in the global selector.

3. **Overfitting presented as success** — The grid search heatmap highlights the best-Sharpe cell. If the UI shows only that cell without the API's `warnings`, `footer.limitations`, and an "in-sample" label, users will apply those parameters to live trading. All optimization results must be labeled "in-sample" and walk-forward validation must appear as the obvious next step, not an optional advanced feature.

4. **Multiple Plotly charts mounted simultaneously causing page freeze** — The Research tab with all 8 modules populated can produce 10–20 Plotly instances. Each takes ~250ms to initialize; 20 charts = 5 seconds of main-thread blocking. Use per-section Run buttons (already mandated by the project) so charts mount one at a time. Never batch-render all research results simultaneously.

5. **Look-ahead bias introduced via parameter recommendations** — Research modules recommend optimal parameters by sweeping full history. If the UI labels these as "Recommended" without "in-sample" qualifier, and the user runs a backtest on the same data with those parameters, the backtest is contaminated by the selection process. Always use the API's `takeaway.headline` / `takeaway.body` text verbatim — it already contains the honest framing. Show a contextual note whenever "Apply to Backtest" is clicked.

6. **No error boundary causes full-page crash on chart anomaly** — Research module backends can return null spreads, empty trade lists, or null metrics. A single `PlotlyChart` receiving malformed data will throw. Without a React error boundary, the entire Pair Analysis page unmounts. Add granular error boundaries at the section level before populating any charts; add an `error.tsx` at the `(dashboard)` layout level as a last-resort fallback.

---

## Implications for Roadmap

Based on the dependency graph in FEATURES.md, the build-order analysis in ARCHITECTURE.md, and the phase-to-pitfall mapping in PITFALLS.md, the following phase structure is recommended. All phases are pure frontend work; no backend changes are needed unless noted.

### Phase 1: Routing and Navigation Scaffold

**Rationale:** Every subsequent phase requires a working `/pair-analysis` route that reads from `PairContext` and a scanner that can navigate to it. Building this first costs little and validates the full navigation loop before any API work begins. It also surfaces any sidebar/routing conflicts early.

**Delivers:** Working `/pair-analysis` page (empty tabs), updated sidebar, scanner "Analyze" row action that updates `PairContext` and navigates. No API calls.

**Addresses:** Scanner click-to-navigate (table stakes), pair-change invalidation pattern (defined once, inherited by all tabs).

**Avoids:** Pitfall 4 (stale results) — establish the `useEffect` pair-change clearing pattern in the shell before any tab has data.

### Phase 2: Statistics Tab

**Rationale:** The simplest tab (auto-fetch, read-only, no user parameters). Exercises the full loop — PairContext → `api.ts` typed call → Plotly charts — and validates the `PlotlyChart` dark-theme patterns with real API responses. A passing Statistics tab means the plumbing is correct for all subsequent tabs.

**Delivers:** Cointegration stat cards (p-value, half-life, hedge ratio, correlation), spread chart, z-score chart with ±1/±2 threshold lines.

**Addresses:** Statistics tab (table stakes), spread chart (table stakes), z-score chart (table stakes).

**Uses:** Fetch-on-activate pattern (Pattern 1 from ARCHITECTURE.md), `PlotlyChart` wrapper.

**Avoids:** Pitfall 6 — no parameter recommendations yet, so no look-ahead labeling risk in this phase.

### Phase 3: Backtest Tab

**Rationale:** The core value proposition. Building this third, after the routing loop and Statistics tab are proven, means the pattern (Run button + loading state + metric display) is learned on the most visible feature. `MetricCard` and `RunButton` shared components created here are reused in Optimize.

**Delivers:** Parameter form (entry/exit thresholds, lookback, stop-loss, position size, fee), explicit Run Backtest button with loading state, equity curve chart, trade log table, metric cards, data quality preflight display, honest reporting footer, overfitting warning banners.

**Addresses:** All P1 backtest features from FEATURES.md, including trade entry/exit markers on spread chart.

**Uses:** `Slider` + `onChangeEnd` pattern, `useTransition` for Run button, Plotly subplots for equity + drawdown, `mantine-datatable` for trade log.

**Avoids:** Pitfall 1 (UI freeze — wire loading state first), Pitfall 5 (parameter form re-run — establish Run button pattern before any API wiring).

### Phase 4: Research Tab

**Rationale:** Depends on Backtest tab being built, because the "Apply to Backtest" cross-tab action needs a Backtest parameter form to pre-fill. Also benefits from having `RunButton` and `MetricCard` already available. The 8-module structure is the most complex UX challenge (lazy rendering, per-module state, accordion layout).

**Delivers:** 8 research modules (lookback sweep, z-score threshold sweep, OOS validation, rolling stability, etc.), each with per-module Run button, chart/table result, `takeaway` callout, and "Apply to Backtest" action that pre-fills Backtest tab with `recommended_backtest_params`.

**Addresses:** Research tab features from FEATURES.md (all P1), rolling cointegration stability chart, contextual takeaway text.

**Uses:** Mantine `Accordion` for section layout, lazy chart mounting (one PlotlyChart per section, mounted only when that section's Run button is clicked).

**Avoids:** Pitfall 3 (simultaneous Plotly mount — per-section triggering), Pitfall 6 (look-ahead labeling — use `takeaway.headline` verbatim, show contextual note on Apply).

### Phase 5: Optimize Tab

**Rationale:** Depends on Backtest tab for sensible parameter axis defaults (grid search axis bounds are derived from working backtest parameters). The most complex UI; building it last means all shared components (RunButton, MetricCard, PlotlyChart patterns) are settled.

**Delivers:** 2-axis parameter grid configuration, Run Grid Search button, Plotly heatmap of Sharpe by parameter combination, best-cell display with robustness score, in-sample labels and limitations callout, "Validate with Walk-Forward" action button, walk-forward fold table with stability verdict badge (Stable / Moderate / Fragile), per-fold train vs. test Sharpe chart.

**Addresses:** Grid search heatmap (differentiator), robustness score (differentiator), walk-forward stability verdict (differentiator).

**Uses:** Plotly `type: 'heatmap'` with `RdYlGn` colorscale, `mantine-datatable` for grid search results ranking, `use-debounce` for combination count preview.

**Avoids:** Pitfall 2 (overfitting as success — "in-sample" labels and limitations callouts are non-negotiable in this phase).

### Phase 6: Scanner Enhancements

**Rationale:** The scanner already exists from Phase 1 (navigation). This phase adds sortable columns, the cointegrated/not-cointegrated visual split, and any filter controls. Done last because it is independent of all Pair Analysis tab work and does not block anything.

**Delivers:** Sortable scanner table with p-value, cointegration badge, half-life, correlation, cointegration score; clear visual split between cointegrated and non-cointegrated pairs; "Analyze" action per row (already wired in Phase 1, now surfaced more clearly in the table UI).

**Addresses:** Scanner sortable table (table stakes), cointegrated visual split (table stakes).

**Uses:** `mantine-datatable` for sortable columns and row actions.

### Phase Ordering Rationale

- The routing scaffold must come first — nothing else can be built without knowing `/pair-analysis` works and `PairContext` flows correctly.
- Statistics before Backtest because Statistics is the simplest validation of the fetch → render pipeline; Backtest builds on that confidence.
- Backtest before Research because Research's "Apply to Backtest" action pre-fills the Backtest parameter form; building it before the form exists would require stubbing.
- Optimize last among the analysis tabs because it depends on Backtest axis defaults and needs all shared components to be stable.
- Scanner enhancements last because they are independent and the scanner already provides minimal navigation in Phase 1.
- This order matches the ARCHITECTURE.md "Build Order" exactly and matches the feature dependency graph in FEATURES.md.

### Research Flags

Phases with standard, well-documented patterns (no deeper research needed):
- **Phase 1 (Scaffold):** Standard Next.js routing and context patterns. All established in the codebase.
- **Phase 2 (Statistics):** Standard fetch-on-activate pattern with existing `PlotlyChart` wrapper. No new patterns.
- **Phase 3 (Backtest):** Run button + form pattern documented explicitly in STACK.md and ARCHITECTURE.md.

Phases that may need targeted implementation research:
- **Phase 4 (Research tab):** The "Apply to Backtest" cross-tab state action needs a clear implementation decision before coding. Specifically: does it lift param state to the page level, or use a ref-based push? The ARCHITECTURE.md recommendation (lift to page level) is right but may need a brief planning session.
- **Phase 5 (Optimize tab):** Grid search heatmap reconstruction from a flat `cells` list to a 2D Plotly matrix requires careful implementation. Walk-forward fold index-to-timestamp mapping is also a noted gotcha. Both are implementation details, not architecture questions.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Core stack is locked in from Phase 1. Two supporting libraries (`use-debounce`, `mantine-datatable`) verified against Mantine v8 and React 19 compatibility. |
| Features | HIGH | Backend is complete; features are strongly constrained by what the API already returns. Feature list derived from direct API schema inspection. |
| Architecture | HIGH | Based on direct codebase inspection of all relevant files. Patterns derived from live code, not hypotheticals. |
| Pitfalls | HIGH | Pitfalls grounded in codebase audit (`CONCERNS.md`), direct backend code inspection (synchronous handlers confirmed), and established backtesting UI literature. |

**Overall confidence:** HIGH

### Gaps to Address

- **Walk-forward index-to-timestamp mapping:** The API returns `train_start_idx` and `test_start_idx` as bar indices, not timestamps. The timestamps array is in the response context but the mapping logic is not yet designed. Address at the start of Phase 5.

- **"Apply to Backtest" cross-tab state design:** Research tab needs to pre-fill Backtest tab's parameter form. ARCHITECTURE.md recommends lifting form state to the page level, but the exact prop/callback shape needs to be defined before implementing either tab. Address at the start of Phase 4.

- **Default strategy parameters source of truth:** PITFALLS.md flags a risk that frontend-hardcoded defaults drift from backend defaults. Consider fetching defaults from a `/api/backtest/defaults` endpoint on mount rather than hardcoding in `api.ts`. Not blocking for MVP but worth a one-line implementation decision.

- **Accordion vs. flat layout for Research tab:** ARCHITECTURE.md recommends Mantine `Accordion` for the 8-module Research tab. PITFALLS.md confirms this avoids the simultaneous Plotly mount problem. Decision is implicit in the research but should be stated explicitly in the phase plan.

---

## Sources

### Primary (HIGH confidence)

- Live codebase inspection (2026-03-31): `PairContext.tsx`, `PlotlyChart.tsx`, `api.ts`, `scanner/page.tsx`, `Header.tsx`, `Sidebar.tsx`, `layout.tsx`, `api/routers/optimization.py`, `api/routers/backtest.py`, `.planning/codebase/CONCERNS.md`, `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md`, `.planning/PROJECT.md`
- [Mantine Tabs docs (v8)](https://mantine.dev/core/tabs/) — `keepMounted`, controlled mode
- [Mantine Slider docs](https://mantine.dev/core/slider/) — `onChangeEnd` vs `onChange`
- [Mantine NumberInput docs](https://mantine.dev/core/number-input/) — `clampBehavior`, `suffix`
- [mantine-datatable GitHub](https://github.com/icflorescu/mantine-datatable) — v8.3.13 Mantine v8 compatibility
- [use-debounce npm](https://www.npmjs.com/package/use-debounce) — v10.1.1, React 19 compatibility
- [Plotly.js subplots docs](https://plotly.com/javascript/subplots/) — shared x-axis via `yaxis.domain`
- [useTransition React docs](https://react.dev/reference/react/useTransition) — `isPending` pattern
- [backtesting.py Parameter Heatmap docs](https://kernc.github.io/backtesting.py/doc/examples/Parameter%20Heatmap%20&%20Optimization.html) — 2D grid search heatmap pattern
- [LuxAlgo — Top 7 Backtesting Metrics](https://www.luxalgo.com/blog/top-7-metrics-for-backtesting-results/) — metric card content
- Backend code: `src/statistical_arbitrage/backtesting/optimization.py` — `max_combinations=500` guard confirmed

### Secondary (MEDIUM confidence)

- [react-plotly.js uirevision issue #90](https://github.com/plotly/react-plotly.js/issues/90) — zoom state preservation pattern (GitHub issue, not official docs)
- Plotly.js GitHub issue #3416 — initialization time with multiple chart instances (~250ms each)
- FastAPI background tasks patterns (leapcell.io, unfoldai.com) — synchronous handler acceptable for single-user tools

### Tertiary (supporting context)

- Backtesting overfitting literature (targethit.ai, starqube.com, auquan/Medium) — p-hacking and data snooping in backtesting UIs
- [Pair Trading Lab Analyzer](https://www.pairtradinglab.com/analyze) — statistics tab layout reference
- [Gainium Crypto Backtesting](https://gainium.io/crypto-backtesting) — equity curve and trade overlay UX patterns
- [QuantInsti Walk-Forward Optimization](https://blog.quantinsti.com/walk-forward-optimization-introduction/) — train/test divergence interpretation

---

*Research completed: 2026-03-31*
*Ready for roadmap: yes*
