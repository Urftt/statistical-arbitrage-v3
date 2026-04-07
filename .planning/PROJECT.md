# Statistical Arbitrage v3

## What This Is

A learning-first crypto statistical arbitrage platform for EUR pairs on Bitvavo. Three pillars: Academy (interactive education), Research & Backtesting (find profitable pairs and validate strategies visually), and Paper Trading (future). The platform teaches users statistical arbitrage concepts through guided experiences, then lets them apply that knowledge to real market data.

## Core Value

Users can visually explore pair relationships, tune strategy parameters, and see exactly how their choices translate to euros gained or lost — making statistical arbitrage intuitive, not abstract.

## Requirements

### Validated

- ✓ Interactive Academy with 5 chapters, 18 lessons covering all stat arb concepts — existing (Phase 1)
- ✓ Real data integration in academy lessons (live pair examples) — existing (Phase 1)
- ✓ Searchable glossary with linked terms — existing (Phase 1)
- ✓ Dark mode Plotly chart system with shared wrapper — existing (Phase 1)
- ✓ Global pair selection context — existing (Phase 1)
- ✓ FastAPI backend with cointegration analysis, backtesting engine, and optimization — existing
- ✓ Parquet-based data cache with incremental Bitvavo fetches — existing
- ✓ 8 research modules (lookback sweep, rolling stability, OOS validation, timeframe comparison, spread methods, z-score thresholds, transaction costs, cointegration methods) — existing (backend)

### Active

- [x] Pair Scanner page — screen all available pairs, surface promising cointegrated candidates with scores — Validated in Phase 6: Scanner Enhancements
- [x] Pair Analysis page with tabbed interface (Statistics, Research, Backtest, Optimize) — Validated in Phase 1: Routing & Navigation Scaffold
- [x] Statistics tab — cointegration strength, spread charts, half-life, correlation, z-score dynamics — Validated in Phase 2: Statistics Tab
- [x] Research tab — all 8 research modules with visual results per selected pair — Validated in Phase 4: Research Tab
- [x] Backtest tab — run strategy with tunable parameters (z-score thresholds, lookback windows, stop-losses, position sizing), see equity curve, trade markers on spread, drawdown chart, P&L metrics (Sharpe, max drawdown, win rate) — Validated in Phase 3: Backtest Tab
- [x] Optimize tab — grid search heatmap, best cell card, walk-forward fold table, stability verdict — Validated in Phase 5: Optimize Tab
- [x] All parameters tunable (z-score entry/exit, lookback windows, stop-losses, position sizing) — Validated in Phase 5: Optimize Tab
- [ ] Visual guidance reusing Academy chart patterns and dark Plotly template
- [ ] Fast feedback where possible (chart updates), explicit "run" button for heavier compute (backtests)
- [ ] Clear profit/loss display in euros with key metrics (Sharpe ratio, max drawdown, win rate)

### Out of Scope

- Paper trading — separate future milestone
- Live trading — separate future milestone
- Summary/dashboard page comparing results across pairs — deferred
- Academy polish/improvements — not part of this milestone
- Mobile responsive design — desktop-first

## Context

This is a brownfield project with a working Academy (Phase 1 complete) and a fully implemented Python backend for analysis, backtesting, and optimization. The backend APIs exist and return data — the main work is building the frontend pages that consume them and present results visually.

The frontend had 5 stub pages (scanner, deep-dive, research, backtest, optimize) from initial scaffolding. Phase 1 restructured these into 2 main pages: Scanner and Pair Analysis (merged deep-dive + research + backtest + optimize). Old stubs are deleted.

The Academy established strong visual patterns (Plotly charts with dark theme, Mantine components, contextual explanations) that should carry over to the research & backtesting pages for consistency.

Backend readiness is uncertain — APIs exist but haven't been tested end-to-end recently. Some may need adjustments.

## Constraints

- **Tech stack**: Python 3.12 + UV, FastAPI, Next.js 16, React 19, Mantine v8, Plotly.js, Polars — all locked in from Phase 1
- **Exchange**: Bitvavo only, EUR pairs
- **Data**: Polars dataframes, never Pandas
- **Charts**: All via PlotlyChart wrapper with dark theme
- **Architecture**: Two-process (FastAPI :8000, Next.js :3000), pure Python core library

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Merge deep-dive + research + backtest + optimize into single Pair Analysis page | User wants everything about a single pair in one place — less navigation, more flow | — Pending |
| Tabbed interface for Pair Analysis (Statistics, Research, Backtest, Optimize) | Clean separation of concerns while keeping context (selected pair) | — Pending |
| Scanner as standalone page | Different purpose: browse many pairs vs analyze one | — Pending |
| Reuse Academy visual patterns | Consistency, proven UX, reduces design decisions | — Pending |
| Skip Summary page for this milestone | Focus on core flow first, summary is nice-to-have | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-07 after Phase 6 completion (milestone complete — all 6 phases delivered)*
