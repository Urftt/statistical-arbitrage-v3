# Statistical Arbitrage v3 — Project Plan

## Vision
A learning-first crypto statistical arbitrage platform. The Academy teaches stat arb interactively using real data (Brilliant-style), Research & Backtesting validates strategies systematically, and Paper Trading tests them live. Education flows into good decisions.

## Tech Stack
- **Backend**: Python 3.12, FastAPI, Polars, statsmodels/scipy, ccxt, Pydantic v2, UV
- **Frontend**: Next.js 16 (App Router), React 19, Mantine v8, Plotly.js, TypeScript strict
- **Testing**: pytest (backend), Playwright (E2E)
- **Data**: Parquet storage, Bitvavo exchange (EUR pairs), CCXT

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
│  ┌──────────────────────────────────────────────────┐   │
│  │ Bitvavo (CCXT) ←→ Parquet Cache                  │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### App Layout
```
┌──────────────────────────────────────────────────────┐
│  Logo          Statistical Arbitrage         [pair]  │
├───────────┬──────────────────────────────────────────┤
│           │                                          │
│ ACADEMY   │                                          │
│  Ch1      │         MAIN CONTENT AREA                │
│  Ch2      │                                          │
│  Ch3      │    Lesson text + interactive demos        │
│  Ch4      │                                          │
│  Ch5      │    [Charts, sliders, comparisons]         │
│           │                                          │
│ RESEARCH  │                                          │
│  Scanner  │                                          │
│  Analyze  │                                          │
│  Research │                                          │
│  Backtest │                                          │
│  Optimize │                                          │
│  Summary  │                                          │
│           │                                          │
│ GLOSSARY  │                                          │
│           │                                          │
└───────────┴──────────────────────────────────────────┘
```

---

## Academy Curriculum

### Chapter 1 — THE BIG IDEA
**Goal**: User understands what stat arb is, why pairs trading works, and why it's powerful.

| # | Lesson | Interactive Element | Type |
|---|--------|-------------------|------|
| 1.1 | What is Statistical Arbitrage? | Animated price divergence/convergence of two real assets. Step through: diverge → bet → converge → profit. | Step-through |
| 1.2 | Why Pairs Trading in Crypto? | Compare: single-asset volatility vs pair spread volatility. Toggle between BTC alone and BTC/ETH spread. | Compare panel |
| 1.3 | Market Neutral: The Superpower | Slider: drag through a market crash. Show how a long-only portfolio drops while a pairs position stays flat. | Slider + compare |

### Chapter 2 — FINDING PAIRS
**Goal**: User can evaluate whether two assets are good candidates for pairs trading.

| # | Lesson | Interactive Element | Type |
|---|--------|-------------------|------|
| 2.1 | Correlation: A First Filter | Scatter plot of multiple pairs. Click different pairs to see correlation values update. Show high vs low correlation. | Pick and explore |
| 2.2 | Cointegration: The Real Test | Compare panel: "correlated but not cointegrated" vs "cointegrated". Two price charts + their spreads side by side. | Compare panel |
| 2.3 | What Makes a Good Pair? | Checklist that evaluates the home pair: ✓ cointegrated, ✓ liquid, ✓ stable over time. Each check runs live. | Step-through |
| 2.4 | Scanning for Candidates | Mini scanner: pick 5-6 coins, run cointegration scan, see a ranked results table. User's first "research" moment. | Pick and explore |
| — | **BIG PICTURE**: Pair Selection | Visual: funnel diagram showing universe → correlation filter → cointegration test → viable pairs. | Summary |

### Chapter 3 — UNDERSTANDING THE SPREAD
**Goal**: User understands the mathematical toolkit for analyzing a pair.

| # | Lesson | Interactive Element | Type |
|---|--------|-------------------|------|
| 3.1 | Building a Spread | Show two price series, then the spread between them. Slider: adjust hedge ratio and watch the spread change. | Slider |
| 3.2 | Hedge Ratios Explained | Visual regression line between two assets. Slider moves the slope. Show how OLS finds the best fit. | Slider |
| 3.3 | Is the Spread Stationary? (ADF Test) | Compare: stationary spread (bounces around mean) vs non-stationary (drifts away). Run ADF on home pair, show p-value with traffic light. | Compare + step-through |
| 3.4 | Z-Scores: Standardizing the Spread | Spread chart → overlay rolling mean and bands → transform to z-score chart. Step through the transformation. | Step-through |
| 3.5 | Half-Life: How Fast Does It Revert? | Slider: show spreads with different half-lives (fast revert vs slow). Then calculate home pair's half-life. | Slider + compare |
| — | **BIG PICTURE**: Your Analytical Toolkit | Visual: flow diagram showing Prices → Spread → Stationarity check → Z-score → Half-life. All connected. | Summary |

