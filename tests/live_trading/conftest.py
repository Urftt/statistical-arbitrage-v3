"""Shared fixtures for live trading tests.

Provides:
- ``persistence_factory``: Creates a PersistenceManager with tmp_path SQLite.
- ``live_engine_factory``: Creates a LiveTradingEngine with all mock components.
- ``make_candles_*``: Deterministic candle sequences that generate known signals.
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from statistical_arbitrage.live_trading.engine import LiveTradingEngine
from statistical_arbitrage.live_trading.order_executor import MockOrderExecutor
from statistical_arbitrage.live_trading.risk_manager import RiskManager
from statistical_arbitrage.paper_trading.data_source import MockCandleDataSource
from statistical_arbitrage.paper_trading.models import SessionConfig
from statistical_arbitrage.paper_trading.persistence import PersistenceManager


def make_signal_candles(
    n: int = 120,
    base_price: float = 100.0,
    seed: int = 42,
) -> list[list[float | int]]:
    """Generate candles that produce z-score entry/exit signals.

    Uses two correlated random-walk price series with structural spread
    shocks that create z-score spikes exceeding ±2.0. This pattern
    reliably produces 5-9 signal events with the default strategy params
    (lookback=30, entry=2.0, exit=0.5).

    Each candle is [timestamp, open, high, low, close, volume].
    - open → used as asset2 price by the engine
    - close → used as asset1 price by the engine
    """
    import numpy as np

    rng = np.random.RandomState(seed)
    # Asset2: random walk
    asset2_returns = rng.randn(n) * 0.5
    asset2_prices = np.cumsum(asset2_returns) + base_price

    # Asset1: co-moves with asset2 via hedge ~1.2, with spread shocks
    noise = rng.randn(n) * 0.3
    hedge = 1.2
    spread_shock = np.zeros(n)
    for i in range(n):
        if 35 <= i <= 45:
            spread_shock[i] = 8.0   # positive spread shock
        if 65 <= i <= 75:
            spread_shock[i] = -8.0  # negative spread shock
        if 95 <= i <= 105:
            spread_shock[i] = 6.0   # another shock

    asset1_prices = hedge * asset2_prices + spread_shock + noise

    candles = []
    for i in range(n):
        ts = 1700000000000 + i * 3600000
        a2 = float(asset2_prices[i])
        a1 = float(asset1_prices[i])
        high = max(a1, a2) + 1
        low = min(a1, a2) - 1
        candles.append([ts, a2, high, low, a1, 1000.0])
    return candles


def make_losing_candles(
    n: int = 120,
    base_price: float = 100.0,
    seed: int = 99,
) -> list[list[float | int]]:
    """Generate candles that produce trades with losses.

    Creates spread shocks that trigger entries, then the spread continues
    in the same direction (against the mean-reversion bet) before hitting
    stop-loss, producing consistent losing trades.
    """
    import numpy as np

    rng = np.random.RandomState(seed)
    asset2_returns = rng.randn(n) * 0.5
    asset2_prices = np.cumsum(asset2_returns) + base_price

    noise = rng.randn(n) * 0.3
    hedge = 1.2
    # Create spread shocks that persist and grow (triggering stop-losses)
    spread_shock = np.zeros(n)
    for i in range(n):
        if 35 <= i <= 55:
            spread_shock[i] = 8.0 + 0.5 * (i - 35)  # growing positive shock → stop-loss
        if 70 <= i <= 90:
            spread_shock[i] = -8.0 - 0.5 * (i - 70)  # growing negative shock → stop-loss

    asset1_prices = hedge * asset2_prices + spread_shock + noise

    candles = []
    for i in range(n):
        ts = 1700000000000 + i * 3600000
        a2 = float(asset2_prices[i])
        a1 = float(asset1_prices[i])
        high = max(a1, a2) + 1
        low = min(a1, a2) - 1
        candles.append([ts, a2, high, low, a1, 1000.0])
    return candles


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


@pytest.fixture
def live_session_config():
    """Live session configuration for testing."""
    return SessionConfig(
        asset1="BTC",
        asset2="EUR",
        timeframe="1h",
        lookback_window=30,
        entry_threshold=2.0,
        exit_threshold=0.5,
        stop_loss=3.0,
        initial_capital=1000.0,
        position_size=0.5,
        transaction_fee=0.0025,
        is_live=True,
    )


@pytest.fixture
def paper_session_config():
    """Paper session configuration for testing."""
    return SessionConfig(
        asset1="BTC",
        asset2="EUR",
        timeframe="1h",
        lookback_window=30,
        entry_threshold=2.0,
        exit_threshold=0.5,
        stop_loss=3.0,
        initial_capital=1000.0,
        position_size=0.5,
        transaction_fee=0.0025,
        is_live=False,
    )
