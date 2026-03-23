"""Typed domain models for paper trading sessions and fill accounting.

All models use Pydantic BaseModel with ``extra="forbid"`` for strict
validation — any unexpected field raises an error at construction time.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from statistical_arbitrage.backtesting.models import StrategyParameters


class SessionStatus(StrEnum):
    """Valid session lifecycle states."""

    created = "created"
    running = "running"
    stopped = "stopped"
    error = "error"
    killed = "killed"


class SessionConfig(BaseModel):
    """User-supplied session configuration.

    Mirrors ``StrategyParameters`` fields for independence — the paper trading
    system does not import from the backtester at runtime.
    """

    model_config = ConfigDict(extra="forbid")

    asset1: str
    asset2: str
    timeframe: str = "1h"
    lookback_window: int = 60
    entry_threshold: float = 2.0
    exit_threshold: float = 0.5
    stop_loss: float = 3.0
    initial_capital: float = 10000.0
    position_size: float = 0.5
    transaction_fee: float = 0.0025
    is_live: bool = False

    def to_strategy_parameters(self) -> StrategyParameters:
        """Bridge to backtester parameters for fill-accounting reuse."""
        return StrategyParameters(
            lookback_window=self.lookback_window,
            entry_threshold=self.entry_threshold,
            exit_threshold=self.exit_threshold,
            stop_loss=self.stop_loss,
            initial_capital=self.initial_capital,
            position_size=self.position_size,
            transaction_fee=self.transaction_fee,
        )


class PaperSession(BaseModel):
    """State of a single paper/live trading session."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    config: SessionConfig
    status: SessionStatus = SessionStatus.created
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    current_equity: float = 0.0
    total_trades: int = 0
    last_error: str | None = None
    is_live: bool = False


class PaperPosition(BaseModel):
    """An open position tracked by the paper trading engine."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    symbol: str
    direction: Literal["long_spread", "short_spread"]
    quantity_asset1: float
    quantity_asset2: float
    entry_price_asset1: float
    entry_price_asset2: float
    hedge_ratio: float
    entry_fee: float = 0.0
    allocated_capital: float = 0.0
    opened_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PaperTrade(BaseModel):
    """A completed round-trip trade."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    trade_id: int
    direction: Literal["long_spread", "short_spread"]
    entry_timestamp: str
    exit_timestamp: str
    entry_reason: str
    exit_reason: str
    bars_held: int
    entry_zscore: float
    exit_zscore: float
    hedge_ratio: float
    quantity_asset1: float
    quantity_asset2: float
    entry_price_asset1: float
    entry_price_asset2: float
    exit_price_asset1: float
    exit_price_asset2: float
    allocated_capital: float
    gross_pnl: float
    total_fees: float
    net_pnl: float
    return_pct: float
    equity_after_trade: float


class PaperEquityPoint(BaseModel):
    """Equity snapshot at a point in time."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    timestamp: str
    equity: float
    cash: float
    unrealized_pnl: float
    position: Literal["flat", "long_spread", "short_spread"]
