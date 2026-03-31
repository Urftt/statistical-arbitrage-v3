# Feature Research

**Domain:** Crypto statistical arbitrage — pair research & backtesting frontend
**Researched:** 2026-03-31
**Confidence:** HIGH (backend already built; features are strongly constrained by what the API already returns)

---

## Context

This research covers the *frontend* milestone only. The backend (FastAPI) is complete with all 8 research modules, a backtesting engine, grid search optimizer, and walk-forward validator. The work is building the UI that consumes these APIs. Features are categorized from the perspective of what a quantitative researcher or trader expects when working with a pair trading research tool.

Reference platforms studied: Pair Trading Lab, backtesting.py, Gainium, CryptoTailor, Tradewell, QuantConnect, AmibrokerWalk-Forward, TrendSpider.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that users assume exist. Missing one of these makes the product feel broken or unusable.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Pair Scanner table with sortable columns** | Every screener has a sortable results table. Users need to sort by p-value, half-life, correlation to find candidates. | MEDIUM | API returns full scan results via `GET /api/academy/scan`. Table needs: p-value, is_cointegrated badge, half-life, correlation, cointegration_score columns. |
| **Cointegrated vs not-cointegrated visual split** | Without a clear pass/fail signal, users can't distinguish which pairs are worth investigating. | LOW | API already categorizes results. Render as two sections or a badge column. |
| **Click a pair to open deep analysis** | Screeners are browse-then-drill patterns. Clicking a row without navigating to analysis is a dead end. | LOW | Navigate to Pair Analysis page with pair pre-selected via PairContext. |
| **Spread chart (price series overlay)** | The most basic visualization for a pair. Users need to see if the two prices track each other. | LOW | API returns `spread` and `timestamps` in CointegrationResponse. Plotly line chart. |
| **Z-score chart with threshold lines** | Z-score with ±entry and ±exit lines drawn is the canonical signal visualization for mean-reversion. | LOW | API returns `zscore` series. Add horizontal lines at ±1, ±2 as overlays. |
| **Equity curve chart** | Every backtesting tool shows equity over time. Missing this = users can't see if a strategy made money. | LOW | API returns `equity_curve` as timestamped list. Plotly line chart. |
| **Key metrics summary (Sharpe, drawdown, win rate, P&L)** | Standard metric card cluster for any backtest result. Users scan these before reading charts. | LOW | API returns `MetricSummary` with all needed fields. Render as stat cards above charts. |
| **Trade log table** | Traders verify individual trades to check exit reasons, P&L, and holding times. Expected by anyone who takes backtesting seriously. | MEDIUM | API returns full `trade_log`. Table with entry/exit timestamps, direction, net_pnl, exit_reason. |
| **Parameter controls for backtest** | Tuning thresholds and lookback is the core interactive loop. A backtest with fixed parameters has no research value. | MEDIUM | Expose: entry_threshold, exit_threshold, lookback_window, stop_loss, position_size, transaction_fee. Sliders or number inputs with "Run Backtest" button. |
| **Cointegration test stats (p-value, half-life, hedge ratio)** | Users need to validate a pair quantitatively before backtesting it. | LOW | Render from CointegrationResponse as a stat card row. |
| **Loading state on heavy operations** | Scans, backtests, and grid searches take 1–30+ seconds. No feedback = users think it crashed. | LOW | Mantine LoadingOverlay or skeleton on result areas. |
| **Error state handling** | API can return 404 (no cached data) or 500 (analysis failed). Silently empty UI = confusion. | LOW | Show inline error with reason; e.g. "No cached data for this pair at 1h" with actionable hint. |

---

### Differentiators (Competitive Advantage)

