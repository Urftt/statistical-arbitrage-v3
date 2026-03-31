# Testing Patterns

**Analysis Date:** 2026-03-31

## Test Framework

**Runner:**
- pytest >= 7.4.0
- pytest-asyncio >= 0.21.0 (for async live trading tests)
- pytest-cov >= 4.1.0 (coverage support)
- Config: `pyproject.toml` — `[tool.pytest.ini_options]` sets `pythonpath = ["."]`

**Assertion Library:**
- Built-in pytest assertions
- `pytest.approx` for floating-point comparisons
- `pytest.raises` for expected exceptions

**Run Commands:**
```bash
# Unit tests only (excludes API integration tests that need cached data)
uv run pytest tests/ --ignore=tests/test_api.py --ignore=tests/test_backtest_api.py --ignore=tests/test_optimization_api.py --ignore=tests/test_research_api.py --ignore=tests/test_trading_api.py

# All tests (requires cached parquet data in data/ directory)
uv run pytest tests/

# Specific test file
uv run pytest tests/test_backtest_engine.py

# Live trading tests only
uv run pytest tests/live_trading/

# With coverage
uv run pytest tests/ --cov=src/statistical_arbitrage --cov=api
```

## Test File Organization

**Location:**
- Separate `tests/` directory at project root (not co-located with source)
- Subdirectory for live trading: `tests/live_trading/`

**Naming:**
- Files: `test_{module_name}.py` — e.g., `test_backtest_engine.py`, `test_optimization.py`
- API integration tests: `test_{domain}_api.py` — e.g., `test_api.py`, `test_backtest_api.py`, `test_research_api.py`, `test_trading_api.py`
- Live trading domain: `tests/live_trading/test_{component}.py` — e.g., `test_live_engine.py`, `test_risk_manager.py`

**Structure:**
```
tests/
├── test_api.py                    # Core API endpoints (health, pairs, OHLCV, analysis)
├── test_backtest_api.py           # Backtest API integration
├── test_backtest_engine.py        # Backtest engine unit tests
├── test_optimization.py           # Grid search unit tests
├── test_optimization_api.py       # Optimization API integration
├── test_overfitting.py            # Overfitting detection tests
├── test_research_api.py           # Research API integration
├── test_research_modules.py       # Research module unit tests
├── test_research_s03.py           # S03 research module tests
├── test_rolling_cointegration.py  # Rolling cointegration tests
├── test_trading_api.py            # Trading API integration
├── test_walkforward.py            # Walk-forward validation tests
└── live_trading/
    ├── __init__.py
    ├── conftest.py                # Shared fixtures for live trading tests
    ├── test_integration.py        # End-to-end live trading integration
    ├── test_kill_switch.py        # Kill switch / emergency stop tests
    ├── test_live_engine.py        # LiveTradingEngine cycle tests
    ├── test_order_executor.py     # Mock + Bitvavo executor tests
    ├── test_persistence.py        # SQLite persistence layer tests
    ├── test_reconciliation.py     # Position reconciliation tests
    ├── test_risk_manager.py       # Risk limit enforcement tests
    ├── test_system_integration.py # Full system integration tests
    └── test_telegram.py           # Telegram notification tests
```

## Test Structure

**Suite Organization — Class-based grouping:**
```python
class TestBacktestEngine:
    def test_executes_signals_on_the_next_bar_without_lookahead(self):
        ...

    def test_accounts_for_fees_and_marks_equity_deterministically(self):
        ...
```

- Test classes group related tests: `TestHealth`, `TestPairsList`, `TestOHLCV`
- Descriptive method names explain the behavior being tested
- No `self` usage in most test methods (classes used purely for grouping)
- Some files use nested classes for sub-grouping: `TestRiskManagerRejections`, `TestRiskManagerApprovals`

**Test Naming Pattern:**
- `test_{what_it_does}` or `test_{condition}_{expected_result}`
- Examples: `test_health_returns_ok`, `test_below_minimum_order_size`, `test_cointegrated_pair_holds_oos`
- Long descriptive names preferred: `test_executes_signals_on_the_next_bar_without_lookahead`

