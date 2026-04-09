---
phase: 260409-sjo
plan: 01
type: summary
status: complete
quick: true
description: Set up Postgres OHLCV table and Bitvavo backfill script
---

# Quick Task 260409-sjo — Summary

**Goal:** Add a Postgres-based hourly OHLCV storage layer parallel to the existing parquet cache, via two standalone scripts (`backfill_ohlcv.py` + `update_ohlcv.py`) plus a shared helper module. Source of candles: Bitvavo REST API (raw `requests`, not CCXT). Destination: user's PostgreSQL 18 instance on Unraid (`192.168.1.53:5432`, db `crypto`, user `luc`).

## Status

**All 4 tasks complete.** Backfill verified against the real Unraid Postgres instance, full historical data loaded, and a daily update cron is running on Unraid via the User Scripts plugin. See the "Resolution" section at the bottom for details.

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

---

## Resolution (2026-04-10)

### Verification and backfill

- Smoke test (`--pair BTC-EUR`) succeeded. Identified and fixed an `execute_values` counter bug: `cur.rowcount` under-counted inserts when Bitvavo's 1440-row page got split across multiple internal batches of `page_size=1000`. Fixed by sizing `page_size = max(len(rows), 2000)` so every call fits in a single batch. Data path was always correct; only the counter was wrong.
- Follow-on enhancements during verification:
  - Auto-load `.env` via python-dotenv so users don't have to export env vars.
  - Extended dotenv search path to include the scripts directory itself (for standalone deployments where scripts live outside a repo).
  - Bumped `UPDATE_LIMIT` from 24 to 168 (one week of hourly candles) — safety cushion for missed runs when the update runs daily.
- **Full historical backfill complete:** 1,898,402 rows across 441 Bitvavo trading markets, history back to 2019-03-08 for BTC-EUR, shorter for newer listings.

### Unraid daily cron (Task 4 follow-through)

- Files copied to `/mnt/user/appdata/ohlcv-updater/` on the Unraid host: `_ohlcv_common.py`, `update_ohlcv.py`.
- Scheduled via the User Scripts plugin, cron `0 0 * * *` (daily at midnight). Script body:
  ```bash
  docker run --rm \
    -v /mnt/user/appdata/ohlcv-updater:/scripts \
    -e POSTGRES_PASSWORD="<password>" \
    --network=host \
    python:3.12-slim \
    bash -lc "pip install --quiet psycopg2-binary requests python-dotenv && python /scripts/update_ohlcv.py"
  ```
  Each run: throwaway `python:3.12-slim` container, installs the three deps, runs `update_ohlcv.py`, upserts the last 168 hourly candles per market, exits. No Python runtime installed on the Unraid host itself.

### Debugging story (worth remembering)

The cron setup got stuck for a long session on `password authentication failed for user "luc"` — despite the same password authenticating successfully from the Mac with the same psycopg2 version. Root cause turned out to be **character fidelity**: the rotated password contained special characters (a single quote among them), and pasting it through the Unraid web terminal into nano (and into `pgpass` via shell expansion) was producing subtly wrong bytes. `wc -c` reported the expected length, but the actual bytes differed from what the user thought they were typing.

The fix was not to debug the transcription path but to **change the value at the authoritative source**: reset the password from inside the Postgres docker container on Unraid using `docker exec -e PGPASSWORD=... postgresql18 psql ... -c "ALTER USER luc WITH PASSWORD 'TempLucCrypto2026'"`. Once the password was a simple, paste-safe string, every layer of the pipeline started working.

**Lesson:** when a character-fidelity issue across paste/terminal/file/shell boundaries is suspected, don't debug the transcription chain — reset the value at its authoritative source to something unambiguous (pure alphanumeric). Passwords containing shell-meta characters (`'`, `$`, `#`, `!`, `"`) cost large amounts of time across layered pipelines and provide no security benefit over length.

### Remaining improvement (not blocking)

Password is currently hardcoded in the User Scripts body on Unraid. Follow-up: read it from `/mnt/user/appdata/ohlcv-updater/pgpass` (strip trailing newline safely) so the secret is out of the User Scripts UI. Safe to do now that the pipeline is proven working end-to-end.
