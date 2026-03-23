"""Typed domain models for live trading — orders, risk checks, and events.

All models use Pydantic BaseModel for serialization consistency with the rest
of the platform.  Event models carry the fields that downstream consumers
(Telegram notifier in S02, API layer in S03) need for formatting.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Core trading models
# ---------------------------------------------------------------------------


class LiveOrder(BaseModel):
    """Represents a single live order submitted to the exchange."""

    order_id: str
    session_id: str
    side: Literal["buy", "sell"]
    symbol: str
    requested_amount: float
    filled_amount: float = 0.0
    fill_price: float = 0.0
    fee: float = 0.0
    status: Literal["pending", "filled", "partial", "failed", "cancelled"] = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    filled_at: datetime | None = None


class RiskCheckResult(BaseModel):
    """Structured result from the RiskManager gate."""

    approved: bool
    reason: str | None = None
    limit_type: Literal[
        "max_position_size",
        "max_concurrent_positions",
        "daily_loss_limit",
        "min_order_size",
    ] | None = None


# ---------------------------------------------------------------------------
# Event models — consumed by Telegram notifier (S02) and API (S03)
# ---------------------------------------------------------------------------


class OrderEvent(BaseModel):
    """Emitted when an order is filled or partially filled."""

    session_id: str
    order: LiveOrder
    position_after: str  # e.g. "long BTC-EUR 0.0012" or "flat"


class ErrorEvent(BaseModel):
    """Emitted on unrecoverable order or engine errors."""

    session_id: str
    error_type: str  # e.g. "InsufficientFunds", "NetworkError"
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RiskBreachEvent(BaseModel):
    """Emitted when a risk check rejects an order."""

    session_id: str
    check_result: RiskCheckResult
    order_details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------


class ReconciliationResult(BaseModel):
    """Result of comparing local position state against exchange balances."""

    matched: bool
    local_positions: dict[str, Any] = Field(default_factory=dict)
    exchange_balances: dict[str, Any] = Field(default_factory=dict)
    discrepancies: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Kill switch
# ---------------------------------------------------------------------------


class KillSwitchResult(BaseModel):
    """Structured result from the kill switch operation."""

    success: bool
    session_id: str
    orders_submitted: int = 0
    orders_failed: int = 0
    positions_closed: int = 0
    errors: list[str] = Field(default_factory=list)
