---
phase: 06-scanner-enhancements
reviewed: 2026-04-07T00:00:00Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - api/main.py
  - api/routers/scanner.py
  - api/schemas.py
  - frontend/src/app/(dashboard)/scanner/page.tsx
  - frontend/src/lib/api.ts
  - src/statistical_arbitrage/data/cache_manager.py
  - tests/test_scanner_api.py
findings:
  critical: 0
  warning: 5
  info: 7
  total: 12
status: issues_found
---

# Phase 6: Code Review Report

**Reviewed:** 2026-04-07
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found

## Summary

Phase 6 rewrites the scanner API (renamed from `academy_scan`), adds an honest
`cached_coin_count` / `dropped_for_completeness` reporting model, fixes the
timeframe-aware completeness formula (Pitfall 3 / D-29), and adds CoinGecko-based
market-cap ranking in `DataCacheManager.get_available_pairs()`. The frontend gets
a 590-line rewrite with Suspense, URL-driven timeframe state, two sortable
sections, and an auto-fetch-on-empty-cache flow.

Overall the code is clean, well-commented, and the explicit references to
decisions (D-XX) and pitfalls in the source make intent easy to verify against
the plans. **No critical issues** were found — the timeframe-aware completeness
formula is correct (no division-by-zero, the `max(..., 1)` guard handles the
single-candle edge case), there are no XSS sinks in the React rewrite, and no
hardcoded secrets or injection vectors anywhere.

The findings below are mostly about silent failure modes that erode the very
"honest reporting" the phase set out to deliver: coins under 100 candles are
silently dropped without surfacing in `dropped_for_completeness`, the CoinGecko
fallback has zero observability, and the alert math `cached_count - dropped`
won't add up to `2 * scanned^(1/2)` whenever any coin is silently filtered. Two
warnings concern frontend hook hygiene (a stale-closure-suppressed effect and an
ESLint comment that hides a real dependency).

## Warnings

### WR-01: Honest reporting incomplete — coins under 100 candles silently dropped

**File:** `api/routers/scanner.py:165-167`
**Issue:** The scanner logs the new D-18 promise as "no more silent drops," but
the loop has two exit paths and only ONE of them is reported. Coins where
`len(df) < 100` are skipped via `continue` without being added to
`dropped_for_completeness` and without being logged. This breaks the math the
frontend alert presents to the user:

```
"Scanned {scanResponse.scanned} pairs from {cachedCount} cached coins.
 Excluded {dropped.length} coins for incomplete data"
```

If 32 coins are cached, 4 are too short (silently dropped), and 28 are tested,
the alert reads "Scanned 378 pairs from 32 cached coins. Excluded 0 coins" —
but C(32, 2) = 496, not 378. The user sees an unexplained gap of 118 pairs.

**Fix:** Either include too-short coins in `dropped_for_completeness` (with a
note in the response or a separate `dropped_too_short` array), or — at minimum
— surface a single counter so the math reconciles:

```python
dropped_too_short: list[str] = []
# ...
if len(df) < 100:
    dropped_too_short.append(symbol)
    continue
```

Then return both lists, and update the frontend alert to display the breakdown.
Alternatively, fold "too short" into the same dropped list with a structured
reason: `dropped_for_completeness: list[{symbol: str, reason: str}]`.

---

### WR-02: CoinGecko fallback has no observability

**File:** `src/statistical_arbitrage/data/cache_manager.py:327-329`
**Issue:** The `except Exception` for the CoinGecko request silently drops every
failure mode (network outage, timeout, HTTP error, malformed JSON, rate limit).
There is no `logger.warning(...)` and there is no module logger at all in
`cache_manager.py`. When CoinGecko goes down or rate-limits us, the ranking
silently degrades to quote-volume-only — which can change the "top 20 coins" the
fetch endpoint pulls without any user-facing signal that the market-cap ranking
just disappeared.

This is the same class of "silent failure" the phase explicitly set out to
eliminate elsewhere (D-18, dropped_for_completeness).

**Fix:** Add a module logger and emit a warning on the fallback path. Also
narrow the catch so genuinely unexpected programming errors (e.g., a typo in
`row.get`) don't get hidden:

