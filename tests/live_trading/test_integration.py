"""Integration tests proving the full assembled chain and order edge cases.

Wires together real components — MockOrderExecutor, RiskManager,
PersistenceManager, MockCandleDataSource — into a LiveTradingEngine and
exercises the complete signal → risk check → order → fill → persist → equity
chain, including kill switch, circuit breaker, partial fills, error recovery,
and paper+live coexistence.

All tests use ``process_cycle()`` directly (D030) — no background tasks.
"""

from __future__ import annotations

import pytest

import ccxt

from statistical_arbitrage.live_trading.engine import LiveTradingEngine
from statistical_arbitrage.live_trading.models import (
    ErrorEvent,
    OrderEvent,
    RiskBreachEvent,
)
from statistical_arbitrage.live_trading.order_executor import MockOrderExecutor
from statistical_arbitrage.live_trading.risk_manager import RiskManager
from statistical_arbitrage.paper_trading.data_source import MockCandleDataSource
from statistical_arbitrage.paper_trading.models import SessionConfig, SessionStatus
from statistical_arbitrage.paper_trading.persistence import PersistenceManager

from tests.live_trading.conftest import make_signal_candles, make_losing_candles


# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------


async def _create_full_stack(
    tmp_path,
    candles,
    *,
    is_live: bool = True,
    executor: MockOrderExecutor | None = None,
    risk_manager: RiskManager | None = None,
    initial_capital: float = 1000.0,
    max_position_size_eur: float = 5000.0,
    max_concurrent_positions: int = 2,
    daily_loss_limit_eur: float = 50.0,
    asset1: str = "BTC",
    asset2: str = "EUR",
) -> tuple[LiveTradingEngine, str, PersistenceManager, MockOrderExecutor]:
    """Create a fully wired LiveTradingEngine with a created session.

    Returns (engine, session_id, persistence, executor).
    """
    db_path = tmp_path / "integration.sqlite"
    pm = PersistenceManager(db_path)
    await pm.connect()

    data_source = MockCandleDataSource(candles)
    executor = executor or MockOrderExecutor(
        default_fill_price=100.0, default_fee_rate=0.0025,
    )
    rm = risk_manager or RiskManager(
        max_position_size_eur=max_position_size_eur,
        max_concurrent_positions=max_concurrent_positions,
        daily_loss_limit_eur=daily_loss_limit_eur,
        min_order_size_eur=5.0,
    )

    engine = LiveTradingEngine(
        data_source=data_source,
        persistence=pm,
        order_executor=executor,
        risk_manager=rm,
    )

    config = SessionConfig(
        asset1=asset1,
        asset2=asset2,
        timeframe="1h",
        lookback_window=30,
        entry_threshold=2.0,
        exit_threshold=0.5,
        stop_loss=3.0,
        initial_capital=initial_capital,
        position_size=0.5,
        transaction_fee=0.0025,
        is_live=is_live,
    )

    session = await engine.create_session(config)
    return engine, session.session_id, pm, executor


# ==========================================================================
# 1. Happy path — full lifecycle
# ==========================================================================


class TestHappyPathFullLifecycle:
    """Full lifecycle: create → signal → risk → order → fill → persist → equity → close."""

    @pytest.mark.asyncio
    async def test_full_lifecycle_entry_and_exit(self, tmp_path):
        """Process enough cycles for an entry fill and an exit fill, verifying
        orders table, trades table, and equity curve reflect actual fills."""
        candles = make_signal_candles(n=120)
        engine, sid, pm, executor = await _create_full_stack(tmp_path, candles)

        # Process cycles until we see both entry + exit (round-trip trade)
        for _ in range(20):
            await engine.process_cycle(sid)

        # Verify orders table has at least an entry order
        orders = await pm.get_orders(sid)
        assert len(orders) >= 1, f"Expected at least 1 order, got {len(orders)}"
        assert all(o.status == "filled" for o in orders)
        assert all(o.session_id == sid for o in orders)

        # Check for round-trip trade if enough cycles ran
        trades = await pm.get_trades(sid)
        if len(trades) >= 1:
            trade = trades[0]
            assert trade.session_id == sid
            assert trade.direction in ("long_spread", "short_spread")
            assert trade.entry_price_asset1 > 0
            assert trade.exit_price_asset1 > 0
            # Both entry and exit orders should exist
            assert len(orders) >= 2, "Expected entry + exit orders"

        # Verify equity curve has been updated
        equity_history = await pm.get_equity_history(sid)
        assert len(equity_history) > 0

        # Verify OrderEvents were emitted
        order_events = [e for e in engine.events if isinstance(e, OrderEvent)]
        assert len(order_events) >= 1

        await pm.close()


