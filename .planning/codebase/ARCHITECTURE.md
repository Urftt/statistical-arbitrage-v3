# Architecture

**Analysis Date:** 2026-03-31

## Pattern Overview

**Overall:** Two-process client-server architecture with a pure Python core library

**Key Characteristics:**
- FastAPI backend (:8000) serves JSON; Next.js frontend (:3000) consumes it
- Core analysis/strategy/backtesting code is a standalone Python library with zero web framework imports
- Frontend is a single-page dashboard app using Mantine + Plotly for all visualization
- Data layer uses a parquet-based cache with incremental API fetches from Bitvavo via CCXT
- Trading engine (paper + live) runs as an async lifecycle managed via FastAPI lifespan

## Layers

**API Layer (HTTP boundary):**
- Purpose: Translate HTTP requests to core library calls, serialize responses as JSON
- Location: `api/`
- Contains: FastAPI routers, Pydantic request/response schemas, numpy-to-Python converters
- Depends on: Core library (`src/statistical_arbitrage/`), config (`config/settings.py`)
- Used by: Frontend via HTTP fetch calls

**Core Library (pure Python):**
- Purpose: All domain logic -- analysis, strategy, backtesting, trading engines
- Location: `src/statistical_arbitrage/`
- Contains: Cointegration analysis, z-score strategy, backtest engine, grid search, walk-forward, paper/live trading
- Depends on: polars, numpy, scipy, statsmodels, ccxt, aiosqlite (no web framework imports)
- Used by: API layer routers

**Data Layer (exchange + cache):**
- Purpose: Fetch OHLCV data from Bitvavo, cache as parquet files, serve from cache
- Location: `src/statistical_arbitrage/data/`
- Contains: CCXT client wrapper (`bitvavo_client.py`), parquet cache manager (`cache_manager.py`)
- Depends on: ccxt, polars, config settings
- Used by: API routers (via FastAPI dependency injection)

**Frontend (Next.js dashboard):**
- Purpose: Interactive UI for learning, research, backtesting, and trading
- Location: `frontend/`
- Contains: App Router pages, Mantine components, Plotly charts, React contexts
- Depends on: Backend API (HTTP), Mantine v8, react-plotly.js
- Used by: End user (browser)

**Configuration:**
- Purpose: Centralized settings via pydantic-settings with .env file support
- Location: `config/settings.py`
- Contains: Nested settings groups (Bitvavo, Data, Strategy, LiveTrading, Telegram)
- Depends on: pydantic-settings, config/.env (optional)
- Used by: Core library, API layer

## Data Flow

**Research/Analysis Flow (read path):**

1. User selects pair + timeframe in frontend (via `PairContext` or page-local state)
2. Frontend calls typed API function from `frontend/src/lib/api.ts` (e.g., `postCointegration()`)
3. API router loads cached parquet data via `DataCacheManager.get_candles()` (singleton via `get_cache_manager()`)
4. If cache miss, `DataCacheManager` fetches from Bitvavo API via CCXT, stores as parquet, returns data
5. Router passes price series to core library function (e.g., `PairAnalysis.test_cointegration()`)
6. Core function returns structured result (dict or dataclass)
7. Router converts to Pydantic response model (with `numpy_to_python()` for safe serialization)
8. Frontend renders response using Mantine components and Plotly charts

**Backtest Flow:**

1. Frontend POSTs `BacktestRequest` with pair, timeframe, days_back, and strategy parameters
2. `api/routers/backtest.py` loads aligned price data via shared `_load_pair_data()` helper from `api/routers/analysis.py`
3. Calls `run_backtest()` from `src/statistical_arbitrage/backtesting/engine.py`
4. Engine runs preflight checks, generates signals via `zscore_mean_reversion`, simulates trades with fee accounting
5. Returns `BacktestResult` with equity curve, trade log, metrics, warnings, and honest reporting footer
6. Response serialized back to frontend

**Trading Flow (paper/live):**

1. Frontend creates a session via `POST /api/trading/sessions`
2. `api/routers/trading.py` delegates to `LiveTradingEngine` (attached to `app.state` during lifespan)
3. Engine creates `PaperSession`, starts async task polling `CandleDataSource`
4. Each cycle: fetch candles, generate z-score signals, execute simulated fills (paper) or real orders (live)
5. Live orders pass through `RiskManager.check_order()` before `OrderExecutor.submit_order()`
6. State persisted to SQLite via `PersistenceManager`

**State Management:**

- **Frontend global state:** `PairContext` provides selected asset1/asset2/timeframe across all dashboard pages. `AcademyDataContext` provides pre-loaded pair data for the Academy wizard.
- **Backend singletons:** `DataCacheManager` singleton (module-level `_cache_manager`), `Settings` singleton (`config/settings.py`)
- **Backend lifespan state:** `LiveTradingEngine` and `PersistenceManager` attached to `app.state` during FastAPI lifespan, shared across all trading router endpoints
- **Per-request state:** No session/auth state. Each analysis/backtest request is stateless -- load from cache, compute, return.

## Key Abstractions

