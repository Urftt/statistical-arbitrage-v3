# Coding Conventions

**Analysis Date:** 2026-03-31

## Naming Patterns

**Python Files:**
- snake_case for all module files: `cointegration.py`, `cache_manager.py`, `zscore_mean_reversion.py`
- Test files prefixed with `test_`: `test_backtest_engine.py`, `test_optimization.py`
- Router files match their domain: `api/routers/analysis.py`, `api/routers/backtest.py`

**Python Functions:**
- snake_case: `run_backtest()`, `calculate_hedge_ratio()`, `test_cointegration()`
- Private helpers prefixed with underscore: `_to_numpy()`, `_load_pair_data()`, `_get_cache_mgr()`
- Test helper factories prefixed with underscore: `_params()`, `_make_correlated_prices()`, `_single_long_fixture()`

**Python Classes:**
- PascalCase: `PairAnalysis`, `StrategyParameters`, `RiskManager`, `LiveTradingEngine`
- Test classes prefixed with `Test`: `TestBacktestEngine`, `TestHealth`, `TestRiskManagerRejections`
- Pydantic models use PascalCase with descriptive suffixes: `BacktestResponse`, `HealthResponse`, `CointegrationResponse`

**Python Variables:**
- snake_case: `hedge_ratio`, `spread_props`, `close1`, `close2`
- Constants in UPPER_SNAKE_CASE: `PROJECT_ROOT`, `BASE_PARAMS`

**TypeScript Files:**
- PascalCase for components: `PlotlyChart.tsx`, `Header.tsx`, `Sidebar.tsx`, `GlossaryLink.tsx`
- PascalCase for lesson components: `Lesson1_1.tsx`, `Lesson2_3.tsx` (chapter_lesson pattern)
- camelCase for utility modules: `api.ts`, `theme.ts`, `glossary.ts`
- PascalCase for context files: `PairContext.tsx`, `AcademyDataContext.tsx`
- Next.js pages use `page.tsx` convention

**TypeScript Functions:**
- camelCase for functions: `fetchPairs()`, `postBacktest()`, `symbolToDash()`
- PascalCase for React components: `PlotlyChart()`, `ScannerPage()`, `PairProvider()`
- Custom hooks prefixed with `use`: `usePairContext()`

**TypeScript Interfaces:**
- PascalCase: `PairInfo`, `BacktestResponse`, `PlotlyChartProps`
- API payload interfaces suffixed with `Payload`: `MetricSummaryPayload`, `EquityCurvePointPayload`
- Request interfaces suffixed with `Request`: `BacktestRequest`, `GridSearchRequest`
- Response interfaces suffixed with `Response`: `BacktestResponse`, `GridSearchResponse`

## Code Style

**Python Formatting:**
- Tool: **Ruff** (linter + formatter)
- Config: `pyproject.toml` — `[tool.ruff]`
- Line length: 100 characters
- Target: Python 3.12
- Lint rules: `["E", "F", "I", "W"]` (pyflakes, pycodestyle errors/warnings, isort)

**Python Linting Commands:**
```bash
uv run ruff check src/ api/   # Lint check
uv run ruff format src/ api/  # Auto-format
```

**TypeScript Formatting:**
- No Prettier configured
- ESLint via `eslint.config.mjs` using `eslint-config-next/core-web-vitals` and `eslint-config-next/typescript`
- TypeScript strict mode enabled in `frontend/tsconfig.json`

**TypeScript Linting Commands:**
```bash
cd frontend && npm run lint   # ESLint
```

## Import Organization

**Python — enforced by Ruff isort (`I` rule):**
1. Standard library imports (`logging`, `math`, `pathlib`)
2. Third-party imports (`fastapi`, `polars`, `numpy`, `pydantic`)
3. Local imports (`from statistical_arbitrage...`, `from api.schemas...`)

Example from `api/routers/analysis.py`:
```python
import logging
from datetime import datetime, timedelta

import polars as pl
from fastapi import APIRouter, Depends, HTTPException

from api.schemas import (
    AnalysisRequest,
    CointegrationResponse,
    ...
)
from src.statistical_arbitrage.analysis.cointegration import PairAnalysis
```

**Python — `from __future__ import annotations`:**
- Used in newer modules (strategy, backtesting models, live trading) for forward references
- Not universally adopted — older modules (cointegration, analysis) omit it

