"""Tests for extended persistence — orders table CRUD, is_live column.

All tests use ``tmp_path`` fixture for SQLite databases (not ``:memory:``),
per KNOWLEDGE.md.
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from datetime import UTC, datetime

from statistical_arbitrage.live_trading.models import LiveOrder
from statistical_arbitrage.paper_trading.models import (
    PaperSession,
    SessionConfig,
    SessionStatus,
)
from statistical_arbitrage.paper_trading.persistence import PersistenceManager


@pytest_asyncio.fixture
async def pm(tmp_path):
    """PersistenceManager with tmp_path SQLite."""
    db_path = tmp_path / "test_persistence.sqlite"
    mgr = PersistenceManager(db_path)
    await mgr.connect()
    yield mgr
    await mgr.close()


def _make_session(
    session_id: str = "sess-1",
    is_live: bool = False,
    **overrides,
) -> PaperSession:
    """Factory for PaperSession with sensible defaults."""
    config = SessionConfig(
        asset1="BTC",
        asset2="EUR",
        is_live=is_live,
    )
    defaults = dict(
        session_id=session_id,
        config=config,
        status=SessionStatus.created,
        current_equity=10000.0,
        total_trades=0,
        is_live=is_live,
    )
    defaults.update(overrides)
    return PaperSession(**defaults)


def _make_order(
    order_id: str = "order-1",
    session_id: str = "sess-1",
    **overrides,
) -> LiveOrder:
    """Factory for LiveOrder with sensible defaults."""
    defaults = dict(
        order_id=order_id,
        session_id=session_id,
        side="buy",
        symbol="BTC/EUR",
        requested_amount=0.001,
        filled_amount=0.001,
        fill_price=50000.0,
        fee=0.125,
        status="filled",
        created_at=datetime.now(UTC),
        filled_at=datetime.now(UTC),
    )
    defaults.update(overrides)
    return LiveOrder(**defaults)


class TestIsLiveColumn:
    """Tests for the is_live column on sessions."""

    @pytest.mark.asyncio
    async def test_session_is_live_true_persists(self, pm):
        """Creating a session with is_live=True persists and loads correctly."""
        session = _make_session(session_id="live-1", is_live=True)
        await pm.save_session(session)

        loaded = await pm.get_session("live-1")
        assert loaded is not None
        assert loaded.is_live is True
        assert loaded.config.is_live is True

    @pytest.mark.asyncio
    async def test_session_is_live_false_default(self, pm):
        """Sessions default to is_live=False for backward compatibility."""
        session = _make_session(session_id="paper-1", is_live=False)
        await pm.save_session(session)

        loaded = await pm.get_session("paper-1")
        assert loaded is not None
        assert loaded.is_live is False

    @pytest.mark.asyncio
    async def test_is_live_survives_upsert(self, pm):
        """Updating a session preserves is_live via ON CONFLICT DO UPDATE."""
        session = _make_session(session_id="upsert-1", is_live=True)
        await pm.save_session(session)

        # Update session status
        session.status = SessionStatus.running
        session.updated_at = datetime.now(UTC)
        await pm.save_session(session)

        loaded = await pm.get_session("upsert-1")
        assert loaded is not None
        assert loaded.is_live is True
        assert loaded.status == SessionStatus.running


class TestOrdersCRUD:
    """Tests for the orders table CRUD operations."""

    @pytest.mark.asyncio
    async def test_save_and_load_order(self, pm):
        """Save an order and load it back by session_id."""
        # Create parent session first (FK constraint)
        session = _make_session(session_id="sess-1", is_live=True)
        await pm.save_session(session)

        order = _make_order(order_id="ord-1", session_id="sess-1")
        await pm.save_order(order)

        orders = await pm.get_orders("sess-1")
        assert len(orders) == 1
        assert orders[0].order_id == "ord-1"
        assert orders[0].session_id == "sess-1"
        assert orders[0].side == "buy"
        assert orders[0].symbol == "BTC/EUR"
        assert orders[0].fill_price == 50000.0
        assert orders[0].status == "filled"

    @pytest.mark.asyncio
    async def test_multiple_orders_per_session(self, pm):
        """Multiple orders for the same session load correctly."""
        session = _make_session(session_id="sess-2", is_live=True)
        await pm.save_session(session)

        for i in range(3):
            order = _make_order(
                order_id=f"ord-{i}",
                session_id="sess-2",
                side="buy" if i % 2 == 0 else "sell",
            )
            await pm.save_order(order)

        orders = await pm.get_orders("sess-2")
        assert len(orders) == 3

    @pytest.mark.asyncio
    async def test_update_order_status(self, pm):
        """Update an order's status and fill details."""
        session = _make_session(session_id="sess-3", is_live=True)
        await pm.save_session(session)

        order = _make_order(
            order_id="ord-update",
            session_id="sess-3",
            status="pending",
            filled_amount=0.0,
            fill_price=0.0,
        )
        await pm.save_order(order)

        # Update to filled
        await pm.update_order_status(
            order_id="ord-update",
            status="filled",
            filled_amount=0.001,
            fill_price=50100.0,
        )

        orders = await pm.get_orders("sess-3")
        assert len(orders) == 1
        assert orders[0].status == "filled"
        assert orders[0].filled_amount == 0.001
        assert orders[0].fill_price == 50100.0
        assert orders[0].filled_at is not None

    @pytest.mark.asyncio
    async def test_orders_empty_for_unknown_session(self, pm):
        """get_orders for a non-existent session returns empty list."""
        orders = await pm.get_orders("nonexistent")
        assert orders == []

    @pytest.mark.asyncio
    async def test_orders_cascade_delete_with_session(self, pm):
        """Orders are cascade-deleted when their parent session is deleted."""
        session = _make_session(session_id="sess-cascade", is_live=True)
        await pm.save_session(session)

        order = _make_order(order_id="ord-cascade", session_id="sess-cascade")
        await pm.save_order(order)

        # Verify order exists
        orders = await pm.get_orders("sess-cascade")
        assert len(orders) == 1

        # Delete session — should cascade to orders
        await pm.delete_session("sess-cascade")

        orders = await pm.get_orders("sess-cascade")
        assert len(orders) == 0

    @pytest.mark.asyncio
    async def test_order_upsert_on_conflict(self, pm):
        """Saving an order with same order_id updates instead of failing."""
        session = _make_session(session_id="sess-upsert", is_live=True)
        await pm.save_session(session)

        order = _make_order(
            order_id="ord-dup",
            session_id="sess-upsert",
            status="pending",
            fill_price=0.0,
        )
        await pm.save_order(order)

        # Save again with updated fields
        order.status = "filled"
        order.fill_price = 51000.0
        order.filled_at = datetime.now(UTC)
        await pm.save_order(order)

        orders = await pm.get_orders("sess-upsert")
        assert len(orders) == 1
        assert orders[0].status == "filled"
        assert orders[0].fill_price == 51000.0