Features that set this tool apart from generic screeners. Aligned with the project's learning-first core value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Research-to-backtest parameter flow** | Each research module (lookback sweep, z-score threshold sweep) returns `recommended_backtest_params`. A single "Apply to Backtest" button pre-fills the Backtest tab with those parameters. No other retail tool automates this. | MEDIUM | Already in API responses. UI needs to pass the payload from Research tab to Backtest tab state. |
| **Contextual takeaway text per research module** | Each of the 8 research modules returns a `takeaway` with severity (info/warning/error). Surfacing this as highlighted callout text teaches users what the result means. | LOW | Already in API response. Render as Mantine Alert with severity color. Do not bury in tooltips. |
| **Data quality preflight display** | The backtest engine runs preflight checks and surfaces blockers and warnings (e.g., "only 12 usable trades", "spread is non-stationary"). Most retail tools hide this. | LOW | `data_quality` field in BacktestResponse. Show before metrics if status is "blocked". |
| **Honest reporting footer** | The API returns an `HonestReportingFooter` with execution assumptions and limitations. Displaying this educates users and builds trust. Very few tools do this. | LOW | Render as a collapsible "Assumptions & Limitations" section at bottom of Backtest tab. |
| **Walk-forward stability verdict badge** | Walk-forward returns a `stability_verdict` ("stable", "moderate", "fragile") and `train_test_divergence` ratio. A clear verdict badge (green/yellow/red) is more actionable than fold metrics tables alone. | LOW | Already computed by API. Badge + divergence ratio + per-fold train vs test Sharpe chart. |
| **Parameter heatmap for grid search** | Plotting Sharpe (or other metric) across a 2D grid of parameter combinations reveals whether the best result is an isolated peak (fragile) or a plateau (robust). Standard in backtesting.py, rare in web apps. | HIGH | API returns `cells` as a flat list with `params` dict. Frontend must reconstruct 2D grid and render as Plotly heatmap. |
| **Robustness score display** | `robustness_score` is the fraction of best-cell neighbors within 80% of best metric. Surfacing this number (and its interpretation) warns users against over-relying on grid search winners. | LOW | Already in GridSearchResponse. Render next to best-cell metrics with a tooltip explanation. |
| **Overfitting engine warnings display** | The backtest engine emits structured `EngineWarning` payloads for overfitting signals (Sharpe > 3.0, smooth equity curve, etc.). Displaying these in a warning banner before metrics is rare in retail tools. | LOW | Use `warnings` list in BacktestResponse. Render as Mantine Alerts sorted by severity. |
| **Rolling cointegration stability chart** | The rolling-stability research module returns per-window p-values over time, showing whether cointegration holds consistently or only in certain periods. Visual presentation of this is nearly absent in consumer tools. | LOW | `results` in RollingStabilityResponse is a list of window-result objects. Plotly line chart of p-value over time with a p=0.05 reference line. |
| **Spread chart with trade entry/exit markers** | Overlaying trade signals on the spread chart (not just the equity curve) lets users visually inspect whether the strategy entered at good z-score extremes. | MEDIUM | `signal_overlay` in BacktestResponse has timestamps and signal_type. Plotly scatter markers on the spread/z-score chart. |

---

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Real-time scanner auto-refresh** | Users want "live" data without clicking anything | Bitvavo API rate limits make continuous polling expensive; scan takes several seconds; creates phantom sense of freshness on a research tool | Explicit "Refresh Data" button that triggers `POST /api/academy/fetch` + re-scan. Show last-fetched timestamp. |
| **Unlimited parameter grid axes (3D+)** | More parameters = feel of thoroughness | 3+ axis grids explode combinatorially; API already caps at `max_combinations`; 3D heatmaps are confusing to interpret | Lock grid search UI to exactly 2 axes at a time. Show "n combinations" count before running. |
| **Save/share backtest results** | Users want to revisit results or share with others | Adds persistence layer, auth, storage concerns out of scope for this milestone; shifts project from research tool to SaaS product | Out of scope for this milestone. Export as JSON button is a future-v2 consideration. |
| **Auto-optimize (pick best parameters automatically)** | Seems like time-saver | This is the classic overfitting trap — auto-picking the best in-sample parameters without walk-forward validation teaches users exactly the wrong habit | Show grid search best cell but require manual confirmation before applying. Display robustness score and overfitting warnings prominently. |
| **Live P&L ticker / unrealized position display** | Looks impressive in demos | This is Paper Trading territory, a separate milestone. Conflating research/backtest with live position display creates confusion about which mode the user is in. | Clear visual label "Research Mode — historical data only" in page header. |
| **Correlation heatmap for all pairs** | Familiar visualization from portfolio tools | For EUR/crypto pairs on Bitvavo, correlation alone is insufficient and misleading (high correlation != cointegrated). Displaying it as a primary metric would teach users the wrong framework. | Correlation is surfaced as one column in the scanner table alongside p-value. Not made the hero visualization. |
| **News / sentiment integration** | Traders want fundamental context for pair breaks | Adds external API dependencies, scope creep, no clear benefit for statistical methodology teaching; pairs break is already covered by rolling stability module | Out of scope. Rolling stability research module already addresses the question "has this relationship held consistently?" |

