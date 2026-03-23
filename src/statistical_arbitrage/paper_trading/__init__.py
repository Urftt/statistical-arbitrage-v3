"""Paper trading package — async engine, persistence, and domain models.

Provides:
- Domain models: SessionConfig, PaperSession, PaperPosition, PaperTrade, etc.
- PersistenceManager: async SQLite CRUD with WAL mode
- PaperTradingEngine: async session lifecycle with polling and fill accounting
- CandleDataSource: injectable protocol for candle fetching
"""

from statistical_arbitrage.paper_trading.data_source import (
    CandleDataSource,
    MockCandleDataSource,
)
from statistical_arbitrage.paper_trading.models import (
    PaperEquityPoint,
    PaperPosition,
    PaperSession,
    PaperTrade,
    SessionConfig,
    SessionStatus,
)
from statistical_arbitrage.paper_trading.persistence import PersistenceManager
from statistical_arbitrage.paper_trading.engine import PaperTradingEngine

__all__ = [
    "CandleDataSource",
    "MockCandleDataSource",
    "PaperEquityPoint",
    "PaperPosition",
    "PaperSession",
    "PaperTrade",
    "PaperTradingEngine",
    "PersistenceManager",
    "SessionConfig",
    "SessionStatus",
]
