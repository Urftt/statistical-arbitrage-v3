# External Integrations

**Analysis Date:** 2026-03-31

## APIs & External Services

**Bitvavo Cryptocurrency Exchange:**
- Purpose: Primary data source for OHLCV candle data and live order execution
- SDK: `ccxt` (sync: `ccxt.bitvavo`, async: `ccxt.async_support.bitvavo`)
- REST URL: `https://api.bitvavo.com/v2` (configurable via `bitvavo_rest_url`)
- WebSocket URL: `wss://ws.bitvavo.com/v2/` (configurable via `bitvavo_ws_url`, declared in settings but not actively used in current code)
- Auth env vars: `BITVAVO_API_KEY`, `BITVAVO_API_SECRET` (loaded from `config/.env`)
- Rate limiting: Built-in CCXT rate limiter + configurable `rate_limit_per_second` (default 10)
- Public data (OHLCV, markets): No API key required
- Private data (orders, balances): API key required
- Client implementations:
  - `src/statistical_arbitrage/data/bitvavo_client.py` - Sync CCXT client for historical data collection
  - `src/statistical_arbitrage/live_trading/order_executor.py` - Async CCXT client (`BitvavoOrderExecutor`) for live order submission
  - `src/statistical_arbitrage/data/cache_manager.py` - Cached data fetching with incremental updates

**Telegram Bot API:**
- Purpose: Trade notifications (fills, errors, risk breaches, daily summaries)
- SDK: Direct HTTP via `httpx.AsyncClient` (no Telegram SDK)
- Base URL: `https://api.telegram.org/bot{token}/sendMessage`
- Auth env vars: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (loaded from `config/.env`)
- Behavior: Graceful no-op when unconfigured (empty token/chat_id)
- Implementation: `src/statistical_arbitrage/live_trading/telegram_notifier.py`
- Message format: HTML with emoji indicators
- Error handling: All HTTP errors caught and logged, never crashes trading loop

## Data Storage

**SQLite (via aiosqlite):**
- Purpose: Persistent storage for paper/live trading sessions
- Location: `data/trading.db` (created automatically on startup)
- Client: `aiosqlite` with WAL journal mode, foreign keys enabled
- Implementation: `src/statistical_arbitrage/paper_trading/persistence.py`
- Tables: `sessions`, `positions`, `trades`, `equity_snapshots`, `orders`
- Pattern: Async context manager, upserts via `ON CONFLICT DO UPDATE`

**Local Filesystem (Parquet/CSV):**
- Purpose: OHLCV candle data cache
- Directories:
  - `data/raw/` - Individual API fetch chunks
  - `data/cache/` - Merged continuous timeseries (one Parquet file per symbol/timeframe)
  - `data/processed/` - Processed analysis results
  - `data/results/` - Output results
- Format: Parquet (default, configurable to CSV)
- Implementation: `src/statistical_arbitrage/data/cache_manager.py`

**No external databases** - All persistence is local (SQLite + Parquet files)

## Authentication & Identity

**Exchange Auth:**
- Bitvavo API key/secret pair via `config/.env`
- Optional: sandbox mode for `BitvavoOrderExecutor` (testnet)
- Public endpoints (OHLCV, markets) work without credentials

**Application Auth:**
- No user authentication on the FastAPI API (single-user platform)
- CORS: Allows all origins (`allow_origins=["*"]`) in `api/main.py`

**Bot Auth:**
- Telegram Bot token from @BotFather

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry, Datadog, etc.)

**Logs:**
- Python `logging` module throughout
- Log level configurable via `settings.log_level` (default "INFO")
- Key loggers: API startup/shutdown, trading engine events, Telegram send status, persistence operations

## CI/CD & Deployment

**Hosting:**
- Local development only (no cloud deployment config detected)
- No Dockerfile, docker-compose, or cloud deployment manifests

**CI Pipeline:**
- None detected (no `.github/workflows/`, no CI config files)

## Environment Configuration

**Required env vars (for full functionality):**
- `BITVAVO_API_KEY` - Bitvavo API key (optional for public data)
- `BITVAVO_API_SECRET` - Bitvavo API secret (optional for public data)

**Optional env vars:**
- `TELEGRAM_BOT_TOKEN` - Telegram bot token for notifications
- `TELEGRAM_CHAT_ID` - Telegram chat/group ID for notifications
- `NEXT_PUBLIC_API_URL` - Frontend API base URL (default: `http://localhost:8000`)

**Secrets location:**
- `config/.env` - Primary secrets file (loaded by pydantic-settings)
- `config/.env.example` - Template with required variable names (committed to repo)

## Webhooks & Callbacks

**Incoming:**
- None (no webhook endpoints)

**Outgoing:**
- Telegram Bot API `sendMessage` - Fire-and-forget notifications on trade events

## Frontend-Backend Communication

**Pattern:** REST API over HTTP (no WebSocket, no SSE, no GraphQL)
- Frontend (`localhost:3000`) calls FastAPI (`localhost:8000`) via `fetch()`
- Typed API client: `frontend/src/lib/api.ts`
- All endpoints return JSON
- Timestamps use epoch milliseconds
- CORS middleware allows all origins

**API Routers:**
- `api/routers/health.py` - Health check
- `api/routers/pairs.py` - Available pairs and OHLCV data
- `api/routers/analysis.py` - Cointegration analysis
- `api/routers/research.py` - 8 research modules (lookback, rolling stability, OOS, timeframe, spread method, z-score threshold, tx cost, coint method)
- `api/routers/backtest.py` - Backtesting engine
- `api/routers/optimization.py` - Grid search and walk-forward optimization
- `api/routers/trading.py` - Live/paper trading session management
- `api/routers/academy_scan.py` - Academy pair scanning with fresh data fetch

---

*Integration audit: 2026-03-31*