**TypeScript:**
1. React/Next.js imports (`'use client'` directive first, then React hooks, Next.js)
2. Mantine component imports (grouped from `@mantine/core`)
3. Icon imports (`@tabler/icons-react`)
4. Local imports using `@/` path alias

Example from `frontend/src/app/(dashboard)/scanner/page.tsx`:
```typescript
'use client';

import { useState, useCallback, useEffect } from 'react';
import {
  Alert, Badge, Button, Chip, Container, ...
} from '@mantine/core';
import { IconSearch, IconRefresh, ... } from '@tabler/icons-react';
import { fetchPairs, fetchAcademyScan, ... } from '@/lib/api';
```

**Path Aliases:**
- TypeScript: `@/*` maps to `./src/*` (configured in `frontend/tsconfig.json`)
- Python: No path aliases; uses package imports `from statistical_arbitrage.xxx`

## Error Handling

**Python API Endpoints:**
- Wrap core logic in `try/except` blocks
- Catch specific `HTTPException` and re-raise, catch generic `Exception` for everything else
- Convert to `HTTPException` with status codes: 404 (data not found), 422 (invalid input), 500 (internal error)
- Log exceptions with `logger.exception()` before raising
- Chain exceptions with `raise ... from e`

Pattern from `api/routers/analysis.py`:
```python
try:
    pa = PairAnalysis(close1, close2)
    result = pa.test_cointegration()
except Exception as e:
    logger.exception("Analysis failed for %s / %s", request.asset1, request.asset2)
    raise HTTPException(status_code=500, detail=f"Analysis failed: {e}") from e
```

**Python Core Library:**
- Raises `ValueError` for invalid inputs (e.g., insufficient data, length mismatches)
- Returns plain dicts or dataclass/Pydantic model instances (no HTTP concerns)
- No try/except in pure computation code — let errors propagate

**TypeScript Frontend:**
- Central `apiFetch<T>()` wrapper in `frontend/src/lib/api.ts` handles all HTTP errors
- Extracts `detail` from FastAPI error payloads for user-facing messages
- Components use try/catch in async handlers, store error in state: `setError(message)`
- Loading/error states use `useState<string | null>(null)` pattern

Pattern from `frontend/src/lib/api.ts`:
```typescript
async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, options);
  } catch (err) {
    throw new Error(`API fetch failed: ${url} — ${err instanceof Error ? err.message : String(err)}`);
  }
  if (!response.ok) {
    // Extract detail from FastAPI error response
    ...
    throw new Error(`API error: ${response.status} ...`);
  }
  return response.json() as Promise<T>;
}
```

## Type Annotation Practices

**Python:**
- Type hints on all function signatures (parameters and return types)
- Pydantic models for all API schemas with `Field()` descriptions
- `Literal` types for constrained string fields: `Literal["ok", "blocked"]`, `Literal["warning", "blocking"]`
- Use `dict[str, Any]` for flexible internal return types
- Pydantic `ConfigDict(extra="forbid")` on backtest models for strict validation
- `Protocol` with `@runtime_checkable` for dependency injection: `OrderExecutor` in `src/statistical_arbitrage/live_trading/order_executor.py`

**TypeScript:**
- Strict mode enabled (`"strict": true` in tsconfig)
- Interfaces for all API response types in `frontend/src/lib/api.ts` (mirror Python schemas)
- Props interfaces for components: `PlotlyChartProps`, `PairContextValue`
- Generic typing on fetch wrapper: `apiFetch<T>()`

## Comments and Docstrings

**Python Module Docstrings:**
- Every module has a top-level docstring explaining purpose
- Format: triple-quoted string, 1-3 sentences

```python
"""Cointegration analysis for pairs trading.

This module provides tools for testing cointegration between asset pairs,
calculating spreads, and analyzing mean-reversion properties.
"""
```

**Python Function Docstrings:**
- Google-style with `Args:` and `Returns:` sections
- Present on public methods, sometimes omitted on private helpers

```python
def test_stationarity(self, series: np.ndarray, name: str = "Series") -> dict:
    """
    Perform Augmented Dickey-Fuller test for stationarity.

    Args:
        series: Time series to test
        name: Name of the series for reporting

    Returns:
        Dictionary with test results
    """
```

**Python Inline Comments:**
- Section separators using `# ---------------------------------------------------------------------------`
- Explanatory comments for non-obvious logic
- Section headers within files: `# POST /api/analysis/cointegration`

