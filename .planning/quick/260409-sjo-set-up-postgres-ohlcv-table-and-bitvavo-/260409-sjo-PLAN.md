---
phase: 260409-sjo
plan: 01
type: execute
wave: 1
depends_on: []
quick: true
description: Set up Postgres OHLCV table and Bitvavo backfill script
files_modified:
  - pyproject.toml
  - scripts/_ohlcv_common.py
  - scripts/backfill_ohlcv.py
  - scripts/update_ohlcv.py
autonomous: false
requirements:
  - QUICK-260409-sjo
user_setup:
  - service: postgres
    why: "Scripts target the user's PostgreSQL 18 instance on Unraid (192.168.1.53:5432, database 'crypto', user 'luc'). Password is read from POSTGRES_PASSWORD env var at runtime."
    env_vars:
      - name: POSTGRES_PASSWORD
        source: "User's Unraid Postgres 'luc' role password (set in the shell that runs the scripts, e.g. export POSTGRES_PASSWORD=...)."
      - name: POSTGRES_HOST
        source: "Optional override. Defaults to 192.168.1.53."
      - name: POSTGRES_PORT
        source: "Optional override. Defaults to 5432."
      - name: POSTGRES_DB
        source: "Optional override. Defaults to crypto."
      - name: POSTGRES_USER
        source: "Optional override. Defaults to luc."
    dashboard_config:
      - task: "Verify network reachability from the dev machine to 192.168.1.53:5432 and that the 'luc' role owns or can CREATE on the 'crypto' database."
        location: "Unraid Postgres 18 container."

must_haves:
  truths:
    - "Running `POSTGRES_PASSWORD=*** uv run --extra postgres python scripts/backfill_ohlcv.py --pair BTC-EUR` creates the ohlcv table (if missing) and inserts hourly BTC-EUR candles into it"
    - "Running `POSTGRES_PASSWORD=*** uv run --extra postgres python scripts/backfill_ohlcv.py` iterates every Bitvavo market with status == 'trading' and backfills all available 1h candles per pair"
    - "Running `POSTGRES_PASSWORD=*** uv run --extra postgres python scripts/update_ohlcv.py` fetches only the latest candle(s) per pair and is idempotent (safe to re-run, no duplicates)"
    - "Re-running either script produces zero new rows for candles already stored (ON CONFLICT DO NOTHING)"
    - "Both scripts emit INFO log lines showing per-pair progress (market, candles fetched, candles inserted)"
    - "POSTGRES_PASSWORD is read from the environment; no password appears in source files"
    - "Existing src/statistical_arbitrage/data/ code is untouched (no imports from it, no edits)"
  artifacts:
    - path: "pyproject.toml"
      provides: "New [project.optional-dependencies] group 'postgres' with psycopg2-binary and requests"
      contains: "postgres ="
    - path: "scripts/_ohlcv_common.py"
      provides: "Shared helpers: connect_db, ensure_table, bitvavo_get, fetch_markets, fetch_candles_page, insert_candles"
      min_lines: 120
    - path: "scripts/backfill_ohlcv.py"
      provides: "Standalone backfill entry point; paginates backwards through all hourly candles for every trading market (or one, via --pair)"
      min_lines: 80
    - path: "scripts/update_ohlcv.py"
      provides: "Standalone hourly-update entry point; fetches only the latest candle(s) per pair, cron-friendly"
      min_lines: 40
  key_links:
    - from: "scripts/backfill_ohlcv.py"
      to: "scripts/_ohlcv_common.py"
      via: "from _ohlcv_common import connect_db, ensure_table, fetch_markets, fetch_candles_page, insert_candles"
      pattern: "from _ohlcv_common import"
    - from: "scripts/update_ohlcv.py"
      to: "scripts/_ohlcv_common.py"
      via: "from _ohlcv_common import connect_db, ensure_table, fetch_markets, fetch_candles_page, insert_candles"
      pattern: "from _ohlcv_common import"
    - from: "scripts/_ohlcv_common.py"
      to: "Bitvavo REST API"
      via: "requests.get('https://api.bitvavo.com/v2/...')"
      pattern: "api\\.bitvavo\\.com/v2"
    - from: "scripts/_ohlcv_common.py"
      to: "PostgreSQL ohlcv table"
      via: "psycopg2.extras.execute_values with ON CONFLICT (symbol, timestamp) DO NOTHING"
      pattern: "ON CONFLICT \\(symbol, timestamp\\) DO NOTHING"
