# Statistical Arbitrage v3 — Project Plan

## Vision
A learning-first crypto statistical arbitrage platform. The Academy teaches stat arb interactively using real data (Brilliant-style), Research & Backtesting validates strategies systematically, and Paper Trading tests them live. Education flows into good decisions.

## Tech Stack
- **Backend**: Python 3.12, FastAPI, Polars, statsmodels/scipy, ccxt, Pydantic v2, UV
- **Frontend**: Next.js 16 (App Router), React 19, Mantine v8, Plotly.js, TypeScript strict
- **Testing**: pytest (backend), browser preview testing
- **Data**: Parquet storage, Bitvavo exchange (EUR pairs), CCXT

---

## Current Status

### Completed
- **Phase 0**: Full backend port (174 unit tests passing), Next.js frontend scaffolded, all routes, dark theme, Plotly wrapper, typed API client, glossary
- **Phase 1 (Academy)**: All 5 chapters, 18 lessons built with chart-first layout and interactive elements (sliders, toggles, segmented controls)
- **Real data in Academy**: Dynamic `RealDataExample` component using `/api/academy/scan` to find real cointegrated/non-cointegrated pairs automatically
- **Scanner page**: Coin selection with chips, timeframe picker, batch cointegration scan with color-coded results table
- **Academy UX**: Chapter jump dropdown, clickable lesson stepper, scroll-to-top, "Start Research" graduation button
- **GlossaryLink**: Hover tooltips (no page navigation), 26+ terms

### In Progress
- Scanner → Deep Dive handoff (click pair to analyze)
- More cached data needed (currently 5 coins: BTC, ETH, ETC, LTC, XRP)

