# Progress Tracker

## Current Status
**Phase**: 1 (Academy) — COMPLETE ✓
**Branch**: merged to `main`
**Next**: Phase 2 — Deep Dive page + Scanner handoff

## Completed

### Phase 0: Port & Scaffold
- [x] Python project setup (pyproject.toml, UV, Python 3.12)
- [x] Backend ported from v2 (src/, api/, config/, tests/)
- [x] 174 unit tests passing
- [x] Next.js 16 + React 19 + Mantine v8 + Plotly initialized
- [x] Dark theme + Plotly wrapper (SSR-safe)
- [x] App shell: 3-pillar sidebar, header with pair selectors
- [x] Typed API client (all v2 endpoints)
- [x] PairContext for global pair state
- [x] Glossary: 26+ terms, searchable page, GlossaryLink component
- [x] All 10 routes scaffolded with placeholder content
- [x] Frontend build passing

### Phase 1: Academy — COMPLETE ✓

#### Academy Framework
- [x] Step-by-step wizard with progress bar, chapter stepper, Back/Next nav
- [x] Curriculum structure: 5 chapters, 18 lessons (lib/academy.ts)
- [x] Clickable stepper steps (allowStepSelect)
- [x] Chapter jump dropdown for cross-chapter navigation
- [x] Scroll to top on navigation
- [x] GlossaryLink → hover tooltip (dark themed, no page navigation)
- [x] "Start Research" graduation button → navigates to /scanner
- [x] Chart-first layout: interactive element up top, explanation below

#### Chapter 1: The Big Idea (3 lessons) ✓
- [x] L1.1: What is Statistical Arbitrage? — mean-reversion strength slider
- [x] L1.2: Pairs Trading Explained — correlation slider + z-score signal chart
- [x] L1.3: Your First Look at Real Data — real crypto pair selector (API data)

#### Chapter 2: Finding Pairs (4 lessons) ✓
- [x] L2.1: Correlation — interactive slider, "correlation trap" showing trending spread
- [x] L2.2: Cointegration — dogs-on-leash intuition, cointegrated vs correlated toggle
- [x] L2.3: Engle-Granger Test — OLS regression scatter + residuals (axes fixed: asset2 on x)
- [x] L2.4: Stationarity & ADF Test — stationary vs non-stationary toggle, stationarity badge uses is_cointegrated

#### Chapter 3: The Spread & Signals (4 lessons) ✓
- [x] L3.1: Building the Spread — hedge ratio slider with scatter + residuals
- [x] L3.2: Z-Scores — rolling window size slider
- [x] L3.3: Entry & Exit Signals — entry + exit threshold sliders with signal markers, exit threshold lines on chart
- [x] L3.4: Half-Life — half-life slider with decay curve, client-side AR(1) + ACF chart

#### Chapter 4: Strategy & Backtesting (4 lessons) ✓
- [x] L4.1: From Signals to Strategy — position size slider + equity curve
- [x] L4.2: Your First Backtest — trade stepper (walk through individual trades)
- [x] L4.3: Reading Backtest Results — metric view switcher (Sharpe, drawdown, win rate)
- [x] L4.4: Overfitting — complexity slider (parameters vs performance)

#### Chapter 5: Putting It All Together (3 lessons) ✓
- [x] L5.1: The Research Pipeline — phase explorer (5 pipeline stages)
- [x] L5.2: Optimization & Walk-Forward — train/test split slider
- [x] L5.3: Graduation — concept review + "Go to Scanner" CTA

#### Live Data System ✓
- [x] `/api/academy/scan` endpoint — auto-fetches top 20 EUR pairs from Bitvavo
- [x] 90%+ data completeness filter to avoid gappy altcoins
- [x] 5-minute scan result cache
- [x] `AcademyDataContext` — shared good pair (lowest p-value) + bad pair (~0.3-0.5 p-value)
- [x] "Load live data" button in AcademyWizard with teal/red pair badges
- [x] Modular tab system: TabRawPrices, TabNormalizedPrices, TabSpread, TabZScore, TabZScoreSlider, TabSignals, TabHalfLife, TabScatterOLS, TabResiduals, TabADFTest
- [x] Each lesson composes only the tabs relevant to its concept

#### Scanner Page ✓
- [x] "Fetch Top 20 Coins from Bitvavo" button
- [x] Coin selection chips, timeframe selector
- [x] Batch cointegration scan with color-coded results table

## Upcoming

### Phase 2: Deep Dive Page + Scanner Handoff
- Scanner → click pair → Deep Dive page
- Full single-pair analysis (prices, spread, z-score, correlation, cointegration results)

### Phase 3: Backtest Page
- Run strategy with specific parameters
- Equity curve, trade log, metrics dashboard

### Phase 4: Research Modules (8 modules)
- Lookback sweep, rolling stability, OOS validation, timeframe comparison
- Spread method, z-score threshold, transaction costs, cointegration method

### Phase 5: Optimization + Summary
- Grid search + walk-forward panels
- Research summary aggregation

## Decisions Log
- **Framework**: Next.js 16 + React 19 + Mantine v8 (stick with React, not switch to Nuxt)
- **Git strategy**: Branch per phase, conventional commits, merge commits to main
- **Testing**: Backend unit tests + `npm run build` as gate + visual verification
- **Academy design**: 5 chapters, ~18 lessons, Brilliant-style interactive, real crypto data from start
- **Target learner**: Data scientist who knows stats, learning finance/stat arb domain
- **Academy graduation**: Full pipeline understanding (pair selection → backtest interpretation)
- **Lesson layout**: Chart-first wizard (interactive element up top, explanation below)
- **Interactivity**: From lesson 1 — every lesson has at least one interactive element
- **UI philosophy**: Calm text with occasional emphasis, no card/badge/alert overload
- **Real data approach**: Modular tab components per lesson, not one-size-fits-all component
- **Pair selection**: Auto-pick good (lowest p-value) and bad (~0.3-0.5 p-value) pairs from live scan