```python
import logging
import urllib.error

logger = logging.getLogger(__name__)
# ...
try:
    # ... existing request ...
    for row in coingecko_rows:
        # ...
except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
    logger.warning(
        "CoinGecko market-cap fetch failed (%s) — falling back to "
        "quote_volume-only ranking", exc
    )
    market_cap_by_base = {}
```

`ValueError` covers `json.JSONDecodeError`. `urllib.error.HTTPError` is a
subclass of `URLError`, so it's covered.

---

### WR-03: `pl.DataFrame(pairs).sort(...)` raises on empty input

**File:** `src/statistical_arbitrage/data/cache_manager.py:347-349`
**Issue:** If `pairs` is an empty list (e.g., Bitvavo returns no EUR markets, or
the markets dict is filtered to zero entries by `info.get("quote") != "EUR"`),
`pl.DataFrame([])` produces a frame with no columns, and `.sort(["market_cap",
"quote_volume"], ...)` raises `ColumnNotFoundError`. The caller in
`scanner.fetch_live_data` then propagates this as a 500 with a confusing
traceback rather than an empty fetch result.

This is unlikely in practice (Bitvavo always has dozens of EUR pairs) but the
defensive cost is one line.

**Fix:**
```python
if not pairs:
    return pl.DataFrame(
        schema={
            "symbol": pl.Utf8, "base": pl.Utf8, "quote": pl.Utf8,
            "market_cap": pl.Float64, "quote_volume": pl.Float64,
        }
    )
return pl.DataFrame(pairs).sort(
    ["market_cap", "quote_volume"], descending=[True, True]
)
```

---

### WR-04: `useEffect` ESLint suppression hides real dependencies

**File:** `frontend/src/app/(dashboard)/scanner/page.tsx:362-377`
**Issue:** The auto-fetch effect lists only `[timeframe]` as a dependency and
suppresses `react-hooks/exhaustive-deps` to silence the linter. The actual
closure captures `refreshCacheState`, `handleFetchData`, and `fetching`. Of
these:

1. `refreshCacheState` and `handleFetchData` are stable per timeframe (both
   `useCallback`-wrapped with `[timeframe]` in their deps), so excluding them
   is functionally equivalent. OK.
2. **`fetching` is the problem.** The effect reads `fetching` to gate the
   auto-fetch (`if (count === 0 && !fetching)`), but because `fetching` is
   excluded from deps, the effect captures whatever value `fetching` had on the
   most recent timeframe-change render. If a fetch is in flight when the
   timeframe changes, the effect re-runs and reads the new `fetching`-from-the-
   render-snapshot value, which may already be `true` from `setFetching(true)`
   inside `handleFetchData` from a previous run — but since the effect only
   re-runs on `timeframe` change, the captured value is whatever React rendered
   most recently. In the typical flow this is fine, but the suppression hides
   the reasoning.

More importantly: if a user rapidly toggles 1h → 4h → 1h while a fetch is in
flight, two parallel auto-fetches can race, and the loser's `setCachedCoinCount`
will overwrite the winner's. The `cancelled` flag inside the IIFE only protects
against in-effect set-state after unmount, not against the parallel
`refreshCacheState` calls.

**Fix:** Use a ref to track in-flight fetches and gate on it explicitly, or
debounce timeframe changes:

```typescript
const fetchInFlightRef = useRef(false);

useEffect(() => {
  let cancelled = false;
  (async () => {
    const count = await refreshCacheState();
    if (cancelled || fetchInFlightRef.current) return;
    if (count === 0) {
      fetchInFlightRef.current = true;
      try {
        await handleFetchData();
      } finally {
        fetchInFlightRef.current = false;
      }
    }
  })();
  return () => { cancelled = true; };
}, [timeframe, refreshCacheState, handleFetchData]);
```

This also lets you drop the eslint-disable comment.

---

### WR-05: `useEffect` reset of section sort uses `set-state-in-effect` anti-pattern

**File:** `frontend/src/app/(dashboard)/scanner/page.tsx:193-195`
**Issue:** The `ScannerSection` resets its `sort` state via a `useEffect`
triggered when `pairs` changes, with an inline ESLint suppression
(`react-hooks/set-state-in-effect`). This causes a double render on every new
scan — first the table renders with the previous sort applied to the new pairs
array, then the effect fires and resets to `NO_SORT`, triggering a second
render. For 100+ pairs this is a visible flicker.