---

<objective>
Add a Postgres-based hourly OHLCV storage layer that lives parallel to (and independent of) the existing parquet cache. Deliver two standalone, runnable scripts plus a tiny shared helper module:

1. `scripts/backfill_ohlcv.py` — one-shot backfill of all available 1h candles for every Bitvavo trading market into a `ohlcv` table on the user's Postgres 18 instance.
2. `scripts/update_ohlcv.py` — lightweight hourly cron job that pulls only the latest candle(s) per market.

Purpose: Give the user a local SQL copy of Bitvavo 1h OHLCV so follow-up research work can query without repeatedly hitting the Bitvavo REST API. This is a operational utility, NOT part of the core library — it must not touch `src/statistical_arbitrage/data/` and must not import from it.

Output: New `scripts/` directory with three Python files, a new `postgres` optional-dependencies group in `pyproject.toml`, and a populated `ohlcv` table on the target Postgres instance (verified manually by the user in the checkpoint).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@./CLAUDE.md
@pyproject.toml

<design_notes>
## Why standalone scripts (not library code)

The user explicitly asked for standalone scripts using `requests` + `psycopg2`, NOT CCXT + the parquet cache manager. This is an operational utility for one person on one machine. Keep it in `scripts/` at repo root so it is clearly separate from `src/statistical_arbitrage/` (which is the pure analysis library). Do NOT import from `src/statistical_arbitrage/data/` and do NOT touch those files.

## Dependencies

Add `requests` and `psycopg2-binary` as an optional dependency group so they do not bloat the default install. The scripts are run via `uv run --extra postgres python scripts/...`. Document this in each script's top docstring.

`psycopg2-binary` (not `psycopg2`) avoids needing local Postgres dev headers on macOS. `requests` is a stable, ubiquitous HTTP client — no SDK required.

## Database connection (env-configurable)

User-specified defaults, overridable via env vars so the scripts stay portable:

| Env var | Default |
|---|---|
| POSTGRES_HOST | 192.168.1.53 |
| POSTGRES_PORT | 5432 |
| POSTGRES_DB | crypto |
| POSTGRES_USER | luc |
| POSTGRES_PASSWORD | (required, no default — raise if missing) |

Read via `os.environ.get(...)`. No `python-dotenv` or `pydantic-settings` — keep it trivially standalone.

## Table schema

Exactly as the user specified. Embed a `CREATE TABLE IF NOT EXISTS` statement in `_ohlcv_common.ensure_table()` and call it from both scripts at startup so either script can bootstrap an empty database.

```sql
CREATE TABLE IF NOT EXISTS ohlcv (
    symbol      TEXT NOT NULL,
    timestamp   TIMESTAMPTZ NOT NULL,
    open        DOUBLE PRECISION,
    high        DOUBLE PRECISION,
    low         DOUBLE PRECISION,
    close       DOUBLE PRECISION,
    volume      DOUBLE PRECISION,
    PRIMARY KEY (symbol, timestamp)
);
```

Note: spacing for `low` is fixed relative to the user's copy (which had `low        DOUBLE` — one extra space). PK covers the idempotency requirement.

## Bitvavo REST API specifics

Base URL: `https://api.bitvavo.com/v2`

- `GET /v2/markets` — returns a list of dicts with fields including `market` (e.g. "BTC-EUR"), `status` ("trading", "halted", ...), `base`, `quote`. Filter to `status == "trading"`.
- `GET /v2/{market}/candles?interval=1h&limit=1440&end=<ms>` — returns an array of candles sorted descending by timestamp. Each candle is a 6-element array: `[timestamp_ms, open, high, low, close, volume]` where OHLCV values are strings. `limit` max is 1440.
- Pagination strategy: start with no `end`, get the newest 1440 candles. Take the oldest candle's timestamp `t_oldest` from that batch. Next request sets `end=t_oldest - 1` (subtract 1 ms to avoid re-fetching that exact candle). Loop until response is empty or length < limit (no more history). Stop.

