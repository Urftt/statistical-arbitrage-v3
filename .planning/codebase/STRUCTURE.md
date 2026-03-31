# Codebase Structure

**Analysis Date:** 2026-03-31

## Directory Layout

```
statistical-arbitrage-v3/
├── api/                             # FastAPI REST API layer
│   ├── main.py                      # App factory, CORS, router registration, lifespan
│   ├── schemas.py                   # Pydantic request/response models (~250 lines)
│   └── routers/                     # Route handlers (one file per domain)
│       ├── health.py                # GET /api/health
│       ├── pairs.py                 # GET /api/pairs, GET /api/pairs/{symbol}/ohlcv
│       ├── analysis.py              # POST /api/analysis/cointegration (+ spread, zscore, stationarity)
│       ├── research.py              # POST /api/research/* (8 modules)
│       ├── backtest.py              # POST /api/backtest
│       ├── optimization.py          # POST /api/optimization/grid-search, walk-forward
│       ├── trading.py               # /api/trading/* (session CRUD, lifecycle, kill switch)
│       └── academy_scan.py          # GET /api/academy/scan, POST /api/academy/fetch
│
├── src/statistical_arbitrage/       # Core Python library (pure, no web imports)
│   ├── __init__.py                  # Package init, version
│   ├── data/                        # Exchange data access + caching
│   │   ├── bitvavo_client.py        # CCXT wrapper for Bitvavo exchange
│   │   └── cache_manager.py         # Parquet cache with incremental fetches
│   ├── analysis/                    # Statistical analysis
│   │   ├── cointegration.py         # PairAnalysis class (ADF, cointegration, spread)
│   │   └── research.py              # 8 research modules (rolling coint, OOS, lookback, etc.)
│   ├── strategy/                    # Signal generation
│   │   └── zscore_mean_reversion.py # Hedge ratio, spread, z-score, signal generation
│   ├── backtesting/                 # Backtest engine + optimization
│   │   ├── models.py                # Pydantic domain models (StrategyParameters, BacktestResult, etc.)
│   │   ├── engine.py                # run_backtest() — fee-aware, look-ahead-safe
│   │   ├── optimization.py          # run_grid_search() — multi-parameter grid search
│   │   ├── walkforward.py           # run_walk_forward() — rolling train/test validation
│   │   ├── overfitting.py           # Overfitting detection heuristics
│   │   └── preflight.py             # Data quality checks before backtest
│   ├── paper_trading/               # Async paper trading
│   │   ├── models.py                # PaperSession, PaperTrade, SessionConfig, etc.
│   │   ├── engine.py                # PaperTradingEngine — async session lifecycle
│   │   ├── data_source.py           # CandleDataSource protocol + MockCandleDataSource
│   │   └── persistence.py           # PersistenceManager — async SQLite (aiosqlite)
│   ├── live_trading/                # Live order execution
│   │   ├── __init__.py              # Package exports (all public classes)
│   │   ├── models.py                # LiveOrder, RiskCheckResult, event types
│   │   ├── engine.py                # LiveTradingEngine (extends PaperTradingEngine)
│   │   ├── order_executor.py        # OrderExecutor protocol, MockOrderExecutor, BitvavoOrderExecutor
│   │   ├── risk_manager.py          # RiskManager — pre-trade risk gate (4 limits)
│   │   └── telegram_notifier.py     # TelegramNotifier — trade alerts (no-op when unconfigured)
│   └── visualization/               # Server-side Plotly chart generators
│       ├── spread_plots.py          # Price comparison, spread, z-score plots
│       └── educational_plots.py     # Academy-specific educational visualizations
│
├── frontend/                        # Next.js 16 frontend
│   ├── package.json                 # Dependencies: Mantine v8, React 19, Plotly.js v3
│   ├── tsconfig.json                # Strict mode, @/* path alias -> ./src/*
│   ├── next.config.ts               # Next.js configuration
│   ├── postcss.config.mjs           # PostCSS for Mantine
│   ├── public/                      # Static assets
│   └── src/
│       ├── app/
│       │   ├── layout.tsx           # Root layout (MantineProvider, dark theme, Notifications)
│       │   ├── globals.css          # Global styles
│       │   └── (dashboard)/         # Route group — all pages share dashboard shell
│       │       ├── layout.tsx       # Dashboard shell (AppShell: Header + Sidebar + PairProvider)
│       │       ├── page.tsx         # / — redirects to /academy
│       │       ├── academy/page.tsx # Academy wizard (5 chapters, 18 lessons)
│       │       ├── scanner/page.tsx # Batch pair cointegration scanner
│       │       ├── deep-dive/page.tsx # Single pair deep analysis
│       │       ├── research/page.tsx  # 8 research modules
│       │       ├── backtest/page.tsx  # Strategy backtesting
│       │       ├── optimize/page.tsx  # Grid search + walk-forward optimization
│       │       ├── summary/page.tsx   # Research summary dashboard
│       │       └── glossary/page.tsx  # Searchable glossary
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Header.tsx       # Top bar with pair selection
│       │   │   └── Sidebar.tsx      # Navigation sidebar with section grouping
│       │   ├── charts/
│       │   │   └── PlotlyChart.tsx   # Shared Plotly wrapper (dark theme, SSR-safe via next/dynamic)
│       │   ├── glossary/
│       │   │   └── GlossaryLink.tsx  # Inline glossary term link component
│       │   └── academy/
│       │       ├── AcademyWizard.tsx  # Main wizard controller for academy flow
│       │       ├── lessons/           # 18 lesson components (Lesson1_1.tsx through Lesson5_3.tsx)
│       │       │   └── index.ts       # Barrel export for all lessons
│       │       └── real-data/         # Live data sections embedded in lessons
│       │           ├── RealDataSection.tsx  # Container for real-data tabs
│       │           ├── tabs.tsx       # Individual real-data tab implementations
│       │           └── index.ts       # Barrel export
│       ├── contexts/
│       │   ├── PairContext.tsx       # Global pair selection (asset1, asset2, timeframe, coins list)
│       │   └── AcademyDataContext.tsx # Academy-specific: pre-loaded good/bad pair data
│       └── lib/
│           ├── api.ts               # Typed API client (all fetch functions + TypeScript interfaces)
│           ├── theme.ts             # Mantine theme + PLOTLY_DARK_TEMPLATE
│           ├── academy.ts           # Chapter/lesson curriculum data structure
│           └── glossary.ts          # Glossary terms + slug helpers
│
├── config/                          # Configuration
│   └── settings.py                  # Pydantic-settings: Bitvavo, Data, Strategy, LiveTrading, Telegram
│
├── data/                            # Runtime data (gitignored contents)
│   ├── cache/                       # Parquet cache files (per symbol/timeframe)
│   ├── raw/                         # Raw API response chunks
│   └── trading.db                   # SQLite database for paper/live trading sessions
│
├── tests/                           # Backend tests (174 unit + API integration)
│   ├── test_backtest_engine.py      # Backtest engine unit tests
│   ├── test_optimization.py         # Grid search unit tests
│   ├── test_walkforward.py          # Walk-forward unit tests
│   ├── test_overfitting.py          # Overfitting detection tests
│   ├── test_research_modules.py     # Research module unit tests
│   ├── test_research_s03.py         # S03 research tests
│   ├── test_rolling_cointegration.py # Rolling cointegration tests
│   ├── test_api.py                  # API integration tests (needs cached data)
│   ├── test_backtest_api.py         # Backtest API integration tests
│   ├── test_optimization_api.py     # Optimization API integration tests
│   ├── test_research_api.py         # Research API integration tests
│   ├── test_trading_api.py          # Trading API integration tests
│   └── live_trading/                # Live trading subsystem tests
│
├── run_api.py                       # API server entry point (uvicorn runner)
├── pyproject.toml                   # Python project config (deps, ruff, pytest)
├── uv.lock                          # UV lockfile
├── CLAUDE.md                        # AI assistant instructions
├── PROGRESS.md                      # Project progress tracker
├── PROJECT_PLAN.md                  # Multi-phase project plan
└── .gitignore                       # Ignores .venv, data/cache, __pycache__, .next, etc.
```

