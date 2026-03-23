"""Tests for OrderExecutor protocol, MockOrderExecutor, and BitvavoOrderExecutor."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import ccxt
import pytest
import pytest_asyncio  # noqa: F401 — ensures asyncio mode is available

from statistical_arbitrage.live_trading.models import LiveOrder
from statistical_arbitrage.live_trading.order_executor import (
    BitvavoOrderExecutor,
    MockOrderExecutor,
    OrderExecutor,
    round_to_significant_figures,
)


# ---------------------------------------------------------------------------
# round_to_significant_figures
# ---------------------------------------------------------------------------


class TestRoundToSignificantFigures:
    def test_small_number(self):
        assert round_to_significant_figures(0.00123456, 5) == pytest.approx(0.0012346)

    def test_large_number(self):
        assert round_to_significant_figures(12345.6, 5) == pytest.approx(12346.0)

    def test_zero(self):
        assert round_to_significant_figures(0.0, 5) == 0.0

    def test_exact_digits(self):
        assert round_to_significant_figures(1.2345, 5) == pytest.approx(1.2345)

    def test_single_sig_fig(self):
        assert round_to_significant_figures(0.009876, 3) == pytest.approx(0.00988)


# ---------------------------------------------------------------------------
# MockOrderExecutor
# ---------------------------------------------------------------------------


class TestMockOrderExecutor:
    @pytest.mark.asyncio
    async def test_returns_configurable_fill(self):
        executor = MockOrderExecutor(default_fill_price=50000.0)
        order = await executor.submit_order("BTC/EUR", "buy", 0.001)

        assert order.fill_price == 50000.0
        assert order.status == "filled"
        assert order.filled_amount == 0.001
        assert order.side == "buy"
        assert order.symbol == "BTC/EUR"

    @pytest.mark.asyncio
    async def test_records_submitted_orders(self):
        executor = MockOrderExecutor()
        await executor.submit_order("ETH/EUR", "buy", 1.0)
        await executor.submit_order("BTC/EUR", "sell", 0.5)

        assert len(executor.submitted_orders) == 2
        assert executor.submitted_orders[0].symbol == "ETH/EUR"
        assert executor.submitted_orders[1].symbol == "BTC/EUR"
        assert executor.submitted_orders[1].side == "sell"

    @pytest.mark.asyncio
    async def test_error_injection(self):
        executor = MockOrderExecutor(
            error_on_next_order=ccxt.InsufficientFunds("not enough EUR")
        )
        with pytest.raises(ccxt.InsufficientFunds, match="not enough EUR"):
            await executor.submit_order("BTC/EUR", "buy", 1.0)

        # Error is one-shot — next call succeeds
        order = await executor.submit_order("BTC/EUR", "buy", 1.0)
        assert order.status == "filled"

    @pytest.mark.asyncio
    async def test_fee_calculation(self):
        executor = MockOrderExecutor(
            default_fill_price=100.0, default_fee_rate=0.0025
        )
        order = await executor.submit_order("ETH/EUR", "buy", 2.0)
        # cost = 2.0 * 100.0 = 200.0, fee = 200.0 * 0.0025 = 0.5
        assert order.fee == pytest.approx(0.5)

    @pytest.mark.asyncio
    async def test_is_runtime_checkable_protocol(self):
        executor = MockOrderExecutor()
        assert isinstance(executor, OrderExecutor)

    @pytest.mark.asyncio
    async def test_close(self):
        executor = MockOrderExecutor()
        assert not executor._closed
        await executor.close()
        assert executor._closed


# ---------------------------------------------------------------------------
# BitvavoOrderExecutor — price extraction
# ---------------------------------------------------------------------------


class TestBitvavoOrderExecutorPriceExtraction:
    def test_average_present(self):
        raw = {"average": 45000.0, "cost": 90.0, "filled": 0.002}
        price = BitvavoOrderExecutor._extract_fill_price(raw)
        assert price == 45000.0

    def test_average_none_cost_filled_present(self):
        raw = {"average": None, "cost": 90.0, "filled": 0.002}
        price = BitvavoOrderExecutor._extract_fill_price(raw)
        assert price == pytest.approx(45000.0)

    def test_both_none(self):
        raw = {"average": None, "cost": None, "filled": None}
        price = BitvavoOrderExecutor._extract_fill_price(raw)
        assert price == 0.0

    def test_filled_zero_fallback(self):
        raw = {"average": None, "cost": 90.0, "filled": 0.0}
        price = BitvavoOrderExecutor._extract_fill_price(raw)
        assert price == 0.0


# ---------------------------------------------------------------------------
# BitvavoOrderExecutor — error classification
# ---------------------------------------------------------------------------


class TestBitvavoOrderExecutorErrors:
    @pytest.mark.asyncio
    async def test_insufficient_funds(self):
        executor = BitvavoOrderExecutor.__new__(BitvavoOrderExecutor)
        mock_exchange = AsyncMock()
        mock_exchange.create_market_order = AsyncMock(
            side_effect=ccxt.InsufficientFunds("balance too low")
        )
        executor._exchange = mock_exchange

        with pytest.raises(ccxt.InsufficientFunds, match="balance too low"):
            await executor.submit_order("BTC/EUR", "buy", 0.001)

    @pytest.mark.asyncio
    async def test_invalid_order(self):
        executor = BitvavoOrderExecutor.__new__(BitvavoOrderExecutor)
        mock_exchange = AsyncMock()
        mock_exchange.create_market_order = AsyncMock(
            side_effect=ccxt.InvalidOrder("below minimum")
        )
        executor._exchange = mock_exchange

        with pytest.raises(ccxt.InvalidOrder, match="below minimum"):
            await executor.submit_order("BTC/EUR", "buy", 0.0001)

    @pytest.mark.asyncio
    async def test_network_error(self):
        executor = BitvavoOrderExecutor.__new__(BitvavoOrderExecutor)
        mock_exchange = AsyncMock()
        mock_exchange.create_market_order = AsyncMock(
            side_effect=ccxt.NetworkError("timeout")
        )
        executor._exchange = mock_exchange

        with pytest.raises(ccxt.NetworkError, match="timeout"):
            await executor.submit_order("BTC/EUR", "buy", 0.001)

    @pytest.mark.asyncio
    async def test_exchange_not_available(self):
        executor = BitvavoOrderExecutor.__new__(BitvavoOrderExecutor)
        mock_exchange = AsyncMock()
        mock_exchange.create_market_order = AsyncMock(
            side_effect=ccxt.ExchangeNotAvailable("maintenance")
        )
        executor._exchange = mock_exchange

        with pytest.raises(ccxt.ExchangeNotAvailable, match="maintenance"):
            await executor.submit_order("BTC/EUR", "buy", 0.001)

    @pytest.mark.asyncio
    async def test_successful_order_extracts_fields(self):
        """Verify a successful CCXT response is correctly mapped to LiveOrder."""
        executor = BitvavoOrderExecutor.__new__(BitvavoOrderExecutor)
        mock_exchange = AsyncMock()
        mock_exchange.create_market_order = AsyncMock(
            return_value={
                "id": "order-abc-123",
                "average": 42000.0,
                "filled": 0.001,
                "cost": 42.0,
                "fee": {"cost": 0.105, "currency": "EUR"},
            }
        )
        executor._exchange = mock_exchange

        order = await executor.submit_order("BTC/EUR", "buy", 0.001)

        assert order.order_id == "order-abc-123"
        assert order.fill_price == 42000.0
        assert order.filled_amount == 0.001
        assert order.fee == pytest.approx(0.105)
        assert order.status == "filled"
