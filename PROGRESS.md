# Progress Tracker

## Current Status
**Phase**: 1 (Academy) — IN PROGRESS
**Branch**: `phase-1/academy-ch1`
**Next**: Chapter 3 — The Spread & Signals (4 lessons)

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
- [x] Glossary: 17 terms, searchable page, GlossaryLink component
- [x] All 10 routes scaffolded with placeholder content
- [x] Frontend build passing

### Phase 1: Academy (Chapters 1-2 done)

#### Academy Framework
- [x] Step-by-step wizard with progress bar, chapter stepper, Back/Next nav
- [x] Curriculum structure: 5 chapters, 18 lessons (lib/academy.ts)
- [x] Clickable stepper steps (allowStepSelect)
- [x] Scroll to top on navigation
- [x] GlossaryLink → hover tooltip (dark themed, no page navigation)
- [x] PlotlyChart accepts string titles (Plotly v3 compat)
- [x] JSX whitespace fix pattern: use {"string"} for text near inline elements

#### Chapter 1: The Big Idea (3 lessons) ✓
- [x] L1.1: What is Statistical Arbitrage? — coffee shop analogy, interactive mean-reversion vs random walk toggle
- [x] L1.2: Pairs Trading Explained — trade anatomy, why both sides matter, interactive z-score chart with threshold slider
- [x] L1.3: Your First Look at Real Data — real OHLCV from API, 3 pair comparisons, graceful error when API unavailable

#### Chapter 2: Finding Pairs (4 lessons) ✓
- [x] L2.1: Correlation — interactive slider, "correlation trap" showing trending spread
- [x] L2.2: Cointegration — dogs-on-leash intuition, cointegrated vs correlated toggle, cheat sheet
- [x] L2.3: Engle-Granger Test — step-by-step OLS regression scatter, residuals chart
- [x] L2.4: Stationarity & ADF Test — stationary vs non-stationary toggle with rolling stats, plain-language ADF

### Still TODO (Phase 1)
- [ ] Chapter 3: The Spread & Signals (4 lessons: spread construction, z-scores, entry/exit signals, half-life)
- [ ] Chapter 4: Strategy & Backtesting (4 lessons)
- [ ] Chapter 5: Putting It All Together (3 lessons)
- [ ] Minor polish: scroll-to-top offset for AppShell header

## Decisions Log
- **Framework**: Next.js 16 + React 19 + Mantine v8 (stick with React, not switch to Nuxt)
- **Git strategy**: Branch per phase, conventional commits, merge commits to main
- **Testing**: Backend unit tests + `npm run build` as gate + visual verification
- **Academy design**: 5 chapters, ~18 lessons, Brilliant-style interactive, real crypto data from start
- **Target learner**: Data scientist who knows stats, learning finance/stat arb domain
- **Academy graduation**: Full pipeline understanding (pair selection → backtest interpretation)
- **Lesson layout**: Step-by-step wizard (not scrollable page or card grid)
- **Interactivity**: From lesson 1 — every lesson has at least one interactive element
- **UI philosophy**: Calm text with occasional emphasis, no card/badge/alert overload

## Session Notes
- API integration tests (43) need cached market data — expected, will pass once data is cached
- v2 had Dash frontend dependencies (dash, dash-bootstrap-components) — removed in v3
- JSX whitespace: React collapses spaces between inline elements and text at line breaks. Fix: wrap adjacent text in {"string"} expressions
- Plotly v3: title and axis titles need {text: "..."} object format, not bare strings. PlotlyChart wrapper handles this for layout.title but axis titles need explicit objects in lesson code
