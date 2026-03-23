"""Standalone risk management gate — pure Python, no async, no web imports.

The ``RiskManager`` validates orders against configurable limits before they
reach the exchange.  It follows the project's established separation pattern
(D032) where analysis/strategy/risk code is kept free from web framework
imports.
"""

from __future__ import annotations

import logging

from statistical_arbitrage.live_trading.models import RiskCheckResult

logger = logging.getLogger(__name__)


class RiskManager:
    """Pre-trade risk gate checking four configurable limits.

    Checks are evaluated in order:
    1. ``min_order_size`` — reject if amount < minimum (Bitvavo €5).
    2. ``max_position_size`` — reject if amount > per-trade maximum.
    3. ``max_concurrent_positions`` — reject if already at capacity.
    4. ``daily_loss_limit`` — reject if cumulative daily loss has reached limit.

    Args:
        max_position_size_eur: Maximum EUR value for a single order.
        max_concurrent_positions: Maximum number of open positions at once.
        daily_loss_limit_eur: Portfolio-level daily realized loss ceiling.
        min_order_size_eur: Minimum order value (Bitvavo minimum).
    """

    def __init__(
        self,
        max_position_size_eur: float = 25.0,
        max_concurrent_positions: int = 2,
        daily_loss_limit_eur: float = 50.0,
        min_order_size_eur: float = 5.0,
    ) -> None:
        self.max_position_size_eur = max_position_size_eur
        self.max_concurrent_positions = max_concurrent_positions
        self.daily_loss_limit_eur = daily_loss_limit_eur
        self.min_order_size_eur = min_order_size_eur

    @classmethod
    def from_settings(cls, settings) -> RiskManager:
        """Create a RiskManager from a ``LiveTradingSettings`` instance."""
        return cls(
            max_position_size_eur=settings.max_position_size_eur,
            max_concurrent_positions=settings.max_concurrent_positions,
            daily_loss_limit_eur=settings.daily_loss_limit_eur,
            min_order_size_eur=settings.min_order_size_eur,
        )

    def check_order(
        self,
        order_amount_eur: float,
        current_positions: int,
        daily_realized_loss: float,
    ) -> RiskCheckResult:
        """Evaluate an order against all risk limits.

        Args:
            order_amount_eur: EUR value of the proposed order.
            current_positions: Number of currently open positions.
            daily_realized_loss: Cumulative realized loss today (positive = loss).

        Returns:
            ``RiskCheckResult`` with ``approved=True`` if all checks pass, or
            ``approved=False`` with the specific ``reason`` and ``limit_type``
            of the first failing check.
        """
        # 1. Minimum order size
        if order_amount_eur < self.min_order_size_eur:
            reason = (
                f"Order amount €{order_amount_eur:.2f} below minimum "
                f"€{self.min_order_size_eur:.2f}"
            )
            logger.info("Risk rejected: %s", reason)
            return RiskCheckResult(
                approved=False, reason=reason, limit_type="min_order_size"
            )

        # 2. Maximum position size
        if order_amount_eur > self.max_position_size_eur:
            reason = (
                f"Order amount €{order_amount_eur:.2f} exceeds max position "
                f"size €{self.max_position_size_eur:.2f}"
            )
            logger.info("Risk rejected: %s", reason)
            return RiskCheckResult(
                approved=False, reason=reason, limit_type="max_position_size"
            )

        # 3. Maximum concurrent positions
        if current_positions >= self.max_concurrent_positions:
            reason = (
                f"Already at max concurrent positions "
                f"({current_positions}/{self.max_concurrent_positions})"
            )
            logger.info("Risk rejected: %s", reason)
            return RiskCheckResult(
                approved=False,
                reason=reason,
                limit_type="max_concurrent_positions",
            )

        # 4. Daily loss limit (>= means the limit has been hit)
        if daily_realized_loss >= self.daily_loss_limit_eur:
            reason = (
                f"Daily realized loss €{daily_realized_loss:.2f} has reached "
                f"limit €{self.daily_loss_limit_eur:.2f}"
            )
            logger.info("Risk rejected (circuit breaker): %s", reason)
            return RiskCheckResult(
                approved=False, reason=reason, limit_type="daily_loss_limit"
            )

        # All checks passed
        return RiskCheckResult(approved=True, reason=None, limit_type=None)
