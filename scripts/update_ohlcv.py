"""update_ohlcv.py -- hourly refresh for the Bitvavo 1h OHLCV Postgres table.

Fetches only the latest page of candles per trading market and upserts with
``ON CONFLICT (symbol, timestamp) DO NOTHING``. Designed to run from cron
every hour -- fast, minimal API calls, idempotent.

Usage::

    # one-time setup
    uv sync --extra postgres

    # run (e.g. from cron)
    POSTGRES_PASSWORD=*** uv run --extra postgres python scripts/update_ohlcv.py

Example crontab line::

    5 * * * * POSTGRES_PASSWORD=*** cd /path/to/repo && \\
        uv run --extra postgres python scripts/update_ohlcv.py \\
        >> /var/log/ohlcv.log 2>&1

Env vars mirror ``scripts/backfill_ohlcv.py``.

Intentionally standalone: uses ``requests`` + ``psycopg2`` directly and does
NOT import from ``src/statistical_arbitrage/``. Polars is not used.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Make "from _ohlcv_common import ..." work when run as
# `python scripts/update_ohlcv.py` from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _ohlcv_common import (  # noqa: E402
    connect_db,
    ensure_table,
    fetch_candles_page,
    fetch_markets,
    insert_candles,
)

logger = logging.getLogger("update_ohlcv")

# Fetch the last 168 candles (1 week of hourly data) per pair. Generous
# cushion for downtime: reboots, NAS maintenance, network outages, or a
# cron that silently misfires will all self-heal on the next run -- up to
# a full week of gap is recoverable without any manual intervention.
# Already-present candles hit ON CONFLICT and are skipped silently, so
# the steady-state cost is: first run fills the gap, subsequent runs
# insert only the new rows since the previous run.
#
# 168 is also well below Bitvavo's max-per-page (1440), so every market
# completes in a single API call -- no pagination required.
UPDATE_LIMIT = 168


def update_market(conn, market: str) -> int:
    """Pull the latest ``UPDATE_LIMIT`` candles for ``market`` and upsert.

    Returns:
        Number of new rows inserted (duplicates skipped by ON CONFLICT).
    """
    page = fetch_candles_page(market, end_ms=None, limit=UPDATE_LIMIT)
    inserted = insert_candles(conn, market, page)
    logger.info(
        "%s: fetched=%d inserted=%d",
        market,
        len(page),
        inserted,
    )
    return inserted


def main() -> int:
    logging.basicConfig(
        level="INFO",
        format="%(asctime)s %(levelname)s %(message)s",
    )
    conn = connect_db()
    try:
        ensure_table(conn)
        markets = fetch_markets()
        logger.info("updating %d markets", len(markets))
        total_inserted = 0
        for market in markets:
            try:
                total_inserted += update_market(conn, market)
            except Exception as exc:  # noqa: BLE001
                logger.exception("%s failed: %s -- continuing", market, exc)
                continue
        logger.info("DONE. total inserted=%d", total_inserted)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
