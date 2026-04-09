"""Shared helpers for the standalone OHLCV Postgres scripts.

Used by backfill_ohlcv.py and update_ohlcv.py. Provides:

- ``connect_db()`` -- psycopg2 connection from ``POSTGRES_*`` env vars.
- ``ensure_table(conn)`` -- idempotent ``CREATE TABLE IF NOT EXISTS ohlcv``.
- ``bitvavo_get(path, params)`` -- HTTP GET with rate-limit awareness.
- ``fetch_markets()`` -- list of market symbols with ``status == 'trading'``.
- ``fetch_candles_page(market, end_ms, limit)`` -- one page of raw 1h candles.
- ``insert_candles(conn, market, candles)`` -- batch upsert via ``execute_values``.

Run scripts with::

    uv sync --extra postgres
    POSTGRES_PASSWORD=*** uv run --extra postgres python scripts/backfill_ohlcv.py

Intentionally standalone: uses ``requests`` + ``psycopg2`` directly and does NOT
import from ``src/statistical_arbitrage/``. Polars is not used -- the data flow
is ``JSON -> list[tuple] -> execute_values`` with no in-memory analytics.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras
import requests
from dotenv import load_dotenv

# Load .env files before any env var lookups.
# Search order (first hit wins; real shell env always beats all of them):
#   1. <scripts_dir>/.env   -- standalone deployments (e.g. Unraid appdata)
#   2. <repo>/.env          -- dev setup, user's personal/local overrides
#   3. <repo>/config/.env   -- dev setup, project-standard shared secrets
_SCRIPTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPTS_DIR.parent
load_dotenv(_SCRIPTS_DIR / ".env")
load_dotenv(_REPO_ROOT / ".env")
load_dotenv(_REPO_ROOT / "config" / ".env")

logger = logging.getLogger(__name__)

BITVAVO_BASE_URL = "https://api.bitvavo.com/v2"
CANDLE_LIMIT = 1440  # Bitvavo max for /candles
REQUEST_SLEEP_SEC = 0.1  # 10 req/sec floor
RATE_REMAINING_THRESHOLD = 50  # pause when remaining drops below this
HTTP_TIMEOUT_SEC = 30


# ---------------------------------------------------------------------------
# Postgres
# ---------------------------------------------------------------------------


def connect_db() -> psycopg2.extensions.connection:
    """Open a psycopg2 connection using POSTGRES_* env vars.

    Defaults match the user's Unraid instance. ``POSTGRES_PASSWORD`` is
    required and has no default -- raises ``RuntimeError`` if unset.

    Returns:
        An open psycopg2 connection. The caller owns closing it.
    """
    password = os.environ.get("POSTGRES_PASSWORD")
    if not password:
        raise RuntimeError(
            "POSTGRES_PASSWORD env var is required. "
            "Example: POSTGRES_PASSWORD=*** uv run --extra postgres "
            "python scripts/backfill_ohlcv.py"
        )
    host = os.environ.get("POSTGRES_HOST", "192.168.1.53")
    port = int(os.environ.get("POSTGRES_PORT", "5432"))
    dbname = os.environ.get("POSTGRES_DB", "crypto")
    user = os.environ.get("POSTGRES_USER", "luc")
    logger.info("connecting to postgres %s@%s:%s/%s", user, host, port, dbname)
    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
    )


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ohlcv (
    symbol     TEXT NOT NULL,
    timestamp  TIMESTAMPTZ NOT NULL,
    open       DOUBLE PRECISION,
    high       DOUBLE PRECISION,
    low        DOUBLE PRECISION,
    close      DOUBLE PRECISION,
    volume     DOUBLE PRECISION,
    PRIMARY KEY (symbol, timestamp)
);
"""


def ensure_table(conn: psycopg2.extensions.connection) -> None:
    """Create the ohlcv table if it does not exist (idempotent)."""
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()


# ---------------------------------------------------------------------------
# Bitvavo REST
# ---------------------------------------------------------------------------