## Rate limiting

Bitvavo uses a weight-based rate limit: 1000 weight/minute default for public endpoints. Each `/candles` call is weight 1. 10 req/sec (sleep 0.1s between calls) is well within limits.

Additionally, parse the response headers `Bitvavo-Ratelimit-Remaining` and `Bitvavo-Ratelimit-ResetAt` (ms epoch). If `remaining < 50`, sleep until `ResetAt + 1s`. Implement this in the shared `bitvavo_get()` helper so both scripts benefit.

## Timestamp handling

Bitvavo returns ms epoch integers. Convert to timezone-aware UTC datetimes for Postgres `TIMESTAMPTZ`:

```python
from datetime import datetime, timezone
ts = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
```

psycopg2 handles tz-aware datetimes natively — no extra adapter needed.

## Batch insert

Use `psycopg2.extras.execute_values` with `ON CONFLICT (symbol, timestamp) DO NOTHING`. Batch size ~1000 rows. This is idiomatic, fast, and idempotent.

## Polars

Not needed here. The data flow is `Bitvavo JSON -> list[tuple] -> execute_values`. No in-memory analytics. Per the user's "if needed" wording and the "keep it simple" directive, skip Polars entirely. Mention this in the top-of-file docstring so the next reader does not wonder why it is missing.

## CLI ergonomics

`backfill_ohlcv.py` supports an optional `--pair BTC-EUR` argument (using `argparse`) to backfill a single pair for dry-run/testing. Without it, backfills every market. `update_ohlcv.py` takes no arguments — it always updates every market (cron-friendly).

## Logging

Use stdlib `logging` at INFO level with format `"%(asctime)s %(levelname)s %(message)s"`. Log:
- startup: DB host / db name / user (never password)
- per market start: "backfilling BTC-EUR..."
- per page: DEBUG level, "fetched 1440 candles, oldest=2019-03-11T00:00:00Z"
- per market end: "BTC-EUR: 52318 candles fetched, 52318 inserted (0 duplicates)"
- final total at script end

## Shared helper vs duplication

User said "two standalone scripts". Interpret generously: duplicate the entry-point logic but share the truly common bits (DB connect, table DDL, HTTP wrapper, insert) in `scripts/_ohlcv_common.py`. Underscore prefix marks it as internal. Both scripts `from _ohlcv_common import ...`. Because `scripts/` is run directly (not as a package), add a short `sys.path` nudge if needed — but in practice `python scripts/backfill_ohlcv.py` runs with `scripts/` as cwd import root, so a plain `from _ohlcv_common import ...` works. Verify with the lint step.

## Ruff compliance

Ruff is already configured (line-length 100, rules E/F/I/W). Run `uv run ruff check scripts/` and `uv run ruff format scripts/` at the end of the implementation task.
</design_notes>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add postgres optional dependencies and create the shared _ohlcv_common.py helper</name>
  <files>pyproject.toml, scripts/_ohlcv_common.py</files>
  <action>
Step 1: Edit `pyproject.toml`. In the `[project.optional-dependencies]` table, add a new group AFTER the existing `dev = [...]` group:

```toml
postgres = [
    "psycopg2-binary>=2.9.9",
    "requests>=2.32.0",
]
```

Do not modify the `dev` group or any other existing section. Keep formatting consistent (4-space indent inside the list, trailing comma on last item). After editing, run `uv sync --extra postgres` from the repo root to install the new deps and update the lockfile. If `uv sync` fails, report the exact error — do NOT downgrade versions without checking with the user.

Step 2: Create `scripts/` directory at the repo root and add `scripts/_ohlcv_common.py`. This module holds all the shared primitives used by both backfill and update scripts.

Module contents (structure — fill in real bodies, do not leave stubs):

