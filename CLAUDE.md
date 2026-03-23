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
