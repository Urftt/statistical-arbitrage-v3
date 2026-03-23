"""System integration tests — full assembled chain proving gaps between prior slices.

Prior coverage gaps addressed:
1. S01 integration tests wire MockOrderExecutor + RiskManager + PersistenceManager
   but never include TelegramNotifier.
2. S02 tests mock the notifier at the AsyncMock level, not through the real
   TelegramNotifier with mocked httpx transport.
3. No test exercises restart recovery for live sessions.
4. No test exercises reconciliation blocking start_session() at system level.
5. No test exercises circuit breaker + Telegram OR kill switch + Telegram at
   the assembled level.

All tests use the real ``TelegramNotifier`` with ``_client`` replaced by a mocked
``httpx.AsyncClient`` — proving the full dispatch path from engine → notifier →
httpx.post.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from statistical_arbitrage.live_trading.engine import LiveTradingEngine
from statistical_arbitrage.live_trading.models import (
    OrderEvent,
    RiskBreachEvent,
)
from statistical_arbitrage.live_trading.order_executor import MockOrderExecutor
from statistical_arbitrage.live_trading.risk_manager import RiskManager
from statistical_arbitrage.live_trading.telegram_notifier import TelegramNotifier
from statistical_arbitrage.paper_trading.data_source import MockCandleDataSource
from statistical_arbitrage.paper_trading.models import (
    PaperPosition,
    SessionConfig,
    SessionStatus,
)
from statistical_arbitrage.paper_trading.persistence import PersistenceManager

from tests.live_trading.conftest import make_losing_candles, make_signal_candles

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
CHAT_ID = "-1001234567890"


# ---------------------------------------------------------------------------
# Shared helper — full system stack with real TelegramNotifier
# ---------------------------------------------------------------------------


async def _create_system_stack(
    tmp_path,
    candles,
    *,
    executor: MockOrderExecutor | None = None,
    risk_manager: RiskManager | None = None,
    max_position_size_eur: float = 5000.0,
    daily_loss_limit_eur: float = 50.0,
    asset1: str = "BTC",
    asset2: str = "EUR",
    db_name: str = "system_int.sqlite",
) -> tuple[LiveTradingEngine, str, PersistenceManager, MockOrderExecutor, TelegramNotifier]:
    """Create the full component graph with a real TelegramNotifier.

    The notifier's ``_client`` is replaced by a mocked ``httpx.AsyncClient``
    whose ``.post`` returns a 200 response — same pattern as
    ``test_telegram.py`` fixtures but applied to the assembled system.

    Returns (engine, session_id, persistence, executor, notifier).
    """
    db_path = tmp_path / db_name
    pm = PersistenceManager(db_path)
    await pm.connect()

    data_source = MockCandleDataSource(candles)
    executor = executor or MockOrderExecutor(
        default_fill_price=100.0, default_fee_rate=0.0025,
    )
    rm = risk_manager or RiskManager(
        max_position_size_eur=max_position_size_eur,
        max_concurrent_positions=2,
        daily_loss_limit_eur=daily_loss_limit_eur,
        min_order_size_eur=5.0,
    )

    # Real TelegramNotifier with mocked httpx transport
    notifier = TelegramNotifier(bot_token=BOT_TOKEN, chat_id=CHAT_ID)
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_client.post.return_value = mock_response
    notifier._client = mock_client

    engine = LiveTradingEngine(
        data_source=data_source,
        persistence=pm,
        order_executor=executor,
        risk_manager=rm,
        notifier=notifier,
    )

    config = SessionConfig(
        asset1=asset1,
        asset2=asset2,
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

    session = await engine.create_session(config)
    return engine, session.session_id, pm, executor, notifier


# ==========================================================================
# 1. Full chain with real TelegramNotifier (mocked httpx)
# ==========================================================================


class TestFullChainWithTelegram:
    """Signal → risk → order → fill → TelegramNotifier._send() via mocked httpx."""

    @pytest.mark.asyncio
    async def test_fill_dispatches_telegram_via_httpx(self, tmp_path):
        """Process cycles until a fill occurs, then verify the real notifier
        called httpx.post with the correct Telegram API URL and payload."""
        candles = make_signal_candles(n=120)
        engine, sid, pm, executor, notifier = await _create_system_stack(
            tmp_path, candles,
        )

        try:
            for _ in range(15):
                await engine.process_cycle(sid)
                await asyncio.sleep(0)  # drain create_task notification callbacks

            # (a) engine.events contains an OrderEvent
            order_events = [e for e in engine.events if isinstance(e, OrderEvent)]
            assert len(order_events) >= 1, "Expected at least one OrderEvent"

            # (b) httpx mock .post was called
            assert notifier._client.post.call_count >= 1, (
                "Expected httpx.post to be called by TelegramNotifier"
            )

            # (c) POST URL contains the Telegram API base + bot token
            call_args = notifier._client.post.call_args_list[0]
            url = call_args.args[0] if call_args.args else call_args[0][0]
            assert f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage" == url

            # (d) Payload text contains "Order Filled" and the symbol
            payload = call_args.kwargs.get("json") or call_args[1].get("json")
            text = payload["text"]
            assert "Order Filled" in text
            assert "BTC" in text
        finally:
            await engine.stop_all()
            await pm.close()


# ==========================================================================
# 2. Restart recovery for live sessions
# ==========================================================================


class TestRestartRecovery:
    """Live sessions with status=running are resumed by recover_sessions()."""

    @pytest.mark.asyncio
    async def test_recover_sessions_resumes_running_live_session(self, tmp_path):
        """Create a live session, process a few cycles, simulate crash by
        leaving status=running in persistence, then create a NEW engine
        and call recover_sessions()."""
        candles = make_signal_candles(n=120)
        engine, sid, pm, executor, notifier = await _create_system_stack(
            tmp_path, candles, db_name="recovery.sqlite",
        )

        try:
            # Process a few cycles to build state
            for _ in range(5):
                await engine.process_cycle(sid)

            # Simulate crash: set session status to running in persistence
            session = await pm.get_session(sid)
            assert session is not None
            session.status = SessionStatus.running
            await pm.save_session(session)

            # Create a NEW engine with the SAME persistence (same db file)
            data_source2 = MockCandleDataSource(candles)
            executor2 = MockOrderExecutor(default_fill_price=100.0, default_fee_rate=0.0025)
            rm2 = RiskManager(
                max_position_size_eur=5000.0,
                max_concurrent_positions=2,
                daily_loss_limit_eur=50.0,
                min_order_size_eur=5.0,
            )
            notifier2 = TelegramNotifier(bot_token=BOT_TOKEN, chat_id=CHAT_ID)
            mock_client2 = AsyncMock(spec=httpx.AsyncClient)
            mock_response2 = MagicMock(spec=httpx.Response)
            mock_response2.status_code = 200
            mock_response2.raise_for_status = MagicMock()
            mock_client2.post.return_value = mock_response2
            notifier2._client = mock_client2

            engine2 = LiveTradingEngine(
                data_source=data_source2,
                persistence=pm,
                order_executor=executor2,
                risk_manager=rm2,
                notifier=notifier2,
            )

            # (a) recover_sessions() returns 1
            recovered = await engine2.recover_sessions()
            assert recovered == 1, f"Expected 1 recovered session, got {recovered}"

            # (b) the session's task is in engine2._tasks
            assert sid in engine2._tasks, "Recovered session should have a task"
            assert not engine2._tasks[sid].done(), "Task should be running"

            # Clean up the background task
            await engine2.stop_all()
        finally:
            await engine.stop_all()
            await pm.close()


# ==========================================================================
# 3. Reconciliation blocks start_session()
# ==========================================================================


class TestReconciliationBlocksStart:
    """start_session() raises ValueError when positions mismatch exchange balances."""

    @pytest.mark.asyncio
    async def test_start_session_raises_on_position_mismatch(self, tmp_path):
        """Create a live session, save a position with quantity_asset1=0.5,
        configure executor to return a balance with zero BTC, then assert
        start_session() raises ValueError with 'reconciliation failed'."""
        candles = make_signal_candles(n=120)

        # Configure executor with mismatched balance (zero BTC vs expected 0.5)
        executor = MockOrderExecutor(
            default_fill_price=100.0,
            default_fee_rate=0.0025,
            balance={"BTC": {"free": 0.0, "used": 0.0, "total": 0.0}},
        )

        engine, sid, pm, _, notifier = await _create_system_stack(
            tmp_path, candles, executor=executor,
        )

        try:
            # Manually save a PaperPosition to persistence with quantity_asset1=0.5
            position = PaperPosition(
                session_id=sid,
                symbol="BTC/EUR",
                direction="long_spread",
                quantity_asset1=0.5,
                quantity_asset2=-0.6,
                entry_price_asset1=100.0,
                entry_price_asset2=100.0,
                hedge_ratio=1.2,
                entry_fee=0.25,
                allocated_capital=50.0,
            )
            await pm.save_position(position)

            # Set session to "created" so start_session() will attempt to start
            session = await pm.get_session(sid)
            assert session is not None
            session.status = SessionStatus.created
            await pm.save_session(session)

            # start_session() should raise ValueError with "reconciliation failed"
            with pytest.raises(ValueError, match="reconciliation failed"):
                await engine.start_session(sid)
        finally:
            await engine.stop_all()
            await pm.close()


# ==========================================================================
# 4. Daily loss circuit breaker + Telegram notification
# ==========================================================================


class TestCircuitBreakerWithTelegram:
    """Daily loss circuit breaker triggers RiskBreachEvent AND Telegram notification."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_sends_telegram_notification(self, tmp_path):
        """Manually set the daily loss breaker, process cycles that generate
        a signal, and verify both the RiskBreachEvent and the httpx.post call
        with 'Risk Limit Breach' in the payload."""
        candles = make_signal_candles(n=120)
        engine, sid, pm, executor, notifier = await _create_system_stack(
            tmp_path, candles,
        )

        try:
            # Manually trigger the circuit breaker
            engine._daily_realized_loss = 55.0
            engine._daily_loss_breached = True

            # Process enough cycles for signals to fire (lookback=30 means
            # signals start around cycle 35+)
            for _ in range(15):
                await engine.process_cycle(sid)
                await asyncio.sleep(0)  # drain create_task notification callbacks

            # (a) engine.events contains a RiskBreachEvent with daily_loss_limit
            breach_events = [
                e for e in engine.events
                if isinstance(e, RiskBreachEvent)
                and e.check_result.limit_type == "daily_loss_limit"
            ]
            assert len(breach_events) > 0, (
                "Expected at least one RiskBreachEvent with limit_type=daily_loss_limit"
            )

            # (b) httpx .post was called with "Risk Limit Breach" in the text
            assert notifier._client.post.call_count >= 1, (
                "Expected httpx.post to be called for risk breach notification"
            )
            # Find the call containing the risk breach message
            found_breach_msg = False
            for call in notifier._client.post.call_args_list:
                payload = call.kwargs.get("json") or call[1].get("json")
                if payload and "Risk Limit Breach" in payload.get("text", ""):
                    found_breach_msg = True
                    break
            assert found_breach_msg, (
                "Expected httpx.post payload to contain 'Risk Limit Breach'"
            )
        finally:
            await engine.stop_all()
            await pm.close()