```python
"""
Shared helpers for the standalone OHLCV Postgres scripts.

Used by backfill_ohlcv.py and update_ohlcv.py. Provides:
- connect_db()          -- psycopg2 connection from POSTGRES_* env vars
- ensure_table(conn)    -- idempotent CREATE TABLE IF NOT EXISTS ohlcv
- bitvavo_get(path, params) -- HTTP GET with rate-limit awareness
- fetch_markets()       -- returns list[str] of markets with status == 'trading'
- fetch_candles_page(market, end_ms=None, limit=1440)
                        -- returns list of raw candle arrays (desc order)
- insert_candles(conn, market, candles) -> int
                        -- batch upsert via execute_values, returns rowcount

Run scripts with:
    uv sync --extra postgres
    POSTGRES_PASSWORD=*** uv run --extra postgres python scripts/backfill_ohlcv.py
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

import psycopg2
import psycopg2.extras
import requests

logger = logging.getLogger(__name__)

BITVAVO_BASE_URL = "https://api.bitvavo.com/v2"
CANDLE_LIMIT = 1440           # Bitvavo max for /candles
REQUEST_SLEEP_SEC = 0.1       # 10 req/sec floor
RATE_REMAINING_THRESHOLD = 50 # pause when remaining drops below this


# ---------------------------------------------------------------------------
# Postgres
# ---------------------------------------------------------------------------

def connect_db() -> psycopg2.extensions.connection:
    """Open a psycopg2 connection using POSTGRES_* env vars.

    Defaults match the user's Unraid instance. POSTGRES_PASSWORD is required
    and has no default -- raises RuntimeError if unset.
    """
    password = os.environ.get("POSTGRES_PASSWORD")
    if not password:
        raise RuntimeError(
            "POSTGRES_PASSWORD env var is required. "
            "Example: POSTGRES_PASSWORD=*** uv run --extra postgres python scripts/backfill_ohlcv.py"
        )
    host = os.environ.get("POSTGRES_HOST", "192.168.1.53")
    port = int(os.environ.get("POSTGRES_PORT", "5432"))
    dbname = os.environ.get("POSTGRES_DB", "crypto")
    user = os.environ.get("POSTGRES_USER", "luc")
    logger.info("connecting to postgres %s@%s:%s/%s", user, host, port, dbname)
    return psycopg2.connect(
        host=host, port=port, dbname=dbname, user=user, password=password
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


def ensure_table(conn) -> None:
    """Create the ohlcv table if it does not exist (idempotent)."""
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()


# ---------------------------------------------------------------------------
# Bitvavo REST
# ---------------------------------------------------------------------------

def bitvavo_get(path: str, params: dict[str, Any] | None = None) -> Any:
    """GET {BITVAVO_BASE_URL}{path} with gentle rate-limit handling.

    Honors Bitvavo-Ratelimit-Remaining / Bitvavo-Ratelimit-ResetAt headers:
    if remaining drops below RATE_REMAINING_THRESHOLD, sleep until the reset
    timestamp. Always sleeps REQUEST_SLEEP_SEC between calls.
    """
    url = f"{BITVAVO_BASE_URL}{path}"
    resp = requests.get(url, params=params or {}, timeout=30)
    resp.raise_for_status()
    remaining = resp.headers.get("Bitvavo-Ratelimit-Remaining")
    reset_at = resp.headers.get("Bitvavo-Ratelimit-ResetAt")
    if remaining is not None and reset_at is not None:
        try:
            remaining_i = int(remaining)
            reset_at_ms = int(reset_at)
            if remaining_i < RATE_REMAINING_THRESHOLD:
                sleep_ms = max(0, reset_at_ms - int(time.time() * 1000)) + 1000
                logger.info(
                    "rate limit low (remaining=%d), sleeping %.1fs until reset",
                    remaining_i, sleep_ms / 1000.0,
                )
                time.sleep(sleep_ms / 1000.0)
        except ValueError:
            pass
    time.sleep(REQUEST_SLEEP_SEC)
    return resp.json()


def fetch_markets() -> list[str]:
    """Return all Bitvavo market symbols currently in 'trading' status."""
    data = bitvavo_get("/markets")
    markets = [
        m["market"]
        for m in data
        if isinstance(m, dict) and m.get("status") == "trading"
    ]
    markets.sort()
    return markets


def fetch_candles_page(
    market: str, end_ms: int | None = None, limit: int = CANDLE_LIMIT
) -> list[list]:
    """Fetch one page of 1h candles for `market`.

    Candles come back sorted descending by timestamp. Each candle is
    [ts_ms, open, high, low, close, volume] with OHLCV values as strings.
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


def insert_candles(conn, market: str, candles: list[list]) -> int:
    """Batch upsert candles for `market`. Returns number of rows inserted
    (duplicates skipped via ON CONFLICT DO NOTHING)."""
    if not candles:
        return 0
    rows = [_candle_to_row(market, c) for c in candles]
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, INSERT_SQL, rows, page_size=1000)
        inserted = cur.rowcount
    conn.commit()
    return inserted
```

