"""Live trading engine — extends PaperTradingEngine with real order execution.

The ``LiveTradingEngine`` subclasses ``PaperTradingEngine`` and replaces
simulated fill execution with real order submission gated by risk checks.
For paper sessions (``is_live=False``), behaviour is unchanged — fills are
simulated as before. For live sessions (``is_live=True``), every order
passes through ``RiskManager.check_order()`` before reaching
``OrderExecutor.submit_order()``.

Implements:
- R019: Live order execution via injectable ``OrderExecutor``
- R020: Risk limit enforcement in the trading loop (4 limits + daily loss circuit breaker)
- D032: Composes OrderExecutor + RiskManager into the paper trading signal pipeline
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

import ccxt

from statistical_arbitrage.backtesting.models import StrategyParameters
from statistical_arbitrage.live_trading.models import (
    ErrorEvent,
    KillSwitchResult,
    LiveOrder,
    OrderEvent,
    ReconciliationResult,
    RiskBreachEvent,
    RiskCheckResult,
)
from statistical_arbitrage.live_trading.order_executor import OrderExecutor
from statistical_arbitrage.live_trading.risk_manager import RiskManager
from statistical_arbitrage.paper_trading.data_source import CandleDataSource
from statistical_arbitrage.paper_trading.engine import PaperTradingEngine
from statistical_arbitrage.paper_trading.models import (
    PaperPosition,
    PaperSession,
    PaperTrade,
    SessionStatus,
)
from statistical_arbitrage.paper_trading.persistence import PersistenceManager

logger = logging.getLogger(__name__)


class LiveTradingEngine(PaperTradingEngine):
    """Trading engine supporting both paper and live sessions.

    For live sessions (``session.config.is_live is True``), orders are
    submitted through the injected ``OrderExecutor`` and gated by the
    ``RiskManager``. For paper sessions, fills are simulated via the
    parent class.

    Implements a daily loss circuit breaker that tracks cumulative
    realized loss across all live sessions and blocks further live
    order submission when the limit is exceeded.

    Args:
        data_source: Injectable candle data provider.
        persistence: Async SQLite persistence layer.
        order_executor: Real or mock order execution backend.
        risk_manager: Pre-trade risk gate.
        notifier: Optional Telegram notifier (ships as None, S02 provides).
    """

    def __init__(
        self,
        data_source: CandleDataSource,
        persistence: PersistenceManager,
        order_executor: OrderExecutor,
        risk_manager: RiskManager,
        notifier: Any | None = None,
    ) -> None:
        super().__init__(data_source=data_source, persistence=persistence)
        self.order_executor = order_executor
        self.risk_manager = risk_manager
        self.notifier = notifier

        # Portfolio-level daily loss tracking
        self._daily_realized_loss: float = 0.0
        self._daily_loss_breached: bool = False

        # Event log for test inspection
        self.events: list[OrderEvent | ErrorEvent | RiskBreachEvent] = []

    # ------------------------------------------------------------------
    # Fire-and-forget notification dispatch
    # ------------------------------------------------------------------

    def _notify(self, coro) -> None:
        """Fire-and-forget notification — exceptions are logged, never raised."""
        task = asyncio.create_task(coro)
        task.add_done_callback(self._on_notify_done)

    @staticmethod
    def _on_notify_done(task: asyncio.Task) -> None:
        """Log unexpected exceptions from notification tasks."""
        if task.cancelled():
            return
        exc = task.exception()
        if exc:
            logger.warning("Notification task failed: %s: %s", type(exc).__name__, exc)

    # ------------------------------------------------------------------
    # Daily loss circuit breaker
    # ------------------------------------------------------------------

    def get_daily_loss(self) -> float:
        """Return current cumulative daily realized loss (positive = loss)."""
        return self._daily_realized_loss

    def reset_daily_loss(self) -> None:
        """Reset the daily loss counter (call at start of trading day)."""
        self._daily_realized_loss = 0.0
        self._daily_loss_breached = False
        logger.info("Daily loss counter reset")

    # ------------------------------------------------------------------
    # Kill switch
    # ------------------------------------------------------------------

    async def kill_session(self, session_id: str) -> KillSwitchResult:
        """Emergency stop — flatten all live positions and kill the session.

        Idempotent: safe to call on sessions that are already killed, stopped,
        or have no open positions.  Exposed as a dashboard button in S03, so
        panic-clicking must not cause errors.

        For each open position a market close order is submitted via
        ``order_executor.submit_order()``.  Failures on individual close
        orders are logged and counted but do not abort the remaining closes.

        Args:
            session_id: Session to kill.

        Returns:
            Structured ``KillSwitchResult`` with order counts and errors.
        """
        session = await self.persistence.get_session(session_id)
        if session is None:
            return KillSwitchResult(
                success=False,
                session_id=session_id,
                errors=[f"Session {session_id} not found"],
            )

        # Idempotent: already killed → no-op success
        if session.status == SessionStatus.killed:
            logger.info("Kill switch no-op: session_id=%s already killed", session_id)
            return KillSwitchResult(success=True, session_id=session_id)

        # Stop polling loop if running
        task = self._tasks.pop(session_id, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Load open positions from persistence
        positions = await self.persistence.get_positions(session_id)
        symbol = f"{session.config.asset1}/{session.config.asset2}"

        orders_submitted = 0
        orders_failed = 0
        positions_closed = 0
        errors: list[str] = []

        # Flatten each open position
        for pos in positions:
            # Determine close side: buy to close short, sell to close long
            if pos.direction == "long_spread":
                close_side = "sell"
            else:
                close_side = "buy"
            close_amount = abs(pos.quantity_asset1)

            try:
                order = await self.order_executor.submit_order(
                    pos.symbol, close_side, close_amount,
                )
                order.session_id = session_id
                orders_submitted += 1

                # Persist the close order
                await self.persistence.save_order(order)

                # Remove position from persistence
                await self.persistence.delete_position(session_id, pos.symbol)
                positions_closed += 1

                # Clean up in-memory state
                self._session_positions.pop(session_id, None)
                self._entry_zscores.pop(session_id, None)

                # Emit order event
                order_event = OrderEvent(
                    session_id=session_id,
                    order=order,
                    position_after="flat (killed)",
                )
                self.events.append(order_event)
                if self.notifier:
                    self._notify(self.notifier.send_fill(order_event))
                logger.info(
                    "Kill switch close order: session_id=%s, order_id=%s, "
                    "side=%s, amount=%.6f, symbol=%s",
                    session_id, order.order_id, close_side, close_amount,
                    pos.symbol,
                )
            except Exception as exc:
                orders_failed += 1
                error_msg = f"Failed to close {pos.direction} {pos.symbol}: {type(exc).__name__}: {exc}"
                errors.append(error_msg)
                logger.error(
                    "Kill switch close order failed: session_id=%s, "
                    "symbol=%s, error_type=%s, message=%s",
                    session_id, pos.symbol, type(exc).__name__, exc,
                )

        # Update session status to killed
        session.status = SessionStatus.killed
        session.updated_at = datetime.now(UTC)
        await self.persistence.save_session(session)

        success = orders_failed == 0
        logger.info(
            "Kill switch completed: session_id=%s, success=%s, "
            "orders_submitted=%d, orders_failed=%d, positions_closed=%d",
            session_id, success, orders_submitted, orders_failed,
            positions_closed,
        )

        return KillSwitchResult(
            success=success,
            session_id=session_id,
            orders_submitted=orders_submitted,
            orders_failed=orders_failed,
            positions_closed=positions_closed,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Position reconciliation
    # ------------------------------------------------------------------

    async def reconcile_positions(self, session_id: str) -> ReconciliationResult:
        """Compare local position state against exchange balances.

        Should be called before starting a live session to detect state
        divergence.  Uses a 1% tolerance per position to account for
        fee-induced balance differences.

        Args:
            session_id: Session to reconcile.

        Returns:
            ``ReconciliationResult`` with matched/mismatched status and
            discrepancy details.
        """
        positions = await self.persistence.get_positions(session_id)

        # No positions → trivially matched
        if not positions:
            return ReconciliationResult(
                matched=True,
                local_positions={},
                exchange_balances={},
                discrepancies=[],
            )

        # Query exchange balances
        exchange_balances = await self.order_executor.fetch_balance()

        local_map: dict[str, float] = {}
        discrepancies: list[str] = []

        for pos in positions:
            # Extract the base asset from the symbol (e.g. "BTC" from "BTC/EUR")
            base_asset = pos.symbol.split("/")[0] if "/" in pos.symbol else pos.symbol
            expected_amount = abs(pos.quantity_asset1)
            local_map[base_asset] = expected_amount

            # Get exchange balance for this asset
            asset_balance = exchange_balances.get(base_asset, {})
            exchange_total = asset_balance.get("total", 0.0)

            # Tolerance: 1% of expected position size
            tolerance = expected_amount * 0.01

            if abs(exchange_total - expected_amount) > tolerance:
                discrepancies.append(
                    f"{base_asset}: local={expected_amount:.6f}, "
                    f"exchange={exchange_total:.6f}, "
                    f"diff={abs(exchange_total - expected_amount):.6f} "
                    f"(tolerance={tolerance:.6f})"
                )

        matched = len(discrepancies) == 0

        if not matched:
            logger.warning(
                "Position reconciliation mismatch: session_id=%s, "
                "discrepancies=%s",
                session_id, discrepancies,
            )
        else:
            logger.info(
                "Position reconciliation matched: session_id=%s, "
                "positions=%d",
                session_id, len(positions),
            )

        return ReconciliationResult(
            matched=matched,
            local_positions=local_map,
            exchange_balances={
                k: v for k, v in exchange_balances.items()
                if k in local_map
            },
            discrepancies=discrepancies,
        )

    async def start_session(self, session_id: str) -> None:
        """Start a session, with reconciliation check for live sessions.

        For live sessions, reconciles positions against exchange balances
        before starting.  If a mismatch is detected, the session is blocked
        from starting and a ``ValueError`` is raised.

        Args:
            session_id: Session to start.

        Raises:
            ValueError: If session not found, already running, or
                reconciliation detects a mismatch.
        """
        session = await self.persistence.get_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")
        if session.status == SessionStatus.running:
            raise ValueError(f"Session {session_id} is already running")

        # Live sessions require reconciliation before start
        if session.config.is_live:
            recon = await self.reconcile_positions(session_id)
            if not recon.matched:
                raise ValueError(
                    f"Position reconciliation failed for session {session_id}: "
                    f"{'; '.join(recon.discrepancies)}"
                )

        session.status = SessionStatus.running
        session.updated_at = datetime.now(UTC)
        await self.persistence.save_session(session)

        task = asyncio.create_task(self._run_session_loop(session_id))
        self._tasks[session_id] = task
        logger.info("Session started: session_id=%s", session_id)

    # ------------------------------------------------------------------
    # Override fill execution
    # ------------------------------------------------------------------

    async def _execute_fill(
        self,
        session: PaperSession,
        signal: Any,
        price1: float,
        price2: float,
        timestamp: str,
        params: StrategyParameters,
    ) -> None:
        """Execute a fill — real orders for live sessions, simulated for paper.

        For live sessions:
        1. Calculate order amount in EUR
        2. Risk check via RiskManager
        3. If rejected: emit RiskBreachEvent, skip
        4. If approved: submit via OrderExecutor
        5. Persist order, update position/trade/equity with actual fill prices

        For paper sessions: delegate to parent (simulated fills).
        """
        if not session.config.is_live:
            # Paper session — use simulated fills from parent class
            await super()._execute_fill(session, signal, price1, price2, timestamp, params)
            return

        # Live session — real order execution
        await self._execute_live_fill(session, signal, price1, price2, timestamp, params)

    async def _execute_live_fill(
        self,
        session: PaperSession,
        signal: Any,
        price1: float,
        price2: float,
        timestamp: str,
        params: StrategyParameters,
    ) -> None:
        """Execute a live fill through OrderExecutor with risk gating."""
        session_id = session.session_id
        current_cash = self._session_equity.get(
            session_id, session.config.initial_capital
        )
        symbol = f"{session.config.asset1}/{session.config.asset2}"

        if signal.signal_type in ("long_entry", "short_entry"):
            await self._execute_live_entry(
                session, signal, price1, price2, timestamp, params,
                current_cash, symbol,
            )
        else:
            await self._execute_live_exit(
                session, signal, price1, price2, timestamp, params,
                current_cash, symbol,
            )

    async def _execute_live_entry(
        self,
        session: PaperSession,
        signal: Any,
        price1: float,
        price2: float,
        timestamp: str,
        params: StrategyParameters,
        current_cash: float,
        symbol: str,
    ) -> None:
        """Execute a live entry: risk check → order submit → persist."""
        session_id = session.session_id

        # Already have a position — skip
        if session_id in self._session_positions:
            return

        # Calculate order amount in EUR
        notional_denominator = price1 + abs(signal.hedge_ratio_at_signal) * price2
        if notional_denominator <= 0:
            return

        allocated_capital = current_cash * params.position_size
        order_amount_eur = allocated_capital  # EUR value of the trade

        # Count open positions across all live sessions
        live_position_count = sum(
            1 for sid, pos in self._session_positions.items()
            if pos.get("is_live", False)
        )

        # Daily loss circuit breaker check
        if self._daily_loss_breached:
            breach_result = RiskCheckResult(
                approved=False,
                reason=f"Daily loss circuit breaker active — cumulative loss €{self._daily_realized_loss:.2f}",
                limit_type="daily_loss_limit",
            )
            event = RiskBreachEvent(
                session_id=session_id,
                check_result=breach_result,
                order_details={"symbol": symbol, "side": signal.direction, "amount_eur": order_amount_eur},
            )
            self.events.append(event)
            if self.notifier:
                self._notify(self.notifier.send_risk_breach(event))
            logger.info(
                "Risk breach (circuit breaker): session_id=%s, reason=%s",
                session_id, breach_result.reason,
            )
            return

        # Risk check
        risk_result = self.risk_manager.check_order(
            order_amount_eur=order_amount_eur,
            current_positions=live_position_count,
            daily_realized_loss=self._daily_realized_loss,
        )

        if not risk_result.approved:
            event = RiskBreachEvent(
                session_id=session_id,
                check_result=risk_result,
                order_details={"symbol": symbol, "side": signal.direction, "amount_eur": order_amount_eur},
            )
            self.events.append(event)
            if self.notifier:
                self._notify(self.notifier.send_risk_breach(event))
            logger.info(
                "Risk breach: session_id=%s, limit_type=%s, reason=%s",
                session_id, risk_result.limit_type, risk_result.reason,
            )
            return

        # Calculate quantities for order submission
        scale = allocated_capital / notional_denominator
        if signal.direction == "long_spread":
            amount = abs(scale)  # base currency amount for asset1
            side = "buy"
        else:
            amount = abs(scale)
            side = "sell"

        # Submit order via OrderExecutor
        try:
            order = await self.order_executor.submit_order(symbol, side, amount)
            order.session_id = session_id
        except (ccxt.InsufficientFunds, ccxt.InvalidOrder) as exc:
            # Unrecoverable order errors — log and skip
            error_event = ErrorEvent(
                session_id=session_id,
                error_type=type(exc).__name__,
                message=str(exc),
            )
            self.events.append(error_event)
            if self.notifier:
                self._notify(self.notifier.send_error(error_event))
            logger.error(
                "Order error: session_id=%s, error_type=%s, symbol=%s, message=%s",
                session_id, type(exc).__name__, symbol, exc,
            )
            return
        except (ccxt.NetworkError, ccxt.ExchangeNotAvailable) as exc:
            # Network/availability errors — log and transition to error state
            error_event = ErrorEvent(
                session_id=session_id,
                error_type=type(exc).__name__,
                message=str(exc),
            )
            self.events.append(error_event)
            if self.notifier:
                self._notify(self.notifier.send_error(error_event))
            logger.error(
                "Order network error: session_id=%s, error_type=%s, message=%s",
                session_id, type(exc).__name__, exc,
            )
            session.status = SessionStatus.error
            session.last_error = f"Order submission failed: {type(exc).__name__}: {exc}"
            session.updated_at = datetime.now(UTC)
            await self.persistence.save_session(session)
            return
        except Exception as exc:
            # Unexpected errors — transition to error state
            error_event = ErrorEvent(
                session_id=session_id,
                error_type=type(exc).__name__,
                message=str(exc),
            )
            self.events.append(error_event)
            if self.notifier:
                self._notify(self.notifier.send_error(error_event))
            logger.error(
                "Unexpected order error: session_id=%s, error=%s",
                session_id, exc,
            )
            session.status = SessionStatus.error
            session.last_error = f"Unexpected order error: {exc}"
            session.updated_at = datetime.now(UTC)
            await self.persistence.save_session(session)
            return

        # Use actual fill prices and amounts from the order
        fill_price = order.fill_price
        fill_fee = order.fee

        # Handle partial fills — adjust position for actual filled amount
        if order.filled_amount > 0 and amount > 0:
            fill_ratio = order.filled_amount / amount
        else:
            fill_ratio = 1.0
        actual_scale = scale * fill_ratio
        actual_allocated = allocated_capital * fill_ratio

        # Calculate quantities using actual filled amount
        if signal.direction == "long_spread":
            quantity_asset1 = actual_scale
            quantity_asset2 = -actual_scale * signal.hedge_ratio_at_signal
        else:
            quantity_asset1 = -actual_scale
            quantity_asset2 = actual_scale * signal.hedge_ratio_at_signal

        # Apply fill — use actual fee from exchange
        current_cash -= fill_fee
        self._session_equity[session_id] = current_cash

        position_data = {
            "direction": signal.direction,
            "entry_signal": signal,
            "entry_timestamp": timestamp,
            "entry_price_asset1": fill_price,  # Use actual fill price
            "entry_price_asset2": price2,
            "entry_cash": current_cash,
            "entry_fee": fill_fee,
            "allocated_capital": actual_allocated,
            "quantity_asset1": quantity_asset1,
            "quantity_asset2": quantity_asset2,
            "hedge_ratio": signal.hedge_ratio_at_signal,
            "is_live": True,
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
                entry_price_asset1=fill_price,
                entry_price_asset2=price2,
                hedge_ratio=signal.hedge_ratio_at_signal,
                entry_fee=fill_fee,
                allocated_capital=actual_allocated,
            )
        )

        # Persist order
        await self.persistence.save_order(order)

        # Emit order event
        order_event = OrderEvent(
            session_id=session_id,
            order=order,
            position_after=f"{signal.direction} {symbol}",
        )
        self.events.append(order_event)
        if self.notifier:
            self._notify(self.notifier.send_fill(order_event))
        logger.info(
            "Live fill executed: event=fill_executed, session_id=%s, order_id=%s, "
            "signal=%s, fill_price=%.4f, fee=%.4f",
            session_id, order.order_id, signal.signal_type, fill_price, fill_fee,
        )

    async def _execute_live_exit(
        self,
        session: PaperSession,
        signal: Any,
        price1: float,
        price2: float,
        timestamp: str,
        params: StrategyParameters,
        current_cash: float,
        symbol: str,
    ) -> None:
        """Execute a live exit: submit close order → persist trade → update equity."""
        session_id = session.session_id
        position = self._session_positions.get(session_id)
        if position is None:
            return

        # Submit close order
        close_amount = abs(position["quantity_asset1"])
        close_side = "sell" if position["direction"] == "long_spread" else "buy"

        try:
            order = await self.order_executor.submit_order(symbol, close_side, close_amount)
            order.session_id = session_id
        except Exception as exc:
            error_event = ErrorEvent(
                session_id=session_id,
                error_type=type(exc).__name__,
                message=str(exc),
            )
            self.events.append(error_event)
            if self.notifier:
                self._notify(self.notifier.send_error(error_event))
            logger.error(
                "Exit order error: session_id=%s, error_type=%s, message=%s",
                session_id, type(exc).__name__, exc,
            )
            return

        # Calculate PnL using actual fill prices
        exit_price1 = order.fill_price  # Actual fill price from exchange
        exit_fee = order.fee

        gross_pnl = float(
            position["quantity_asset1"] * (exit_price1 - position["entry_price_asset1"])
            + position["quantity_asset2"] * (price2 - position["entry_price_asset2"])
        )
        net_pnl = gross_pnl - exit_fee
        current_cash += gross_pnl - exit_fee
        self._session_equity[session_id] = current_cash

        trade_count = self._session_trades.get(session_id, 0) + 1
        self._session_trades[session_id] = trade_count

        entry_signal = position["entry_signal"]
        total_fees = position["entry_fee"] + exit_fee
        final_net_pnl = net_pnl - position["entry_fee"]

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
            exit_price_asset1=exit_price1,
            exit_price_asset2=price2,
            allocated_capital=position["allocated_capital"],
            gross_pnl=gross_pnl,
            total_fees=total_fees,
            net_pnl=final_net_pnl,
            return_pct=final_net_pnl / position["allocated_capital"]
            if position["allocated_capital"] > 0
            else 0.0,
            equity_after_trade=current_cash,
        )

        await self.persistence.save_trade(trade)
        await self.persistence.save_order(order)
        await self.persistence.delete_position(session_id, symbol)
        del self._session_positions[session_id]
        self._entry_zscores.pop(session_id, None)

        # Track daily loss for circuit breaker (positive loss = losing trade)
        if final_net_pnl < 0:
            self._daily_realized_loss += abs(final_net_pnl)
            logger.info(
                "Daily loss updated: session_id=%s, trade_net_pnl=%.4f, "
                "cumulative_daily_loss=%.4f, limit=%.2f",
                session_id, final_net_pnl, self._daily_realized_loss,
                self.risk_manager.daily_loss_limit_eur,
            )
            # Check if circuit breaker should trigger
            if self._daily_realized_loss >= self.risk_manager.daily_loss_limit_eur:
                self._daily_loss_breached = True
                breach_result = RiskCheckResult(
                    approved=False,
                    reason=(
                        f"Daily loss circuit breaker triggered: "
                        f"€{self._daily_realized_loss:.2f} >= "
                        f"€{self.risk_manager.daily_loss_limit_eur:.2f}"
                    ),
                    limit_type="daily_loss_limit",
                )
                breach_event = RiskBreachEvent(
                    session_id=session_id,
                    check_result=breach_result,
                )
                self.events.append(breach_event)
                if self.notifier:
                    self._notify(self.notifier.send_risk_breach(breach_event))
                logger.warning(
                    "DAILY LOSS CIRCUIT BREAKER TRIGGERED: session_id=%s, "
                    "cumulative_loss=€%.2f, limit=€%.2f",
                    session_id, self._daily_realized_loss,
                    self.risk_manager.daily_loss_limit_eur,
                )

        # Emit order event
        order_event = OrderEvent(
            session_id=session_id,
            order=order,
            position_after="flat",
        )
        self.events.append(order_event)
        if self.notifier:
            self._notify(self.notifier.send_fill(order_event))
        logger.info(
            "Live exit executed: event=fill_executed, session_id=%s, order_id=%s, "
            "signal=%s, net_pnl=%.4f",
            session_id, order.order_id, signal.signal_type, final_net_pnl,
        )
