# Codebase Concerns

**Analysis Date:** 2026-03-31

## Security Considerations

**CORS Wildcard on API (High):**
- Risk: `allow_origins=["*"]` with `allow_credentials=True` allows any website to make authenticated requests to the API. While currently localhost-only, this is a security antipattern that will be dangerous if the API is ever exposed on a network.
- Files: `api/main.py` (lines 101-107)
- Current mitigation: API runs on localhost only
- Recommendation: Restrict `allow_origins` to `["http://localhost:3000"]` and any known LAN/Tailscale addresses. Remove `allow_credentials=True` if cookies are not used.

**No API Authentication (High):**
- Risk: All API endpoints are publicly accessible with zero authentication. The trading endpoints (`/sessions`, `/sessions/{id}/start`, etc.) can start/stop live trading sessions without any auth.
- Files: `api/routers/trading.py`, all files in `api/routers/`
- Current mitigation: None. Localhost-only deployment is the implicit boundary.
- Recommendation: Add API key middleware or Bearer token auth, at minimum for trading endpoints. Consider a simple shared-secret approach for local use.

**No API Rate Limiting (Medium):**
- Risk: No rate limiting on any endpoint. CPU-heavy endpoints like grid search (`/optimization/grid-search`) and walk-forward (`/optimization/walk-forward`) could be abused to exhaust server resources.
- Files: `api/routers/optimization.py`, `api/routers/research.py`
- Current mitigation: Grid search has a `max_combinations=500` guard in `src/statistical_arbitrage/backtesting/optimization.py` (line 59)
- Recommendation: Add rate limiting middleware (e.g., `slowapi`) especially for compute-heavy endpoints.

**API Keys in Settings with Empty Defaults (Low):**
- Risk: `bitvavo_api_key` and `bitvavo_api_secret` default to empty strings. If a developer accidentally starts the live trading engine without configuring keys, the `BitvavoOrderExecutor` will fail at runtime rather than at startup validation.
- Files: `config/settings.py` (lines 27-28), `src/statistical_arbitrage/live_trading/order_executor.py` (lines 163-177)
- Current mitigation: Default startup uses `MockOrderExecutor` in `api/main.py` (line 49)
- Recommendation: Add a validator that raises at startup if live trading is enabled but API keys are empty.

## Performance Concerns

**Synchronous Route Handlers with CPU-Heavy Computation (High):**
- Problem: All analysis, research, and optimization route handlers are synchronous (`def` not `async def`). FastAPI runs these in a thread pool, but each request blocks a thread for the duration of CPU-heavy statistical computations (cointegration tests, grid search, walk-forward analysis).
- Files: `api/routers/analysis.py` (lines 144, 211, 237, 268), `api/routers/research.py` (lines 78, 172, 213, 253, 322, 374, 439, 502), `api/routers/optimization.py` (lines ~50, ~190)
- Cause: Statistical computations (statsmodels `coint`, `adfuller`, NumPy `polyfit`) are inherently CPU-bound. With the default thread pool, concurrent requests will compete for CPU and may starve the async event loop.
- Improvement: For long-running computations (grid search, walk-forward), consider running them in a `ProcessPoolExecutor` via `asyncio.run_in_executor()`, or implement a task queue pattern with status polling.

**No Data Pagination on Large Responses (Medium):**
- Problem: Endpoints return full datasets without pagination. The OHLCV endpoint returns all candles for a symbol in a single response, and research endpoints return complete result sets.
- Files: `api/routers/pairs.py`, `api/routers/analysis.py`
- Cause: Single-user learning platform assumption
- Improvement: Add optional `limit`/`offset` query parameters for future scalability.

**Cache Manager Uses Synchronous CCXT (Medium):**
- Problem: `DataCacheManager` uses synchronous `ccxt.bitvavo` for API calls. When triggered from a sync FastAPI handler in a thread, this blocks the thread during network I/O. Multiple concurrent data fetches will exhaust the thread pool.
- Files: `src/statistical_arbitrage/data/bitvavo_client.py` (line 83 — `self.client.fetch_ohlcv()`), `src/statistical_arbitrage/data/cache_manager.py`
- Improvement: Use `ccxt.async_support.bitvavo` in the cache manager, matching the pattern already used in `src/statistical_arbitrage/live_trading/order_executor.py`.

**Global Singleton Cache Manager Not Thread-Safe (Medium):**
- Problem: `get_cache_manager()` uses a module-level global with no locking. Multiple threads (from sync FastAPI handlers) could race to create the singleton or read/write cache files concurrently.
- Files: `src/statistical_arbitrage/data/cache_manager.py` (lines 328-337)
- Improvement: Use `threading.Lock` for singleton creation, or move to FastAPI dependency injection with `app.state`.

