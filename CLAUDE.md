# CLAUDE.md — Statistical Arbitrage v3

## Project Overview
Learning-first crypto statistical arbitrage platform. Three pillars: Academy (interactive education), Research & Backtesting (find profitable pairs and validate strategies), Paper Trading (planned later). Bitvavo exchange, EUR pairs.

## Tech Stack

### Backend (Python)
- **Python 3.12** with **UV** package manager
- **FastAPI + Uvicorn** — REST API at `localhost:8000`
- **Polars** (not Pandas) for all dataframes
- **statsmodels/scipy** for statistical tests
- **ccxt** for exchange API (Bitvavo)
- **pydantic-settings** for config

### Frontend (TypeScript)
- **Next.js 16** (App Router) at `localhost:3000`
- **React 19** with **Mantine v8** component library
- **Plotly.js** via `react-plotly.js` for all charts
- **Dark mode only**

## Quick Commands
```bash
# Backend
uv sync --all-extras          # Install Python deps
uv run python run_api.py      # Start API server (http://localhost:8000)
uv run pytest tests/ --ignore=tests/test_api.py --ignore=tests/test_backtest_api.py --ignore=tests/test_optimization_api.py --ignore=tests/test_research_api.py --ignore=tests/test_trading_api.py  # Unit tests (174 tests)
uv run pytest tests/           # All tests (needs cached data for API tests)
uv run ruff check src/ api/   # Lint
uv run ruff format src/ api/  # Format

# Frontend
cd frontend
npm install                   # Install Node deps
npm run dev                   # Start Next.js dev server (http://localhost:3000)
npm run build                 # Production build
npm run lint                  # ESLint
```

## Project Structure
```
api/                                 # FastAPI backend
├── main.py                          # App factory, CORS, router registration
├── schemas.py                       # Pydantic request/response models
└── routers/                         # Route handlers

src/statistical_arbitrage/           # Core Python library (pure, no web imports)
├── data/                            # Bitvavo client + cache manager
├── analysis/                        # Cointegration, research modules
├── strategy/                        # Z-score mean-reversion signals
├── backtesting/                     # Engine, optimization, walk-forward
├── paper_trading/                   # Async paper trading engine
├── live_trading/                    # Live trading + risk management
└── visualization/                   # Plotly chart generators

frontend/                            # Next.js frontend
├── src/
│   ├── app/
│   │   ├── layout.tsx               # Root layout (Mantine provider, dark theme)
│   │   └── (dashboard)/
│   │       ├── layout.tsx           # Dashboard shell (sidebar + header)
│   │       ├── page.tsx             # / — redirects to /academy
│   │       ├── academy/page.tsx     # Academy (5 chapters, 18 lessons)
│   │       ├── scanner/page.tsx     # Pair scanner
│   │       ├── deep-dive/page.tsx   # Single pair analysis
│   │       ├── research/page.tsx    # 8 research modules
│   │       ├── backtest/page.tsx    # Backtesting
│   │       ├── optimize/page.tsx    # Grid search + walk-forward
│   │       ├── summary/page.tsx     # Research summary (NEW in v3)
│   │       └── glossary/page.tsx    # Searchable glossary
│   ├── components/
│   │   ├── layout/                  # Header.tsx, Sidebar.tsx
│   │   ├── charts/PlotlyChart.tsx   # Shared Plotly wrapper (dark theme, SSR-safe)
│   │   └── glossary/GlossaryLink.tsx
│   ├── contexts/PairContext.tsx      # Global pair selection state
│   └── lib/
│       ├── api.ts                   # Typed API client
│       ├── theme.ts                 # Mantine theme + Plotly dark template
│       └── glossary.ts              # Glossary terms + slug helpers

config/settings.py                   # Pydantic settings
tests/                               # Backend tests (174 unit + API integration)
```

## Architecture Patterns
- **Two-process architecture**: FastAPI (:8000) serves JSON; Next.js (:3000) consumes it
- **Pure Python core**: Analysis/strategy/backtesting code has zero web framework imports
- **Charts**: `react-plotly.js` loaded via `next/dynamic` with `ssr: false`
- **Global state**: `PairContext` provides selected pair across all pages
- **API client**: `frontend/src/lib/api.ts` — typed fetch wrappers for all endpoints
- **Dark mode only**: Mantine dark scheme + matched Plotly template