Notes on implementation discipline:
- Do NOT import from `src/statistical_arbitrage/` anywhere.
- Do NOT touch `config/settings.py` or anything in `src/`.
- Keep the module under ~200 lines total. Line length 100.
- Use `from __future__ import annotations` so `psycopg2.extensions.connection` works without string quoting.
- Match the existing repo docstring style (Google-ish, section separators using `# ---` lines).

Run `uv run ruff check scripts/_ohlcv_common.py` and `uv run ruff format scripts/_ohlcv_common.py` at the end. Fix any ruff errors before moving on.
  </action>
  <verify>
    <automated>test -f scripts/_ohlcv_common.py && grep -q "execute_values" scripts/_ohlcv_common.py && grep -q "ON CONFLICT (symbol, timestamp) DO NOTHING" scripts/_ohlcv_common.py && grep -q "postgres = \[" pyproject.toml && uv run ruff check scripts/_ohlcv_common.py</automated>
  </verify>
  <done>
pyproject.toml has a `postgres` optional-dependency group listing `psycopg2-binary` and `requests`; `uv sync --extra postgres` succeeded; `scripts/_ohlcv_common.py` exists and defines `connect_db`, `ensure_table`, `bitvavo_get`, `fetch_markets`, `fetch_candles_page`, and `insert_candles`; `ruff check` passes on the new file; no files inside `src/statistical_arbitrage/` were modified.
  </done>
</task>

<task type="auto">
  <name>Task 2: Implement scripts/backfill_ohlcv.py — full historical backfill entry point</name>
  <files>scripts/backfill_ohlcv.py</files>
  <action>
Create `scripts/backfill_ohlcv.py`. This is the one-shot backfill script: paginates backwards through all available 1h candles for every trading market on Bitvavo (or one, if `--pair` is given) and inserts them into the `ohlcv` Postgres table.

Required structure:

```python
"""
backfill_ohlcv.py -- one-shot historical backfill of Bitvavo 1h OHLCV into Postgres.

Fetches every market where status == 'trading' on Bitvavo, paginates backwards
through all available hourly candles, and inserts into the `ohlcv` table with
ON CONFLICT (symbol, timestamp) DO NOTHING (safe to re-run).

Usage:
    # one-time setup
    uv sync --extra postgres

    # backfill everything
    POSTGRES_PASSWORD=*** uv run --extra postgres python scripts/backfill_ohlcv.py

    # backfill a single market (for testing)
    POSTGRES_PASSWORD=*** uv run --extra postgres python scripts/backfill_ohlcv.py --pair BTC-EUR

Env vars:
    POSTGRES_PASSWORD  (required)
    POSTGRES_HOST      (default 192.168.1.53)
    POSTGRES_PORT      (default 5432)
    POSTGRES_DB        (default crypto)
    POSTGRES_USER      (default luc)

Intentionally standalone: uses requests + psycopg2 directly and does NOT import
from src/statistical_arbitrage/. Polars is not used -- the data flow is
JSON -> list[tuple] -> execute_values, no in-memory analytics needed.
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
    """Paginate backwards through all 1h candles for `market`.

    Returns (fetched, inserted). Stops when a page is empty or short.
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
        # Candles are sorted DESC -- oldest is the last one.
        oldest_ts = int(page[-1][0])
        logger.debug(
            "%s: page of %d candles, oldest=%d", market, len(page), oldest_ts
        )
        if len(page) < CANDLE_LIMIT:
            break
        end_ms = oldest_ts - 1
    logger.info(
        "%s: fetched=%d inserted=%d (duplicates skipped=%d)",
        market, total_fetched, total_inserted, total_fetched - total_inserted,
    )
    return total_fetched, total_inserted


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Backfill Bitvavo 1h OHLCV into Postgres.")
    p.add_argument(
        "--pair",
        help="Optional single market to backfill, e.g. BTC-EUR. Default: all trading markets.",
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
            grand_fetched, grand_inserted, len(markets),
        )
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Implementation notes:
- The `sys.path.insert(...)` dance is needed because `scripts/` is not a Python package and we want `python scripts/backfill_ohlcv.py` from the repo root to import `_ohlcv_common`. The `# noqa: E402` comment silences the "import not at top" ruff warning for the deliberately-placed import below the path tweak.
- Wrap each market in a try/except so one bad market (e.g. obscure altcoin with weird data) does not abort the whole run. Log and continue.
- Use `raise SystemExit(main())` rather than bare `main()` so the exit code reaches the shell cleanly for cron/scripting.
- Pagination loop invariant: each iteration sets `end_ms = oldest_ts_of_previous_page - 1`. Loop exits when either (a) page is empty or (b) page length < CANDLE_LIMIT (meaning we have drained the history).