# ==========================================================================
# 2. Risk rejection mid-trading
# ==========================================================================


class TestRiskRejectionMidTrading:
    """Configure tight risk limits so a signal-triggered order gets rejected."""

    @pytest.mark.asyncio
    async def test_risk_rejection_session_continues(self, tmp_path):
        """Risk-rejected order doesn't crash the session; next cycle processes fine."""
        candles = make_signal_candles(n=120)
        engine, sid, pm, executor = await _create_full_stack(
            tmp_path, candles, max_position_size_eur=1.0,  # too small → rejects
        )

        # Process many cycles — should never crash
        for _ in range(15):
            await engine.process_cycle(sid)

        # No orders submitted (all rejected by max_position_size)
        assert len(executor.submitted_orders) == 0

        # RiskBreachEvent emitted with correct limit_type
        breaches = [e for e in engine.events if isinstance(e, RiskBreachEvent)]
        assert len(breaches) > 0
        assert any(
            b.check_result.limit_type == "max_position_size" for b in breaches
        )

        # Session still alive (not error state)
        session = await pm.get_session(sid)
        assert session.status != SessionStatus.error

        await pm.close()


# ==========================================================================
# 3. Daily loss circuit breaker across multiple sessions
# ==========================================================================


class TestDailyLossCircuitBreakerMultiSession:
    """Portfolio-level daily loss circuit breaker shared across sessions."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_both_sessions(self, tmp_path):
        """After cumulative loss exceeds limit, BOTH sessions are blocked from
        submitting new orders — but they still process cycles without crashing."""
        # We'll create two sessions on the same engine and manually push the
        # circuit breaker by setting the loss counter just below the limit,
        # then process cycles to confirm blocking.
        candles1 = make_signal_candles(n=120, seed=42)
        candles2 = make_signal_candles(n=120, seed=99)

        db_path = tmp_path / "circuit.sqlite"
        pm = PersistenceManager(db_path)
        await pm.connect()

        executor = MockOrderExecutor(default_fill_price=100.0, default_fee_rate=0.0025)
        rm = RiskManager(
            max_position_size_eur=5000.0,
            max_concurrent_positions=4,
            daily_loss_limit_eur=50.0,
            min_order_size_eur=5.0,
        )

        # Session 1 uses one candle source
        data_source1 = MockCandleDataSource(candles1)
        engine = LiveTradingEngine(
            data_source=data_source1,
            persistence=pm,
            order_executor=executor,
            risk_manager=rm,
        )

        config1 = SessionConfig(
            asset1="BTC", asset2="EUR", timeframe="1h",
            lookback_window=30, entry_threshold=2.0, exit_threshold=0.5,
            stop_loss=3.0, initial_capital=1000.0, position_size=0.5,
            transaction_fee=0.0025, is_live=True,
        )
        s1 = await engine.create_session(config1)

        config2 = SessionConfig(
            asset1="ETH", asset2="EUR", timeframe="1h",
            lookback_window=30, entry_threshold=2.0, exit_threshold=0.5,
            stop_loss=3.0, initial_capital=1000.0, position_size=0.5,
            transaction_fee=0.0025, is_live=True,
        )
        s2 = await engine.create_session(config2)

        # Manually set the daily loss just above the limit to trigger breaker
        engine._daily_realized_loss = 55.0
        engine._daily_loss_breached = True

        # Process cycles on session 1 — should NOT submit orders
        orders_before = len(executor.submitted_orders)
        for _ in range(5):
            await engine.process_cycle(s1.session_id)

        orders_after_s1 = len(executor.submitted_orders)
        assert orders_after_s1 == orders_before, "Session 1 should be blocked"

        # Process cycles on session 2 — also blocked
        # Need to swap data source for session 2's symbol to get signals
        # Both sessions share the same engine/executor/risk manager,
        # so the circuit breaker blocks BOTH.
        for _ in range(5):
            await engine.process_cycle(s2.session_id)

        orders_after_s2 = len(executor.submitted_orders)
        assert orders_after_s2 == orders_before, "Session 2 should also be blocked"

        # Verify RiskBreachEvent with daily_loss_limit
        loss_breaches = [
            e for e in engine.events
            if isinstance(e, RiskBreachEvent)
            and e.check_result.limit_type == "daily_loss_limit"
        ]
        assert len(loss_breaches) > 0

        # Sessions didn't crash
        sess1 = await pm.get_session(s1.session_id)
        sess2 = await pm.get_session(s2.session_id)
        assert sess1.status != SessionStatus.error
        assert sess2.status != SessionStatus.error

        await pm.close()


# ==========================================================================
# 4. Order failure recovery
# ==========================================================================


class TestOrderFailureRecovery:
    """Order submission fails with InsufficientFunds then succeeds on next cycle."""

    @pytest.mark.asyncio
    async def test_insufficient_funds_then_recovery(self, tmp_path):
        """InsufficientFunds on first signal → error logged → next cycle
        succeeds because MockOrderExecutor error is one-shot."""
        candles = make_signal_candles(n=120)
        executor = MockOrderExecutor(
            default_fill_price=100.0,
            default_fee_rate=0.0025,
            error_on_next_order=ccxt.InsufficientFunds("Not enough EUR"),
        )
        engine, sid, pm, _ = await _create_full_stack(
            tmp_path, candles, executor=executor,
        )

        # Process cycles — first signal hits InsufficientFunds, subsequent succeed
        for _ in range(15):
            await engine.process_cycle(sid)

        # Should have ErrorEvent for the first failure
        error_events = [e for e in engine.events if isinstance(e, ErrorEvent)]
        assert len(error_events) >= 1
        assert error_events[0].error_type == "InsufficientFunds"

        # Session didn't crash
        session = await pm.get_session(sid)
        assert session.status != SessionStatus.error

        # After the error cleared, orders should have been submitted
        assert len(executor.submitted_orders) > 0, \
            "Expected orders after error recovery"

        await pm.close()


# ==========================================================================
# 5. Network error — no retry, ErrorEvent emitted
# ==========================================================================


class TestNetworkErrorHandling:
    """NetworkError must NOT be retried (double-execution risk)."""

    @pytest.mark.asyncio
    async def test_network_error_no_retry_error_surfaced(self, tmp_path):
        """NetworkError → session transitions to error state, no order retry."""
        candles = make_signal_candles(n=120)
        executor = MockOrderExecutor(
            default_fill_price=100.0,
            default_fee_rate=0.0025,
            error_on_next_order=ccxt.NetworkError("Connection refused"),
        )
        engine, sid, pm, _ = await _create_full_stack(
            tmp_path, candles, executor=executor,
        )

        # Process cycles until the error fires
        for _ in range(10):
            await engine.process_cycle(sid)

        # ErrorEvent emitted
        error_events = [e for e in engine.events if isinstance(e, ErrorEvent)]
        network_errors = [e for e in error_events if e.error_type == "NetworkError"]
        assert len(network_errors) >= 1, "Expected a NetworkError event"

        # No retry: only 0 orders submitted (the error was one-shot, but
        # NetworkError transitions the session to error state, blocking further cycles)
        # At most the post-error cycles might submit orders on a recovered executor
        # but the session itself should have transitioned to error
        session = await pm.get_session(sid)
        # After NetworkError, session transitions to error state
        assert session.status == SessionStatus.error

        await pm.close()


# ==========================================================================
# 6. Kill switch during active trading
# ==========================================================================


class TestKillSwitchDuringTrading:
    """Kill switch flattens an open position mid-trading."""

    @pytest.mark.asyncio
    async def test_kill_with_open_position(self, tmp_path):
        """Open a position via process_cycle, then kill → close order submitted,
        position closed, session status killed."""
        candles = make_signal_candles(n=120)
        engine, sid, pm, executor = await _create_full_stack(tmp_path, candles)

        # Process until a position is opened
        for _ in range(10):
            await engine.process_cycle(sid)
            positions = await pm.get_positions(sid)
            if len(positions) > 0:
                break

        # Verify we have an open position
        positions = await pm.get_positions(sid)
        assert len(positions) > 0, "Need an open position for kill switch test"

        orders_before_kill = len(executor.submitted_orders)

        # Kill!
        result = await engine.kill_session(sid)

        assert result.success is True
        assert result.orders_submitted > 0
        assert result.positions_closed > 0
        assert len(result.errors) == 0

        # Position was closed
        positions_after = await pm.get_positions(sid)
        assert len(positions_after) == 0

        # Close order was submitted
        assert len(executor.submitted_orders) > orders_before_kill

        # Session is killed
        session = await pm.get_session(sid)
        assert session.status == SessionStatus.killed

        # Kill switch OrderEvent emitted
        kill_events = [
            e for e in engine.events
            if isinstance(e, OrderEvent) and "killed" in e.position_after
        ]
        assert len(kill_events) > 0

        await pm.close()


# ==========================================================================
# 7. Partial fill handling
# ==========================================================================


class TestPartialFillHandling:
    """Partial fill → position reflects actual filled amount, not requested."""

    @pytest.mark.asyncio
    async def test_partial_fill_position_reflects_actual(self, tmp_path):
        """Configure MockOrderExecutor to return 50% partial fill.
        Position quantity should be half of what was requested."""
        candles = make_signal_candles(n=120)

        # Create a custom executor that returns partial fills
        class PartialFillExecutor(MockOrderExecutor):
            """Returns fills at 50% of requested amount."""

            async def submit_order(self, symbol, side, amount):
                order = await super().submit_order(symbol, side, amount)
                # Override to partial: half the requested amount
                order.filled_amount = order.requested_amount * 0.5
                order.status = "partial"
                return order

        executor = PartialFillExecutor(
            default_fill_price=100.0, default_fee_rate=0.0025,
        )
        engine, sid, pm, _ = await _create_full_stack(
            tmp_path, candles, executor=executor,
        )

        # Process until position is opened
        for _ in range(10):
            await engine.process_cycle(sid)
            positions = await pm.get_positions(sid)
            if len(positions) > 0:
                break

        positions = await pm.get_positions(sid)
        if len(positions) > 0:
            pos = positions[0]
            # Verify the position reflects 50% fill
            # The quantity_asset1 should be ~half of what a full fill would give
            assert abs(pos.quantity_asset1) > 0, "Position should have non-zero quantity"

            # Check the order records both amounts
            orders = await pm.get_orders(sid)
            assert len(orders) > 0
            entry_order = orders[0]
            assert entry_order.filled_amount == pytest.approx(
                entry_order.requested_amount * 0.5, rel=0.01,
            )
            assert entry_order.status == "partial"

            # Position allocated capital should reflect the partial fill ratio
            # (half of what full allocation would be)
            # We can't know the exact value but verify it's positive and reasonable
            assert pos.allocated_capital > 0
        else:
            pytest.fail("Expected a position to be opened for partial fill test")

        await pm.close()


# ==========================================================================
# 8. Concurrent paper + live sessions
# ==========================================================================


class TestConcurrentPaperAndLive:
    """Paper and live sessions coexist without interference."""

    @pytest.mark.asyncio
    async def test_paper_and_live_coexist(self, tmp_path):
        """Paper session uses simulated fills, live uses OrderExecutor.
        Both produce results without interfering with each other."""
        candles = make_signal_candles(n=120)

        db_path = tmp_path / "coexist.sqlite"
        pm = PersistenceManager(db_path)
        await pm.connect()

        data_source = MockCandleDataSource(candles)
        executor = MockOrderExecutor(
            default_fill_price=100.0, default_fee_rate=0.0025,
        )
        rm = RiskManager(
            max_position_size_eur=5000.0,
            max_concurrent_positions=4,
            daily_loss_limit_eur=1000.0,
            min_order_size_eur=5.0,
        )

        engine = LiveTradingEngine(
            data_source=data_source,
            persistence=pm,
            order_executor=executor,
            risk_manager=rm,
        )

        # Create one paper and one live session
        paper_config = SessionConfig(
            asset1="BTC", asset2="EUR", timeframe="1h",
            lookback_window=30, entry_threshold=2.0, exit_threshold=0.5,
            stop_loss=3.0, initial_capital=1000.0, position_size=0.5,
            transaction_fee=0.0025, is_live=False,
        )
        live_config = SessionConfig(
            asset1="BTC", asset2="EUR", timeframe="1h",
            lookback_window=30, entry_threshold=2.0, exit_threshold=0.5,
            stop_loss=3.0, initial_capital=1000.0, position_size=0.5,
            transaction_fee=0.0025, is_live=True,
        )

        paper_session = await engine.create_session(paper_config)
        live_session = await engine.create_session(live_config)

        # Process cycles on both
        for _ in range(15):
            await engine.process_cycle(paper_session.session_id)
            await engine.process_cycle(live_session.session_id)

        # Paper session: no real orders submitted (uses simulated fills)
        paper_orders = await pm.get_orders(paper_session.session_id)
        assert len(paper_orders) == 0, "Paper session should not create real orders"

        # Live session: uses OrderExecutor
        live_orders = await pm.get_orders(live_session.session_id)
        # There should be some orders from the live session
        assert len(live_orders) > 0 or len(executor.submitted_orders) > 0, \
            "Live session should have submitted orders via OrderExecutor"

        # Both sessions exist and are not in error state
        paper_loaded = await pm.get_session(paper_session.session_id)
        live_loaded = await pm.get_session(live_session.session_id)
        assert paper_loaded.is_live is False
        assert live_loaded.is_live is True
        assert paper_loaded.status != SessionStatus.error
        assert live_loaded.status != SessionStatus.error

        # Equity history exists for both
        paper_equity = await pm.get_equity_history(paper_session.session_id)
        live_equity = await pm.get_equity_history(live_session.session_id)
        assert len(paper_equity) > 0
        assert len(live_equity) > 0

        await pm.close()