**DataCacheManager (singleton):**
- Purpose: Transparent caching layer between Bitvavo API and analysis code
- Location: `src/statistical_arbitrage/data/cache_manager.py`
- Pattern: Singleton via `get_cache_manager()`, lazy CCXT client init, incremental delta fetches, parquet storage
- Key method: `get_candles(symbol, timeframe, days_back)` -- cache-first, fetch on miss

**PairAnalysis:**
- Purpose: Cointegration testing, spread calculation, stationarity analysis for a pair
- Location: `src/statistical_arbitrage/analysis/cointegration.py`
- Pattern: Stateful class initialized with two price series, methods return structured dicts

**BacktestEngine (functional):**
- Purpose: Fee-aware, look-ahead-safe backtesting with honest reporting
- Location: `src/statistical_arbitrage/backtesting/engine.py`
- Pattern: Top-level `run_backtest()` function, returns `BacktestResult` Pydantic model
- Composes: `zscore_mean_reversion.build_rolling_strategy_data()` + `generate_signal_events()` + fill accounting

**PaperTradingEngine / LiveTradingEngine (class hierarchy):**
- Purpose: Async session-based trading with simulated or real execution
- Location: `src/statistical_arbitrage/paper_trading/engine.py`, `src/statistical_arbitrage/live_trading/engine.py`
- Pattern: `LiveTradingEngine` extends `PaperTradingEngine`. Paper = simulated fills. Live = risk-gated real orders via injectable `OrderExecutor` protocol.
- Dependencies injected: `CandleDataSource` (Protocol), `PersistenceManager`, `OrderExecutor`, `RiskManager`, `TelegramNotifier`

**Pydantic API Schemas:**
- Purpose: Type-safe request/response boundary between frontend and backend
- Location: `api/schemas.py`
- Pattern: Mirror TypeScript interfaces in `frontend/src/lib/api.ts`. Backend models wrap core library dataclasses/dicts.

## Entry Points

**FastAPI Server:**
- Location: `run_api.py` -> `api/main.py`
- Triggers: `uv run python run_api.py` or `uvicorn api.main:app`
- Responsibilities: Starts uvicorn on port 8000, initializes trading engine in lifespan, registers all routers

**Next.js Dev Server:**
- Location: `frontend/package.json` (`npm run dev`)
- Triggers: `cd frontend && npm run dev`
- Responsibilities: Serves frontend on port 3000, proxies nothing (direct fetch to :8000)

**Root redirect:**
- Location: `frontend/src/app/(dashboard)/page.tsx`
- Behavior: `redirect('/academy')` -- the landing page is the Academy

## Error Handling

**Strategy:** Exceptions in core library bubble up; API routers catch and return HTTP errors

**Patterns:**
- API routers wrap core calls in try/except, raise `HTTPException` with status 500 and detail message
- `_load_pair_data()` in `api/routers/analysis.py` raises `HTTPException(404)` when cache files are missing
- Backtest engine uses preflight checks (`backtesting/preflight.py`) that return structured `EngineWarning` objects with `blocking` or `warning` severity
- Frontend `apiFetch()` in `frontend/src/lib/api.ts` throws `Error` with status code and detail message on non-2xx responses
- Trading engine logs errors and stores `last_error` on session objects

## Cross-Cutting Concerns

**Logging:** Standard Python `logging` module throughout backend. No structured logging framework.

**Validation:** Pydantic v2 models for all API boundaries (`api/schemas.py`, `backtesting/models.py`, `paper_trading/models.py`, `live_trading/models.py`). `BacktestModel` base uses `extra="forbid"` for strict validation.

**Authentication:** None. No auth on API endpoints. CORS allows all origins (`allow_origins=["*"]`).

**Numpy Serialization:** `api/schemas.py` provides `numpy_to_python()` recursive converter to handle numpy types (inf/nan -> None) before JSON serialization.

## Module Dependency Graph

```
frontend/src/lib/api.ts  --(HTTP)-->  api/routers/*

api/routers/health.py       --> data/cache_manager
api/routers/pairs.py         --> data/cache_manager
api/routers/analysis.py      --> analysis/cointegration, data/cache_manager
api/routers/research.py      --> analysis/research, data/cache_manager (via analysis._load_pair_data)
api/routers/backtest.py      --> backtesting/engine, data/cache_manager (via analysis._load_pair_data)
api/routers/optimization.py  --> backtesting/optimization, backtesting/walkforward, data/cache_manager
api/routers/trading.py       --> live_trading/engine (via app.state)
api/routers/academy_scan.py  --> analysis/cointegration, data/cache_manager

backtesting/engine.py        --> strategy/zscore_mean_reversion, backtesting/models, backtesting/overfitting, backtesting/preflight
backtesting/optimization.py  --> backtesting/engine, backtesting/models, backtesting/overfitting
backtesting/walkforward.py   --> backtesting/engine, backtesting/optimization, backtesting/models

paper_trading/engine.py      --> strategy/zscore_mean_reversion, paper_trading/data_source, paper_trading/models, paper_trading/persistence
live_trading/engine.py       --> paper_trading/engine, live_trading/order_executor, live_trading/risk_manager, live_trading/models

data/cache_manager.py        --> data/bitvavo_client (lazy), config/settings
data/bitvavo_client.py       --> ccxt, config/settings

config/settings.py           --> pydantic-settings (standalone, no internal deps)
```

---

*Architecture analysis: 2026-03-31*
