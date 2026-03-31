# Roadmap: Statistical Arbitrage v3 — Research & Backtesting

## Overview

This milestone builds the research and backtesting frontend on top of a complete Python backend. Work flows from a navigation scaffold that enables the scanner-to-analysis user journey, through four analysis tabs (Statistics, Research, Backtest, Optimize) built in dependency order, to a polished scanner table. Every phase delivers a coherent, independently verifiable capability that compounds on the one before it.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Routing & Navigation Scaffold** - Working /pair-analysis route, updated sidebar, and scanner drill-down navigation
- [ ] **Phase 2: Statistics Tab** - Cointegration stat cards, spread chart, and z-score chart with threshold lines
- [ ] **Phase 3: Backtest Tab** - Full backtest loop: parameter form, run button, equity curve, trade log, metrics, and honest reporting
- [ ] **Phase 4: Research Tab** - 8 research modules with per-module run buttons, takeaway callouts, and Apply-to-Backtest action
- [ ] **Phase 5: Optimize Tab** - Grid search heatmap, best-cell display, walk-forward validation, and stability verdict
- [ ] **Phase 6: Scanner Enhancements** - Sortable scanner table with cointegration badges and cointegrated/non-cointegrated visual split

## Phase Details

### Phase 1: Routing & Navigation Scaffold
**Goal**: Users can navigate from Scanner to Pair Analysis and back, with pair selection flowing correctly across the app
**Depends on**: Nothing (first phase)
**Requirements**: NAV-01, NAV-02, NAV-03, NAV-04, NAV-05
**Success Criteria** (what must be TRUE):
  1. User can click Scanner and Pair Analysis in the sidebar and land on the correct pages
  2. User can click a pair row in the Scanner and arrive at Pair Analysis with that pair shown in the header
  3. User can change the selected pair from the Pair Analysis header without leaving the page
  4. Pair Analysis shows four tab labels (Statistics, Research, Backtest, Optimize) and switching tabs does not re-fetch completed results
  5. Switching to a new pair clears any previously loaded tab results so stale data is never displayed
**Plans:** 2 plans
Plans:
- [ ] 01-01-PLAN.md — Sidebar restructure, old stub deletion, and Pair Analysis tabbed page
- [ ] 01-02-PLAN.md — Scanner row click-to-navigate and full flow verification
**UI hint**: yes

### Phase 2: Statistics Tab
**Goal**: Users can inspect the statistical relationship of their selected pair through cointegration metrics and spread/z-score charts
**Depends on**: Phase 1
**Requirements**: STAT-01, STAT-02, STAT-03, UX-01, UX-03
**Success Criteria** (what must be TRUE):
  1. User can view four stat cards showing p-value, half-life, hedge ratio, and correlation for the selected pair
  2. User can view a spread chart rendered in the dark Plotly theme consistent with the Academy
  3. User can view a z-score chart with horizontal entry and exit threshold lines drawn at configurable levels
  4. When the API returns an error, an inline message with an actionable description appears instead of a blank chart
**Plans**: TBD
**UI hint**: yes

### Phase 3: Backtest Tab
**Goal**: Users can run a backtest against their selected pair, see exactly how parameter choices translate to euros gained or lost, and trust the results through honest reporting
**Depends on**: Phase 2
**Requirements**: BT-01, BT-02, BT-03, BT-04, BT-05, BT-06, BT-07, BT-08, BT-09, BT-10, UX-02, UX-04
**Success Criteria** (what must be TRUE):
  1. User can set entry/exit thresholds, lookback window, stop-loss, position size, and transaction fee, then press Run Backtest and see a loading indicator during computation
  2. User can view an equity curve, a drawdown chart, and trade entry/exit markers overlaid on the spread or z-score chart after the backtest completes
  3. User can view metric cards showing Sharpe ratio, max drawdown, win rate, and total P&L in EUR, all labelled with the pair used to generate them
  4. User can view a trade log table with entry/exit timestamps, direction, net P&L, and exit reason
  5. User can expand an Assumptions and Limitations section showing data quality preflight warnings and the honest reporting footer before acting on results
  6. User sees overfitting warning banners (e.g., Sharpe above 3.0) displayed inline when the backtest engine flags them
**Plans**: TBD
**UI hint**: yes

### Phase 4: Research Tab
**Goal**: Users can run any of the 8 research modules independently, read contextual takeaways, and carry recommended parameters directly into the Backtest tab
**Depends on**: Phase 3
**Requirements**: RSRCH-01, RSRCH-02, RSRCH-03, RSRCH-04, RSRCH-05
**Success Criteria** (what must be TRUE):
  1. User can expand any of the 8 research module sections and press that section's Run button to load results without triggering other sections
  2. Each completed module shows its chart results and a contextual takeaway callout (info, warning, or error severity) using the backend's own headline and body text verbatim
  3. User can view the rolling cointegration stability chart showing p-value over time with a significance reference line
  4. User can click Apply to Backtest on a module and see the Backtest tab's parameter form pre-filled with that module's recommended parameters
**Plans**: TBD
**UI hint**: yes

### Phase 5: Optimize Tab
**Goal**: Users can run a grid search across two strategy parameters, inspect the heatmap to find robust combinations, and validate stability through walk-forward analysis before trusting any parameter set
**Depends on**: Phase 3
**Requirements**: OPT-01, OPT-02, OPT-03, OPT-04, OPT-05
**Success Criteria** (what must be TRUE):
  1. User can select two parameters and define their sweep ranges, then run grid search and see a heatmap of Sharpe values across all combinations
  2. User can see the best parameter combination displayed with its metrics and robustness score, labelled in-sample
  3. User can run walk-forward validation and view a per-fold table showing train and test Sharpe for each fold
  4. User can see a stability verdict badge (Stable, Moderate, or Fragile) summarising walk-forward results
**Plans**: TBD
**UI hint**: yes

### Phase 6: Scanner Enhancements
**Goal**: Users can efficiently browse all available pair candidates, sort by key metrics, and immediately distinguish cointegrated pairs from non-cointegrated ones
**Depends on**: Phase 1
**Requirements**: SCAN-01, SCAN-02, SCAN-03, SCAN-04
**Success Criteria** (what must be TRUE):
  1. User can view a table of all pair candidates with p-value, cointegration score, half-life, and correlation columns and sort by any column
  2. User can visually distinguish cointegrated pairs from non-cointegrated pairs through a badge or section split
  3. User sees a loading indicator while the scan is running and an actionable error message if the scan fails
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Routing & Navigation Scaffold | 0/2 | Planning complete | - |
| 2. Statistics Tab | 0/? | Not started | - |
| 3. Backtest Tab | 0/? | Not started | - |
| 4. Research Tab | 0/? | Not started | - |
| 5. Optimize Tab | 0/? | Not started | - |
| 6. Scanner Enhancements | 0/? | Not started | - |
