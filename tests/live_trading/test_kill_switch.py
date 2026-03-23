"""Kill switch tests — idempotent emergency stop that flattens live positions.

Tests the ``LiveTradingEngine.kill_session()`` method across all edge cases:
session with positions, no positions, already killed, already stopped, and
partial close-order failures.
"""

from __future__ import annotations

import pytest
import pytest_asyncio

import ccxt

from statistical_arbitrage.live_trading.engine import LiveTradingEngine
from statistical_arbitrage.live_trading.models import KillSwitchResult, OrderEvent
from statistical_arbitrage.live_trading.order_executor import MockOrderExecutor
from statistical_arbitrage.live_trading.risk_manager import RiskManager
from statistical_arbitrage.paper_trading.data_source import MockCandleDataSource
from statistical_arbitrage.paper_trading.models import (
    PaperPosition,
    SessionConfig,
    SessionStatus,
)
from statistical_arbitrage.paper_trading.persistence import PersistenceManager
from tests.live_trading.conftest import make_signal_candles


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_engine(
    persistence: PersistenceManager,
    mock_executor: MockOrderExecutor | None = None,
    risk_manager: RiskManager | None = None,
    candles: list | None = None,
) -> LiveTradingEngine:
    """Create a fully wired LiveTradingEngine for testing."""
    if candles is None:
        candles = make_signal_candles()
    data_source = MockCandleDataSource(candles)
    executor = mock_executor or MockOrderExecutor(
        default_fill_price=100.0, default_fee_rate=0.0025,
    )
    rm = risk_manager or RiskManager(
        max_position_size_eur=25.0,
        max_concurrent_positions=2,
        daily_loss_limit_eur=50.0,
        min_order_size_eur=5.0,
    )
    return LiveTradingEngine(
        data_source=data_source,
        persistence=persistence,
        order_executor=executor,
        risk_manager=rm,
    )