After writing, run `uv run ruff check scripts/backfill_ohlcv.py` and `uv run ruff format scripts/backfill_ohlcv.py`.
  </action>
  <verify>
    <automated>test -f scripts/backfill_ohlcv.py && grep -q "backfill_market" scripts/backfill_ohlcv.py && grep -q "fetch_candles_page" scripts/backfill_ohlcv.py && grep -q 'raise SystemExit(main())' scripts/backfill_ohlcv.py && uv run ruff check scripts/backfill_ohlcv.py && uv run python -c "import ast; ast.parse(open('scripts/backfill_ohlcv.py').read())"</automated>
  </verify>
  <done>
`scripts/backfill_ohlcv.py` exists, passes ruff, parses cleanly under Python 3.12, imports helpers from `_ohlcv_common`, supports the `--pair` flag, and loops over every Bitvavo trading market paginating backwards until exhaustion. `ON CONFLICT DO NOTHING` semantics inherited from `insert_candles` make it safe to re-run.
  </done>
</task>

<task type="auto">
  <name>Task 3: Implement scripts/update_ohlcv.py — lightweight hourly update + human verification</name>
  <files>scripts/update_ohlcv.py</files>
  <action>
Create `scripts/update_ohlcv.py`. This is the lightweight cron script: for every trading market, pull only the latest page (one `fetch_candles_page` call with no `end` param) and upsert. Any already-present candles are silently skipped via `ON CONFLICT DO NOTHING`, so it is safe to run hourly (or more often) without duplicates.

```python
"""
update_ohlcv.py -- hourly refresh for the Bitvavo 1h OHLCV Postgres table.

Fetches only the latest page of candles per trading market and upserts with
ON CONFLICT (symbol, timestamp) DO NOTHING. Designed to run from cron every
hour -- fast, minimal API calls, idempotent.

Usage:
    # once
    uv sync --extra postgres

    # run (e.g. from cron)
    POSTGRES_PASSWORD=*** uv run --extra postgres python scripts/update_ohlcv.py

Example crontab line:
    5 * * * * POSTGRES_PASSWORD=*** cd /path/to/repo && \
        uv run --extra postgres python scripts/update_ohlcv.py >> /var/log/ohlcv.log 2>&1

Env vars mirror scripts/backfill_ohlcv.py.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _ohlcv_common import (  # noqa: E402
    connect_db,
    ensure_table,
    fetch_candles_page,
    fetch_markets,
    insert_candles,
)

logger = logging.getLogger("update_ohlcv")

UPDATE_LIMIT = 24  # fetch the last 24 candles per pair -- generous cushion
                   # vs. the once-per-hour cadence, so a missed run still heals.


def update_market(conn, market: str) -> int:
    page = fetch_candles_page(market, end_ms=None, limit=UPDATE_LIMIT)
    inserted = insert_candles(conn, market, page)
    logger.info(
        "%s: fetched=%d inserted=%d", market, len(page), inserted,
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
```