## Directory Purposes

**`api/`:**
- Purpose: FastAPI HTTP layer -- thin endpoints that delegate to core library
- Contains: App factory (`main.py`), Pydantic schemas (`schemas.py`), route handlers (`routers/`)
- Key files: `api/main.py` (app creation + lifespan), `api/schemas.py` (all request/response types)

**`src/statistical_arbitrage/`:**
- Purpose: Pure Python core library with all domain logic
- Contains: Six subpackages (data, analysis, strategy, backtesting, paper_trading, live_trading) + visualization
- Key constraint: No web framework imports allowed -- must be testable and reusable standalone

**`frontend/src/app/(dashboard)/`:**
- Purpose: All user-facing pages under the dashboard shell layout
- Contains: Page components for each feature area
- Key pattern: Route group `(dashboard)` shares `layout.tsx` with AppShell, Header, Sidebar, and PairProvider

**`frontend/src/components/`:**
- Purpose: Reusable UI components
- Contains: Layout shell, chart wrapper, glossary links, academy lessons
- Key file: `charts/PlotlyChart.tsx` -- all Plotly charts go through this wrapper

**`frontend/src/lib/`:**
- Purpose: Shared utilities, API client, theme, curriculum data
- Contains: Typed fetch functions, TypeScript interfaces mirroring backend schemas, theme config
- Key file: `api.ts` -- single source of truth for all backend API interactions