**TypeScript:**
- JSDoc `/** ... */` comments on exported functions and components
- No inline TSDoc `@param`/`@returns` tags — just description paragraphs
- Section separators matching Python style: `// ---------------------------------------------------------------------------`

## Function Design

**Python:**
- Pure functions preferred in core library (no side effects, no web framework imports)
- Factory pattern for test data: `_make_correlated_prices()`, `make_signal_candles()`
- Pydantic models as function parameters for complex inputs: `StrategyParameters`
- Return dicts from analysis functions, Pydantic models from API layer

**TypeScript:**
- React components are default exports for pages, named exports for reusable components
- API functions are async, return typed promises
- Hooks use `useCallback` for stable references passed as props
- State initialization follows `const [value, setValue] = useState<Type>(initial)` pattern

## Module Design

**Python Exports:**
- `__init__.py` files used for re-exports in packages
- Core library (`src/statistical_arbitrage/`) exports classes and functions
- API layer imports from core library — never the reverse

**TypeScript Barrel Files:**
- Used for lesson components: `frontend/src/components/academy/lessons/index.ts`
- Used for real-data components: `frontend/src/components/academy/real-data/index.ts`
- Not used everywhere — direct imports are common

## Frontend Component Patterns

**Mantine Usage:**
- All UI built with Mantine v8 components: `Container`, `Stack`, `Paper`, `Title`, `Text`, `Select`, `Button`, `Table`, `Alert`, `Badge`, `Chip`
- Icons from `@tabler/icons-react`
- `AppShell` for dashboard layout with header (60px) and sidebar (260px): `frontend/src/app/(dashboard)/layout.tsx`
- Dark color scheme enforced at root: `<html data-mantine-color-scheme="dark">`
- Theme defined in `frontend/src/lib/theme.ts` using `createTheme()`
- Notifications via `@mantine/notifications` at root layout

**Plotly Charts:**
- All charts go through `PlotlyChart` wrapper: `frontend/src/components/charts/PlotlyChart.tsx`
- Loaded via `next/dynamic` with `ssr: false` to avoid SSR issues
- Shows `Skeleton` placeholder while loading
- Auto-merges dark theme template from `PLOTLY_DARK_TEMPLATE`
- Config defaults: `responsive: true`, `displayModeBar: false`

**Page Pattern:**
- Every page is `'use client'`
- Pages use `useState` for loading, error, and data states
- Data fetching in `useEffect` with cancellation flag pattern:
```typescript
useEffect(() => {
  let cancelled = false;
  async function load() {
    try { ... }
    catch { ... }
    finally { if (!cancelled) setLoading(false); }
  }
  load();
  return () => { cancelled = true; };
}, []);
```

**Context Pattern:**
- Global state via React Context: `PairContext` in `frontend/src/contexts/PairContext.tsx`
- Provider wraps dashboard layout
- Custom hook `usePairContext()` with null-check guard
- `AcademyDataContext` for academy-specific shared data

## API Endpoint Patterns

**URL Structure:**
- All endpoints under `/api/` prefix
- Domain routers: `/api/health`, `/api/pairs`, `/api/analysis`, `/api/research`, `/api/backtest`, `/api/optimization`, `/api/trading`, `/api/academy`
- Kebab-case for multi-word paths: `/api/research/lookback-window`, `/api/research/rolling-stability`, `/api/research/oos-validation`
- Path parameters use dash-separated symbols: `/api/pairs/ETH-EUR/ohlcv`

**HTTP Methods:**
- `GET` for read-only: health, pairs list, OHLCV data
- `POST` for analysis/computation: cointegration, backtest, research modules, optimization

**Request/Response:**
- POST bodies use Pydantic models defined in `api/schemas.py`
- Responses use Pydantic `response_model` for automatic validation and OpenAPI docs
- Numpy types converted via `numpy_to_python()` helper before serialization
- Timestamps are epoch milliseconds (integers)

**Router Registration:**
- Routers defined with `APIRouter(prefix="/api/...", tags=["..."])` per domain
- All registered in `api/main.py` via `app.include_router()`
- FastAPI Depends for dependency injection (cache manager)

**Settings:**
- Nested Pydantic settings in `config/settings.py`
- Singleton: `settings = Settings()`
- `.env` file loaded from `config/.env` (exists, not read for security)

---

*Convention analysis: 2026-03-31*