Implementation notes:
- `UPDATE_LIMIT = 24` gives a safety cushion: if the cron job misses a run (machine reboot, network blip, etc.), the next run still fills the gap up to 24 hours back. New candles are inserted, old ones hit `ON CONFLICT` and are skipped — no duplicates.
- Same per-market try/except pattern so a single bad market does not abort the whole update.
- No CLI args — keep the cron interface trivial.
- Same `sys.path` nudge as the backfill script so `_ohlcv_common` resolves.

Run `uv run ruff check scripts/` and `uv run ruff format scripts/` to cover all three files at once. Fix any warnings.

Final sanity: `uv run python -c "import ast; [ast.parse(open(p).read()) for p in ['scripts/_ohlcv_common.py','scripts/backfill_ohlcv.py','scripts/update_ohlcv.py']]"` should exit 0.
  </action>
  <verify>
    <automated>test -f scripts/update_ohlcv.py && grep -q "UPDATE_LIMIT" scripts/update_ohlcv.py && grep -q "fetch_candles_page" scripts/update_ohlcv.py && uv run ruff check scripts/ && uv run python -c "import ast; [ast.parse(open(p).read()) for p in ['scripts/_ohlcv_common.py','scripts/backfill_ohlcv.py','scripts/update_ohlcv.py']]"</automated>
  </verify>
  <done>
`scripts/update_ohlcv.py` exists, passes ruff, parses under Python 3.12, calls `fetch_candles_page(market, end_ms=None, limit=UPDATE_LIMIT)` per market, and upserts via `insert_candles`. All three scripts (`_ohlcv_common.py`, `backfill_ohlcv.py`, `update_ohlcv.py`) pass `uv run ruff check scripts/`.
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <name>Task 4: Human-verify end-to-end against the real Unraid Postgres</name>
  <files>scripts/_ohlcv_common.py, scripts/backfill_ohlcv.py, scripts/update_ohlcv.py</files>
  <action>PAUSE for human verification. Do not run the scripts against the real Postgres instance automatically -- the user owns the POSTGRES_PASSWORD secret and the network path to 192.168.1.53. Present the verification steps in &lt;how-to-verify&gt; and wait for an "approved" resume signal before marking the plan complete.</action>
  <verify>
    <automated>test -f scripts/_ohlcv_common.py && test -f scripts/backfill_ohlcv.py && test -f scripts/update_ohlcv.py</automated>
  </verify>
  <done>User ran the smoke test (`backfill_ohlcv.py --pair BTC-EUR`), confirmed the `ohlcv` table exists in the `crypto` database on 192.168.1.53 with BTC-EUR rows, verified idempotency on re-run, and typed "approved" in the resume signal.</done>
  <what-built>
Three files:
- `scripts/_ohlcv_common.py` -- shared DB + Bitvavo helpers
- `scripts/backfill_ohlcv.py` -- full historical backfill (all markets, or `--pair BTC-EUR`)
- `scripts/update_ohlcv.py` -- hourly cron update

Plus a new `postgres` optional-dependency group in `pyproject.toml` (psycopg2-binary + requests).

Claude has installed the deps, lint-checked the code, and confirmed the scripts parse cleanly, but has NOT run them against the real database -- that requires the POSTGRES_PASSWORD secret and network access to 192.168.1.53 which only the user has.
  </what-built>
  <how-to-verify>
1. Export the password in your shell:
   ```bash
   export POSTGRES_PASSWORD='<your-luc-role-password>'
   ```

2. Smoke test the backfill on ONE market first (fast, ~1-2 min):
   ```bash
   uv sync --extra postgres
   uv run --extra postgres python scripts/backfill_ohlcv.py --pair BTC-EUR
   ```
   Expected: log lines showing "connecting to postgres luc@192.168.1.53:5432/crypto",
   "backfilling BTC-EUR ...", a series of per-page DEBUG/INFO lines, and a final
   "BTC-EUR: fetched=N inserted=N" line where N is in the tens of thousands
   (Bitvavo BTC-EUR 1h data goes back to ~March 2019, so N should be ~50-60k).

3. Verify the table and row count in Postgres:
   ```bash
   psql -h 192.168.1.53 -U luc -d crypto -c \
     "SELECT symbol, COUNT(*), MIN(timestamp), MAX(timestamp) FROM ohlcv GROUP BY symbol;"
   ```
   Expected: one row for BTC-EUR with a count matching the script output and a
   MIN timestamp around 2019-03.