**`frontend/src/contexts/`:**
- Purpose: React context providers for global state
- Contains: `PairContext.tsx` (pair selection across pages), `AcademyDataContext.tsx` (pre-loaded data for lessons)

**`config/`:**
- Purpose: Application configuration via pydantic-settings
- Contains: `settings.py` with nested settings groups, reads from `config/.env` (if present)

**`data/`:**
- Purpose: Runtime data storage (not committed to git)
- Contains: `cache/` (parquet files), `raw/` (API chunks), `trading.db` (SQLite)

**`tests/`:**
- Purpose: Backend test suite
- Contains: Unit tests (run without external deps) and API integration tests (need cached data)

## Key File Locations

**Entry Points:**
- `run_api.py`: Start backend API server (`uv run python run_api.py`)
- `api/main.py`: FastAPI app factory and lifespan (trading engine init/shutdown)
- `frontend/src/app/layout.tsx`: Root Next.js layout (MantineProvider)
- `frontend/src/app/(dashboard)/layout.tsx`: Dashboard shell with navigation

**Configuration:**
- `config/settings.py`: All backend settings (Bitvavo, data paths, strategy defaults, risk limits, Telegram)
- `pyproject.toml`: Python dependencies, ruff config, pytest config
- `frontend/package.json`: Node dependencies, scripts
- `frontend/tsconfig.json`: TypeScript config with `@/*` path alias
- `frontend/postcss.config.mjs`: PostCSS for Mantine CSS processing

**Core Logic:**
- `src/statistical_arbitrage/analysis/cointegration.py`: PairAnalysis class
- `src/statistical_arbitrage/analysis/research.py`: 8 research modules (rolling coint, OOS, lookback, spread methods, timeframe, z-score threshold, tx cost, coint methods)
- `src/statistical_arbitrage/strategy/zscore_mean_reversion.py`: Signal generation (hedge ratio, spread, z-score, signals)
- `src/statistical_arbitrage/backtesting/engine.py`: `run_backtest()` main entry point
- `src/statistical_arbitrage/backtesting/optimization.py`: `run_grid_search()`
- `src/statistical_arbitrage/backtesting/walkforward.py`: `run_walk_forward()`
- `src/statistical_arbitrage/paper_trading/engine.py`: `PaperTradingEngine`
- `src/statistical_arbitrage/live_trading/engine.py`: `LiveTradingEngine`

**Data Access:**
- `src/statistical_arbitrage/data/cache_manager.py`: `DataCacheManager` + `get_cache_manager()` singleton
- `src/statistical_arbitrage/data/bitvavo_client.py`: `BitvavoDataCollector` CCXT wrapper

**Frontend API:**
- `frontend/src/lib/api.ts`: All typed fetch functions and TypeScript interfaces (matches `api/schemas.py`)
- `frontend/src/lib/theme.ts`: Mantine theme + Plotly dark template
- `frontend/src/lib/academy.ts`: Curriculum structure (5 chapters, 18 lessons)
- `frontend/src/lib/glossary.ts`: Glossary terms and slug helpers

**Testing:**
- `tests/test_backtest_engine.py`: Core backtest engine tests
- `tests/test_optimization.py`: Grid search tests
- `tests/test_walkforward.py`: Walk-forward validation tests
- `tests/test_research_modules.py`: Research function unit tests
- `tests/test_api.py`: API integration tests (needs cached data)

