"""Live trading package — order execution, risk management, engine, and domain models.

This package provides the building blocks for live order execution on Bitvavo:
- ``OrderExecutor`` protocol (injectable, runtime-checkable)
- ``MockOrderExecutor`` and ``BitvavoOrderExecutor`` implementations
- ``RiskManager`` standalone risk gate
- ``LiveTradingEngine`` extending PaperTradingEngine for real order execution
- Domain models: ``LiveOrder``, ``RiskCheckResult``, event types
"""

from statistical_arbitrage.live_trading.models import (
    ErrorEvent,
    KillSwitchResult,
    LiveOrder,
    OrderEvent,
    ReconciliationResult,
    RiskBreachEvent,
    RiskCheckResult,
)
from statistical_arbitrage.live_trading.order_executor import (
    BitvavoOrderExecutor,
    MockOrderExecutor,
    OrderExecutor,
    round_to_significant_figures,
)
from statistical_arbitrage.live_trading.risk_manager import RiskManager
from statistical_arbitrage.live_trading.engine import LiveTradingEngine
from statistical_arbitrage.live_trading.telegram_notifier import TelegramNotifier

__all__ = [
    "BitvavoOrderExecutor",
    "ErrorEvent",
    "KillSwitchResult",
    "LiveOrder",
    "LiveTradingEngine",
    "MockOrderExecutor",
    "OrderEvent",
    "OrderExecutor",
    "ReconciliationResult",
    "RiskBreachEvent",
    "RiskCheckResult",
    "RiskManager",
    "TelegramNotifier",
    "round_to_significant_figures",
]
