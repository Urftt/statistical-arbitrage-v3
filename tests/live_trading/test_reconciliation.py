"""Position reconciliation tests — verify local state vs exchange balances.

Tests the ``LiveTradingEngine.reconcile_positions()`` method and the
reconciliation gate in ``start_session()`` for live sessions.
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from statistical_arbitrage.live_trading.engine import LiveTradingEngine
from statistical_arbitrage.live_trading.models import ReconciliationResult
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
    balance: dict[str, dict[str, float]] | None = None,
) -> LiveTradingEngine:
    """Create a LiveTradingEngine with controllable exchange balance."""
    candles = make_signal_candles()
    data_source = MockCandleDataSource(candles)
    executor = MockOrderExecutor(
        default_fill_price=100.0,
        default_fee_rate=0.0025,
        balance=balance or {"EUR": {"free": 1000.0, "used": 0.0, "total": 1000.0}},
    )
    rm = RiskManager(
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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestReconcilePositions:
    """Reconcile local positions against exchange balances."""

    @pytest.mark.asyncio
    async def test_reconcile_matching_position(self, persistence):
        """Position matches exchange balance → matched=True."""
        balance = {
            "BTC": {"free": 0.01, "used": 0.0, "total": 0.01},
            "EUR": {"free": 500.0, "used": 0.0, "total": 500.0},
        }
        engine = await _create_engine(persistence, balance=balance)

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

        # Insert position matching the exchange balance
        pos = PaperPosition(
            session_id=sid,
            symbol="BTC/EUR",
            direction="long_spread",
            quantity_asset1=0.01,
            quantity_asset2=-1.2,
            entry_price_asset1=100.0,
            entry_price_asset2=100.0,
            hedge_ratio=1.2,
        )
        await persistence.save_position(pos)

        result = await engine.reconcile_positions(sid)

        assert result.matched is True
        assert len(result.discrepancies) == 0
        assert "BTC" in result.local_positions

    @pytest.mark.asyncio
    async def test_reconcile_mismatching_position(self, persistence):
        """Position doesn't match exchange balance → matched=False with discrepancies."""
        balance = {
            "BTC": {"free": 0.05, "used": 0.0, "total": 0.05},  # Much more than local
            "EUR": {"free": 500.0, "used": 0.0, "total": 500.0},
        }
        engine = await _create_engine(persistence, balance=balance)

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

        pos = PaperPosition(
            session_id=sid,
            symbol="BTC/EUR",
            direction="long_spread",
            quantity_asset1=0.01,
            quantity_asset2=-1.2,
            entry_price_asset1=100.0,
            entry_price_asset2=100.0,
            hedge_ratio=1.2,
        )
        await persistence.save_position(pos)

        result = await engine.reconcile_positions(sid)

        assert result.matched is False
        assert len(result.discrepancies) == 1
        assert "BTC" in result.discrepancies[0]

    @pytest.mark.asyncio
    async def test_reconcile_no_positions(self, persistence):
        """No positions → trivially matched."""
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

        result = await engine.reconcile_positions(sid)

        assert result.matched is True
        assert len(result.discrepancies) == 0
        assert result.local_positions == {}

    @pytest.mark.asyncio
    async def test_reconcile_within_tolerance(self, persistence):
        """Balance slightly off (within 1% tolerance) → matched=True."""
        # 0.01 BTC position, exchange has 0.01005 (0.5% off, within 1%)
        balance = {
            "BTC": {"free": 0.01005, "used": 0.0, "total": 0.01005},
            "EUR": {"free": 500.0, "used": 0.0, "total": 500.0},
        }
        engine = await _create_engine(persistence, balance=balance)

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

        pos = PaperPosition(
            session_id=sid,
            symbol="BTC/EUR",
            direction="long_spread",
            quantity_asset1=0.01,
            quantity_asset2=-1.2,
            entry_price_asset1=100.0,
            entry_price_asset2=100.0,
            hedge_ratio=1.2,
        )
        await persistence.save_position(pos)

        result = await engine.reconcile_positions(sid)

        assert result.matched is True
        assert len(result.discrepancies) == 0


class TestReconciliationBlocksStart:
    """Reconciliation mismatch blocks live session start."""

    @pytest.mark.asyncio
    async def test_start_live_session_with_mismatch_blocked(self, persistence):
        """Start live session with reconciliation mismatch → ValueError raised."""
        # Exchange has 0.05 BTC but local position is 0.01
        balance = {
            "BTC": {"free": 0.05, "used": 0.0, "total": 0.05},
            "EUR": {"free": 500.0, "used": 0.0, "total": 500.0},
        }
        engine = await _create_engine(persistence, balance=balance)

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

        # Insert mismatching position
        pos = PaperPosition(
            session_id=sid,
            symbol="BTC/EUR",
            direction="long_spread",
            quantity_asset1=0.01,
            quantity_asset2=-1.2,
            entry_price_asset1=100.0,
            entry_price_asset2=100.0,
            hedge_ratio=1.2,
        )
        await persistence.save_position(pos)

        with pytest.raises(ValueError, match="reconciliation failed"):
            await engine.start_session(sid)

        # Session should NOT be running
        session = await persistence.get_session(sid)
        assert session.status != SessionStatus.running
