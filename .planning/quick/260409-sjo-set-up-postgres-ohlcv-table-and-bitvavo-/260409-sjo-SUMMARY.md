---
phase: 260409-sjo
plan: 01
type: summary
status: checkpoint-reached
quick: true
description: Set up Postgres OHLCV table and Bitvavo backfill script
---

# Quick Task 260409-sjo — Summary

**Goal:** Add a Postgres-based hourly OHLCV storage layer parallel to the existing parquet cache, via two standalone scripts (`backfill_ohlcv.py` + `update_ohlcv.py`) plus a shared helper module. Source of candles: Bitvavo REST API (raw `requests`, not CCXT). Destination: user's PostgreSQL 18 instance on Unraid (`192.168.1.53:5432`, db `crypto`, user `luc`).

## Status

**3 of 4 tasks complete.** Auto tasks done, committed, and merged into `main`. Task 4 is a `checkpoint:human-verify` — the user must run the scripts against their real Postgres server and confirm row counts / idempotency before the plan can be closed.

## Completed Tasks

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Add `postgres` optional deps + shared `_ohlcv_common.py` | `df1b3a9` | `pyproject.toml`, `uv.lock`, `scripts/_ohlcv_common.py` (234 lines) |
| 2 | Implement `backfill_ohlcv.py` | `cb480d4` | `scripts/backfill_ohlcv.py` (153 lines) |
| 3 | Implement `update_ohlcv.py` | `3de2947` | `scripts/update_ohlcv.py` (94 lines) |

All three commits are now on `main` (fast-forwarded from worktree `worktree-agent-a40936da`).

## Key Decisions (resolved during planning)

- **Script location:** `scripts/` at repo root — matches user's "standalone" instruction, not inside `src/statistical_arbitrage/`.
- **Deps:** New `[project.optional-dependencies] postgres` group (`psycopg2-binary>=2.9.9`, `requests>=2.32.0`). Install via `uv sync --extra postgres --extra dev`. Does not bloat the default install.
- **Env vars:** `POSTGRES_PASSWORD` required (no default). `POSTGRES_HOST/PORT/DB/USER` default to user-specified values but overridable.
- **Pagination:** Walks backwards via `end = oldest_ts_of_prev_page - 1`, stops on empty page or page size < 1440 (Bitvavo's max `limit`).
- **Rate limiting:** `time.sleep(0.1)` baseline (10 req/sec, well under Bitvavo's 1000 weight/min) plus adaptive sleep-until-reset when `Bitvavo-Ratelimit-Remaining` header drops below 50.
- **Batch insert:** `psycopg2.extras.execute_values` with `page_size=1000` + `ON CONFLICT (symbol, timestamp) DO NOTHING` — idempotent.
- **Timestamps:** Bitvavo ms-epoch → `datetime.fromtimestamp(ms/1000, tz=timezone.utc)` → psycopg2 writes as `TIMESTAMPTZ` natively.
- **Table DDL:** Embedded in `ensure_table()`, called from both entry points at startup — either script can bootstrap an empty database.
- **Shared helper:** Thin `scripts/_ohlcv_common.py` (underscore = internal). Entry points stay readable; `sys.path` nudge in each script so `from _ohlcv_common import ...` resolves without packaging.
- **Polars:** Not used — the data flow is `JSON → list[tuple] → execute_values`, no in-memory transforms needed. Noted in the helper's docstring.
- **Update cushion:** `UPDATE_LIMIT = 24` so a missed cron run self-heals up to 24h of gap.
- **Per-pair resilience:** Backfill wraps each market in try/except so one bad pair does not abort the whole run.
- **CLI:** `backfill_ohlcv.py --pair BTC-EUR` for smoke testing; `update_ohlcv.py` is argument-free (cron-friendly).

## Automated Verification (all passed during execution)

- `uv run ruff check scripts/` — clean
- `python -c "import ast; ..."` — all three scripts parse
- `grep -rn "from statistical_arbitrage" scripts/` — zero matches (scripts are fully decoupled)
- `grep -rn "import ccxt" scripts/` — zero matches
- `git diff --stat src/statistical_arbitrage/data/` — empty (existing data layer untouched)
- `scripts/_ohlcv_common.py` contains `execute_values` and `ON CONFLICT (symbol, timestamp) DO NOTHING`

## Checkpoint — What You Need To Do

The scripts have not been executed against your real Postgres yet (intentional — that's Task 4). To verify:

```bash
# 1. Install the postgres extra
uv sync --extra postgres --extra dev

# 2. Export your DB password
export POSTGRES_PASSWORD='<your-luc-role-password>'

# 3. Smoke test on one market (~1-2 min)
uv run --extra postgres python scripts/backfill_ohlcv.py --pair BTC-EUR

# 4. Confirm rows landed
psql -h 192.168.1.53 -U luc -d crypto -c \
  "SELECT symbol, COUNT(*), MIN(timestamp), MAX(timestamp) FROM ohlcv GROUP BY symbol;"

# 5. Idempotency — re-run the same command
uv run --extra postgres python scripts/backfill_ohlcv.py --pair BTC-EUR
# Expected: fetched=N, inserted=0 (duplicates skipped)

# 6. Hourly update path
uv run --extra postgres python scripts/update_ohlcv.py
```

Expected: BTC-EUR row count in the tens of thousands (~50-60k rows, history back to ~March 2019). Second run inserts 0 rows.

Once you have verified the smoke test, you can run the full backfill for all pairs:

```bash
uv run --extra postgres python scripts/backfill_ohlcv.py
```

Heads up: the full backfill will take a while (several hundred markets × thousands of candles each, throttled at ~10 req/sec).

## Issues Encountered

1. **Quick task directory existed only on main, not in the fresh worktree.** The executor copied the PLAN.md into the worktree before starting. No code impact.
2. **`uv sync --extra postgres` dropped the `dev` extras (ruff/pytest).** `uv sync` treats extras as an additive opt-in list; re-ran as `uv sync --extra postgres --extra dev` to restore lint tooling. Documented in the verification commands above.

## Files

- **Created:** `scripts/_ohlcv_common.py`, `scripts/backfill_ohlcv.py`, `scripts/update_ohlcv.py`
- **Modified:** `pyproject.toml` (new `postgres` optional-deps group), `uv.lock`
- **Untouched:** `src/statistical_arbitrage/data/` — existing CCXT + parquet cache left fully alone per user instruction