# ==========================================================================
# 5. Kill switch with open positions + Telegram
# ==========================================================================


class TestKillSwitchWithTelegram:
    """Kill switch closes positions AND dispatches Telegram notifications."""

    @pytest.mark.asyncio
    async def test_kill_closes_positions_and_notifies_telegram(self, tmp_path):
        """Process cycles until a position is opened, then kill the session.
        Verify: positions closed, status killed, httpx.post called with fill."""
        candles = make_signal_candles(n=120)
        engine, sid, pm, executor, notifier = await _create_system_stack(
            tmp_path, candles,
        )

        try:
            # Process until a position is opened
            for _ in range(15):
                await engine.process_cycle(sid)
                await asyncio.sleep(0)
                positions = await pm.get_positions(sid)
                if len(positions) > 0:
                    break

            # Verify we have an open position
            positions = await pm.get_positions(sid)
            assert len(positions) > 0, "Need an open position for kill switch test"

            # Reset mock call count to isolate kill-switch notifications
            notifier._client.post.reset_mock()

            # Kill the session
            result = await engine.kill_session(sid)
            await asyncio.sleep(0)  # drain notification callbacks

            # (a) kill result is successful with orders submitted and positions closed
            assert result.success is True
            assert result.orders_submitted > 0
            assert result.positions_closed > 0

            # (b) positions list is empty after kill
            positions_after = await pm.get_positions(sid)
            assert len(positions_after) == 0, "All positions should be closed"

            # (c) session status is killed
            session = await pm.get_session(sid)
            assert session is not None
            assert session.status == SessionStatus.killed

            # (d) httpx mock .post was called with "Order Filled" in the text
            assert notifier._client.post.call_count >= 1, (
                "Expected httpx.post to be called for close order fill notification"
            )
            found_fill_msg = False
            for call in notifier._client.post.call_args_list:
                payload = call.kwargs.get("json") or call[1].get("json")
                if payload and "Order Filled" in payload.get("text", ""):
                    found_fill_msg = True
                    break
            assert found_fill_msg, (
                "Expected httpx.post payload to contain 'Order Filled' for close order"
            )
        finally:
            await engine.stop_all()
            await pm.close()