---

## Feature Dependencies

```
[Scanner Table]
    └──requires──> [GET /api/academy/scan returns data]
    └──enables──>  [Click to Pair Analysis Page]
                       └──requires──> [PairContext (already exists)]

[Pair Analysis Page — Statistics Tab]
    └──requires──> [POST /api/analysis/cointegration]
    └──shows──>    [Spread chart + Z-score chart]

[Pair Analysis Page — Research Tab]
    └──requires──> [Statistics Tab cointegration data (hedge ratio)] (used as seed)
    └──contains──> [8 research modules, each fires own API call]
    └──emits──>    [recommended_backtest_params per module]
                       └──feeds──> [Backtest Tab via shared state]

[Pair Analysis Page — Backtest Tab]
    └──requires──> [parameter controls pre-filled (from Research Tab OR manual)]
    └──requires──> [POST /api/backtest]
    └──shows──>    [Equity curve + trade log + metric cards + signal overlay]
    └──enables──>  [Optimize Tab (takes working backtest params as baseline)]

[Pair Analysis Page — Optimize Tab — Grid Search]
    └──requires──> [Backtest Tab base parameters (axis bounds derived from them)]
    └──requires──> [POST /api/optimization/grid-search]
    └──shows──>    [Heatmap + best cell + robustness score]
    └──enables──>  [Walk-Forward (takes grid-search best params as axes)]

[Pair Analysis Page — Optimize Tab — Walk-Forward]
    └──requires──> [Grid search axes (or manual axis definition)]
    └──requires──> [POST /api/optimization/walk-forward]
    └──shows──>    [Per-fold train/test Sharpe + stability verdict]
```

### Dependency Notes

- **Pair Analysis requires pair selection:** All tabs use the selected pair from PairContext. Scanner page is the primary entry point, but pair can also be selected directly in the Pair Analysis page header.
- **Research tab is independent of Backtest tab** but feeds into it via the "Apply to Backtest" button. This one-way push keeps tabs decoupled while enabling the research-to-backtest flow.
- **Optimize tab depends on a valid backtest baseline** because grid search axes need sensible min/max bounds. Defaulting axes to the current backtest parameters is the right starting point.
- **Walk-Forward depends on grid search axes** because you need to define which parameters to optimize over. They can share the same axis definitions.

---

## MVP Definition

### Launch With (this milestone)

Minimum needed to validate the research & backtesting frontend.

- [ ] **Scanner page** — sortable table with p-value, cointegration badge, half-life, correlation; click to navigate to Pair Analysis
- [ ] **Pair Analysis — Statistics tab** — cointegration stat cards + spread chart + z-score chart
- [ ] **Pair Analysis — Research tab** — all 8 modules with charts and takeaway callouts; "Apply to Backtest" button per module that produces `recommended_backtest_params`
- [ ] **Pair Analysis — Backtest tab** — parameter controls, run button, equity curve, trade markers on spread/z-score, trade log table, metric cards, data quality preflight, honest reporting footer, overfitting warnings
- [ ] **Pair Analysis — Optimize tab** — grid search with 2-axis heatmap, best cell display, robustness score, walk-forward fold table with stability verdict badge
- [ ] **Global pair selector in page header** — allows changing the pair without returning to scanner

### Add After Validation (v1.x)

- [ ] **Research tab "Apply All" button** — apply the intersection of all module recommendations to the backtest in one click (needs UX design around conflicts)
- [ ] **Backtest drawdown chart** — separate chart showing drawdown over time (currently only `max_drawdown_pct` scalar is surfaced in MVP)
- [ ] **Scanner filters** — filter by cointegration only, half-life range, minimum correlation

### Future Consideration (v2+)

