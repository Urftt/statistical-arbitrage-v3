# Technology Stack

**Analysis Date:** 2026-03-31

## Languages

**Primary:**
- Python 3.12+ - Backend API, core analysis library, strategy engine, backtesting, live trading
- TypeScript 5.x (strict mode) - Frontend application

**Secondary:**
- SQL (SQLite dialect) - Persistence layer for trading sessions (`src/statistical_arbitrage/paper_trading/persistence.py`)

## Runtime

**Environment:**
- Python 3.12+ (specified in `pyproject.toml` as `requires-python = ">=3.12"`)
- Node.js (version not pinned; no `.nvmrc` present)

**Package Managers:**
- **UV** for Python - Build backend: `uv_build` (>=0.9.5,<0.11.0)
  - Lockfile: `uv.lock` (present)
  - Install: `uv sync --all-extras`
- **npm** for Node.js
  - Lockfile: `frontend/package-lock.json` (present)
  - Install: `cd frontend && npm install`

## Frameworks

**Core:**
- **FastAPI** >=0.115.0 - REST API framework (`api/main.py`)
- **Uvicorn** >=0.30.0 (with `standard` extras) - ASGI server (`run_api.py`)
- **Next.js** 16.2.1 - Frontend framework with App Router (`frontend/package.json`)
- **React** 19.2.4 - UI rendering (`frontend/package.json`)

**UI Components:**
- **Mantine** v8.3.18 - Component library (core, hooks, notifications)
  - PostCSS integration: `postcss-preset-mantine` ^1.18.0, `postcss-simple-vars` ^7.0.1
  - Config: `frontend/postcss.config.mjs`

**Charting:**
- **Plotly.js** ^3.4.0 - Chart rendering
- **react-plotly.js** ^2.6.0 - React wrapper (loaded via `next/dynamic` with `ssr: false`)

**Testing:**
- **pytest** >=7.4.0 - Test runner
- **pytest-cov** >=4.1.0 - Coverage reporting
- **pytest-asyncio** >=0.21.0 - Async test support

**Linting & Formatting:**
- **ruff** >=0.1.0 - Python linter and formatter
  - Config in `pyproject.toml`: line-length 100, target Python 3.12, rules: E, F, I, W
- **ESLint** ^9 with `eslint-config-next` 16.2.1 - TypeScript/React linting
  - Config: `frontend/eslint.config.mjs`
- **mypy** >=1.7.0 - Python static type checker (dev dependency)

**Build/Dev:**
- **uv_build** >=0.9.5,<0.11.0 - Python build backend (`pyproject.toml`)
- **Next.js** built-in bundler (Turbopack) - Frontend builds

## Key Dependencies

**Critical (Python):**
- `polars` >=0.20.0 - All dataframe operations (never use Pandas)
- `ccxt` >=4.2.0 - Exchange API client for Bitvavo (sync and async)
- `statsmodels` >=0.14.0 - Statistical tests (cointegration, ADF)
- `scipy` >=1.11.0 - Scientific computing, statistical functions
- `numpy` >=1.26.0 - Numerical operations
- `pydantic` >=2.5.0 - Data validation and serialization
- `pydantic-settings` >=2.1.0 - Configuration management (`config/settings.py`)

**Infrastructure (Python):**
- `httpx` >=0.27.0 - Async HTTP client (Telegram notifications)
- `aiosqlite` >=0.20.0 - Async SQLite driver for trading persistence
- `python-dotenv` >=1.0.0 - Environment variable loading
- `plotly` >=5.18.0 - Server-side chart generation (visualization module)

**Critical (Frontend):**
- `@tabler/icons-react` ^3.40.0 - Icon library
- `@types/react-plotly.js` ^2.6.4 - Plotly type definitions

## Configuration

**Environment:**
- Python settings via `pydantic-settings` with `.env` file at `config/.env`
- Example env file: `config/.env.example` (present)
- Frontend env: `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`)
- No `.env` files in repo root or `frontend/` directory

**TypeScript:**
- Config: `frontend/tsconfig.json`
- Strict mode enabled
- Path alias: `@/*` maps to `./src/*`
- Module resolution: bundler
- Target: ES2017

**Build:**
- `pyproject.toml` - Python project configuration (dependencies, ruff, pytest)
- `frontend/next.config.ts` - Next.js configuration (currently empty/default)
- `frontend/postcss.config.mjs` - PostCSS with Mantine preset

## Platform Requirements

**Development:**
- Python 3.12+
- Node.js (compatible with Next.js 16)
- UV package manager
- npm package manager
- Two processes: FastAPI on :8000, Next.js on :3000

**Production:**
- FastAPI served via Uvicorn (host 0.0.0.0, port 8000)
- Next.js production build (`npm run build && npm start`)
- SQLite file at `data/trading.db` for persistence
- Bitvavo API credentials for live data/trading
- Optional: Telegram bot token for notifications

## Run Commands

**Backend:**
```bash
uv sync --all-extras                # Install all Python dependencies
uv run python run_api.py            # Start API (http://localhost:8000, auto-reload)
uv run pytest tests/ --ignore=tests/test_api.py --ignore=tests/test_backtest_api.py --ignore=tests/test_optimization_api.py --ignore=tests/test_research_api.py --ignore=tests/test_trading_api.py  # Unit tests (174 tests)
uv run pytest tests/                # All tests (needs cached data for API tests)
uv run ruff check src/ api/         # Lint Python
uv run ruff format src/ api/        # Format Python
```

**Frontend:**
```bash
cd frontend
npm install                         # Install Node dependencies
npm run dev                         # Dev server (http://localhost:3000, binds 0.0.0.0)
npm run build                       # Production build
npm run lint                        # ESLint
```

---

*Stack analysis: 2026-03-31*
