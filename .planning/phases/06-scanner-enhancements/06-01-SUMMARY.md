---
phase: 06-scanner-enhancements
plan: "01"
subsystem: backend-api, frontend-client
tags: [scanner, cointegration, api-rename, completeness-fix, typescript]
dependency_graph:
  requires: []
  provides: [scanner-api, scan-response-types]
  affects: [academy-data-context, frontend-scanner-page]
tech_stack:
  added: []
  patterns: [timeframe-aware-completeness, backwards-compat-alias]
key_files:
  created:
    - api/routers/scanner.py
    - tests/test_scanner_api.py
  modified:
    - api/schemas.py
    - api/main.py
    - frontend/src/lib/api.ts
  deleted:
    - api/routers/academy_scan.py
decisions:
  - "D-16: Renamed /api/academy/scan -> /api/scanner/scan and deleted academy_scan.py"
  - "D-17: Removed fresh and coins[] params from scanner endpoint"
  - "D-18: Added cached_coin_count and dropped_for_completeness to ScanResponse"
  - "D-21: Preserved in-memory scan cache with 5-minute TTL in scanner.py"
  - "D-23: Preserved 90% completeness threshold"
  - "D-29: Fixed timeframe-aware completeness formula (1d no longer always-zero)"
  - "Backwards-compat alias: fetchAcademyScan delegates to fetchScan, AcademyScanPair/AcademyScanResponse are type aliases"
metrics:
  duration: "~20 minutes"
  completed: "2026-04-07"
  tasks_completed: 5
  files_changed: 6
---

# Phase 6 Plan 01: Scanner Backend Rename and Completeness Fix Summary

Renamed the scanner backend from `academy_scan.py` to `scanner.py`, fixed a timeframe-blind completeness bug that caused all 1d scans to return zero results, exposed dropped-for-completeness coins and cached coin count in the response, and atomically updated the TypeScript client and AcademyDataContext so the Academy keeps working without code changes.

## What Was Built

### Backend: api/routers/scanner.py (renamed from academy_scan.py)

- New `/api/scanner` prefix replacing the old `/api/academy` prefix (D-16)
- `GET /api/scanner/scan` — scans cached pairs for cointegration
- `POST /api/scanner/fetch` — fetches fresh OHLCV from Bitvavo
- Fixed completeness formula bug (D-29 / Pitfall 3): `expected_candles = max(int(span_ms / timeframe_ms), 1)` now uses `DataCacheManager.TIMEFRAME_MS` to compute the correct expected candle count per timeframe. The old formula hardcoded `3_600_000` (1h) which made 1d data appear ~4% complete and silently dropped all coins.
- Removed `fresh` and `coins[]` query params (D-17)
- Added `cached_coin_count` (coins in cache before filtering) and `dropped_for_completeness` (coins excluded by 90% completeness check) to every scan response (D-18)
- Preserved in-memory scan cache with 5-minute TTL (D-21)
- Preserved 90% completeness threshold (D-23)

### Backend: api/schemas.py

Added two new Pydantic models:
- `ScanPair` — single pair result with all cointegration fields
- `ScanResponse` — full scan response with `cached_coin_count` and `dropped_for_completeness` fields

### Backend: api/main.py

- Replaced `from api.routers import academy_scan` with `scanner` (alphabetically sorted)
- Replaced `application.include_router(academy_scan.router)` with `scanner.router`
- App now serves `/api/scanner/scan` and `/api/scanner/fetch`; `/api/academy/scan` returns 404

### Tests: tests/test_scanner_api.py

Wave 0 test scaffold covering:
- `TestScannerEndpoints` — D-16: new endpoint exists, old returns 404
- `TestScannerScanResponse` — D-18: response shape, pair categorization
- `TestRemovedParameters` — D-17: fresh and coins[] not in function signature
- `TestCompletenessFormula` — D-29: 1d timeframe returns non-empty when cache data exists

Result: 10 passed, 1 skipped (test_pair_row_has_all_columns skipped because the 1h cache had no data available in the test environment — not a failure)

### Frontend: frontend/src/lib/api.ts

- New `ScanPair` and `ScanResponse` TypeScript interfaces with all D-18 fields
- New `fetchScan()` function targeting `/api/scanner/scan`
- `fetchAcademyScan()` kept as backwards-compat wrapper (delegates to fetchScan, ignores `_fresh` argument)
- `AcademyScanPair` and `AcademyScanResponse` kept as type aliases for `ScanPair`/`ScanResponse`
- `fetchLiveData()` URL updated from `/api/academy/fetch` to `/api/scanner/fetch`
- All `/api/academy/` URL references removed from api.ts

### Frontend: frontend/src/contexts/AcademyDataContext.tsx