### Next Up
- Phase 6: Deep Dive page, Backtest page
- Phase 7: 8 research modules
- Phase 8: Optimization + Summary

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                    │
│                                                         │
│  ┌──────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ Academy  │  │ Research & Back  │  │   Glossary    │  │
│  │ 5 chaps  │  │ test             │  │   + Links     │  │
│  │ 18 lessons│  │ Scan → Analyze → │  │               │  │
│  │          │  │ Research → Back  │  │               │  │
│  │          │  │ test → Optimize  │  │               │  │
│  └──────────┘  └──────────────────┘  └───────────────┘  │
│                         │                               │
│              REST API (fetch)                            │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────┐
│                   BACKEND (FastAPI)                      │
│                                                         │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │  Data   │ │ Analysis │ │ Strategy │ │ Backtesting│  │
│  │ Cache   │ │ Coint.   │ │ Z-Score  │ │ Engine     │  │
│  │ Manager │ │ Research │ │ Signals  │ │ Optimizer  │  │
│  └─────────┘ └──────────┘ └──────────┘ └────────────┘  │
│                                                         │
│  ┌─────────┐ ┌──────────────────────────────────────┐   │
│  │ Academy │ │ Bitvavo (CCXT) ←→ Parquet Cache      │   │
│  │ Scan    │ └──────────────────────────────────────┘   │
│  └─────────┘                                            │
└─────────────────────────────────────────────────────────┘
```

---

## Academy Curriculum (BUILT)

### Chapter 1 — THE BIG IDEA (3 lessons)
| # | Lesson | Interactive Element |
|---|--------|-------------------|
| 1.1 | What is Statistical Arbitrage? | Mean-reversion strength slider |
| 1.2 | Pairs Trading Explained | Correlation slider + z-score signal chart |
| 1.3 | Your First Look at Real Data | Real crypto pair selector (API data) |

### Chapter 2 — FINDING PAIRS (4 lessons)
| # | Lesson | Interactive Element |
|---|--------|-------------------|
| 2.1 | Correlation — The Familiar Friend | Correlation slider (r = -1 to +1) |
| 2.2 | Cointegration — The Real Test | Leash tightness slider |
| 2.3 | The Engle-Granger Test | Hedge ratio slider (find optimal beta) |
| 2.4 | Stationarity & The ADF Test | Stationary vs non-stationary toggle |

### Chapter 3 — THE SPREAD & SIGNALS (4 lessons)
| # | Lesson | Interactive Element |
|---|--------|-------------------|
| 3.1 | Building the Spread | Hedge ratio slider with scatter + residuals |
| 3.2 | Z-Scores — Standardizing the Spread | Rolling window size slider |
| 3.3 | Entry & Exit Signals | Entry + exit threshold sliders with signal markers |
| 3.4 | Half-Life — How Fast Does It Revert? | Half-life slider with decay curve |

### Chapter 4 — STRATEGY & BACKTESTING (4 lessons)
| # | Lesson | Interactive Element |
|---|--------|-------------------|
| 4.1 | From Signals to Strategy | Position size slider + equity curve |
| 4.2 | Your First Backtest | Trade stepper (walk through individual trades) |
| 4.3 | Reading Backtest Results | Metric view switcher (Sharpe, drawdown, win rate) |
| 4.4 | Overfitting — The Silent Killer | Complexity slider (parameters vs performance) |

### Chapter 5 — PUTTING IT ALL TOGETHER (3 lessons)
| # | Lesson | Interactive Element |
|---|--------|-------------------|
| 5.1 | The Research Pipeline | Phase explorer (5 pipeline stages) |
| 5.2 | Optimization & Walk-Forward | Train/test split slider |
| 5.3 | Graduation — Ready for Research | Concept review + "Go to Scanner" CTA |

---

## Research & Backtesting Flow

### 1. Scanner (BUILT)
- Coin selection with toggle chips (auto-selects all available)
- Timeframe selector (1h, 4h, 1d)
- Batch cointegration scan via `/api/academy/scan`
- Color-coded results table (green = cointegrated, red = not)
- Summary cards (total, cointegrated count, not cointegrated count)

### 2. Pair Analyzer (Deep Dive) — TODO
- Selected pair's full analysis
- Price comparison, spread, z-score, correlation
- Cointegration test results
- "Looks promising? Run research modules →"

### 3. Research Modules (8 modules) — TODO
Each module: configuration panel → run → results + takeaway + "backtest this" button

| Module | What it answers |
|--------|----------------|
| Lookback Window Sweep | What lookback period works best? |
| Rolling Stability | Is the cointegration stable over time? |
| Out-of-Sample Validation | Does in-sample cointegration predict OOS? |
| Timeframe Comparison | Which timeframe (15m, 1h, 4h) works best? |
| Spread Method | Price-level vs log-price vs ratio spread? |
| Z-Score Threshold | What entry/exit thresholds maximize returns? |
| Transaction Costs | At what fee level does the strategy break? |
| Cointegration Method | Engle-Granger vs alternatives? |

### 4. Backtester — TODO
- Run strategy with specific parameters
- Results: equity curve, trade log, metrics
- Data quality report + honest assumptions footer

### 5. Optimizer — TODO
- Grid Search + Walk-Forward panels
- Overfitting detection

### 6. Research Summary — TODO
- Aggregate findings across modules

---

## API Endpoints

### Existing (ported from v2)
- `GET /api/pairs` — list cached pairs
- `GET /api/pairs/{symbol}/ohlcv` — OHLCV data
- `POST /api/analysis/cointegration` — full cointegration test
- `POST /api/analysis/spread` — spread calculation
- `POST /api/analysis/zscore` — z-score calculation
- `POST /api/analysis/stationarity` — ADF test
- `POST /api/research/*` — 8 research modules
- `POST /api/backtest` — backtest execution
- `POST /api/optimization/grid-search` — grid search
- `POST /api/optimization/walk-forward` — walk-forward validation
- `GET/POST /api/trading/sessions/*` — paper/live trading

### New (v3)
- `GET /api/academy/scan` — batch cointegration scan for Academy + Scanner

---

## Key Design Principles
1. **Education first** — Academy is the hero. Every UX decision serves learning.
2. **Real data always** — Dynamic pair scanning, not hardcoded examples.
3. **Chart first, explain after** — Interactive element up top, text below.
4. **Interactive over passive** — Show, don't tell. Sliders > paragraphs.
5. **Honest results** — Backtests include assumptions, limitations, and overfitting warnings.
6. **Pure Python core** — Analysis/strategy/backtesting code has zero web framework imports.
7. **Look-ahead safety** — All backtesting signals use only data available at each bar.