The cleaner pattern is to derive the sort state from the parent (lift the
`sort` state to `ScannerContent` and reset it when `scanResponse` changes via
the same code path that calls `setScanResponse`), or to use a `key` prop on
`ScannerSection` so React unmounts/remounts the component (and therefore resets
its internal state) when pairs identity changes:

```tsx
<ScannerSection
  key={`coint-${scanResponse?.timeframe}-${scanResponse?.scanned}`}
  ...
/>
```

The `key` approach is the idiomatic React way to "reset state when input
changes" and avoids both the lint suppression and the double render.

**Fix:** Use a `key` prop on each `ScannerSection` based on the scan identity,
and remove the `useEffect`/`useState` reset pair entirely. Two-state-per-render
becomes one.

---

## Info

### IN-01: Scan-cache TTL has no eviction — entries linger forever after timeframe drop

**File:** `api/routers/scanner.py:24-27`
**Issue:** `_scan_cache` and `_scan_cache_ts` are module-level dicts with a
5-minute TTL check on read, but no entries are ever removed except by
`_scan_cache.clear()` in `fetch_live_data`. For the bounded set of timeframes
(1h, 4h, 1d, plus a few days_back values) this is fine — at most ~30 entries —
but a documentation note explaining the bounded key space would prevent a
future contributor from worrying about an unbounded leak.

**Fix:** Add a comment near the cache definition:

```python
# Bounded by (timeframe, days_back) cardinality — ~30 keys max in practice.
# Entries past their TTL are recomputed on next access; eviction is not needed.
_scan_cache: dict[str, dict] = {}
```

---

### IN-02: Scan cache stores plain dict; FastAPI re-validates on every cache hit

**File:** `api/routers/scanner.py:118-148, 246-248`
**Issue:** The cache returns the raw `dict` (not a `ScanResponse` instance), and
because the route declares `response_model=ScanResponse`, FastAPI runs Pydantic
validation on every cache hit. For a scan with 500+ pairs this costs ~10-50ms
of CPU per cached call — small, but the cache becomes less of a "cache" than
intended.

**Fix:** Either store a pre-validated `ScanResponse` (and add `response_model`
exclusion via `response_model_exclude_none=False`), or store the JSON string
and serve it directly via a `Response(content=..., media_type="application/json")`.
The latter is what most "expensive endpoint" caches do. Not urgent.

---

### IN-03: `_scan_cache` shared globally — single asyncio loop is fine, thread-pool deployment is not

**File:** `api/routers/scanner.py:25-26`
**Issue:** Two module-level dicts shared across all requests. Under uvicorn's
default single-worker async deployment this is safe (sync def routes run on the
threadpool, but `_scan_cache.clear()` and `dict.__setitem__` are atomic in
CPython under the GIL). If anyone later switches to gunicorn with multiple
workers, each worker has its own copy and the cache becomes inconsistent.

**Fix:** Add a comment noting "single-process only — switch to redis for
multi-worker deployments." No code change needed today.

---

### IN-04: `_fresh = true` parameter signature documents an unused parameter

**File:** `frontend/src/lib/api.ts:890-896`
**Issue:** The backwards-compat alias `fetchAcademyScan` accepts `_fresh = true`
to preserve the old call signature. The leading underscore is the right
convention to mark "intentionally unused", but TypeScript's `noUnusedParameters`
doesn't honor that prefix (it's a Python convention). If/when strict mode is
tightened, this will produce a warning. Consider renaming to a destructured
unused or simply dropping the parameter and updating callers in the same PR.