## Fixtures and Factories

**Shared Fixtures (conftest.py):**
- `tests/live_trading/conftest.py` provides fixtures for the live trading test suite
- No root-level `conftest.py`

**Live Trading Fixtures:**
```python
# From tests/live_trading/conftest.py

@pytest_asyncio.fixture
async def persistence(tmp_path):
    """Create a connected PersistenceManager with a tmp_path SQLite DB."""
    db_path = tmp_path / "test.sqlite"
    pm = PersistenceManager(db_path)
    await pm.connect()
    yield pm
    await pm.close()

@pytest.fixture
def mock_executor():
    """Create a MockOrderExecutor with default settings."""
    return MockOrderExecutor(default_fill_price=100.0, default_fee_rate=0.0025)

@pytest.fixture
def risk_manager():
    """Create a RiskManager with default conservative limits."""
    return RiskManager(
        max_position_size_eur=25.0,
        max_concurrent_positions=2,
        daily_loss_limit_eur=50.0,
        min_order_size_eur=5.0,
    )

@pytest.fixture
def signal_candles():
    """Candles that produce z-score entry/exit signals."""
    return make_signal_candles()
```

**Factory Functions (inline in test files):**
- Private helper functions prefixed with `_` for creating test data
- Pattern used consistently across test files

```python
# From tests/test_backtest_engine.py
def _params(**overrides) -> StrategyParameters:
    base = {
        "lookback_window": 3,
        "entry_threshold": 1.0,
        ...
    }
    base.update(overrides)
    return StrategyParameters(**base)

# From tests/test_optimization.py
def _make_correlated_prices(n: int = 600, seed: int = 42) -> tuple:
    ...

# From tests/test_research_modules.py
def _make_cointegrated_pair(n: int, noise_std: float = 0.3, seed: int = 42) -> tuple:
    ...
```

**Deterministic Test Data:**
- All synthetic data uses fixed `seed` parameter for reproducibility
- `make_signal_candles()` and `make_losing_candles()` in conftest generate known signal patterns
- Candle data structured as `[timestamp, open, high, low, close, volume]`
- Timestamps are epoch milliseconds starting from a fixed base

## Mocking

**Framework:** No external mocking library — uses custom mock classes and `pytest_asyncio`

**Mock Classes (production code, used in tests):**
- `MockOrderExecutor` in `src/statistical_arbitrage/live_trading/order_executor.py` — configurable fill prices, fee rates, error injection, submission recording
- `MockCandleDataSource` in `src/statistical_arbitrage/paper_trading/data_source.py` — feeds predetermined candle sequences

**Pattern — Dependency Injection with Protocol:**
```python
# Production code defines Protocol
@runtime_checkable
class OrderExecutor(Protocol):
    async def submit_order(...) -> LiveOrder: ...
    async def close(self) -> None: ...

# MockOrderExecutor implements the Protocol
class MockOrderExecutor:
    def __init__(self, default_fill_price=100.0, default_fee_rate=0.0025): ...

# Tests inject mock
engine = LiveTradingEngine(
    data_source=MockCandleDataSource(candles),
    persistence=pm,  # real PersistenceManager with tmp_path
    order_executor=MockOrderExecutor(...),
    risk_manager=RiskManager(...),
)
```

**What to Mock:**
- External services: order execution (Bitvavo API), Telegram notifications
- Data sources: candle data feeds
- File system: use `tmp_path` fixture for SQLite databases

**What NOT to Mock:**
- Core computation: backtest engine, strategy logic, risk manager, persistence layer
- These use real implementations even in tests

**API Integration Tests:**
- Use `fastapi.testclient.TestClient` with the real app
- No mocking of internal services — requires actual cached parquet data
- Module-level client: `client = TestClient(app)`

```python
# From tests/test_api.py
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

class TestHealth:
    def test_health_returns_ok(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
```

## Test Types