## Error Handling Gaps

**Broad Exception Catching Throughout (Medium):**
- Problem: 30+ locations catch `except Exception` — some silently swallow errors, some log and re-raise as HTTP 500. This masks root causes and makes debugging difficult.
- Files (silent swallowing):
  - `src/statistical_arbitrage/analysis/research.py` (lines 77, 193, 202, 579) — silently returns None/empty results on statistical test failures
  - `src/statistical_arbitrage/backtesting/walkforward.py` (lines 209, 238) — logs but continues with degraded results
  - `src/statistical_arbitrage/backtesting/optimization.py` (line 117) — logs but continues
- Files (re-raised as generic 500):
  - `api/routers/analysis.py` (lines 165, 223, 250, 299)
  - `api/routers/research.py` (lines 103, 187, 228, 292, 335, 392, 460)
- Impact: Users see generic "failed" messages; actual errors (data issues, numerical instability) are hidden.
- Fix approach: Catch specific exceptions (`ValueError`, `LinAlgError`, `np.linalg.LinAlgError`) and return structured error responses with actionable messages.

**Silent Pass on Cancelled Tasks (Low):**
- Problem: Three locations catch exceptions with bare `pass` — these catch `CancelledError` appropriately but also swallow any unexpected errors during task cleanup.
- Files:
  - `src/statistical_arbitrage/live_trading/engine.py` (line 163)
  - `src/statistical_arbitrage/paper_trading/engine.py` (line 128)
  - `api/routers/trading.py` (line 290) — catches `Exception` with `pass` when cancelling a task
- Fix approach: Narrow these to `except (asyncio.CancelledError, Exception): pass` or at minimum log unexpected exceptions.

**No Error Boundaries in Frontend (Medium):**
- Problem: No React error boundary components exist. No `error.tsx` or `loading.tsx` files in the Next.js app directory. An unhandled rendering error in any page will crash the entire application.
- Files: `frontend/src/app/(dashboard)/` — no `error.tsx` found at any level
- Fix approach: Add `error.tsx` at the `(dashboard)` layout level to catch rendering errors gracefully. Add `loading.tsx` for Suspense boundaries.

## Incomplete Implementations

**5 Stub Pages (High):**
- Problem: Five frontend pages are empty stubs showing only "Coming soon" text. These pages have corresponding backend APIs that are fully implemented but unreachable from the UI.
- Files:
  - `frontend/src/app/(dashboard)/deep-dive/page.tsx` (16 lines — stub)
  - `frontend/src/app/(dashboard)/research/page.tsx` (16 lines — stub)
  - `frontend/src/app/(dashboard)/backtest/page.tsx` (16 lines — stub)
  - `frontend/src/app/(dashboard)/optimize/page.tsx` (16 lines — stub)
  - `frontend/src/app/(dashboard)/summary/page.tsx` (16 lines — stub)
- Impact: Blocks the core research/backtesting workflow in the UI. Backend has 8 research modules, full backtest engine, grid search, and walk-forward — all inaccessible via frontend.
- Fix approach: Implement each page incrementally. Research and backtest pages are highest priority.

**API Client Has Typed Functions for Unbuilt Pages (Low):**
- Problem: `frontend/src/lib/api.ts` (911 lines) defines typed API functions for all backend endpoints, but many are unused because the corresponding pages are stubs.
- Impact: No functional impact, but creates maintenance burden keeping types in sync with a backend API that may evolve before pages are built.

## Tech Debt

**Print Statements Instead of Logger (Medium):**
- Issue: 8 `print()` calls remain in production code paths, mixing unstructured output with the logging framework.
- Files:
  - `src/statistical_arbitrage/__init__.py` (line 11)
  - `src/statistical_arbitrage/data/cache_manager.py` (lines 247, 263, 318, 323)
  - `src/statistical_arbitrage/data/bitvavo_client.py` (lines 237, 276, 283)
- Impact: Logs are inconsistent; print output cannot be filtered by log level or sent to log aggregators.
- Fix approach: Replace all `print()` with `logger.info()` or `logger.debug()`.

**Duplicated `_get_cache_mgr` Dependency (Low):**
- Issue: The `_get_cache_mgr` FastAPI dependency function is defined identically in two places: `api/routers/analysis.py` (line 37) and `api/routers/academy_scan.py` (line 30). A third variant `get_cache_mgr` exists in `api/routers/health.py` (line 14) and `api/routers/pairs.py` (line 17).
- Impact: Four definitions of essentially the same function. Any change to cache manager initialization must be updated in all locations.
- Fix approach: Move to a shared `api/dependencies.py` module and import from there.

