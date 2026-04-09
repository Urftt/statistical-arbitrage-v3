"""backfill_ohlcv.py -- one-shot historical backfill of Bitvavo 1h OHLCV into Postgres.

Fetches every market where ``status == 'trading'`` on Bitvavo, paginates
backwards through all available hourly candles, and inserts into the ``ohlcv``
table with ``ON CONFLICT (symbol, timestamp) DO NOTHING`` (safe to re-run).

Usage::

    # one-time setup
    uv sync --extra postgres

    # backfill everything
    POSTGRES_PASSWORD=*** uv run --extra postgres python scripts/backfill_ohlcv.py

    # backfill a single market (fast smoke test)
    POSTGRES_PASSWORD=*** uv run --extra postgres \
        python scripts/backfill_ohlcv.py --pair BTC-EUR

Env vars:

- ``POSTGRES_PASSWORD``  (required)
- ``POSTGRES_HOST``      (default ``192.168.1.53``)
- ``POSTGRES_PORT``      (default ``5432``)
- ``POSTGRES_DB``        (default ``crypto``)
- ``POSTGRES_USER``      (default ``luc``)

Intentionally standalone: uses ``requests`` + ``psycopg2`` directly and does
NOT import from ``src/statistical_arbitrage/``. Polars is not used -- the data
flow is ``JSON -> list[tuple] -> execute_values``, no in-memory analytics
needed.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Make "from _ohlcv_common import ..." work when run as
# `python scripts/backfill_ohlcv.py` from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _ohlcv_common import (  # noqa: E402
    CANDLE_LIMIT,
    connect_db,
    ensure_table,
    fetch_candles_page,
    fetch_markets,
    insert_candles,
)

logger = logging.getLogger("backfill_ohlcv")


def backfill_market(conn, market: str) -> tuple[int, int]:
    """Paginate backwards through all 1h candles for ``market``.

    Starts at ``end=None`` (newest candles), then on each iteration rolls
    ``end_ms`` to ``oldest_ts - 1`` so the next page begins immediately
    before the oldest candle we already fetched. Stops when Bitvavo returns
    an empty page or a short page (length < ``CANDLE_LIMIT``), which both
    mean we have drained all available history.

    Args:
        conn: Open psycopg2 connection.
        market: Market symbol such as ``"BTC-EUR"``.

    Returns:
        ``(total_fetched, total_inserted)`` -- totals across all pages.
        Duplicates count as fetched but not inserted (ON CONFLICT skips them).
    """
    logger.info("backfilling %s ...", market)
    total_fetched = 0
    total_inserted = 0
    end_ms: int | None = None
    while True:
        page = fetch_candles_page(market, end_ms=end_ms, limit=CANDLE_LIMIT)
        if not page:
            break
        total_fetched += len(page)
        total_inserted += insert_candles(conn, market, page)
        # Candles are sorted DESC -- oldest is the last one in the list.
        oldest_ts = int(page[-1][0])
        logger.debug("%s: page of %d candles, oldest=%d", market, len(page), oldest_ts)
        if len(page) < CANDLE_LIMIT:
            break
        end_ms = oldest_ts - 1
    duplicates = total_fetched - total_inserted
    logger.info(
        "%s: fetched=%d inserted=%d (duplicates skipped=%d)",
        market,
        total_fetched,
        total_inserted,
        duplicates,
    )
    return total_fetched, total_inserted


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Backfill Bitvavo 1h OHLCV into Postgres.",
    )
    p.add_argument(
        "--pair",
        help=("Optional single market to backfill, e.g. BTC-EUR. Default: all trading markets."),
    )
    p.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    conn = connect_db()
    try:
        ensure_table(conn)
        if args.pair:
            markets = [args.pair]
        else:
            markets = fetch_markets()
            logger.info("found %d trading markets", len(markets))
        grand_fetched = 0
        grand_inserted = 0
        for i, market in enumerate(markets, start=1):
            logger.info("[%d/%d] %s", i, len(markets), market)
            try:
                fetched, inserted = backfill_market(conn, market)
            except Exception as exc:  # noqa: BLE001
                logger.exception("%s failed: %s -- continuing", market, exc)
                continue
            grand_fetched += fetched
            grand_inserted += inserted
        logger.info(
            "DONE. total fetched=%d inserted=%d across %d markets",
            grand_fetched,
            grand_inserted,
            len(markets),
        )
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