## Coding Conventions
- Use **Polars** for dataframe ops, never Pandas
- Type hints on all Python function signatures
- Use `ruff` for Python linting and formatting
- Strategy/backtesting/analysis code must be **pure Python**
- Frontend uses TypeScript strict mode
- All Plotly charts go through the `PlotlyChart` wrapper
- API timestamps are **epoch milliseconds**
- Glossary terms linked via `<GlossaryLink term="..." />` component

<!-- GSD:project-start source:PROJECT.md -->
## Project

**Statistical Arbitrage v3**

A learning-first crypto statistical arbitrage platform for EUR pairs on Bitvavo. Three pillars: Academy (interactive education), Research & Backtesting (find profitable pairs and validate strategies visually), and Paper Trading (future). The platform teaches users statistical arbitrage concepts through guided experiences, then lets them apply that knowledge to real market data.

**Core Value:** Users can visually explore pair relationships, tune strategy parameters, and see exactly how their choices translate to euros gained or lost — making statistical arbitrage intuitive, not abstract.

### Constraints

- **Tech stack**: Python 3.12 + UV, FastAPI, Next.js 16, React 19, Mantine v8, Plotly.js, Polars — all locked in from Phase 1
- **Exchange**: Bitvavo only, EUR pairs
- **Data**: Polars dataframes, never Pandas
- **Charts**: All via PlotlyChart wrapper with dark theme
- **Architecture**: Two-process (FastAPI :8000, Next.js :3000), pure Python core library
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.12+ - Backend API, core analysis library, strategy engine, backtesting, live trading
- TypeScript 5.x (strict mode) - Frontend application
- SQL (SQLite dialect) - Persistence layer for trading sessions (`src/statistical_arbitrage/paper_trading/persistence.py`)
## Runtime
- Python 3.12+ (specified in `pyproject.toml` as `requires-python = ">=3.12"`)
- Node.js (version not pinned; no `.nvmrc` present)
- **UV** for Python - Build backend: `uv_build` (>=0.9.5,<0.11.0)
- **npm** for Node.js
## Frameworks
- **FastAPI** >=0.115.0 - REST API framework (`api/main.py`)
- **Uvicorn** >=0.30.0 (with `standard` extras) - ASGI server (`run_api.py`)
- **Next.js** 16.2.1 - Frontend framework with App Router (`frontend/package.json`)
- **React** 19.2.4 - UI rendering (`frontend/package.json`)
- **Mantine** v8.3.18 - Component library (core, hooks, notifications)
- **Plotly.js** ^3.4.0 - Chart rendering
- **react-plotly.js** ^2.6.0 - React wrapper (loaded via `next/dynamic` with `ssr: false`)
- **pytest** >=7.4.0 - Test runner
- **pytest-cov** >=4.1.0 - Coverage reporting
- **pytest-asyncio** >=0.21.0 - Async test support
- **ruff** >=0.1.0 - Python linter and formatter
- **ESLint** ^9 with `eslint-config-next` 16.2.1 - TypeScript/React linting
- **mypy** >=1.7.0 - Python static type checker (dev dependency)
- **uv_build** >=0.9.5,<0.11.0 - Python build backend (`pyproject.toml`)
- **Next.js** built-in bundler (Turbopack) - Frontend builds
## Key Dependencies
- `polars` >=0.20.0 - All dataframe operations (never use Pandas)
- `ccxt` >=4.2.0 - Exchange API client for Bitvavo (sync and async)
- `statsmodels` >=0.14.0 - Statistical tests (cointegration, ADF)
- `scipy` >=1.11.0 - Scientific computing, statistical functions
- `numpy` >=1.26.0 - Numerical operations
- `pydantic` >=2.5.0 - Data validation and serialization
- `pydantic-settings` >=2.1.0 - Configuration management (`config/settings.py`)
- `httpx` >=0.27.0 - Async HTTP client (Telegram notifications)
- `aiosqlite` >=0.20.0 - Async SQLite driver for trading persistence
- `python-dotenv` >=1.0.0 - Environment variable loading
- `plotly` >=5.18.0 - Server-side chart generation (visualization module)
- `@tabler/icons-react` ^3.40.0 - Icon library
- `@types/react-plotly.js` ^2.6.4 - Plotly type definitions
## Configuration
- Python settings via `pydantic-settings` with `.env` file at `config/.env`
- Example env file: `config/.env.example` (present)
- Frontend env: `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`)
- No `.env` files in repo root or `frontend/` directory
- Config: `frontend/tsconfig.json`
- Strict mode enabled
- Path alias: `@/*` maps to `./src/*`
- Module resolution: bundler
- Target: ES2017
- `pyproject.toml` - Python project configuration (dependencies, ruff, pytest)
- `frontend/next.config.ts` - Next.js configuration (currently empty/default)
- `frontend/postcss.config.mjs` - PostCSS with Mantine preset
## Platform Requirements
- Python 3.12+
- Node.js (compatible with Next.js 16)
- UV package manager
- npm package manager
- Two processes: FastAPI on :8000, Next.js on :3000
- FastAPI served via Uvicorn (host 0.0.0.0, port 8000)
- Next.js production build (`npm run build && npm start`)
- SQLite file at `data/trading.db` for persistence
- Bitvavo API credentials for live data/trading
- Optional: Telegram bot token for notifications
## Run Commands
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- snake_case for all module files: `cointegration.py`, `cache_manager.py`, `zscore_mean_reversion.py`
- Test files prefixed with `test_`: `test_backtest_engine.py`, `test_optimization.py`
- Router files match their domain: `api/routers/analysis.py`, `api/routers/backtest.py`
- snake_case: `run_backtest()`, `calculate_hedge_ratio()`, `test_cointegration()`
- Private helpers prefixed with underscore: `_to_numpy()`, `_load_pair_data()`, `_get_cache_mgr()`
- Test helper factories prefixed with underscore: `_params()`, `_make_correlated_prices()`, `_single_long_fixture()`
- PascalCase: `PairAnalysis`, `StrategyParameters`, `RiskManager`, `LiveTradingEngine`
- Test classes prefixed with `Test`: `TestBacktestEngine`, `TestHealth`, `TestRiskManagerRejections`
- Pydantic models use PascalCase with descriptive suffixes: `BacktestResponse`, `HealthResponse`, `CointegrationResponse`
- snake_case: `hedge_ratio`, `spread_props`, `close1`, `close2`
- Constants in UPPER_SNAKE_CASE: `PROJECT_ROOT`, `BASE_PARAMS`
- PascalCase for components: `PlotlyChart.tsx`, `Header.tsx`, `Sidebar.tsx`, `GlossaryLink.tsx`
- PascalCase for lesson components: `Lesson1_1.tsx`, `Lesson2_3.tsx` (chapter_lesson pattern)
- camelCase for utility modules: `api.ts`, `theme.ts`, `glossary.ts`
- PascalCase for context files: `PairContext.tsx`, `AcademyDataContext.tsx`
- Next.js pages use `page.tsx` convention
- camelCase for functions: `fetchPairs()`, `postBacktest()`, `symbolToDash()`
- PascalCase for React components: `PlotlyChart()`, `ScannerPage()`, `PairProvider()`
- Custom hooks prefixed with `use`: `usePairContext()`
- PascalCase: `PairInfo`, `BacktestResponse`, `PlotlyChartProps`
- API payload interfaces suffixed with `Payload`: `MetricSummaryPayload`, `EquityCurvePointPayload`
- Request interfaces suffixed with `Request`: `BacktestRequest`, `GridSearchRequest`
- Response interfaces suffixed with `Response`: `BacktestResponse`, `GridSearchResponse`
## Code Style
- Tool: **Ruff** (linter + formatter)
- Config: `pyproject.toml` — `[tool.ruff]`
- Line length: 100 characters
- Target: Python 3.12
- Lint rules: `["E", "F", "I", "W"]` (pyflakes, pycodestyle errors/warnings, isort)
- No Prettier configured
- ESLint via `eslint.config.mjs` using `eslint-config-next/core-web-vitals` and `eslint-config-next/typescript`
- TypeScript strict mode enabled in `frontend/tsconfig.json`
## Import Organization
- Used in newer modules (strategy, backtesting models, live trading) for forward references
- Not universally adopted — older modules (cointegration, analysis) omit it
- TypeScript: `@/*` maps to `./src/*` (configured in `frontend/tsconfig.json`)
- Python: No path aliases; uses package imports `from statistical_arbitrage.xxx`
## Error Handling
- Wrap core logic in `try/except` blocks
- Catch specific `HTTPException` and re-raise, catch generic `Exception` for everything else
- Convert to `HTTPException` with status codes: 404 (data not found), 422 (invalid input), 500 (internal error)
- Log exceptions with `logger.exception()` before raising
- Chain exceptions with `raise ... from e`
- Raises `ValueError` for invalid inputs (e.g., insufficient data, length mismatches)
- Returns plain dicts or dataclass/Pydantic model instances (no HTTP concerns)
- No try/except in pure computation code — let errors propagate
- Central `apiFetch<T>()` wrapper in `frontend/src/lib/api.ts` handles all HTTP errors
- Extracts `detail` from FastAPI error payloads for user-facing messages
- Components use try/catch in async handlers, store error in state: `setError(message)`
- Loading/error states use `useState<string | null>(null)` pattern
## Type Annotation Practices
- Type hints on all function signatures (parameters and return types)
- Pydantic models for all API schemas with `Field()` descriptions
- `Literal` types for constrained string fields: `Literal["ok", "blocked"]`, `Literal["warning", "blocking"]`
- Use `dict[str, Any]` for flexible internal return types
- Pydantic `ConfigDict(extra="forbid")` on backtest models for strict validation
- `Protocol` with `@runtime_checkable` for dependency injection: `OrderExecutor` in `src/statistical_arbitrage/live_trading/order_executor.py`
- Strict mode enabled (`"strict": true` in tsconfig)
- Interfaces for all API response types in `frontend/src/lib/api.ts` (mirror Python schemas)
- Props interfaces for components: `PlotlyChartProps`, `PairContextValue`
- Generic typing on fetch wrapper: `apiFetch<T>()`
## Comments and Docstrings
- Every module has a top-level docstring explaining purpose
- Format: triple-quoted string, 1-3 sentences
- Google-style with `Args:` and `Returns:` sections
- Present on public methods, sometimes omitted on private helpers
- Section separators using `# ---------------------------------------------------------------------------`
- Explanatory comments for non-obvious logic
- Section headers within files: `# POST /api/analysis/cointegration`
- JSDoc `/** ... */` comments on exported functions and components
- No inline TSDoc `@param`/`@returns` tags — just description paragraphs
- Section separators matching Python style: `// ---------------------------------------------------------------------------`
## Function Design
- Pure functions preferred in core library (no side effects, no web framework imports)
- Factory pattern for test data: `_make_correlated_prices()`, `make_signal_candles()`
- Pydantic models as function parameters for complex inputs: `StrategyParameters`
- Return dicts from analysis functions, Pydantic models from API layer
- React components are default exports for pages, named exports for reusable components
- API functions are async, return typed promises
- Hooks use `useCallback` for stable references passed as props
- State initialization follows `const [value, setValue] = useState<Type>(initial)` pattern
## Module Design
- `__init__.py` files used for re-exports in packages
- Core library (`src/statistical_arbitrage/`) exports classes and functions
- API layer imports from core library — never the reverse
- Used for lesson components: `frontend/src/components/academy/lessons/index.ts`
- Used for real-data components: `frontend/src/components/academy/real-data/index.ts`
- Not used everywhere — direct imports are common
## Frontend Component Patterns
- All UI built with Mantine v8 components: `Container`, `Stack`, `Paper`, `Title`, `Text`, `Select`, `Button`, `Table`, `Alert`, `Badge`, `Chip`
- Icons from `@tabler/icons-react`
- `AppShell` for dashboard layout with header (60px) and sidebar (260px): `frontend/src/app/(dashboard)/layout.tsx`
- Dark color scheme enforced at root: `<html data-mantine-color-scheme="dark">`
- Theme defined in `frontend/src/lib/theme.ts` using `createTheme()`
- Notifications via `@mantine/notifications` at root layout
- All charts go through `PlotlyChart` wrapper: `frontend/src/components/charts/PlotlyChart.tsx`
- Loaded via `next/dynamic` with `ssr: false` to avoid SSR issues
- Shows `Skeleton` placeholder while loading
- Auto-merges dark theme template from `PLOTLY_DARK_TEMPLATE`
- Config defaults: `responsive: true`, `displayModeBar: false`
- Every page is `'use client'`
- Pages use `useState` for loading, error, and data states
- Data fetching in `useEffect` with cancellation flag pattern:
- Global state via React Context: `PairContext` in `frontend/src/contexts/PairContext.tsx`
- Provider wraps dashboard layout
- Custom hook `usePairContext()` with null-check guard
- `AcademyDataContext` for academy-specific shared data
## API Endpoint Patterns
- All endpoints under `/api/` prefix
- Domain routers: `/api/health`, `/api/pairs`, `/api/analysis`, `/api/research`, `/api/backtest`, `/api/optimization`, `/api/trading`, `/api/academy`
- Kebab-case for multi-word paths: `/api/research/lookback-window`, `/api/research/rolling-stability`, `/api/research/oos-validation`
- Path parameters use dash-separated symbols: `/api/pairs/ETH-EUR/ohlcv`
- `GET` for read-only: health, pairs list, OHLCV data
- `POST` for analysis/computation: cointegration, backtest, research modules, optimization
- POST bodies use Pydantic models defined in `api/schemas.py`
- Responses use Pydantic `response_model` for automatic validation and OpenAPI docs
- Numpy types converted via `numpy_to_python()` helper before serialization
- Timestamps are epoch milliseconds (integers)
- Routers defined with `APIRouter(prefix="/api/...", tags=["..."])` per domain
- All registered in `api/main.py` via `app.include_router()`
- FastAPI Depends for dependency injection (cache manager)
- Nested Pydantic settings in `config/settings.py`
- Singleton: `settings = Settings()`
- `.env` file loaded from `config/.env` (exists, not read for security)
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- FastAPI backend (:8000) serves JSON; Next.js frontend (:3000) consumes it
- Core analysis/strategy/backtesting code is a standalone Python library with zero web framework imports
- Frontend is a single-page dashboard app using Mantine + Plotly for all visualization
- Data layer uses a parquet-based cache with incremental API fetches from Bitvavo via CCXT
- Trading engine (paper + live) runs as an async lifecycle managed via FastAPI lifespan
## Layers
- Purpose: Translate HTTP requests to core library calls, serialize responses as JSON
- Location: `api/`
- Contains: FastAPI routers, Pydantic request/response schemas, numpy-to-Python converters
- Depends on: Core library (`src/statistical_arbitrage/`), config (`config/settings.py`)
- Used by: Frontend via HTTP fetch calls
- Purpose: All domain logic -- analysis, strategy, backtesting, trading engines
- Location: `src/statistical_arbitrage/`
- Contains: Cointegration analysis, z-score strategy, backtest engine, grid search, walk-forward, paper/live trading
- Depends on: polars, numpy, scipy, statsmodels, ccxt, aiosqlite (no web framework imports)
- Used by: API layer routers
- Purpose: Fetch OHLCV data from Bitvavo, cache as parquet files, serve from cache
- Location: `src/statistical_arbitrage/data/`
- Contains: CCXT client wrapper (`bitvavo_client.py`), parquet cache manager (`cache_manager.py`)
- Depends on: ccxt, polars, config settings
- Used by: API routers (via FastAPI dependency injection)
- Purpose: Interactive UI for learning, research, backtesting, and trading
- Location: `frontend/`
- Contains: App Router pages, Mantine components, Plotly charts, React contexts
- Depends on: Backend API (HTTP), Mantine v8, react-plotly.js
- Used by: End user (browser)
- Purpose: Centralized settings via pydantic-settings with .env file support
- Location: `config/settings.py`
- Contains: Nested settings groups (Bitvavo, Data, Strategy, LiveTrading, Telegram)
- Depends on: pydantic-settings, config/.env (optional)
- Used by: Core library, API layer
## Data Flow
- **Frontend global state:** `PairContext` provides selected asset1/asset2/timeframe across all dashboard pages. `AcademyDataContext` provides pre-loaded pair data for the Academy wizard.
- **Backend singletons:** `DataCacheManager` singleton (module-level `_cache_manager`), `Settings` singleton (`config/settings.py`)
- **Backend lifespan state:** `LiveTradingEngine` and `PersistenceManager` attached to `app.state` during FastAPI lifespan, shared across all trading router endpoints
- **Per-request state:** No session/auth state. Each analysis/backtest request is stateless -- load from cache, compute, return.
## Key Abstractions
- Purpose: Transparent caching layer between Bitvavo API and analysis code
- Location: `src/statistical_arbitrage/data/cache_manager.py`
- Pattern: Singleton via `get_cache_manager()`, lazy CCXT client init, incremental delta fetches, parquet storage
- Key method: `get_candles(symbol, timeframe, days_back)` -- cache-first, fetch on miss
- Purpose: Cointegration testing, spread calculation, stationarity analysis for a pair
- Location: `src/statistical_arbitrage/analysis/cointegration.py`
- Pattern: Stateful class initialized with two price series, methods return structured dicts
- Purpose: Fee-aware, look-ahead-safe backtesting with honest reporting
- Location: `src/statistical_arbitrage/backtesting/engine.py`
- Pattern: Top-level `run_backtest()` function, returns `BacktestResult` Pydantic model
- Composes: `zscore_mean_reversion.build_rolling_strategy_data()` + `generate_signal_events()` + fill accounting
- Purpose: Async session-based trading with simulated or real execution
- Location: `src/statistical_arbitrage/paper_trading/engine.py`, `src/statistical_arbitrage/live_trading/engine.py`
- Pattern: `LiveTradingEngine` extends `PaperTradingEngine`. Paper = simulated fills. Live = risk-gated real orders via injectable `OrderExecutor` protocol.
- Dependencies injected: `CandleDataSource` (Protocol), `PersistenceManager`, `OrderExecutor`, `RiskManager`, `TelegramNotifier`
- Purpose: Type-safe request/response boundary between frontend and backend
- Location: `api/schemas.py`
- Pattern: Mirror TypeScript interfaces in `frontend/src/lib/api.ts`. Backend models wrap core library dataclasses/dicts.
## Entry Points
- Location: `run_api.py` -> `api/main.py`
- Triggers: `uv run python run_api.py` or `uvicorn api.main:app`
- Responsibilities: Starts uvicorn on port 8000, initializes trading engine in lifespan, registers all routers
- Location: `frontend/package.json` (`npm run dev`)
- Triggers: `cd frontend && npm run dev`
- Responsibilities: Serves frontend on port 3000, proxies nothing (direct fetch to :8000)
- Location: `frontend/src/app/(dashboard)/page.tsx`
- Behavior: `redirect('/academy')` -- the landing page is the Academy
## Error Handling
- API routers wrap core calls in try/except, raise `HTTPException` with status 500 and detail message
- `_load_pair_data()` in `api/routers/analysis.py` raises `HTTPException(404)` when cache files are missing
- Backtest engine uses preflight checks (`backtesting/preflight.py`) that return structured `EngineWarning` objects with `blocking` or `warning` severity
- Frontend `apiFetch()` in `frontend/src/lib/api.ts` throws `Error` with status code and detail message on non-2xx responses
- Trading engine logs errors and stores `last_error` on session objects
## Cross-Cutting Concerns
## Module Dependency Graph
```
```
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