## Naming Conventions

**Files:**
- Python: `snake_case.py` (e.g., `cache_manager.py`, `zscore_mean_reversion.py`)
- TypeScript pages: `page.tsx` (Next.js convention)
- TypeScript components: `PascalCase.tsx` (e.g., `PlotlyChart.tsx`, `AcademyWizard.tsx`)
- TypeScript lib: `camelCase.ts` (e.g., `api.ts`, `theme.ts`, `glossary.ts`)
- Academy lessons: `Lesson{chapter}_{lesson}.tsx` (e.g., `Lesson1_1.tsx`, `Lesson3_2.tsx`)

**Directories:**
- Python packages: `snake_case` (e.g., `paper_trading`, `live_trading`)
- Frontend route segments: `kebab-case` (e.g., `deep-dive`, `academy`)
- Frontend component groups: `kebab-case` (e.g., `real-data`, `layout`)

## Where to Add New Code

**New API Endpoint:**
- Create router file: `api/routers/{domain}.py`
- Add Pydantic schemas: `api/schemas.py`
- Register router: `api/main.py` (import + `application.include_router()`)
- Add TypeScript interfaces + fetch function: `frontend/src/lib/api.ts`

**New Analysis/Research Module:**
- Add function to `src/statistical_arbitrage/analysis/research.py` (follows pattern: takes numpy arrays, returns structured results + Takeaway)
- Add router endpoint in `api/routers/research.py`
- Add schema types in `api/schemas.py`
- Add TS types + fetch function in `frontend/src/lib/api.ts`

**New Frontend Page:**
- Create `frontend/src/app/(dashboard)/{route}/page.tsx`
- Add navigation entry in `frontend/src/components/layout/Sidebar.tsx`
- Page automatically gets dashboard shell (Header + Sidebar + PairProvider) from `(dashboard)/layout.tsx`

**New Academy Lesson:**
- Create `frontend/src/components/academy/lessons/Lesson{Ch}_{Ls}.tsx`
- Export from `frontend/src/components/academy/lessons/index.ts`
- Add lesson entry to `frontend/src/lib/academy.ts` CHAPTERS array
- Add real-data tabs in `frontend/src/components/academy/real-data/tabs.tsx` if needed

**New Reusable Component:**
- Place in `frontend/src/components/{category}/`
- Use Mantine components, follow dark-mode-only convention
- Charts must use `PlotlyChart` wrapper from `frontend/src/components/charts/PlotlyChart.tsx`

**New Strategy or Backtesting Feature:**
- Strategy logic: `src/statistical_arbitrage/strategy/` (new file or extend `zscore_mean_reversion.py`)
- Backtest models: `src/statistical_arbitrage/backtesting/models.py`
- Engine integration: `src/statistical_arbitrage/backtesting/engine.py`

**New Trading Feature:**
- Paper trading: `src/statistical_arbitrage/paper_trading/`
- Live trading: `src/statistical_arbitrage/live_trading/`
- Follow injectable dependency pattern (Protocol + implementations)
- Wire in `api/main.py` lifespan if it needs startup/shutdown lifecycle

**New Tests:**
- Unit tests: `tests/test_{module}.py`
- API integration tests: `tests/test_{domain}_api.py` (need cached parquet data)
- Live trading tests: `tests/live_trading/`

## Special Directories

**`data/`:**
- Purpose: Runtime parquet cache, raw API responses, SQLite trading database
- Generated: Yes (by DataCacheManager and PersistenceManager)
- Committed: No (directory structure only, contents gitignored)

**`.venv/`:**
- Purpose: Python virtual environment (UV-managed)
- Generated: Yes (`uv sync`)
- Committed: No

**`frontend/.next/`:**
- Purpose: Next.js build output and dev cache
- Generated: Yes (`npm run build` or `npm run dev`)
- Committed: No

**`frontend/node_modules/`:**
- Purpose: Node.js dependencies
- Generated: Yes (`npm install`)
- Committed: No

**`.planning/codebase/`:**
- Purpose: GSD codebase analysis documents (this file)
- Generated: Yes (by mapping agents)
- Committed: Yes

---

*Structure analysis: 2026-03-31*