**Unit Tests (run without external dependencies):**
- Backtest engine: `tests/test_backtest_engine.py` (144 lines)
- Optimization: `tests/test_optimization.py` (301 lines)
- Walk-forward: `tests/test_walkforward.py` (300 lines)
- Overfitting detection: `tests/test_overfitting.py` (260 lines)
- Research modules: `tests/test_research_modules.py` (206 lines), `tests/test_research_s03.py` (143 lines)
- Rolling cointegration: `tests/test_rolling_cointegration.py` (220 lines)
- Risk manager: `tests/live_trading/test_risk_manager.py`
- Order executor: `tests/live_trading/test_order_executor.py`
- Persistence: `tests/live_trading/test_persistence.py`
- Kill switch: `tests/live_trading/test_kill_switch.py`
- Telegram: `tests/live_trading/test_telegram.py`
- Total: ~174 unit tests

**API Integration Tests (require cached parquet data):**
- Core API: `tests/test_api.py` (526 lines)
- Backtest API: `tests/test_backtest_api.py`
- Research API: `tests/test_research_api.py` (198 lines)
- Optimization API: `tests/test_optimization_api.py`
- Trading API: `tests/test_trading_api.py` (355 lines)
- These are excluded from the default test command

**System Integration Tests:**
- `tests/live_trading/test_integration.py` (561 lines) — end-to-end live trading flows
- `tests/live_trading/test_system_integration.py` (422 lines) — full system integration
- `tests/live_trading/test_live_engine.py` (372 lines) — engine cycle tests

**Frontend Tests:**
- No frontend test framework configured (no jest/vitest config)
- No test files in `frontend/`

## Async Testing

**Pattern — `@pytest.mark.asyncio` for async tests:**
```python
class TestTelegramNotifier:
    @pytest.mark.asyncio
    async def test_sends_message(self, notifier, mock_server):
        await notifier.send_message("test")
        assert mock_server.last_request is not None
```

**Async Fixtures — `@pytest_asyncio.fixture`:**
```python
@pytest_asyncio.fixture
async def persistence(tmp_path):
    db_path = tmp_path / "test.sqlite"
    pm = PersistenceManager(db_path)
    await pm.connect()
    yield pm
    await pm.close()
```

## Common Assertion Patterns

**Floating-Point Comparisons:**
```python
assert trade.hedge_ratio == pytest.approx(2.0)
assert trade.net_pnl == pytest.approx(expected_net_pnl)
```

**Exception Testing:**
```python
with pytest.raises(ValueError, match="fold_count must be >= 2"):
    run_walk_forward(...)

with pytest.raises(ValueError, match="Not enough data"):
    rolling_cointegration(...)
```

**API Response Assertions:**
```python
resp = client.get("/api/health")
assert resp.status_code == 200
data = resp.json()
assert data["status"] == "ok"
assert isinstance(data["pairs_cached"], int)
```

**Structural Assertions:**
```python
# Check all required fields present
for field in ("symbol", "base", "quote", "timeframe", "candles", "start", "end", "file_size_mb"):
    assert field in pair, f"Missing field: {field}"
```

**Result Type Assertions:**
```python
assert all(isinstance(r, OOSResult) for r in results)
```

## Coverage

**Requirements:** No enforced coverage threshold
**Tool:** pytest-cov is available but no coverage config in pyproject.toml

**View Coverage:**
```bash
uv run pytest tests/ --cov=src/statistical_arbitrage --cov=api --cov-report=html
```

## Test Data Dependencies

**Cached Parquet Data:**
- API integration tests require pre-cached OHLCV parquet files in `data/` directory
- Files follow pattern: `{SYMBOL}_{timeframe}.parquet` (e.g., `ETH-EUR_1h.parquet`)
- Unit tests generate synthetic data inline — no external data dependency
- This is why API tests are excluded from the default test command

**SQLite (tmp_path):**
- Live trading tests create ephemeral SQLite databases via pytest `tmp_path` fixture
- Automatically cleaned up after test completion

---

*Testing analysis: 2026-03-31*
