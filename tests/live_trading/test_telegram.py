"""Tests for TelegramNotifier — message formatting, error handling, and no-op paths.

All tests mock ``httpx.AsyncClient.post`` at the instance level so no real
HTTP calls are made.  Uses ``@pytest.mark.asyncio`` for async test methods.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from statistical_arbitrage.live_trading.models import (
    ErrorEvent,
    LiveOrder,
    OrderEvent,
    RiskBreachEvent,
    RiskCheckResult,
)
from statistical_arbitrage.live_trading.telegram_notifier import TelegramNotifier

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
CHAT_ID = "-1001234567890"


@pytest.fixture
def notifier() -> TelegramNotifier:
    """Create a TelegramNotifier with mocked httpx client."""
    n = TelegramNotifier(bot_token=BOT_TOKEN, chat_id=CHAT_ID)
    # Replace the real httpx.AsyncClient with a mock
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_client.post.return_value = mock_response
    n._client = mock_client
    return n


@pytest.fixture
def sample_order_event() -> OrderEvent:
    """Sample OrderEvent for fill notifications."""
    order = LiveOrder(
        order_id="ord-001",
        session_id="sess-abc",
        side="buy",
        symbol="BTC-EUR",
        requested_amount=0.001,
        filled_amount=0.001,
        fill_price=45000.1234,
        fee=1.125,
        status="filled",
    )
    return OrderEvent(
        session_id="sess-abc",
        order=order,
        position_after="long BTC-EUR 0.001",
    )


@pytest.fixture
def sample_error_event() -> ErrorEvent:
    """Sample ErrorEvent for error notifications."""
    return ErrorEvent(
        session_id="sess-abc",
        error_type="InsufficientFunds",
        message="Not enough EUR balance to place order",
        timestamp=datetime(2025, 3, 15, 14, 30, 0, tzinfo=UTC),
    )


@pytest.fixture
def sample_risk_breach_event() -> RiskBreachEvent:
    """Sample RiskBreachEvent for risk breach notifications."""
    return RiskBreachEvent(
        session_id="sess-abc",
        check_result=RiskCheckResult(
            approved=False,
            reason="Order size €30.00 exceeds max €25.00",
            limit_type="max_position_size",
        ),
        order_details={"side": "buy", "amount_eur": 30.0, "symbol": "BTC-EUR"},
    )


@pytest.fixture
def sample_daily_summary() -> dict:
    """Sample daily summary dict."""
    return {
        "date": "2025-03-15",
        "total_pnl": 12.50,
        "trade_count": 8,
        "session_count": 3,
    }


# ---------------------------------------------------------------------------
# Message formatting tests
# ---------------------------------------------------------------------------


class TestMessageFormatting:
    @pytest.mark.asyncio
    async def test_send_fill_formats_correctly(
        self, notifier: TelegramNotifier, sample_order_event: OrderEvent
    ):
        await notifier.send_fill(sample_order_event)

        notifier._client.post.assert_called_once()
        call_kwargs = notifier._client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")

        assert payload["chat_id"] == CHAT_ID
        assert payload["parse_mode"] == "HTML"
        text = payload["text"]
        assert "Order Filled" in text
        assert "BTC-EUR" in text
        assert "buy" in text
        assert "45000.1234" in text
        assert "1.1250" in text
        assert "filled" in text
        assert "long BTC-EUR 0.001" in text
        assert "sess-abc" in text

    @pytest.mark.asyncio
    async def test_send_error_formats_correctly(
        self, notifier: TelegramNotifier, sample_error_event: ErrorEvent
    ):
        await notifier.send_error(sample_error_event)

        notifier._client.post.assert_called_once()
        call_kwargs = notifier._client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")

        text = payload["text"]
        assert "Trading Error" in text
        assert "InsufficientFunds" in text
        assert "Not enough EUR balance" in text
        assert "sess-abc" in text

    @pytest.mark.asyncio
    async def test_send_risk_breach_formats_correctly(
        self, notifier: TelegramNotifier, sample_risk_breach_event: RiskBreachEvent
    ):
        await notifier.send_risk_breach(sample_risk_breach_event)

        notifier._client.post.assert_called_once()
        call_kwargs = notifier._client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")

        text = payload["text"]
        assert "Risk Limit Breach" in text
        assert "max_position_size" in text
        assert "exceeds max" in text
        assert "sess-abc" in text

    @pytest.mark.asyncio
    async def test_send_daily_summary_formats_correctly(
        self, notifier: TelegramNotifier, sample_daily_summary: dict
    ):
        await notifier.send_daily_summary(sample_daily_summary)

        notifier._client.post.assert_called_once()
        call_kwargs = notifier._client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")

        text = payload["text"]
        assert "Daily Trading Summary" in text
        assert "2025-03-15" in text
        assert "12.50" in text
        assert "8" in text
        assert "3" in text


# ---------------------------------------------------------------------------
# API URL and payload structure
# ---------------------------------------------------------------------------


class TestAPIContract:
    @pytest.mark.asyncio
    async def test_send_uses_correct_api_url(
        self, notifier: TelegramNotifier, sample_order_event: OrderEvent
    ):
        await notifier.send_fill(sample_order_event)

        call_args = notifier._client.post.call_args
        url = call_args.args[0] if call_args.args else call_args[0][0]
        assert url == f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    @pytest.mark.asyncio
    async def test_all_messages_use_html_parse_mode(
        self,
        notifier: TelegramNotifier,
        sample_order_event: OrderEvent,
        sample_error_event: ErrorEvent,
        sample_risk_breach_event: RiskBreachEvent,
        sample_daily_summary: dict,
    ):
        """Every message type sets parse_mode=HTML."""
        await notifier.send_fill(sample_order_event)
        await notifier.send_error(sample_error_event)
        await notifier.send_risk_breach(sample_risk_breach_event)
        await notifier.send_daily_summary(sample_daily_summary)

        assert notifier._client.post.call_count == 4
        for call in notifier._client.post.call_args_list:
            payload = call.kwargs.get("json") or call[1].get("json")
            assert payload["parse_mode"] == "HTML"


# ---------------------------------------------------------------------------
# Error handling — failures must be caught, never raised
# ---------------------------------------------------------------------------


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_connection_error_caught_and_logged(
        self, notifier: TelegramNotifier, sample_order_event: OrderEvent
    ):
        notifier._client.post = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        # Must not raise
        await notifier.send_fill(sample_order_event)

    @pytest.mark.asyncio
    async def test_http_error_caught_and_logged(
        self, notifier: TelegramNotifier, sample_order_event: OrderEvent
    ):
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_response
        )
        notifier._client.post = AsyncMock(return_value=mock_response)
        # Must not raise
        await notifier.send_fill(sample_order_event)

    @pytest.mark.asyncio
    async def test_timeout_caught_and_logged(
        self, notifier: TelegramNotifier, sample_order_event: OrderEvent
    ):
        notifier._client.post = AsyncMock(
            side_effect=httpx.TimeoutException("Request timed out")
        )
        # Must not raise
        await notifier.send_fill(sample_order_event)

    @pytest.mark.asyncio
    async def test_unexpected_exception_caught(
        self, notifier: TelegramNotifier, sample_order_event: OrderEvent
    ):
        notifier._client.post = AsyncMock(
            side_effect=RuntimeError("Something unexpected")
        )
        # Must not raise
        await notifier.send_fill(sample_order_event)


# ---------------------------------------------------------------------------
# Disabled / no-op behaviour
# ---------------------------------------------------------------------------


class TestDisabledNotifier:
    @pytest.mark.asyncio
    async def test_empty_token_is_noop(self, sample_order_event: OrderEvent):
        notifier = TelegramNotifier(bot_token="", chat_id=CHAT_ID)
        notifier._client = AsyncMock(spec=httpx.AsyncClient)
        await notifier.send_fill(sample_order_event)
        notifier._client.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_chat_id_is_noop(self, sample_order_event: OrderEvent):
        notifier = TelegramNotifier(bot_token=BOT_TOKEN, chat_id="")
        notifier._client = AsyncMock(spec=httpx.AsyncClient)
        await notifier.send_fill(sample_order_event)
        notifier._client.post.assert_not_called()


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


class TestLifecycle:
    @pytest.mark.asyncio
    async def test_close_closes_client(self):
        notifier = TelegramNotifier(bot_token=BOT_TOKEN, chat_id=CHAT_ID)
        notifier._client = AsyncMock(spec=httpx.AsyncClient)
        await notifier.close()
        notifier._client.aclose.assert_awaited_once()


# ---------------------------------------------------------------------------
# Engine ↔ Notifier integration tests
# ---------------------------------------------------------------------------


class TestTelegramEngineIntegration:
    """Integration tests proving the engine dispatches notifications correctly.

    Uses the ``_create_full_stack`` pattern from ``test_integration.py`` but
    injects a mock notifier.  After ``process_cycle()``, each test calls
    ``await asyncio.sleep(0)`` to drain the ``create_task`` callbacks.
    """

    @staticmethod
    async def _create_notified_engine(
        tmp_path,
        candles,
        *,
        notifier=None,
        executor=None,
        max_position_size_eur: float = 5000.0,
    ):
        """Create a fully-wired LiveTradingEngine with an optional notifier."""
        from statistical_arbitrage.live_trading.engine import LiveTradingEngine
        from statistical_arbitrage.live_trading.order_executor import MockOrderExecutor
        from statistical_arbitrage.live_trading.risk_manager import RiskManager
        from statistical_arbitrage.paper_trading.data_source import MockCandleDataSource
        from statistical_arbitrage.paper_trading.models import SessionConfig
        from statistical_arbitrage.paper_trading.persistence import PersistenceManager

        db_path = tmp_path / "telegram_int.sqlite"
        pm = PersistenceManager(db_path)
        await pm.connect()

        data_source = MockCandleDataSource(candles)
        executor = executor or MockOrderExecutor(
            default_fill_price=100.0, default_fee_rate=0.0025,
        )
        rm = RiskManager(
            max_position_size_eur=max_position_size_eur,
            max_concurrent_positions=2,
            daily_loss_limit_eur=50.0,
            min_order_size_eur=5.0,
        )

        engine = LiveTradingEngine(
            data_source=data_source,
            persistence=pm,
            order_executor=executor,
            risk_manager=rm,
            notifier=notifier,
        )

        config = SessionConfig(
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
        session = await engine.create_session(config)
        return engine, session.session_id, pm, executor

    @pytest.mark.asyncio
    async def test_engine_fill_triggers_send_fill(self, tmp_path):
        """An entry fill dispatches notifier.send_fill with the OrderEvent."""
        import asyncio
        from tests.live_trading.conftest import make_signal_candles

        mock_notifier = AsyncMock()
        candles = make_signal_candles(n=120)
        engine, sid, pm, _ = await self._create_notified_engine(
            tmp_path, candles, notifier=mock_notifier,
        )

        # Process cycles until a fill occurs
        for _ in range(15):
            await engine.process_cycle(sid)
            await asyncio.sleep(0)  # drain create_task callbacks

        # Should have at least one OrderEvent → send_fill called
        order_events = [e for e in engine.events if isinstance(e, OrderEvent)]
        assert len(order_events) >= 1, "Expected at least one OrderEvent"
        assert mock_notifier.send_fill.await_count >= 1
        # Verify the argument is an OrderEvent
        first_call = mock_notifier.send_fill.await_args_list[0]
        assert isinstance(first_call.args[0], OrderEvent)

        await pm.close()

    @pytest.mark.asyncio
    async def test_engine_error_triggers_send_error(self, tmp_path):
        """An order error dispatches notifier.send_error."""
        import asyncio
        import ccxt
        from tests.live_trading.conftest import make_signal_candles
        from statistical_arbitrage.live_trading.order_executor import MockOrderExecutor

        mock_notifier = AsyncMock()
        candles = make_signal_candles(n=120)
        executor = MockOrderExecutor(
            default_fill_price=100.0,
            default_fee_rate=0.0025,
            error_on_next_order=ccxt.InsufficientFunds("Not enough EUR"),
        )
        engine, sid, pm, _ = await self._create_notified_engine(
            tmp_path, candles, notifier=mock_notifier, executor=executor,
        )

        for _ in range(10):
            await engine.process_cycle(sid)
            await asyncio.sleep(0)

        error_events = [e for e in engine.events if isinstance(e, ErrorEvent)]
        assert len(error_events) >= 1
        assert mock_notifier.send_error.await_count >= 1
        first_call = mock_notifier.send_error.await_args_list[0]
        assert isinstance(first_call.args[0], ErrorEvent)

        await pm.close()

    @pytest.mark.asyncio
    async def test_engine_risk_breach_triggers_send_risk_breach(self, tmp_path):
        """A risk rejection dispatches notifier.send_risk_breach."""
        import asyncio
        from tests.live_trading.conftest import make_signal_candles

        mock_notifier = AsyncMock()
        candles = make_signal_candles(n=120)
        engine, sid, pm, _ = await self._create_notified_engine(
            tmp_path, candles, notifier=mock_notifier,
            max_position_size_eur=1.0,  # too small → all orders rejected
        )

        for _ in range(10):
            await engine.process_cycle(sid)
            await asyncio.sleep(0)

        breach_events = [e for e in engine.events if isinstance(e, RiskBreachEvent)]
        assert len(breach_events) >= 1
        assert mock_notifier.send_risk_breach.await_count >= 1
        first_call = mock_notifier.send_risk_breach.await_args_list[0]
        assert isinstance(first_call.args[0], RiskBreachEvent)

        await pm.close()

    @pytest.mark.asyncio
    async def test_engine_without_notifier_works(self, tmp_path):
        """Engine with notifier=None processes fills without error (backward compat)."""
        import asyncio
        from tests.live_trading.conftest import make_signal_candles

        candles = make_signal_candles(n=120)
        engine, sid, pm, _ = await self._create_notified_engine(
            tmp_path, candles, notifier=None,
        )

        # Should not raise — notifier is None, dispatch is guarded
        for _ in range(15):
            await engine.process_cycle(sid)
            await asyncio.sleep(0)

        order_events = [e for e in engine.events if isinstance(e, OrderEvent)]
        assert len(order_events) >= 1, "Fills should still occur without notifier"

        await pm.close()

    @pytest.mark.asyncio
    async def test_notifier_exception_does_not_crash_engine(self, tmp_path):
        """If notifier.send_fill raises, the engine still processes fills."""
        import asyncio
        from tests.live_trading.conftest import make_signal_candles

        mock_notifier = AsyncMock()
        mock_notifier.send_fill.side_effect = RuntimeError("Telegram API down")
        mock_notifier.send_error.side_effect = RuntimeError("Telegram API down")
        mock_notifier.send_risk_breach.side_effect = RuntimeError("Telegram API down")

        candles = make_signal_candles(n=120)
        engine, sid, pm, executor = await self._create_notified_engine(
            tmp_path, candles, notifier=mock_notifier,
        )

        # Should not crash despite the notifier raising on every call
        for _ in range(15):
            await engine.process_cycle(sid)
            await asyncio.sleep(0)

        # Engine still processed events
        order_events = [e for e in engine.events if isinstance(e, OrderEvent)]
        assert len(order_events) >= 1, "Engine should process fills even if notifier fails"

        # Orders were still submitted
        assert len(executor.submitted_orders) > 0

        await pm.close()