4. Idempotency check -- run the same command again:
   ```bash
   uv run --extra postgres python scripts/backfill_ohlcv.py --pair BTC-EUR
   ```
   Expected: logs show "fetched=N inserted=0 (duplicates skipped=N)" -- zero new
   rows, because ON CONFLICT DO NOTHING kicks in.

5. Test the hourly update path:
   ```bash
   uv run --extra postgres python scripts/update_ohlcv.py
   ```
   Expected: one "fetched=24 inserted=0..1" line per trading market, and a final
   "DONE. total inserted=X" summary. On first run right after the backfill, most
   markets will be 0 or 1 inserted; markets NOT in the backfill (because you only
   backfilled BTC-EUR) will insert up to 24 rows each.

6. OPTIONAL full backfill (can take 30-90 min depending on # of markets):
   ```bash
   uv run --extra postgres python scripts/backfill_ohlcv.py
   ```
   Let it run. Verify final totals look sane (hundreds of markets, millions of
   rows total).

If any step fails, capture the full error output (especially the first traceback)
and report back before approving.
  </how-to-verify>
  <resume-signal>Type "approved" if all verification steps passed, or paste the failing output if something went wrong.</resume-signal>
</task>

</tasks>

<verification>
Overall phase checks (after all tasks complete and human verification approves):

1. `ls scripts/` shows exactly: `_ohlcv_common.py`, `backfill_ohlcv.py`, `update_ohlcv.py`.
2. `uv run ruff check scripts/` exits 0.
3. `uv run python -c "import ast; [ast.parse(open(p).read()) for p in ['scripts/_ohlcv_common.py','scripts/backfill_ohlcv.py','scripts/update_ohlcv.py']]"` exits 0.
4. `grep -r "from statistical_arbitrage" scripts/` returns nothing (no imports from the core library).
5. `grep -r "import ccxt" scripts/` returns nothing (not reusing CCXT).
6. `git diff --stat src/statistical_arbitrage/data/` shows zero changes (existing data layer untouched).
7. `git diff --stat pyproject.toml` shows only the new `postgres` group added.
8. Human checkpoint (Task 4) confirmed the scripts work against the real Unraid Postgres: table created, BTC-EUR backfilled, idempotent on re-run, update script healthy.
</verification>

<success_criteria>
- pyproject.toml has a `postgres` optional-deps group with psycopg2-binary and requests, and `uv sync --extra postgres` succeeds.
- `scripts/_ohlcv_common.py`, `scripts/backfill_ohlcv.py`, `scripts/update_ohlcv.py` all exist, pass ruff, and parse cleanly under Python 3.12.
- Neither script imports from `src/statistical_arbitrage/` or from `ccxt`; both use `requests` for HTTP and `psycopg2` for DB as the user requested.
- `backfill_ohlcv.py --pair BTC-EUR` successfully creates the `ohlcv` table (if absent), paginates through all available history, and inserts ~50k+ rows on a fresh DB (human-verified).
- Re-running the backfill on the same data produces zero new inserts (idempotency confirmed via ON CONFLICT DO NOTHING).
- `update_ohlcv.py` runs without error against the populated DB, only pulling and inserting the most recent candles.
- POSTGRES_PASSWORD is read from env vars; no passwords are hardcoded anywhere in the scripts.
- Logging at INFO level reports per-market progress (fetched / inserted counts) and a final total.
- The existing parquet cache and Bitvavo CCXT client in `src/statistical_arbitrage/data/` are completely untouched.
</success_criteria>

<output>
After completion, create `.planning/quick/260409-sjo-set-up-postgres-ohlcv-table-and-bitvavo-/260409-sjo-SUMMARY.md` capturing: (1) what the three scripts do and how they are invoked, (2) the env var contract (`POSTGRES_*`), (3) the observed row counts / markets from the human-verification step, (4) the cron line the user is expected to add for `update_ohlcv.py`, and (5) an explicit note that the existing `src/statistical_arbitrage/data/` code was not modified (confirming the parallel-but-independent design).
</output>
