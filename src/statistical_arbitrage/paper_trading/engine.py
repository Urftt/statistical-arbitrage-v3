"""Async paper trading engine — session lifecycle and signal-driven fill accounting.

The ``PaperTradingEngine`` manages one or more concurrent paper trading sessions,
each running as an asyncio.Task that polls ``CandleDataSource`` for new candles,
generates z-score mean-reversion signals, and executes simulated fills.

Key design decisions:
- ``process_cycle()`` is the public, deterministic entry point for testing (D030).
- Fill accounting in ``_execute_fill()`` mirrors ``backtesting/engine.py`` exactly.
- The engine holds no web framework imports — it is standalone (D026).
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import numpy as np

from statistical_arbitrage.backtesting.models import StrategyParameters
from statistical_arbitrage.paper_trading.data_source import CandleDataSource
from statistical_arbitrage.paper_trading.models import (
    PaperEquityPoint,
    PaperPosition,
    PaperSession,
    PaperTrade,
    SessionConfig,
    SessionStatus,
)
from statistical_arbitrage.paper_trading.persistence import PersistenceManager
from statistical_arbitrage.strategy.zscore_mean_reversion import (
    build_rolling_strategy_data,
    generate_signal_events,
)

logger = logging.getLogger(__name__)


class PaperTradingEngine:
    """Async engine managing paper trading sessions.

    Each session polls a ``CandleDataSource`` for OHLCV data, generates
    z-score signals via the shared strategy code, and executes simulated
    fills with accounting that matches the backtester.

    Args:
        data_source: Injectable candle data provider.
        persistence: Async SQLite persistence layer.
    """

    def __init__(
        self,
        data_source: CandleDataSource,
        persistence: PersistenceManager,
    ) -> None:
        self.data_source = data_source
        self.persistence = persistence
        self._tasks: dict[str, asyncio.Task] = {}

        # Per-session accounting state (in-memory, not persisted)
        self._session_equity: dict[str, float] = {}
        self._session_trades: dict[str, int] = {}
        self._session_positions: dict[str, dict[str, Any]] = {}
        self._signal_counters: dict[str, int] = {}
        self._entry_zscores: dict[str, float] = {}

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    async def create_session(self, config: SessionConfig) -> PaperSession:
        """Create a new session and persist it.

        Args:
            config: User-supplied session configuration.

        Returns:
            The created session with status 'created'.
        """
        session = PaperSession(
            session_id=str(uuid.uuid4()),
            config=config,
            status=SessionStatus.created,
            current_equity=config.initial_capital,
            total_trades=0,
            is_live=config.is_live,
        )
        self._session_equity[session.session_id] = config.initial_capital
        self._session_trades[session.session_id] = 0
        self._signal_counters[session.session_id] = 0
        await self.persistence.save_session(session)
        logger.info(
            "Session created: session_id=%s, pair=%s-%s, is_live=%s",
            session.session_id,
            config.asset1,
            config.asset2,
            session.is_live,
        )
        return session

    async def start_session(self, session_id: str) -> None:
        """Start a session's polling loop as a background task."""
        session = await self.persistence.get_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")
        if session.status == SessionStatus.running:
            raise ValueError(f"Session {session_id} is already running")

        session.status = SessionStatus.running
        session.updated_at = datetime.now(UTC)
        await self.persistence.save_session(session)

        task = asyncio.create_task(self._run_session_loop(session_id))
        self._tasks[session_id] = task
        logger.info("Session started: session_id=%s", session_id)

    async def stop_session(self, session_id: str) -> None:
        """Stop a session's polling loop."""
        task = self._tasks.pop(session_id, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        session = await self.persistence.get_session(session_id)
        if session:
            session.status = SessionStatus.stopped
            session.updated_at = datetime.now(UTC)
            await self.persistence.save_session(session)
        logger.info("Session stopped: session_id=%s", session_id)

    async def stop_all(self) -> None:
        """Stop all running sessions."""
        session_ids = list(self._tasks.keys())
        for sid in session_ids:
            await self.stop_session(sid)

    async def get_session_status(self, session_id: str) -> PaperSession | None:
        """Load current session state from persistence."""
        return await self.persistence.get_session(session_id)

    async def get_all_sessions(self) -> list[PaperSession]:
        """Load all sessions from persistence."""
        return await self.persistence.get_all_sessions()

    async def recover_sessions(self) -> int:
        """Resume sessions that were 'running' when the engine last stopped.

        Returns:
            Number of sessions recovered.
        """
        active = await self.persistence.get_active_sessions()
        count = 0
        for session in active:
            if session.session_id not in self._tasks:
                self._session_equity[session.session_id] = session.current_equity
                self._session_trades[session.session_id] = session.total_trades
                self._signal_counters[session.session_id] = 0
                task = asyncio.create_task(
                    self._run_session_loop(session.session_id)
                )
                self._tasks[session.session_id] = task
                count += 1
        if count:
            logger.info("Sessions recovered: count=%d", count)
        return count

    # ------------------------------------------------------------------
    # Core processing
    # ------------------------------------------------------------------

    async def process_cycle(self, session_id: str) -> int:
        """Run one fetch→signal→fill→persist cycle for a session.

        This is the public, deterministic entry point for testing (D030).

        Args:
            session_id: Session to process.

        Returns:
            Number of signals processed in this cycle.
        """
        session = await self.persistence.get_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        config = session.config
        params = config.to_strategy_parameters()
        symbol = f"{config.asset1}/{config.asset2}"

        # Fetch candles
        candles = await self.data_source.fetch_ohlcv(
            symbol=symbol, timeframe=config.timeframe
        )

        if len(candles) < params.lookback_window:
            return 0

        # Extract prices
        timestamps = [c[0] for c in candles]
        asset1_prices = np.array([c[4] for c in candles], dtype=float)  # close
        # For pairs trading, we need asset2. We use asset1 close as both
        # for simplicity in the paper engine — the data source provides
        # a single symbol. In production, this would be two separate fetches.
        # For the mock/test scenario, we encode both prices in candle data.
        asset2_prices = np.array([c[1] for c in candles], dtype=float)  # open as asset2

        # Build strategy data
        strategy_data = build_rolling_strategy_data(
            asset1_prices, asset2_prices, params.lookback_window
        )

        # Generate signals
        signals, _ = generate_signal_events(
            zscore=strategy_data["zscore"],
            timestamps=[str(t) for t in timestamps],
            params=params,
            hedge_ratios=strategy_data["hedge_ratio"],
        )

        # Process only new signals since last cycle
        counter = self._signal_counters.get(session_id, 0)
        new_signals = signals[counter:]
        self._signal_counters[session_id] = len(signals)

        # Execute fills for new signals
        signals_processed = 0
        for signal in new_signals:
            exec_idx = signal.execution_index
            if exec_idx >= len(asset1_prices):
                continue

            price1 = float(asset1_prices[exec_idx])
            price2 = float(asset2_prices[exec_idx])
            timestamp = str(timestamps[exec_idx])

            await self._execute_fill(
                session=session,
                signal=signal,
                price1=price1,
                price2=price2,
                timestamp=timestamp,
                params=params,
            )
            signals_processed += 1

        # Update equity snapshot
        current_equity = self._session_equity.get(
            session_id, config.initial_capital
        )

        # Check for open position and compute unrealized PnL
        position = self._session_positions.get(session_id)
        if position and len(asset1_prices) > 0:
            price1 = float(asset1_prices[-1])
            price2 = float(asset2_prices[-1])
            unrealized = float(
                position["quantity_asset1"] * (price1 - position["entry_price_asset1"])
                + position["quantity_asset2"] * (price2 - position["entry_price_asset2"])
            )
            equity = position.get("entry_cash", current_equity) + unrealized
            pos_label = position["direction"]
        else:
            equity = current_equity
            unrealized = 0.0
            pos_label = "flat"

        if timestamps:
            await self.persistence.save_equity_point(
                PaperEquityPoint(
                    session_id=session_id,
                    timestamp=str(timestamps[-1]),
                    equity=equity,
                    cash=current_equity,
                    unrealized_pnl=unrealized,
                    position=pos_label,
                )
            )

        # Update session state
        session.current_equity = equity
        session.total_trades = self._session_trades.get(session_id, 0)
        session.updated_at = datetime.now(UTC)
        await self.persistence.save_session(session)

        return signals_processed

    async def _execute_fill(
        self,
        session: PaperSession,
        signal: Any,
        price1: float,
        price2: float,
        timestamp: str,
        params: StrategyParameters,
    ) -> None:
        """Execute a fill — simulated for paper, overridden for live.

        This method mirrors the backtesting engine's fill accounting exactly.
        LiveTradingEngine overrides this for real order submission.
        """
        session_id = session.session_id
        current_cash = self._session_equity.get(
            session_id, session.config.initial_capital
        )

        if signal.signal_type in ("long_entry", "short_entry"):
            # Entry fill — only if no open position
            if session_id in self._session_positions:
                return

            notional_denominator = price1 + abs(signal.hedge_ratio_at_signal) * price2
            if notional_denominator <= 0:
                return

            allocated_capital = current_cash * params.position_size
            scale = allocated_capital / notional_denominator

            if signal.direction == "long_spread":
                quantity_asset1 = scale
                quantity_asset2 = -scale * signal.hedge_ratio_at_signal
            else:
                quantity_asset1 = -scale
                quantity_asset2 = scale * signal.hedge_ratio_at_signal

            entry_notional = abs(quantity_asset1) * price1 + abs(quantity_asset2) * price2
            entry_fee = entry_notional * params.transaction_fee
            current_cash -= entry_fee
            self._session_equity[session_id] = current_cash

            symbol = f"{session.config.asset1}/{session.config.asset2}"

            position_data = {
                "direction": signal.direction,
                "entry_signal": signal,
                "entry_timestamp": timestamp,
                "entry_price_asset1": price1,
                "entry_price_asset2": price2,
                "entry_cash": current_cash,
                "entry_fee": entry_fee,
                "allocated_capital": allocated_capital,
                "quantity_asset1": quantity_asset1,
                "quantity_asset2": quantity_asset2,
                "hedge_ratio": signal.hedge_ratio_at_signal,
            }
            self._session_positions[session_id] = position_data
            self._entry_zscores[session_id] = signal.zscore_at_signal

            # Persist position
            await self.persistence.save_position(
                PaperPosition(
                    session_id=session_id,
                    symbol=symbol,
                    direction=signal.direction,
                    quantity_asset1=quantity_asset1,
                    quantity_asset2=quantity_asset2,
                    entry_price_asset1=price1,
                    entry_price_asset2=price2,
                    hedge_ratio=signal.hedge_ratio_at_signal,
                    entry_fee=entry_fee,
                    allocated_capital=allocated_capital,
                )
            )
            logger.info(
                "Fill executed: event=fill_executed, session_id=%s, signal=%s, price1=%.4f, price2=%.4f",
                session_id, signal.signal_type, price1, price2,
            )

        else:
            # Exit fill — close open position
            position = self._session_positions.get(session_id)
            if position is None:
                return

            exit_notional = (
                abs(position["quantity_asset1"]) * price1
                + abs(position["quantity_asset2"]) * price2
            )
            exit_fee = exit_notional * params.transaction_fee
            gross_pnl = float(
                position["quantity_asset1"] * (price1 - position["entry_price_asset1"])
                + position["quantity_asset2"] * (price2 - position["entry_price_asset2"])
            )
            net_pnl = gross_pnl - exit_fee
            current_cash += gross_pnl - exit_fee
            self._session_equity[session_id] = current_cash

            trade_count = self._session_trades.get(session_id, 0) + 1
            self._session_trades[session_id] = trade_count

            entry_signal = position["entry_signal"]

            trade = PaperTrade(
                session_id=session_id,
                trade_id=trade_count,
                direction=position["direction"],
                entry_timestamp=position["entry_timestamp"],
                exit_timestamp=timestamp,
                entry_reason=entry_signal.signal_type,
                exit_reason=signal.signal_type,
                bars_held=signal.execution_index - entry_signal.execution_index,
                entry_zscore=entry_signal.zscore_at_signal,
                exit_zscore=signal.zscore_at_signal,
                hedge_ratio=position["hedge_ratio"],
                quantity_asset1=position["quantity_asset1"],
                quantity_asset2=position["quantity_asset2"],
                entry_price_asset1=position["entry_price_asset1"],
                entry_price_asset2=position["entry_price_asset2"],
                exit_price_asset1=price1,
                exit_price_asset2=price2,
                allocated_capital=position["allocated_capital"],
                gross_pnl=gross_pnl,
                total_fees=position["entry_fee"] + exit_fee,
                net_pnl=net_pnl - position["entry_fee"],
                return_pct=(net_pnl - position["entry_fee"]) / position["allocated_capital"]
                if position["allocated_capital"] > 0
                else 0.0,
                equity_after_trade=current_cash,
            )

            await self.persistence.save_trade(trade)

            symbol = f"{session.config.asset1}/{session.config.asset2}"
            await self.persistence.delete_position(session_id, symbol)
            del self._session_positions[session_id]
            self._entry_zscores.pop(session_id, None)

            logger.info(
                "Fill executed: event=fill_executed, session_id=%s, signal=%s, net_pnl=%.4f",
                session_id, signal.signal_type, trade.net_pnl,
            )

    # ------------------------------------------------------------------
    # Internal polling loop
    # ------------------------------------------------------------------

    async def _run_session_loop(self, session_id: str) -> None:
        """Background polling loop for a session."""
        session = await self.persistence.get_session(session_id)
        if session is None:
            return

        poll_interval = 60  # default 60 seconds
        try:
            while True:
                await self._process_cycle_with_retry(session_id)
                await asyncio.sleep(poll_interval)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error(
                "Session error: event=session_error, session_id=%s, error=%s",
                session_id, exc,
            )
            session = await self.persistence.get_session(session_id)
            if session:
                session.status = SessionStatus.error
                session.last_error = str(exc)
                session.updated_at = datetime.now(UTC)
                await self.persistence.save_session(session)
            self._tasks.pop(session_id, None)

    async def _process_cycle_with_retry(
        self, session_id: str, max_retries: int = 5
    ) -> int:
        """Run process_cycle with exponential backoff retry."""
        delays = [1, 2, 4, 8, 16]
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                result = await self.process_cycle(session_id)
                if attempt > 0:
                    logger.info(
                        "Data source recovered: event=data_source_recovered, "
                        "session_id=%s, after_retries=%d",
                        session_id, attempt,
                    )
                return result
            except Exception as exc:
                last_error = exc
                if attempt < max_retries:
                    delay = delays[min(attempt, len(delays) - 1)]
                    logger.warning(
                        "Data source error: event=data_source_error, "
                        "session_id=%s, error=%s, retry=%d, delay=%ds",
                        session_id, exc, attempt + 1, delay,
                    )
                    await asyncio.sleep(delay)

        # Max retries exhausted
        assert last_error is not None
        session = await self.persistence.get_session(session_id)
        if session:
            session.status = SessionStatus.error
            session.last_error = f"{last_error} (after {max_retries} retries)"
            session.updated_at = datetime.now(UTC)
            await self.persistence.save_session(session)
        self._tasks.pop(session_id, None)
        raise last_error
