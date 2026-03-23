"""Async SQLite persistence for paper/live trading sessions.

Uses aiosqlite with WAL mode for concurrent read safety. Creates 4 base
tables (sessions, positions, trades, equity_snapshots) with cascade delete
via foreign keys.

Uses ``ON CONFLICT DO UPDATE`` (not INSERT OR REPLACE) to avoid triggering
cascade deletes — see KNOWLEDGE.md.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from statistical_arbitrage.live_trading.models import LiveOrder
from statistical_arbitrage.paper_trading.models import (
    PaperEquityPoint,
    PaperPosition,
    PaperSession,
    PaperTrade,
    SessionConfig,
    SessionStatus,
)

logger = logging.getLogger(__name__)


class PersistenceManager:
    """Async SQLite persistence layer for paper/live trading sessions.

    Usable as an async context manager::

        async with PersistenceManager("path/to/db.sqlite") as pm:
            await pm.save_session(session)

    Args:
        db_path: Path to SQLite file, or ``":memory:"`` for in-memory testing.
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = str(db_path)
        self._db: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Open the database connection and initialize tables."""
        self._db = await aiosqlite.connect(self.db_path)
        await self._db.execute("PRAGMA foreign_keys = ON")
        if self.db_path != ":memory:":
            await self._db.execute("PRAGMA journal_mode = WAL")
        logger.info("PersistenceManager connected to %s", self.db_path)
        await self._init_db()

    async def close(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None
            logger.info("PersistenceManager closed")

    async def __aenter__(self) -> PersistenceManager:
        await self.connect()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    @property
    def db(self) -> aiosqlite.Connection:
        """Return the active connection or raise."""
        if self._db is None:
            raise RuntimeError("PersistenceManager is not connected")
        return self._db

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    async def _init_db(self) -> None:
        """Create all tables if they don't exist."""
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                config TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'created',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                current_equity REAL NOT NULL DEFAULT 0.0,
                total_trades INTEGER NOT NULL DEFAULT 0,
                last_error TEXT,
                is_live INTEGER NOT NULL DEFAULT 0
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                session_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                quantity_asset1 REAL NOT NULL,
                quantity_asset2 REAL NOT NULL,
                entry_price_asset1 REAL NOT NULL,
                entry_price_asset2 REAL NOT NULL,
                hedge_ratio REAL NOT NULL,
                entry_fee REAL NOT NULL DEFAULT 0.0,
                allocated_capital REAL NOT NULL DEFAULT 0.0,
                opened_at TEXT NOT NULL,
                PRIMARY KEY (session_id, symbol),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                trade_id INTEGER NOT NULL,
                direction TEXT NOT NULL,
                entry_timestamp TEXT NOT NULL,
                exit_timestamp TEXT NOT NULL,
                entry_reason TEXT NOT NULL,
                exit_reason TEXT NOT NULL,
                bars_held INTEGER NOT NULL,
                entry_zscore REAL NOT NULL,
                exit_zscore REAL NOT NULL,
                hedge_ratio REAL NOT NULL,
                quantity_asset1 REAL NOT NULL,
                quantity_asset2 REAL NOT NULL,
                entry_price_asset1 REAL NOT NULL,
                entry_price_asset2 REAL NOT NULL,
                exit_price_asset1 REAL NOT NULL,
                exit_price_asset2 REAL NOT NULL,
                allocated_capital REAL NOT NULL,
                gross_pnl REAL NOT NULL,
                total_fees REAL NOT NULL,
                net_pnl REAL NOT NULL,
                return_pct REAL NOT NULL,
                equity_after_trade REAL NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS equity_snapshots (
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                equity REAL NOT NULL,
                cash REAL NOT NULL,
                unrealized_pnl REAL NOT NULL,
                position TEXT NOT NULL,
                PRIMARY KEY (session_id, timestamp),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                session_id TEXT NOT NULL,
                side TEXT NOT NULL,
                symbol TEXT NOT NULL,
                requested_amount REAL NOT NULL,
                filled_amount REAL NOT NULL,
                fill_price REAL NOT NULL,
                fee REAL NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                filled_at TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)
        await self.db.commit()
        logger.info("Database tables initialized")

    # ------------------------------------------------------------------
    # Session CRUD
    # ------------------------------------------------------------------

    async def save_session(self, session: PaperSession) -> None:
        """Upsert a session — uses ON CONFLICT DO UPDATE to avoid cascade."""
        config_json = session.config.model_dump_json()
        await self.db.execute(
            """
            INSERT INTO sessions (session_id, config, status, created_at, updated_at,
                                  current_equity, total_trades, last_error, is_live)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                config = excluded.config,
                status = excluded.status,
                updated_at = excluded.updated_at,
                current_equity = excluded.current_equity,
                total_trades = excluded.total_trades,
                last_error = excluded.last_error,
                is_live = excluded.is_live
            """,
            (
                session.session_id,
                config_json,
                session.status.value,
                session.created_at.isoformat(),
                session.updated_at.isoformat(),
                session.current_equity,
                session.total_trades,
                session.last_error,
                1 if session.is_live else 0,
            ),
        )
        await self.db.commit()

    async def get_session(self, session_id: str) -> PaperSession | None:
        """Load a single session by ID."""
        cursor = await self.db.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_session(row)

    async def get_all_sessions(self) -> list[PaperSession]:
        """Load all sessions."""
        cursor = await self.db.execute("SELECT * FROM sessions ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [self._row_to_session(row) for row in rows]

    async def get_active_sessions(self) -> list[PaperSession]:
        """Load sessions with status 'running'."""
        cursor = await self.db.execute(
            "SELECT * FROM sessions WHERE status = ? ORDER BY created_at DESC",
            ("running",),
        )
        rows = await cursor.fetchall()
        return [self._row_to_session(row) for row in rows]

    async def delete_session(self, session_id: str) -> None:
        """Delete a session and all cascaded children."""
        await self.db.execute(
            "DELETE FROM sessions WHERE session_id = ?", (session_id,)
        )
        await self.db.commit()

    def _row_to_session(self, row: tuple) -> PaperSession:
        """Convert a raw SQLite row to a PaperSession."""
        config = SessionConfig.model_validate_json(row[1])
        return PaperSession(
            session_id=row[0],
            config=config,
            status=SessionStatus(row[2]),
            created_at=datetime.fromisoformat(row[3]),
            updated_at=datetime.fromisoformat(row[4]),
            current_equity=row[5],
            total_trades=row[6],
            last_error=row[7],
            is_live=bool(row[8]),
        )

    # ------------------------------------------------------------------
    # Position CRUD
    # ------------------------------------------------------------------

    async def save_position(self, position: PaperPosition) -> None:
        """Upsert a position — uses ON CONFLICT DO UPDATE."""
        await self.db.execute(
            """
            INSERT INTO positions (session_id, symbol, direction, quantity_asset1,
                                   quantity_asset2, entry_price_asset1, entry_price_asset2,
                                   hedge_ratio, entry_fee, allocated_capital, opened_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id, symbol) DO UPDATE SET
                direction = excluded.direction,
                quantity_asset1 = excluded.quantity_asset1,
                quantity_asset2 = excluded.quantity_asset2,
                entry_price_asset1 = excluded.entry_price_asset1,
                entry_price_asset2 = excluded.entry_price_asset2,
                hedge_ratio = excluded.hedge_ratio,
                entry_fee = excluded.entry_fee,
                allocated_capital = excluded.allocated_capital,
                opened_at = excluded.opened_at
            """,
            (
                position.session_id,
                position.symbol,
                position.direction,
                position.quantity_asset1,
                position.quantity_asset2,
                position.entry_price_asset1,
                position.entry_price_asset2,
                position.hedge_ratio,
                position.entry_fee,
                position.allocated_capital,
                position.opened_at.isoformat(),
            ),
        )
        await self.db.commit()

    async def get_positions(self, session_id: str) -> list[PaperPosition]:
        """Load all open positions for a session."""
        cursor = await self.db.execute(
            "SELECT * FROM positions WHERE session_id = ?", (session_id,)
        )
        rows = await cursor.fetchall()
        return [
            PaperPosition(
                session_id=row[0],
                symbol=row[1],
                direction=row[2],
                quantity_asset1=row[3],
                quantity_asset2=row[4],
                entry_price_asset1=row[5],
                entry_price_asset2=row[6],
                hedge_ratio=row[7],
                entry_fee=row[8],
                allocated_capital=row[9],
                opened_at=datetime.fromisoformat(row[10]),
            )
            for row in rows
        ]

    async def delete_position(self, session_id: str, symbol: str) -> None:
        """Remove a position (on trade close)."""
        await self.db.execute(
            "DELETE FROM positions WHERE session_id = ? AND symbol = ?",
            (session_id, symbol),
        )
        await self.db.commit()

    # ------------------------------------------------------------------
    # Trade CRUD
    # ------------------------------------------------------------------

    async def save_trade(self, trade: PaperTrade) -> None:
        """Insert a completed trade."""
        await self.db.execute(
            """
            INSERT INTO trades (session_id, trade_id, direction, entry_timestamp,
                               exit_timestamp, entry_reason, exit_reason, bars_held,
                               entry_zscore, exit_zscore, hedge_ratio,
                               quantity_asset1, quantity_asset2,
                               entry_price_asset1, entry_price_asset2,
                               exit_price_asset1, exit_price_asset2,
                               allocated_capital, gross_pnl, total_fees,
                               net_pnl, return_pct, equity_after_trade)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade.session_id,
                trade.trade_id,
                trade.direction,
                trade.entry_timestamp,
                trade.exit_timestamp,
                trade.entry_reason,
                trade.exit_reason,
                trade.bars_held,
                trade.entry_zscore,
                trade.exit_zscore,
                trade.hedge_ratio,
                trade.quantity_asset1,
                trade.quantity_asset2,
                trade.entry_price_asset1,
                trade.entry_price_asset2,
                trade.exit_price_asset1,
                trade.exit_price_asset2,
                trade.allocated_capital,
                trade.gross_pnl,
                trade.total_fees,
                trade.net_pnl,
                trade.return_pct,
                trade.equity_after_trade,
            ),
        )
        await self.db.commit()

    async def get_trades(self, session_id: str) -> list[PaperTrade]:
        """Load all trades for a session, ordered by trade_id."""
        cursor = await self.db.execute(
            """SELECT session_id, trade_id, direction, entry_timestamp, exit_timestamp,
                      entry_reason, exit_reason, bars_held, entry_zscore, exit_zscore,
                      hedge_ratio, quantity_asset1, quantity_asset2,
                      entry_price_asset1, entry_price_asset2,
                      exit_price_asset1, exit_price_asset2,
                      allocated_capital, gross_pnl, total_fees,
                      net_pnl, return_pct, equity_after_trade
               FROM trades WHERE session_id = ? ORDER BY trade_id""",
            (session_id,),
        )
        rows = await cursor.fetchall()
        return [
            PaperTrade(
                session_id=row[0],
                trade_id=row[1],
                direction=row[2],
                entry_timestamp=row[3],
                exit_timestamp=row[4],
                entry_reason=row[5],
                exit_reason=row[6],
                bars_held=row[7],
                entry_zscore=row[8],
                exit_zscore=row[9],
                hedge_ratio=row[10],
                quantity_asset1=row[11],
                quantity_asset2=row[12],
                entry_price_asset1=row[13],
                entry_price_asset2=row[14],
                exit_price_asset1=row[15],
                exit_price_asset2=row[16],
                allocated_capital=row[17],
                gross_pnl=row[18],
                total_fees=row[19],
                net_pnl=row[20],
                return_pct=row[21],
                equity_after_trade=row[22],
            )
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Equity CRUD
    # ------------------------------------------------------------------

    async def save_equity_point(self, point: PaperEquityPoint) -> None:
        """Insert or update an equity snapshot."""
        await self.db.execute(
            """
            INSERT OR REPLACE INTO equity_snapshots
                (session_id, timestamp, equity, cash, unrealized_pnl, position)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                point.session_id,
                point.timestamp,
                point.equity,
                point.cash,
                point.unrealized_pnl,
                point.position,
            ),
        )
        await self.db.commit()

    async def get_equity_history(self, session_id: str) -> list[PaperEquityPoint]:
        """Load equity history for a session, ordered by timestamp."""
        cursor = await self.db.execute(
            "SELECT * FROM equity_snapshots WHERE session_id = ? ORDER BY timestamp",
            (session_id,),
        )
        rows = await cursor.fetchall()
        return [
            PaperEquityPoint(
                session_id=row[0],
                timestamp=row[1],
                equity=row[2],
                cash=row[3],
                unrealized_pnl=row[4],
                position=row[5],
            )
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Order CRUD (live trading extension)
    # ------------------------------------------------------------------

    async def save_order(self, order: LiveOrder) -> None:
        """Insert a live order record."""
        await self.db.execute(
            """
            INSERT INTO orders (order_id, session_id, side, symbol, requested_amount,
                               filled_amount, fill_price, fee, status, created_at, filled_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(order_id) DO UPDATE SET
                filled_amount = excluded.filled_amount,
                fill_price = excluded.fill_price,
                fee = excluded.fee,
                status = excluded.status,
                filled_at = excluded.filled_at
            """,
            (
                order.order_id,
                order.session_id,
                order.side,
                order.symbol,
                order.requested_amount,
                order.filled_amount,
                order.fill_price,
                order.fee,
                order.status,
                order.created_at.isoformat(),
                order.filled_at.isoformat() if order.filled_at else None,
            ),
        )
        await self.db.commit()

    async def get_orders(self, session_id: str) -> list[LiveOrder]:
        """Load all orders for a session, ordered by created_at."""
        cursor = await self.db.execute(
            """SELECT order_id, session_id, side, symbol, requested_amount,
                      filled_amount, fill_price, fee, status, created_at, filled_at
               FROM orders WHERE session_id = ? ORDER BY created_at""",
            (session_id,),
        )
        rows = await cursor.fetchall()
        return [
            LiveOrder(
                order_id=row[0],
                session_id=row[1],
                side=row[2],
                symbol=row[3],
                requested_amount=row[4],
                filled_amount=row[5],
                fill_price=row[6],
                fee=row[7],
                status=row[8],
                created_at=datetime.fromisoformat(row[9]),
                filled_at=datetime.fromisoformat(row[10]) if row[10] else None,
            )
            for row in rows
        ]

    async def update_order_status(
        self,
        order_id: str,
        status: str,
        filled_amount: float | None = None,
        fill_price: float | None = None,
    ) -> None:
        """Update an order's status and optionally fill details."""
        if filled_amount is not None and fill_price is not None:
            await self.db.execute(
                """UPDATE orders SET status = ?, filled_amount = ?, fill_price = ?,
                   filled_at = ? WHERE order_id = ?""",
                (status, filled_amount, fill_price, datetime.now(UTC).isoformat(), order_id),
            )
        else:
            await self.db.execute(
                "UPDATE orders SET status = ? WHERE order_id = ?",
                (status, order_id),
            )
        await self.db.commit()