### Chapter 4 — THE TRADING STRATEGY
**Goal**: User understands how z-scores become trading signals and what a complete strategy looks like.

| # | Lesson | Interactive Element | Type |
|---|--------|-------------------|------|
| 4.1 | From Z-Score to Trading Signal | Z-score chart with entry/exit threshold lines. Step through: "z crosses +2 → go short spread" etc. | Step-through |
| 4.2 | Entry, Exit & Stop-Loss | Slider: adjust entry threshold (1.5-3.0), exit (0-1.0), stop-loss (3.0-5.0). Watch signals appear/disappear on chart. | Slider |
| 4.3 | The Signal State Machine | State diagram: flat → long → flat, flat → short → flat, with stop-loss paths. Animate through a real trade sequence. | Step-through |
| 4.4 | Transaction Costs: Reality Check | Slider: adjust fee rate (0.1%-0.5%). Show how many trades become unprofitable. Before/after PnL comparison. | Slider + compare |
| — | **BIG PICTURE**: Your Complete Trading System | Visual: full pipeline from pair selection → spread → z-score → signals → trade execution → PnL. | Summary |

### Chapter 5 — DOES IT ACTUALLY WORK?
**Goal**: User can run and interpret a backtest, and understands overfitting dangers.

| # | Lesson | Interactive Element | Type |
|---|--------|-------------------|------|
| 5.1 | Your First Backtest | One-click backtest of home pair with default parameters. Show equity curve building trade by trade. Step through individual trades. | Step-through |
| 5.2 | Reading Backtest Results | Interactive results dashboard. Click on metrics (Sharpe, drawdown, win rate) to get explanations. Highlight what's good/bad. | Pick and explore |
| 5.3 | The Overfitting Trap | Compare: "too good to be true" overfit results vs "honest" results. Show how optimizing on past data doesn't predict the future. | Compare panel |
| 5.4 | Walk-Forward Validation | Step-through animation: data splits into train/test windows. Show how parameters chosen on training data perform on unseen test data. | Step-through |
| — | **BIG PICTURE**: Ready for Research | Visual: "You now understand the complete stat arb pipeline. Time to find your own opportunities." Shows path to Research. | Summary |

### Graduation
- Completion page summarizing all 5 chapters
- Direct link to Research & Backtesting
- Academy remains fully accessible as reference

---

## Research & Backtesting Flow

### Guided Workflow (suggested order, all accessible)

```
SCAN → ANALYZE → RESEARCH → BACKTEST → OPTIMIZE → SUMMARY
```

#### 1. Scanner
- Select coins from available pairs
- Run batch cointegration scan
- Ranked results table (p-value, hedge ratio, half-life)
- Click a pair to move to Analyze

#### 2. Pair Analyzer (Deep Dive)
- Selected pair's full analysis
- Price comparison, spread, z-score, correlation
- Cointegration test results
- "Looks promising? Run research modules →"

#### 3. Research Modules (8 modules)
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

#### 4. Backtester
- Run strategy with specific parameters
- Results: equity curve, trade log, metrics (Sharpe, Sortino, max DD, win rate, profit factor)
- Data quality report + honest assumptions footer
- Pre-filled from research module handoffs or manual configuration

#### 5. Optimizer
- **Grid Search**: Define parameter axes, sweep combinations, heatmap visualization
- **Walk-Forward**: Rolling train/test validation with stability verdict
- Overfitting detection and fragility warnings

#### 6. Research Summary (NEW in v3)
- Aggregates findings from all research modules run on a pair
- Shows: best parameters found, stability assessment, confidence level
- One-click "Run comprehensive backtest" with aggregated best parameters
- Comparison table if multiple pairs have been researched

---

## Build Phases