def bitvavo_get(path: str, params: dict[str, Any] | None = None) -> Any:
    """GET ``{BITVAVO_BASE_URL}{path}`` with gentle rate-limit handling.

    Honors Bitvavo's ``Bitvavo-Ratelimit-Remaining`` /
    ``Bitvavo-Ratelimit-ResetAt`` response headers: if remaining drops below
    ``RATE_REMAINING_THRESHOLD``, sleep until the reset timestamp (+1s buffer).
    Always sleeps ``REQUEST_SLEEP_SEC`` between calls as a gentle floor.

    Args:
        path: Path component appended to ``BITVAVO_BASE_URL`` (e.g. ``/markets``).
        params: Optional query-string dict.

    Returns:
        Parsed JSON payload (list or dict, per the endpoint).
    """
    url = f"{BITVAVO_BASE_URL}{path}"
    resp = requests.get(url, params=params or {}, timeout=HTTP_TIMEOUT_SEC)
    resp.raise_for_status()
    remaining = resp.headers.get("Bitvavo-Ratelimit-Remaining")
    reset_at = resp.headers.get("Bitvavo-Ratelimit-ResetAt")
    if remaining is not None and reset_at is not None:
        try:
            remaining_i = int(remaining)
            reset_at_ms = int(reset_at)
        except ValueError:
            remaining_i = None
            reset_at_ms = None
        if remaining_i is not None and remaining_i < RATE_REMAINING_THRESHOLD:
            sleep_ms = max(0, reset_at_ms - int(time.time() * 1000)) + 1000
            logger.info(
                "rate limit low (remaining=%d), sleeping %.1fs until reset",
                remaining_i,
                sleep_ms / 1000.0,
            )
            time.sleep(sleep_ms / 1000.0)
    time.sleep(REQUEST_SLEEP_SEC)
    return resp.json()


def fetch_markets() -> list[str]:
    """Return all Bitvavo market symbols currently in 'trading' status."""
    data = bitvavo_get("/markets")
    if not isinstance(data, list):
        raise RuntimeError(f"unexpected /markets response: {data!r}")
    markets = [m["market"] for m in data if isinstance(m, dict) and m.get("status") == "trading"]
    markets.sort()
    return markets


def fetch_candles_page(
    market: str,
    end_ms: int | None = None,
    limit: int = CANDLE_LIMIT,
) -> list[list]:
    """Fetch one page of 1h candles for ``market``.

    Candles are returned sorted descending by timestamp. Each candle is a
    six-element list ``[ts_ms, open, high, low, close, volume]`` where the
    OHLCV values are strings.

    Args:
        market: Market symbol such as ``"BTC-EUR"``.
        end_ms: Optional exclusive upper bound (epoch ms). Omit for the most
            recent candles.
        limit: Page size. Bitvavo max is ``CANDLE_LIMIT``.

    Returns:
        Raw list-of-lists candle data from the Bitvavo API.
    """
    params: dict[str, Any] = {"interval": "1h", "limit": limit}
    if end_ms is not None:
        params["end"] = end_ms
    data = bitvavo_get(f"/{market}/candles", params=params)
    if not isinstance(data, list):
        raise RuntimeError(f"unexpected candles response for {market}: {data!r}")
    return data


# ---------------------------------------------------------------------------
# Insert
# ---------------------------------------------------------------------------


def _candle_to_row(market: str, candle: list) -> tuple:
    """Convert a raw Bitvavo candle list to a typed insert tuple."""
    ts_ms = int(candle[0])
    ts = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    return (
        market,
        ts,
        float(candle[1]),
        float(candle[2]),
        float(candle[3]),
        float(candle[4]),
        float(candle[5]),
    )


INSERT_SQL = (
    "INSERT INTO ohlcv (symbol, timestamp, open, high, low, close, volume) "
    "VALUES %s ON CONFLICT (symbol, timestamp) DO NOTHING"
)


def insert_candles(
    conn: psycopg2.extensions.connection,
    market: str,
    candles: list[list],
) -> int:
    """Batch-upsert candles for ``market``.

    Uses ``psycopg2.extras.execute_values`` with
    ``ON CONFLICT (symbol, timestamp) DO NOTHING`` so the operation is
    idempotent: re-running on identical data produces zero new rows.

    Args:
        conn: Open psycopg2 connection.
        market: Market symbol (stored in the ``symbol`` column).
        candles: Raw Bitvavo candle lists (see ``fetch_candles_page``).

    Returns:
        Number of rows inserted (duplicates skipped via ON CONFLICT).
    """
    if not candles:
        return 0
    rows = [_candle_to_row(market, c) for c in candles]
    with conn.cursor() as cur:
        # page_size MUST be >= len(rows) so execute_values sends a single
        # internal batch; otherwise cur.rowcount only reflects the LAST
        # batch, under-counting inserts. Bitvavo's max candles/page is 1440.
        psycopg2.extras.execute_values(cur, INSERT_SQL, rows, page_size=max(len(rows), 2000))
        inserted = cur.rowcount
    conn.commit()
    return inserted