**Fix:** Either drop the parameter (it's documented as ignored) or add a
`/* eslint-disable @typescript-eslint/no-unused-vars */` directive. Search for
`fetchAcademyScan(` callers — if all of them already pass two args, the third
positional is undefined and removable.

---

### IN-05: `numpy_to_python` only converts top-level fields; nested dicts in `coint` are re-wrapped redundantly

**File:** `api/routers/scanner.py:212-228`
**Issue:** The scanner calls `numpy_to_python` three times on three independent
dicts and then constructs a new dict with cherry-picked keys. This works, but
each call to `numpy_to_python` walks the full subtree. For a 500-pair scan
that's 1500 walks. A cheaper pattern is to construct the final pair-row dict
first and call `numpy_to_python` on it once.

**Fix:** Defer the conversion to a single call after constructing the row, or
to a single call after building `results`. Performance is not in v1 scope, but
this is also a clarity improvement.

---

### IN-06: `print()` in `cache_manager.get_candles` should be `logger.info`

**File:** `src/statistical_arbitrage/data/cache_manager.py:247, 263, 370, 375`
**Issue:** Several `print()` calls remain in the cache manager for fetch and
write events (and `bulk_download` uses emoji-prefixed prints). These predate
Phase 6, but they leak into the FastAPI access log without a logger prefix and
can't be filtered by level. The phase touched this file (added
`get_available_pairs`) without converting to logging, so it's a logical place
to call out the inconsistency — `cache_manager.py` has zero `logger` usage.

**Fix:** Add `logger = logging.getLogger(__name__)` at the top of the module
and replace `print()` with `logger.info()` / `logger.warning()`. Pre-existing
issue but related to WR-02 (which proposes adding the logger anyway).

---

### IN-07: Test `test_one_day_timeframe_returns_non_empty` is the only meaningful regression test for the Pitfall-3 fix, but it skips on a cold cache

**File:** `tests/test_scanner_api.py:125-145`
**Issue:** This is the test that locks in the timeframe-aware completeness
fix, but it skips when `cached_coin_count < 2`, which is exactly the state of
a fresh CI checkout. Net result: in CI the regression test never runs and the
fix could silently regress.

The unit-level invariant the test wants to assert ("the formula
`expected = max(span_ms / timeframe_ms, 1)` produces non-zero completeness for
1d data") can be tested directly without a TestClient call by extracting the
formula into a small pure function and unit-testing it with a synthetic Polars
DataFrame:

```python
def _completeness(df: pl.DataFrame, timeframe_ms: int) -> float:
    ts = df["timestamp"].sort().to_list()
    span_ms = ts[-1] - ts[0]
    expected = max(int(span_ms / timeframe_ms), 1)
    return len(df) / expected
```

Then test that `_completeness(synthetic_1d_df, 86_400_000) >= 0.9`. This runs
on every CI invocation and catches the original bug.

**Fix:** Extract the formula and add a pure unit test alongside the integration
test. The integration test stays as a smoke check.

---

## Notes

- **Timeframe-aware completeness formula (the centerpiece fix):** Verified at
  `api/routers/scanner.py:159-172`. The lookup
  `DataCacheManager.TIMEFRAME_MS.get(timeframe, 3_600_000)` defaults to 1h
  (not zero) so there is no division-by-zero risk. The `max(int(span_ms /
  timeframe_ms), 1)` guard handles the degenerate single-candle case
  (`span_ms == 0`). The formula is correct.

- **`cached_coin_count` honesty (D-18):** Verified at `scanner.py:135` —
  computed BEFORE any filtering, so it reports the real cache size. The
  `max_pairs` truncation is gone. Good.

- **CoinGecko URL safety:** The URL is hardcoded with no user input
  interpolation, so there is zero injection risk. The `User-Agent` header is
  also hardcoded. URL construction is safe.

- **XSS / `dangerouslySetInnerHTML`:** None present in the scanner page
  rewrite. All user-facing strings flow through Mantine `<Text>` components
  which escape by default. The `dropped.join(', ')` pattern is safe — Mantine
  handles the rendering.

- **React hooks rules:** All hooks (`useState`, `useEffect`, `useCallback`,
  `useMemo`) are called unconditionally at the top of the component bodies.
  No conditional hook calls. Compliance: clean.

- **Test isolation:** The integration tests share a process-wide singleton
  `_cache_manager` and module-level `_scan_cache`. Tests run in module-load
  order, so `test_one_day_timeframe_returns_non_empty` may be polluted by
  earlier `test_new_scanner_fetch_endpoint_exists` writing to the cache. In
  practice this only affects local runs where Bitvavo is reachable; in CI
  both tests skip cleanly. Acceptable.

- **`fetchAcademyScan` backward-compat alias:** Reasonable temporary bridge.
  Add a TODO/issue to remove it once `AcademyDataContext.tsx` migrates to
  `fetchScan`.

---

_Reviewed: 2026-04-07_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