- [ ] **Summary/dashboard page** — compare multiple pairs side-by-side (already in PROJECT.md as deferred)
- [ ] **Export backtest as JSON** — for users who want to archive results
- [ ] **Persist parameter presets** — save named parameter sets per pair
- [ ] **Mobile layout** — PROJECT.md explicitly defers this

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Scanner sortable table | HIGH | MEDIUM | P1 |
| Statistics tab stat cards + charts | HIGH | LOW | P1 |
| Backtest metric cards | HIGH | LOW | P1 |
| Equity curve chart | HIGH | LOW | P1 |
| Backtest parameter controls | HIGH | MEDIUM | P1 |
| Z-score chart with threshold lines | HIGH | LOW | P1 |
| Trade log table | MEDIUM | MEDIUM | P1 |
| Research modules with takeaway text | HIGH | MEDIUM | P1 |
| Research → Backtest "Apply" button | HIGH | LOW | P1 |
| Grid search heatmap | MEDIUM | HIGH | P1 |
| Walk-forward fold table + verdict | MEDIUM | MEDIUM | P1 |
| Trade entry/exit markers on spread | HIGH | MEDIUM | P1 |
| Data quality preflight display | MEDIUM | LOW | P1 |
| Honest reporting footer | MEDIUM | LOW | P1 |
| Overfitting warning banners | MEDIUM | LOW | P1 |
| Robustness score display | MEDIUM | LOW | P1 |
| Rolling stability chart | MEDIUM | LOW | P1 |
| Scanner cointegrated/not split | MEDIUM | LOW | P1 |
| Backtest drawdown chart | MEDIUM | MEDIUM | P2 |
| Scanner filters panel | LOW | MEDIUM | P2 |
| Summary/dashboard page | LOW | HIGH | P3 |
| Export JSON | LOW | LOW | P3 |

**Priority key:**
- P1: Required for this milestone — must ship
- P2: Add after core is validated
- P3: Future milestone

---

## Competitor Feature Analysis

| Feature | Pair Trading Lab | backtesting.py | Our Approach |
|---------|-----------------|----------------|--------------|
| Sortable pair scanner | Yes — large database, filter by ADF, half-life, CAGR | No — Python-only, no scanner | Yes — EUR/Bitvavo pairs only, sortable table |
| Spread + z-score charts | Yes | Via Bokeh interactive chart | Yes — Plotly dark theme |
| Equity curve | Yes | Yes — Bokeh | Yes — Plotly |
| Trade log | Yes | Yes | Yes |
| Parameter heatmap | No | Yes — `plot_heatmaps()` | Yes — 2-axis Plotly heatmap |
| Walk-forward validation | No | No (separate library) | Yes — built in |
| Research modules with takeaways | No | No | Yes — unique differentiator |
| Honest reporting footer | No | No | Yes — unique differentiator |
| Overfitting warnings inline | No | No | Yes — unique differentiator |
| Research → Backtest apply button | No | No | Yes — unique differentiator |
| Academy integration | No | No | Yes — links to lessons in context |

---

## Sources

- [Pair Trading Lab Analyzer](https://www.pairtradinglab.com/analyze) — reference for statistics tab layout and cointegration metrics display
- [backtesting.py Parameter Heatmap docs](https://kernc.github.io/backtesting.py/doc/examples/Parameter%20Heatmap%20&%20Optimization.html) — heatmap pattern for 2D grid search
- [AmibrokerWalk-Forward documentation](https://www.amibroker.com/guide/h_walkforward.html) — walk-forward fold display reference
- [LuxAlgo — Top 7 Backtesting Metrics](https://www.luxalgo.com/blog/top-7-metrics-for-backtesting-results/) — metric card content and interpretation thresholds
- [Gainium Crypto Backtesting](https://gainium.io/crypto-backtesting) — trade overlay and equity curve UX patterns
- [CryptoTailor Backtest](https://cryptotailor.io/backtest) — equity curve as primary result visualization
- [QuantInsti Walk-Forward Optimization](https://blog.quantinsti.com/walk-forward-optimization-introduction/) — train/test divergence interpretation
- [FrontierLedger — Why Most Backtests Fail](https://frontierledger.ai/foundations-core-concepts/why-most-backtests-fail-overfitting-look-ahead-bias-and-data-snooping) — overfitting warning content
- Domain code analysis: `/api/routers/`, `/src/statistical_arbitrage/backtesting/models.py`, `/api/schemas.py`

---

*Feature research for: crypto statistical arbitrage research & backtesting frontend*
*Researched: 2026-03-31*