async def _create_session_with_position(
    engine: LiveTradingEngine,
    persistence: PersistenceManager,
    config: SessionConfig | None = None,
    direction: str = "long_spread",
) -> str:
    """Create a live session and manually insert an open position.

    Returns the session_id.
    """
    cfg = config or SessionConfig(
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
    session = await engine.create_session(cfg)
    sid = session.session_id

    # Insert an open position directly into persistence
    pos = PaperPosition(
        session_id=sid,
        symbol="BTC/EUR",
        direction=direction,
        quantity_asset1=0.01 if direction == "long_spread" else -0.01,
        quantity_asset2=-1.2 if direction == "long_spread" else 1.2,
        entry_price_asset1=100.0,
        entry_price_asset2=100.0,
        hedge_ratio=1.2,
        entry_fee=0.25,
        allocated_capital=500.0,
    )
    await persistence.save_position(pos)

    # Also set in-memory position state for consistency
    engine._session_positions[sid] = {
        "direction": direction,
        "quantity_asset1": pos.quantity_asset1,
        "quantity_asset2": pos.quantity_asset2,
        "entry_price_asset1": pos.entry_price_asset1,
        "entry_price_asset2": pos.entry_price_asset2,
        "is_live": True,
    }

    return sid


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestKillSwitchWithPositions:
    """Kill switch with open positions → closes them via market orders."""

    @pytest.mark.asyncio
    async def test_kill_one_long_position(self, persistence):
        """Kill session with 1 open long → sell order submitted, position closed, status killed."""
        engine = await _create_engine(persistence)
        sid = await _create_session_with_position(engine, persistence, direction="long_spread")

        result = await engine.kill_session(sid)

        assert result.success is True
        assert result.session_id == sid
        assert result.orders_submitted == 1
        assert result.orders_failed == 0
        assert result.positions_closed == 1
        assert result.errors == []

        # Verify: close order was a sell (closing a long)
        assert len(engine.order_executor.submitted_orders) == 1
        close_order = engine.order_executor.submitted_orders[0]
        assert close_order.side == "sell"
        assert close_order.symbol == "BTC/EUR"

        # Verify: session status is killed
        session = await persistence.get_session(sid)
        assert session.status == SessionStatus.killed

        # Verify: position removed from persistence
        positions = await persistence.get_positions(sid)
        assert len(positions) == 0

        # Verify: OrderEvent emitted
        order_events = [e for e in engine.events if isinstance(e, OrderEvent)]
        assert len(order_events) == 1
        assert "killed" in order_events[0].position_after

    @pytest.mark.asyncio
    async def test_kill_two_positions_long_and_short(self, persistence):
        """Kill session with 2 positions → both close orders submitted."""
        engine = await _create_engine(persistence)
        cfg = SessionConfig(
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
        session = await engine.create_session(cfg)
        sid = session.session_id

        # Insert two positions with different symbols
        pos_long = PaperPosition(
            session_id=sid,
            symbol="BTC/EUR",
            direction="long_spread",
            quantity_asset1=0.01,
            quantity_asset2=-1.2,
            entry_price_asset1=100.0,
            entry_price_asset2=100.0,
            hedge_ratio=1.2,
            entry_fee=0.25,
            allocated_capital=500.0,
        )
        pos_short = PaperPosition(
            session_id=sid,
            symbol="ETH/EUR",
            direction="short_spread",
            quantity_asset1=-0.5,
            quantity_asset2=0.6,
            entry_price_asset1=50.0,
            entry_price_asset2=50.0,
            hedge_ratio=1.2,
            entry_fee=0.12,
            allocated_capital=250.0,
        )
        await persistence.save_position(pos_long)
        await persistence.save_position(pos_short)

        result = await engine.kill_session(sid)

        assert result.success is True
        assert result.orders_submitted == 2
        assert result.positions_closed == 2
        assert result.orders_failed == 0

        # Verify both orders: sell for long, buy for short
        orders = engine.order_executor.submitted_orders
        assert len(orders) == 2
        sides = {o.side for o in orders}
        assert sides == {"sell", "buy"}

        # Verify all positions cleared
        positions = await persistence.get_positions(sid)
        assert len(positions) == 0

        # Session is killed
        session = await persistence.get_session(sid)
        assert session.status == SessionStatus.killed


class TestKillSwitchEdgeCases:
    """Edge cases: no positions, already killed, already stopped."""

    @pytest.mark.asyncio
    async def test_kill_no_positions(self, persistence):
        """Kill session with no open positions → success, no orders, status killed."""
        engine = await _create_engine(persistence)
        cfg = SessionConfig(
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
        session = await engine.create_session(cfg)
        sid = session.session_id

        result = await engine.kill_session(sid)

        assert result.success is True
        assert result.orders_submitted == 0
        assert result.orders_failed == 0
        assert result.positions_closed == 0

        session = await persistence.get_session(sid)
        assert session.status == SessionStatus.killed

    @pytest.mark.asyncio
    async def test_kill_already_killed_is_idempotent(self, persistence):
        """Kill session that's already killed → success, no new orders."""
        engine = await _create_engine(persistence)
        sid = await _create_session_with_position(engine, persistence)

        # Kill once
        result1 = await engine.kill_session(sid)
        assert result1.success is True
        assert result1.orders_submitted == 1

        orders_before = len(engine.order_executor.submitted_orders)

        # Kill again — idempotent
        result2 = await engine.kill_session(sid)
        assert result2.success is True
        assert result2.orders_submitted == 0
        assert result2.orders_failed == 0

        # No new orders submitted
        assert len(engine.order_executor.submitted_orders) == orders_before

    @pytest.mark.asyncio
    async def test_kill_stopped_session_with_positions(self, persistence):
        """Kill a stopped session that has positions → positions flattened, status killed."""
        engine = await _create_engine(persistence)
        sid = await _create_session_with_position(engine, persistence)

        # Manually set session to stopped
        session = await persistence.get_session(sid)
        session.status = SessionStatus.stopped
        await persistence.save_session(session)

        result = await engine.kill_session(sid)

        assert result.success is True
        assert result.orders_submitted == 1
        assert result.positions_closed == 1

        session = await persistence.get_session(sid)
        assert session.status == SessionStatus.killed


class TestKillSwitchFailures:
    """Kill switch with partial order failures."""

    @pytest.mark.asyncio
    async def test_kill_with_close_order_failure(self, persistence):
        """Close order fails → partial kill reported, error in result."""
        # Use an executor that will fail on the first order
        executor = MockOrderExecutor(default_fill_price=100.0, default_fee_rate=0.0025)
        executor.error_on_next_order = ccxt.InsufficientFunds("Not enough BTC")

        engine = await _create_engine(persistence, mock_executor=executor)
        sid = await _create_session_with_position(engine, persistence)

        result = await engine.kill_session(sid)

        assert result.success is False
        assert result.orders_submitted == 0
        assert result.orders_failed == 1
        assert result.positions_closed == 0
        assert len(result.errors) == 1
        assert "InsufficientFunds" in result.errors[0]

        # Session status is still updated to killed even on partial failure
        session = await persistence.get_session(sid)
        assert session.status == SessionStatus.killed

    @pytest.mark.asyncio
    async def test_kill_result_has_correct_counts(self, persistence):
        """Verify KillSwitchResult fields have correct counts."""
        engine = await _create_engine(persistence)
        sid = await _create_session_with_position(engine, persistence)

        result = await engine.kill_session(sid)

        assert isinstance(result, KillSwitchResult)
        assert result.session_id == sid
        assert result.success is True
        assert result.orders_submitted == 1
        assert result.orders_failed == 0
        assert result.positions_closed == 1
        assert isinstance(result.errors, list)
        assert len(result.errors) == 0