### Phase 0: Project Setup
- [ ] Initialize Python project (pyproject.toml, UV)
- [ ] Port backend core from v2 (src/statistical_arbitrage/*)
- [ ] Port API layer from v2 (api/*)
- [ ] Port config and settings
- [ ] Port and run backend tests
- [ ] Initialize Next.js frontend with Mantine v8
- [ ] Set up dark theme + Plotly wrapper
- [ ] Create app layout (sidebar with 3 pillars, header, main content area)
- [ ] Set up API client (typed fetch wrappers)
- [ ] Glossary data + GlossaryLink component

### Phase 1: Academy — Chapter 1 (The Big Idea)
- [ ] Academy page with chapter/lesson sidebar navigation
- [ ] Lesson component framework (text + interactive slot + next/prev)
- [ ] Home pair selection (first-time setup)
- [ ] Lesson 1.1: What is Statistical Arbitrage? (step-through animation)
- [ ] Lesson 1.2: Why Pairs Trading in Crypto? (compare panel)
- [ ] Lesson 1.3: Market Neutral: The Superpower (slider + compare)

### Phase 2: Academy — Chapter 2 (Finding Pairs)
- [ ] Lesson 2.1: Correlation (pick and explore)
- [ ] Lesson 2.2: Cointegration (compare panel)
- [ ] Lesson 2.3: What Makes a Good Pair? (step-through checklist)
- [ ] Lesson 2.4: Scanning for Candidates (mini scanner)
- [ ] Big Picture: Pair Selection (summary visual)

### Phase 3: Academy — Chapter 3 (Understanding the Spread)
- [ ] Lesson 3.1: Building a Spread (slider)
- [ ] Lesson 3.2: Hedge Ratios Explained (slider + regression)
- [ ] Lesson 3.3: ADF Test (compare + step-through)
- [ ] Lesson 3.4: Z-Scores (step-through transformation)
- [ ] Lesson 3.5: Half-Life (slider + compare)
- [ ] Big Picture: Analytical Toolkit (summary visual)

### Phase 4: Academy — Chapter 4 (The Trading Strategy)
- [ ] Lesson 4.1: Z-Score to Signal (step-through)
- [ ] Lesson 4.2: Entry, Exit & Stop-Loss (slider)
- [ ] Lesson 4.3: Signal State Machine (animated state diagram)
- [ ] Lesson 4.4: Transaction Costs (slider + compare)
- [ ] Big Picture: Complete Trading System (summary visual)

### Phase 5: Academy — Chapter 5 (Validation)
- [ ] Lesson 5.1: First Backtest (step-through)
- [ ] Lesson 5.2: Reading Results (interactive dashboard)
- [ ] Lesson 5.3: Overfitting Trap (compare panel)
- [ ] Lesson 5.4: Walk-Forward (step-through animation)
- [ ] Big Picture: Ready for Research (summary visual)
- [ ] Graduation page + handoff to Research

### Phase 6: Research & Backtesting — Core
- [ ] Scanner page (batch cointegration scan + results table)
- [ ] Pair Analyzer page (deep dive view)
- [ ] Backtester page (run + results view with equity curve, trade log, metrics)
- [ ] URL-based presets (shareable backtest configs)

### Phase 7: Research & Backtesting — Modules
- [ ] Research page with 8-tab layout
- [ ] Lookback Window Sweep module
- [ ] Rolling Stability module
- [ ] Out-of-Sample Validation module
- [ ] Timeframe Comparison module
- [ ] Spread Method module
- [ ] Z-Score Threshold module
- [ ] Transaction Cost module
- [ ] Cointegration Method module
- [ ] Module → Backtest handoff buttons

### Phase 8: Research & Backtesting — Optimization + Summary
- [ ] Optimizer page: Grid Search panel
- [ ] Optimizer page: Walk-Forward panel
- [ ] Research Summary page (aggregate findings, combined backtest)
- [ ] Cross-module parameter recommendations

### Phase 9: Glossary + Polish
- [ ] Glossary page (searchable, anchor links)
- [ ] GlossaryLink integration throughout Academy and Research
- [ ] E2E tests (Playwright)
- [ ] Polish: loading states, error handling, responsive design

---

## Key Design Principles
1. **Education first** — Academy is the hero. Every UX decision serves learning.
2. **Real data always** — No fake examples. Real crypto pairs, real markets.
3. **Interactive over passive** — Show, don't tell. Sliders > paragraphs.
4. **Honest results** — Backtests include assumptions, limitations, and overfitting warnings.
5. **Pure Python core** — Analysis/strategy/backtesting code has zero web framework imports.
6. **Look-ahead safety** — All backtesting signals use only data available at each bar.