No changes needed. The backwards-compat alias covers the `fetchAcademyScan('1h', 90, true)` call site.

## Decisions Implemented

| Decision | Implementation |
|----------|---------------|
| D-16 | Renamed file and changed APIRouter prefix to /api/scanner |
| D-17 | Removed `fresh: bool = Query(...)` and `coins` params from scan_pairs() |
| D-18 | Added cached_coin_count and dropped_for_completeness to ScanResponse |
| D-21 | Preserved _scan_cache dict with SCAN_CACHE_TTL=300 |
| D-23 | min_completeness = 0.90 preserved |
| D-29 | Fixed: `timeframe_ms = DataCacheManager.TIMEFRAME_MS.get(timeframe, 3_600_000)` then `expected_candles = max(int(span_ms / timeframe_ms), 1)` |

## Deviations from Plan

**1. [Rule 2 - Missing critical functionality] Import style: used `statistical_arbitrage.*` not `src.statistical_arbitrage.*`**
- Found during: Task 1
- Issue: The plan's code template used `from src.statistical_arbitrage...` prefix but the worktree's venv installs the package at `statistical_arbitrage.*` directly via a `.pth` file.
- Fix: Used `from statistical_arbitrage...` (without `src.` prefix) in `scanner.py` - the same pattern the rest of the codebase uses.
- Files modified: api/routers/scanner.py

**2. [Rule 1 - Bug] Worktree missing data/ module and data symlink**
- Found during: Task 0 test collection
- Issue: The worktree was created from a git commit that did not have `src/statistical_arbitrage/data/` tracked (it's an untracked working-tree file in the main repo). Tests couldn't import `cache_manager`.
- Fix: Copied `data/` module from main repo to worktree `src/statistical_arbitrage/data/`, created symlink `data -> /main-repo/data` so cached parquet files are shared.
- This is infrastructure setup, not a code deviation.

**3. Pre-existing lint issues**
- `api/schemas.py` had 4 pre-existing E501 (line-too-long) errors not caused by this plan's changes. Fixed 1 I001 (import sort) that ruff auto-fixed.
- `frontend/` lint has 6 pre-existing errors in `Lesson1_3.tsx`, `pair-analysis/page.tsx` — none in files modified by this plan. My changes added 1 warning (`_fresh` unused, intentional).

## Known Limitation: Academy Cold-Cache Behavior

Removing `fresh=true` (D-17) means the Academy lesson page no longer auto-fetches data when called with a cold cache. Previously `fetchAcademyScan(fresh=true)` triggered a Bitvavo fetch before scanning. Now `fetchAcademyScan` delegates to `fetchScan` which reads from cache only.

**Acceptance rationale (Pitfall 4):** The scanner page (Plan 06-02) will auto-fetch on empty cache, so the Academy will see warm data once any user has visited the scanner first. Documented for Plan 06-02 awareness.

## New API Surface

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scanner/scan` | GET | Scan cached pairs for cointegration |
| `/api/scanner/fetch` | POST | Fetch fresh OHLCV from Bitvavo |

### Public TypeScript Types

```typescript
export interface ScanPair { ... }          // Primary type
export interface ScanResponse { ... }      // Primary type
export type AcademyScanPair = ScanPair;    // Backwards-compat alias
export type AcademyScanResponse = ScanResponse; // Backwards-compat alias
export async function fetchScan(...)       // Primary function
export async function fetchAcademyScan(...)  // Backwards-compat wrapper
```

## Commits

| Hash | Description |
|------|-------------|
| bb2deae | test(06-01): add Wave 0 scanner API test scaffold |
| 36342d7 | feat(06-01): create scanner.py with renamed prefix, fixed completeness formula, and dropped-coins exposure |
| 8545846 | feat(06-01): add ScanPair and ScanResponse Pydantic models to api/schemas.py |
| 5345d05 | feat(06-01): wire scanner router into api/main.py and remove academy_scan import |
| 09b251a | feat(06-01): update frontend api.ts with new ScanResponse interface and scanner URLs |

## Self-Check: PASSED

- [x] `api/routers/scanner.py` exists
- [x] `api/routers/academy_scan.py` deleted
- [x] `api/schemas.py` contains ScanPair and ScanResponse
- [x] `api/main.py` registers scanner.router
- [x] `tests/test_scanner_api.py` exists with all 4 test classes
- [x] `frontend/src/lib/api.ts` has ScanResponse, fetchScan, fetchAcademyScan alias
- [x] Production build passes (`npm run build` exit 0)
- [x] Scanner tests: 10 passed, 1 skipped
- [x] Full unit suite: 199 passed, 1 skipped (no regressions)
- [x] All commits exist: bb2deae, 36342d7, 8545846, 5345d05, 09b251a