**Private Attribute Access Across Module Boundaries (Low):**
- Issue: `api/routers/trading.py` (line 284) accesses `engine._tasks` (private dict) directly to cancel a task during session deletion.
- Impact: Tight coupling to `LiveTradingEngine` internals; breaks if internal structure changes.
- Fix approach: Add a public `engine.cancel_task(session_id)` method.

## Frontend Concerns

**Zero Frontend Tests (High):**
- Problem: No test files exist anywhere in `frontend/src/`. No testing framework is configured (no Jest, Vitest, or Playwright in `package.json`).
- Files: `frontend/package.json` — no test dependencies, no test script
- Impact: Any frontend change is untested. Refactoring lesson components (18 lesson files averaging 280 lines each) carries high regression risk.
- Fix approach: Add Vitest + React Testing Library. Start with unit tests for `api.ts` and `PairContext.tsx`.

**No Memoization on Expensive Plotly Renders (Low):**
- Problem: 90 `useCallback`/`useMemo` calls exist across the codebase (mostly in academy lessons), but Plotly chart data objects are not memoized. Plotly re-renders are expensive.
- Files: `frontend/src/components/charts/PlotlyChart.tsx`, various lesson components
- Impact: Minor — noticeable on rapid state changes but acceptable for a learning platform.

## Deployment & Operations

**No CI/CD Pipeline (Medium):**
- Problem: No `.github/workflows/`, no Dockerfile, no docker-compose, no deployment configuration of any kind.
- Impact: No automated testing on PR, no automated deployment. Manual-only process.
- Fix approach: Add a minimal GitHub Actions workflow for `ruff check`, `pytest`, and `npm run build`.

**No Dockerfile or Container Config (Medium):**
- Problem: No containerization. The two-process architecture (FastAPI + Next.js) requires manual setup of Python 3.12, UV, Node.js, and both processes.
- Impact: Difficult to reproduce the environment or deploy to any hosting platform.
- Fix approach: Create a `docker-compose.yml` with two services (api + frontend) and corresponding Dockerfiles.

**No Health Check Beyond Basic Ping (Low):**
- Problem: The `/health` endpoint only checks if the cache manager can be instantiated. It does not verify database connectivity, exchange API reachability, or trading engine status.
- Files: `api/routers/health.py` (25 lines)
- Fix approach: Add checks for SQLite connection (`trading.db`), Bitvavo API ping, and trading engine session count.

## Scaling Limits

**SQLite for Trading Persistence (Medium):**
- Problem: Trading sessions, positions, and trades are stored in SQLite (`data/trading.db`). WAL mode is enabled for concurrent reads, but SQLite has a single-writer constraint.
- Files: `src/statistical_arbitrage/paper_trading/persistence.py` (uses `aiosqlite`)
- Current capacity: Adequate for single-user paper/live trading with 2 concurrent sessions
- Limit: Will not scale to multiple users or high-frequency polling
- Scaling path: Migrate to PostgreSQL if multi-user support is needed

**File-Based Cache (Low):**
- Problem: OHLCV data is cached as Parquet files on the local filesystem. No TTL or eviction policy — "cache forever, only fetch deltas."
- Files: `src/statistical_arbitrage/data/cache_manager.py`
- Current capacity: Works well for single-user with tens of trading pairs
- Limit: Disk usage grows unbounded; no cache invalidation if exchange data is corrected
- Scaling path: Add optional TTL-based eviction; consider Redis for multi-process sharing

## Test Coverage Gaps

**Frontend: Zero Coverage (High):**
- What's not tested: All React components, contexts, API client, routing
- Files: Entire `frontend/src/` directory
- Risk: UI regressions go undetected; lesson content changes could break interactivity
- Priority: High

**Live Trading Integration Path Not Tested in CI (Medium):**
- What's not tested: The actual `BitvavoOrderExecutor` path — tests use `MockOrderExecutor` only. Real exchange interaction (order submission, fill parsing, error recovery) is untested.
- Files: `src/statistical_arbitrage/live_trading/order_executor.py` (lines 150-308), `tests/live_trading/test_order_executor.py`
- Risk: Production order execution could fail in unexpected ways
- Priority: Medium — sandbox/testnet integration tests would address this

**API Tests Require Pre-Cached Data (Medium):**
- What's not tested: API tests (`test_api.py`, `test_backtest_api.py`, `test_optimization_api.py`, `test_research_api.py`, `test_trading_api.py`) are excluded from the default test command because they require cached OHLCV data files to exist.
- Files: `CLAUDE.md` shows the `--ignore` flags for these tests
- Risk: API endpoint regressions not caught by default test run
- Priority: Medium — add fixtures or mock the cache manager

---

*Concerns audit: 2026-03-31*
