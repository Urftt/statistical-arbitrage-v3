# Requirements: Statistical Arbitrage v3 — Research & Backtesting

**Defined:** 2026-03-31
**Core Value:** Users can visually explore pair relationships, tune strategy parameters, and see exactly how their choices translate to euros gained or lost.

## v1 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### Navigation & Layout

- [x] **NAV-01**: User can navigate between Scanner and Pair Analysis pages from the sidebar
- [x] **NAV-02**: User can click a pair in the Scanner to open Pair Analysis with that pair pre-selected
- [x] **NAV-03**: User can change the selected pair from the Pair Analysis page header without returning to Scanner
- [x] **NAV-04**: Pair Analysis page uses tabbed interface (Statistics, Research, Backtest, Optimize)
- [x] **NAV-05**: Tab state clears when the user changes the selected pair (prevents stale results)

### Scanner

- [ ] **SCAN-01**: User can view a sortable table of all available pair candidates with p-value, cointegration score, half-life, and correlation columns
- [ ] **SCAN-02**: User can visually distinguish cointegrated pairs from non-cointegrated pairs (badge or section split)
- [ ] **SCAN-03**: Scanner shows loading state while scan is running
- [ ] **SCAN-04**: Scanner shows error state with actionable message if scan fails

### Statistics Tab

- [x] **STAT-01**: User can view cointegration stat cards (p-value, half-life, hedge ratio, correlation) for the selected pair
- [x] **STAT-02**: User can view a spread chart showing the price relationship between the two coins
- [x] **STAT-03**: User can view a z-score chart with entry/exit threshold lines drawn at configurable levels

### Research Tab

- [ ] **RSRCH-01**: User can run each of the 8 research modules independently for the selected pair
- [ ] **RSRCH-02**: Each research module displays its chart results and a contextual takeaway callout (info/warning/error severity)
- [ ] **RSRCH-03**: User can click "Apply to Backtest" on a research module to pre-fill the Backtest tab with recommended parameters
- [ ] **RSRCH-04**: Research modules load lazily (not all at once) to prevent chart initialization performance issues
- [ ] **RSRCH-05**: User can view rolling cointegration stability chart showing p-value over time with significance reference line

### Backtest Tab

- [ ] **BT-01**: User can configure all strategy parameters: entry threshold, exit threshold, lookback window, stop-loss, position size, transaction fee
- [ ] **BT-02**: User can run a backtest with a "Run Backtest" button and see a loading state during computation
- [x] **BT-03**: User can view an equity curve chart showing portfolio value over time
- [x] **BT-04**: User can view trade entry/exit markers overlaid on the spread or z-score chart
- [x] **BT-05**: User can view a drawdown chart showing how deep underwater the strategy went over time
- [ ] **BT-06**: User can view key metric cards: Sharpe ratio, max drawdown, win rate, total P&L in EUR
- [ ] **BT-07**: User can view a trade log table with entry/exit timestamps, direction, net P&L, and exit reason
- [ ] **BT-08**: User sees data quality preflight warnings before results if the backtest engine detects issues
- [ ] **BT-09**: User can expand an "Assumptions & Limitations" section showing the honest reporting footer
- [ ] **BT-10**: User sees overfitting warning banners (e.g., Sharpe > 3.0, smooth equity curve) when the engine detects them

### Optimize Tab

- [ ] **OPT-01**: User can configure a 2-axis grid search by selecting which two parameters to sweep and their ranges
- [ ] **OPT-02**: User can run grid search and view a parameter heatmap showing metric values across parameter combinations
- [ ] **OPT-03**: User can view the best parameter combination with its metrics and robustness score
- [ ] **OPT-04**: User can run walk-forward validation and view a fold table with train/test Sharpe per fold
- [ ] **OPT-05**: User can see a stability verdict badge (stable/moderate/fragile) for walk-forward results

### UX Quality

- [x] **UX-01**: All charts use the existing dark Plotly template consistent with the Academy
- [ ] **UX-02**: All heavy computations (backtest, grid search, walk-forward) show loading states with appropriate feedback
- [x] **UX-03**: API errors display inline with actionable messages (not silent failures)
- [ ] **UX-04**: Results display includes a "generated for [pair]" context label to prevent misattribution

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Scanner Enhancements

- **SCAN-05**: User can filter scanner results by cointegration status, half-life range, minimum correlation
- **SCAN-06**: User can refresh market data before re-scanning

### Research Enhancements

- **RSRCH-06**: User can click "Apply All" to merge recommended parameters from multiple research modules into one backtest configuration

### Export & Persistence

- **EXP-01**: User can export backtest results as JSON
- **EXP-02**: User can save named parameter presets per pair

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Paper trading | Separate future milestone |
| Live trading | Separate future milestone |
| Summary/dashboard page | Deferred — focus on core flow first |
| Real-time scanner auto-refresh | Bitvavo rate limits; research tool doesn't need live data |
| 3D+ parameter grid search | Combinatorial explosion; 2-axis is sufficient and interpretable |
| Auto-optimize (pick best params) | Classic overfitting trap; contradicts learning-first mission |
| Live P&L / position display | Paper trading territory, not research |
| News/sentiment integration | Scope creep; rolling stability module covers relationship breaks |
| Correlation heatmap as primary viz | Misleading — high correlation != cointegrated |
| Save/share results | Adds persistence/auth concerns out of scope |
| Mobile layout | Desktop-first per PROJECT.md |
| Academy improvements | Not part of this milestone |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| NAV-01 | Phase 1 | Complete |
| NAV-02 | Phase 1 | Complete |
| NAV-03 | Phase 1 | Complete |
| NAV-04 | Phase 1 | Complete |
| NAV-05 | Phase 1 | Complete |
| SCAN-01 | Phase 6 | Pending |
| SCAN-02 | Phase 6 | Pending |
| SCAN-03 | Phase 6 | Pending |
| SCAN-04 | Phase 6 | Pending |
| STAT-01 | Phase 2 | Complete |
| STAT-02 | Phase 2 | Complete |
| STAT-03 | Phase 2 | Complete |
| RSRCH-01 | Phase 4 | Pending |
| RSRCH-02 | Phase 4 | Pending |
| RSRCH-03 | Phase 4 | Pending |
| RSRCH-04 | Phase 4 | Pending |
| RSRCH-05 | Phase 4 | Pending |
| BT-01 | Phase 3 | Pending |
| BT-02 | Phase 3 | Pending |
| BT-03 | Phase 3 | Complete |
| BT-04 | Phase 3 | Complete |
| BT-05 | Phase 3 | Complete |
| BT-06 | Phase 3 | Pending |
| BT-07 | Phase 3 | Pending |
| BT-08 | Phase 3 | Pending |
| BT-09 | Phase 3 | Pending |
| BT-10 | Phase 3 | Pending |
| OPT-01 | Phase 5 | Pending |
| OPT-02 | Phase 5 | Pending |
| OPT-03 | Phase 5 | Pending |
| OPT-04 | Phase 5 | Pending |
| OPT-05 | Phase 5 | Pending |
| UX-01 | Phase 2 | Complete |
| UX-02 | Phase 3 | Pending |
| UX-03 | Phase 2 | Complete |
| UX-04 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 36 total
- Mapped to phases: 36
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-31*
*Last updated: 2026-03-31 after roadmap creation — all 36 requirements mapped*
