# Phase 6: Scanner Enhancements - Research

**Researched:** 2026-04-07
**Domain:** FastAPI router rename + React/Next.js 16 sortable table + URL query state + Mantine v8 table patterns
**Confidence:** HIGH (most critical claims verified directly against live codebase and Next.js 16 bundled docs)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Sort Interaction Model**
- D-01: Clickable column headers trigger sort. No separate sort dropdown.
- D-02: Three-state cycle: ascending → descending → none. "None" returns to default order (D-03).
- D-03: Default sort = p-value ascending.
- D-04: Click-target separation: header clicks inside `<Table.Thead>`, row click-to-navigate stays inside `<Table.Tbody>`. No `stopPropagation` needed.

**Cointegrated vs Non-Cointegrated Split**
- D-05: Two stacked sections, both visible. Top = "Cointegrated (N)" teal accent. Bottom = "Not cointegrated (N)" dimmed accent. Each is its own Mantine `Table`.
- D-06: Independent sort state per section.
- D-07: Keep existing scan stats Paper cards above tables.
- D-08: Always render both section headings; empty section shows "No pairs in this category."

**Sortable Column Scope & Defaults**
- D-09: Sortable columns: p-value, Coint. Score, Hedge Ratio, Half-Life, Correlation, Observations. Pair label is NOT sortable. Status column gone.
- D-10: Natural-direction defaults per column on first click: p-value asc, Coint. Score desc, Hedge Ratio asc, Half-Life asc, Correlation desc, Observations desc.
- D-11: Null `half_life` values always sort last regardless of direction.
- D-12: Sort indicators: `IconChevronUp`/`IconChevronDown` active, `IconArrowsSort` dimmed inactive.

**Column Set & Labelling Cleanup**
- D-13: Drop Status column. 7 columns: Pair, p-value, Coint. Score, Hedge Ratio, Half-Life, Correlation, Observations.
- D-14: Rename "Score" → "Coint. Score".
- D-15: Half-life shown as `"X bars (Yh)"` or `"X bars (Yd)"`. Null → "N/A" dimmed.

**Backend Endpoint Strategy**
- D-16: Rename `api/routers/academy_scan.py` → `api/routers/scanner.py` with prefix `/api/scanner`. Update `AcademyDataContext.tsx:137` to call new path. One canonical endpoint.
- D-17: Endpoint inputs: `timeframe` + `days_back` + `max_pairs` only. No `coins[]` parameter. No `fresh` parameter.
- D-18: Response gains `dropped_for_completeness: list[str]` and `cached_coin_count: int`.

**Fetch Flow Redesign**
- D-19: Fetch button passes current timeframe + smart days_back to backend.
- D-20: Auto-fetch on first land when cache is empty for selected timeframe.
- D-21: Fetch invalidates in-memory scan cache (already present, preserve).
- D-22: Cache status text line: `"32 coins cached for 1h, last updated 2h ago"`.

**Completeness Filter Handling**
- D-23: Keep 90% completeness filter in backend. Expose dropped coins in response.
- D-24: Frontend shows Mantine `Alert` above results listing dropped coins. Inline, neutral, dismissible. Only when `dropped_for_completeness.length > 0`.

**Control Surface After Dropping Chips**
- D-25: Final controls: Timeframe `Select` + "Fetch top 20 from Bitvavo" `Button` + cache status line + "Scan N pairs" `Button`. Drop all chip state.
- D-26: "Scan N pairs" math = `C(coins-in-cache-for-timeframe, 2)`.
- D-27: Persist timeframe in URL: `/scanner?timeframe=4h`.

**History Horizon (days_back)**
- D-28: Smart per-timeframe defaults, computed frontend-side: `1h → 90`, `4h → 180`, `1d → 365`.
- D-29: Auto-bump fixes the daily timeframe zero-results bug.

### Claude's Discretion
- Exact copy text in section headings and Alert messages
- Hover state styling on sortable headers
- Whether fetch and scan buttons sit side-by-side or stacked
- Loading skeleton vs Loader spinner for cache status line
- Whether dropped-coins Alert is dismissible across re-scans
- Number formatting precision per metric column

### Deferred Ideas (OUT OF SCOPE)
- SCAN-05: Filter by p-value/half-life/correlation range
- SCAN-06: Refresh and re-scan combo button (explicit)
- Per-coin "scan only these" chip filter
- Multi-column sort, sort persistence across re-scans
- Configurable days_back or completeness threshold UI inputs
- Cancel-during-scan, progress bar
- Per-row completeness column/icon
- Exporting scan results
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SCAN-01 | User can view a sortable table of all available pair candidates with p-value, cointegration score, half-life, and correlation columns and sort by any column | Sortable table pattern documented in Architecture Patterns; three-state sort state design verified |
| SCAN-02 | User can visually distinguish cointegrated pairs from non-cointegrated pairs through a badge or section split | Two-section split (D-05) is cleaner than badge; both Mantine `Table` instances on same page confirmed viable |
| SCAN-03 | Scanner shows loading state while scan is running | Existing `scanning` + `Loader` pattern already present; extends naturally to fetch state |
| SCAN-04 | Scanner shows error state with actionable message if scan fails | Existing `scanError` Alert pattern preserved; `try/catch` in `runScan` |
</phase_requirements>

---

## Summary

Phase 6 spans both a backend endpoint rename/contract change and a substantial frontend rewrite of `scanner/page.tsx`. The backend work is a clean file rename with additive schema changes. The frontend work replaces the chip filter with a leaner control surface, introduces two-section split tables with three-state sort, and adds URL-driven timeframe state and auto-fetch behavior.

The existing codebase already has all the patterns needed: `useSearchParams` + `router.replace` for URL state (established in `pair-analysis/page.tsx`), `useRouter` for row navigation (established in `scanner/page.tsx`), Mantine `Alert` for inline warnings, Mantine `Table.Thead`/`Table.Tbody`, and `IconTabler` icons. No new patterns need to be invented. The sortable header is the only genuinely new pattern — it is 15–20 lines of custom logic, not a library component.

The most critical correctness risk is the `AcademyDataContext.tsx` call to the old endpoint URL. If the endpoint is renamed without updating this context, the Academy page silently breaks. The plan must treat these as atomic: rename the file, update the prefix, update AcademyDataContext in the same wave.

**Primary recommendation:** Rename backend file first (with AcademyDataContext update), then refactor frontend in a second wave — isolating the break risk to the backend wave and the UI complexity to the frontend wave.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Mantine `Table` | v8.3.18 | Table structure with Thead/Tbody | Already in use; no new dep |
| `@tabler/icons-react` | ^3.40.0 | Sort indicator icons | Already in use; consistent icon family |
| `useSearchParams` / `useRouter` | Next.js 16.2.1 | URL query param state | Established in `pair-analysis/page.tsx`; documented in bundled Next.js docs |
| FastAPI `APIRouter` | >=0.115.0 | Router prefix rename | Trivial: change `prefix=` arg and filename |
| Pydantic `BaseModel` | >=2.5.0 | New response schema fields | Additive — no breaking change |
| `DataCacheManager.list_cached()` | project | Cache status computation | Already returns per-symbol info; aggregate inline in router |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `useCallback` + `useState` | React 19 | Sort state management per section | Established pattern in this codebase |
| `useEffect` cancellation flag | React 19 | Mount-time auto-fetch | Established pattern in this codebase |
| Mantine `Alert` | v8.3.18 | Dropped-coins notification | Already in scanner page; same pattern |
| `Suspense` boundary | React 19 | Wrap `useSearchParams` to avoid prerender failure | Required in Next.js 16 production builds |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom sort state (useState) | TanStack Table | TanStack adds a dependency and ~50kB; custom sort is 15–20 lines for the 6-column, two-section case |
| `router.replace` for timeframe URL | `router.push` | `replace` avoids polluting browser history with every timeframe toggle; matches Phase 1 tab pattern |
| Inline cache-status computation in router | New `/api/scanner/cache-status` endpoint | Inline is cheaper: `list_cached()` is already called in `scan_pairs()`; no extra round-trip needed |

**Installation:** No new packages required.

---

## Architecture Patterns

### Recommended File Change Map

```
api/
├── routers/
│   ├── academy_scan.py              → DELETE (rename to scanner.py)
│   └── scanner.py                   → NEW (renamed, prefix /api/scanner)
├── main.py                          → UPDATE import + include_router
└── schemas.py                       → ADD ScanPair, ScanResponse, FetchScanResponse

frontend/src/
├── lib/api.ts                       → UPDATE: add ScanPair, ScanResponse interfaces;
│                                      add fetchScan(), update fetchLiveData();
│                                      keep AcademyScanResponse + fetchAcademyScan as aliases
├── contexts/AcademyDataContext.tsx  → UPDATE line 137: call new /api/scanner/scan URL
└── app/(dashboard)/scanner/
    └── page.tsx                     → REWRITE (remove chips, add sections + sort + URL state)
```

### Pattern 1: Backend Router Rename (D-16)

**What:** Rename the file, change the `prefix` arg, update `api/main.py` imports. AcademyDataContext calls the same endpoint — its URL must be updated atomically.

**Old:**
```python
# api/routers/academy_scan.py
router = APIRouter(prefix="/api/academy", tags=["academy"])
```

**New:**
```python
# api/routers/scanner.py
router = APIRouter(prefix="/api/scanner", tags=["scanner"])
```

**api/main.py import change:**
```python
# Before:
from api.routers import academy_scan, analysis, backtest, health, optimization, pairs, research, trading
# ...
application.include_router(academy_scan.router)

# After:
from api.routers import scanner, analysis, backtest, health, optimization, pairs, research, trading
# ...
application.include_router(scanner.router)
```

**AcademyDataContext.tsx update (line 137):**
```typescript
// Before:
const scan = await fetchAcademyScan('1h', 90, true);
// After (call updated function that hits /api/scanner/scan):
const scan = await fetchScan('1h', 90);
```

The `fetchAcademyScan` function in `api.ts` hits `/api/academy/scan`. After the rename, the Academy must call `/api/scanner/scan`. Two options:
- Option A (recommended): Update `fetchAcademyScan` to point to the new URL and keep the same TypeScript name — zero call-site changes. Simpler.
- Option B: Add `fetchScan` and update `AcademyDataContext` to call it. Cleaner naming.

Recommendation: **Option A for the backend wave** (update the URL inside `fetchAcademyScan`, keep name). This minimises the diff touching AcademyDataContext. The scanner page itself gets the new `fetchScan` function.

[VERIFIED: live codebase — `api/main.py:9`, `api/main.py:117`, `api/routers/academy_scan.py:22`]

### Pattern 2: Additive Response Schema (D-18)

**What:** Add two fields to the scan response. AcademyScanResponse in `api.ts` does not use a discriminated union — adding optional fields to the Pydantic model is safe.

New Pydantic model in `api/schemas.py`:
```python
class ScanPair(BaseModel):
    """Single pair result from the scanner."""
    asset1: str = Field(description="First asset symbol (e.g. ETH/EUR)")
    asset2: str = Field(description="Second asset symbol (e.g. BTC/EUR)")
    p_value: float = Field(description="Engle-Granger cointegration p-value")
    is_cointegrated: bool = Field(description="True if p_value < 0.05")
    hedge_ratio: float = Field(description="OLS hedge ratio")
    half_life: float | None = Field(description="Mean-reversion half-life in bars, or null")
    correlation: float = Field(description="Pearson correlation coefficient")
    cointegration_score: float = Field(description="Cointegration test statistic")
    observations: int = Field(description="Number of aligned candles used")

class ScanResponse(BaseModel):
    """Response from GET /api/scanner/scan."""
    cointegrated: list[ScanPair] = Field(description="Pairs with p_value < 0.05")
    not_cointegrated: list[ScanPair] = Field(description="Pairs with p_value >= 0.05")
    scanned: int = Field(description="Total pairs tested")
    timeframe: str = Field(description="Timeframe used for the scan")
    cached_coin_count: int = Field(description="Coins in cache before completeness filter")
    dropped_for_completeness: list[str] = Field(
        description="Coin symbols dropped by the 90% completeness filter"
    )
```

The existing `academy_scan.py` response dict does not go through a typed Pydantic model (it returns a raw `dict`). The scanner router should add `response_model=ScanResponse` to the endpoint decorator to enforce the schema.

[VERIFIED: live codebase — `api/routers/academy_scan.py:102-247` — current `scan_pairs()` returns raw `dict`, no `response_model`]

### Pattern 3: Dropped Coins Collection (D-23)

**What:** Collect coins that fail the 90% completeness check and return them.

In `scanner.py`, modify the pre-load loop (currently lines 163-186 in `academy_scan.py`):

```python
series_map: dict[str, pl.DataFrame] = {}
dropped_for_completeness: list[str] = []

for base in base_list:
    symbol = f"{base}/EUR"
    try:
        df = cache_mgr.get_candles(symbol, timeframe, days_back=days_back)
        if len(df) < 100:
            continue  # Under minimum candle count — not part of "completeness" drop

        ts = df["timestamp"].sort().to_list()
        total_hours = (ts[-1] - ts[0]) / 3_600_000
        expected = max(int(total_hours), 1)
        completeness = len(df) / expected

        if completeness < min_completeness:
            dropped_for_completeness.append(symbol)
            continue

        series_map[base] = df
    except Exception:
        logger.warning("Failed to load %s", symbol)
```

The `cached_coin_count` is `len(base_list)` (total coins in cache before any filtering).

[VERIFIED: live codebase — `api/routers/academy_scan.py:160-186`]

### Pattern 4: Smart days_back (D-28)

**What:** Frontend computes days_back from timeframe; backend does not change its parameter signature.

```typescript
// In scanner/page.tsx or api.ts
const DAYS_BACK_BY_TIMEFRAME: Record<string, number> = {
  '1h': 90,
  '4h': 180,
  '1d': 365,
};

function daysBackForTimeframe(tf: string): number {
  return DAYS_BACK_BY_TIMEFRAME[tf] ?? 90;
}
```

Both `fetchScan` and `fetchLiveData` calls pass `daysBackForTimeframe(timeframe)` as `days_back`.

Why frontend computes it: backend stays simple (no conditional logic for defaults), and the frontend is the single source of truth for "which timeframe is selected". This avoids a circular dependency where the backend needs to know the UI's intended horizon.

[ASSUMED — no locked decision on where the mapping lives; the frontend-side approach is consistent with D-28 wording "frontend computes"]

### Pattern 5: URL Timeframe State (D-27)

**What:** Read `?timeframe=` on mount, write it on every Select change.

Established pattern from `pair-analysis/page.tsx` lines 44-51:

```typescript
// Read:
const searchParams = useSearchParams();
const pathname = usePathname();
const timeframe = searchParams.get('timeframe') ?? '1h';

// Write (on Select onChange):
function handleTimeframeChange(value: string) {
  const params = new URLSearchParams(searchParams.toString());
  params.set('timeframe', value);
  router.replace(pathname + '?' + params.toString());
}
```

**CRITICAL:** In Next.js 16, a Client Component that calls `useSearchParams` must be wrapped in a `<Suspense>` boundary to avoid a production build error (`Missing Suspense boundary with useSearchParams`). The current `pair-analysis/page.tsx` already handles this correctly via its `PairAnalysisContent` inner component wrapped in `<Suspense>`. The scanner page must follow the same pattern.

[VERIFIED: Next.js 16.2.1 bundled docs — `use-search-params.md` lines 178-180: "During production builds, a static page that calls `useSearchParams` from a Client Component must be wrapped in a `Suspense` boundary, otherwise the build fails"]

The scanner page is currently `'use client'` and does NOT wrap in Suspense. When `useSearchParams` is added, a Suspense wrapper must be added. Pattern:

```typescript
// scanner/page.tsx
import { Suspense } from 'react';

function ScannerContent() {
  const searchParams = useSearchParams();
  // ... all current component logic
}

export default function ScannerPage() {
  return (
    <Suspense fallback={null}>
      <ScannerContent />
    </Suspense>
  );
}
```

[VERIFIED: `pair-analysis/page.tsx:1-4` uses the same Suspense wrapping pattern]

### Pattern 6: Three-State Sortable Table Headers

**What:** Mantine v8 has no built-in sortable table. Custom sort state with three-state cycle.

```typescript
type SortDirection = 'asc' | 'desc' | null;
interface SortState {
  column: string | null;
  direction: SortDirection;
}

// Natural direction per column (D-10)
const NATURAL_DIRECTION: Record<string, SortDirection> = {
  p_value: 'asc',
  cointegration_score: 'desc',
  hedge_ratio: 'asc',
  half_life: 'asc',
  correlation: 'desc',
  observations: 'desc',
};

function nextSortState(current: SortState, column: string): SortState {
  if (current.column !== column) {
    return { column, direction: NATURAL_DIRECTION[column] ?? 'asc' };
  }
  if (current.direction === NATURAL_DIRECTION[column]) {
    // Flip to opposite
    return { column, direction: current.direction === 'asc' ? 'desc' : 'asc' };
  }
  // Third click: reset
  return { column: null, direction: null };
}
```

Sort application — handling null half_life last (D-11):
```typescript
function sortPairs(pairs: ScanPair[], sort: SortState): ScanPair[] {
  if (!sort.column || !sort.direction) return pairs;
  return [...pairs].sort((a, b) => {
    const key = sort.column as keyof ScanPair;
    const av = a[key] as number | null;
    const bv = b[key] as number | null;
    if (av == null && bv == null) return 0;
    if (av == null) return 1;  // nulls last
    if (bv == null) return -1;
    return sort.direction === 'asc' ? av - bv : bv - av;
  });
}
```

Sort icon rendering per header:
```typescript
function SortIcon({ column, sort }: { column: string; sort: SortState }) {
  if (sort.column !== column) return <IconArrowsSort size={14} opacity={0.4} />;
  if (sort.direction === 'asc') return <IconChevronUp size={14} />;
  return <IconChevronDown size={14} />;
}
```

[ASSUMED — Mantine v8 has no built-in sortable Table; this is the standard community pattern. The preserving-ui-state.md bundled docs confirm the "Activity Patterns Demo" (sortable table) as a Next.js 16 example]

### Pattern 7: Two-Section Component Decomposition (D-05, D-06)

**What:** Extract a reusable `ScannerSection` component to avoid duplicating table JSX.

Recommended decomposition — single named export used twice in `scanner/page.tsx`:

```typescript
interface ScannerSectionProps {
  title: string;          // "Cointegrated (4)" or "Not cointegrated (12)"
  accent: string;         // "teal" | "dimmed"
  pairs: ScanPair[];
  timeframe: string;
  onRowClick: (asset1: string, asset2: string) => void;
}

export function ScannerSection({ title, accent, pairs, timeframe, onRowClick }: ScannerSectionProps) {
  const [sort, setSort] = useState<SortState>({ column: null, direction: null });
  const sorted = sortPairs(pairs, sort);
  // ... Table.Thead with sort headers + Table.Tbody with row click
}
```

This matches the Phase 2–5 pattern of extracting tab components to `components/pair-analysis/`. The section component could live in `scanner/page.tsx` (inline) or in a new file `components/scanner/ScannerSection.tsx`. Given it is only used in one page, inline is simpler — matches how the existing scanner page is structured.

[VERIFIED: `pair-analysis/page.tsx`, `components/pair-analysis/` pattern — but scanner page is currently all-inline; staying inline is consistent]

### Pattern 8: Auto-Fetch on Empty Cache (D-20)

**What:** On page mount, check `cached_coin_count` for the selected timeframe. If zero, auto-fire `handleFetchData`.

The cache information does not require a new endpoint. The existing `GET /api/pairs` endpoint returns all cached datasets with their timeframe. The scanner page already calls `fetchPairs()` in `loadAvailableCoins()`. After the chip removal, `loadAvailableCoins` is replaced by a simpler `fetchCacheState` that counts coins for the current timeframe from the `fetchPairs()` result:

```typescript
// On mount + after timeframe change:
useEffect(() => {
  let cancelled = false;
  async function checkCache() {
    try {
      const res = await fetchPairs();
      const count = new Set(
        res.pairs.filter(p => p.timeframe === timeframe).map(p => p.base)
      ).size;
      if (!cancelled) {
        setCachedCoinCount(count);
        if (count === 0) {
          handleFetchData();  // D-20: auto-fetch when empty
        }
      }
    } catch { /* silent */ }
  }
  checkCache();
  return () => { cancelled = true; };
}, [timeframe]);  // re-run when timeframe changes
```

**Important:** `handleFetchData` must be stable (wrapped in `useCallback` with no changing deps or using a ref) so it can be called from inside the effect without being in the dependency array.

[VERIFIED: `api/routers/pairs.py` returns cached pair info — `fetchPairs()` in api.ts already calls `/api/pairs`]

### Pattern 9: Cache Status Line (D-22)

**What:** Display `"32 coins cached for 1h, last updated 2h ago"`.

`cachedCoinCount` comes from the `fetchPairs()` result (see Pattern 8). The "last updated" timestamp requires reading `end` from the most recent candle in the cache. `PairInfo.end` is the ISO 8601 datetime of the latest candle — compute the most recent `end` across all pairs for the selected timeframe:

```typescript
const lastUpdated = pairs
  .filter(p => p.timeframe === timeframe)
  .map(p => new Date(p.end).getTime())
  .reduce((max, t) => Math.max(max, t), 0);

const relativeTime = lastUpdated
  ? formatRelativeTime(lastUpdated)  // e.g., "2h ago"
  : null;
```

A simple `formatRelativeTime(ms: number): string` utility (< 10 lines) computes the human-readable string. No external dependency needed.

[VERIFIED: `api/schemas.py:74` — `PairInfo.end: str` is ISO 8601 datetime string; `frontend/src/lib/api.ts:843-895` — `fetchPairs()` already returns `PairInfo[]`]

### Anti-Patterns to Avoid
- **Do not call `GET /api/scanner/scan` with `fresh=true`:** The `fresh` parameter is removed per D-17. The scan endpoint reads from cache only. Fetching is separate.
- **Do not add `stopPropagation` to header `onClick`:** Header and row live in different DOM subtrees (`Thead` vs `Tbody`). Click events do not bubble across them. [VERIFIED: DOM spec; D-04]
- **Do not `router.push` for timeframe changes:** Use `router.replace` to avoid polluting browser history.
- **Do not use `dynamic` export for force-rendering:** Next.js 16 docs deprecate `export const dynamic = 'force-dynamic'`. Use `connection()` in Server Components instead. The scanner page is `'use client'`, so this is irrelevant — but do not add a `dynamic` export as a workaround.
- **Do not put `useSearchParams` at the top level of a `'use client'` page without Suspense:** Production builds fail. Wrap inner content in `<Suspense>`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Relative timestamps | Custom date formatting | Inline `formatRelativeTime` (10 lines) | Only need hours/days — no library justified |
| Sortable table | TanStack Table / react-table | Custom sort state (3 functions, ~25 lines total) | Two tables, 6 columns, no pagination — library is overkill |
| URL state management | Custom URL store | `useSearchParams` + `router.replace` | Already used in `pair-analysis/page.tsx`; documented in Next.js 16 bundled docs |
| Cache status endpoint | New `/api/scanner/cache-status` | Derive from existing `GET /api/pairs` response | No extra round-trip; `fetchPairs()` already called on mount |

**Key insight:** This phase adds zero new dependencies. All patterns are either already in the codebase or are trivial custom implementations.

---

## Common Pitfalls

### Pitfall 1: AcademyDataContext Silently Breaks
**What goes wrong:** Renaming the endpoint URL without updating `AcademyDataContext.tsx:137` causes the Academy page to fail silently on load.
**Why it happens:** `AcademyDataContext` calls `fetchAcademyScan()` which is hard-coded to `/api/academy/scan`. After the rename, that URL returns 404. The Academy does not surface this as a visible error in all code paths.
**How to avoid:** The backend rename wave must include updating `fetchAcademyScan`'s URL in `api.ts` (or switching AcademyDataContext to call a new `fetchScan` function) in the same commit.
**Warning signs:** Academy page shows blank pair data after backend wave.

[VERIFIED: `api/routers/academy_scan.py:22` — prefix is `/api/academy`; `frontend/src/lib/api.ts:878-880` — hard-coded to `/api/academy/scan`; `frontend/src/contexts/AcademyDataContext.tsx:137` — calls `fetchAcademyScan('1h', 90, true)`]

### Pitfall 2: Missing Suspense Boundary on useSearchParams
**What goes wrong:** Production build fails with `Missing Suspense boundary with useSearchParams` error.
**Why it happens:** Next.js 16 requires `useSearchParams` in a Client Component to be wrapped in `<Suspense>` during static prerendering. Dev mode does not enforce this.
**How to avoid:** Wrap the scanner page's inner content in `<Suspense fallback={null}>` (matching `pair-analysis/page.tsx` pattern).
**Warning signs:** `npm run build` fails; dev server works fine.

[VERIFIED: Next.js 16.2.1 bundled docs — `use-search-params.md:178-180`]

### Pitfall 3: Daily Timeframe Completeness Check False-Positive
**What goes wrong:** The completeness check at `academy_scan.py:172-178` calculates `total_hours = (ts[-1] - ts[0]) / 3_600_000` and computes `completeness = len(df) / total_hours`. For 1d candles, a coin with 90 daily candles spanning 90 days gives `completeness = 90 / (90*24) = 0.042` — it fails the 90% check even though it has perfect 1d data. This means the `dropped_for_completeness` list will be misleadingly full of coins for `1d` timeframe.
**Why it happens:** The completeness formula assumes hourly candles. It is not timeframe-aware.
**How to avoid:** Fix the formula to use the timeframe's candle interval in hours, not hard-code hours:

```python
TIMEFRAME_HOURS = {"1h": 1, "4h": 4, "1d": 24}
candle_hours = TIMEFRAME_HOURS.get(timeframe, 1)
total_candles_expected = max(int(total_hours / candle_hours), 1)
completeness = len(df) / total_candles_expected
```

This is a **blocker for the 1d timeframe** — without this fix, D-29 (daily timeframe works) will not be achieved even after the days_back bump.
**Warning signs:** Scanning with `1d` timeframe shows zero results and all coins in `dropped_for_completeness`.

[VERIFIED: `api/routers/academy_scan.py:172-178` — formula divides by `total_hours` not `total_candles_expected`]

### Pitfall 4: `fresh` Parameter Removal Breaks Academy
**What goes wrong:** The Academy calls `fetchAcademyScan(..., fresh=true)` which passes `fresh=true` to the scan endpoint. After D-17 removes the `fresh` parameter from the backend, the Academy call will send an unexpected query parameter. FastAPI silently ignores extra query params, so this is not a hard error — but the Academy will no longer get auto-refreshed data on scan.
**Why it happens:** The `fresh` parameter drove auto-fetch inside `scan_pairs()`. Removing it means the endpoint only reads from cache.
**How to avoid:** After removing `fresh` from the backend, the Academy must not depend on the scan endpoint to fetch data for it. The Academy's "load data" path should call the fetch endpoint explicitly if it needs fresh data, or just read from cache (which is fine since the scanner auto-fetches on empty cache now).
**Warning signs:** Academy shows stale or no data if cache happens to be cold.

[VERIFIED: `api/routers/academy_scan.py:107` — `fresh: bool = Query(default=True)` param exists; `frontend/src/contexts/AcademyDataContext.tsx:137` — passes `fresh=true`]

### Pitfall 5: Sort State Retained Across Re-Scans
**What goes wrong:** After running a new scan, results change but the sort state still points to the old column, potentially showing wrong ordering or crashes when the column set changes.
**Why it happens:** `useState` for sort is initialized once and doesn't reset with new scan results.
**How to avoid:** Reset sort state when new scan results arrive: `setSortCointegrated({ column: null, direction: null })` inside the `runScan` success path. D-02 notes "none returns to default order" — the default (p-value asc) is the natural order of results from the backend, so `null` sort is correct on fresh scan.

### Pitfall 6: useEffect / handleFetchData Stale Closure in Auto-Fetch
**What goes wrong:** Auto-fetch on mount (D-20) references `handleFetchData` inside `useEffect`. If `handleFetchData` is recreated every render (not stable), adding it to the dependency array causes an infinite loop; excluding it causes a stale closure.
**Why it happens:** Standard React closure problem with `useCallback` + `useEffect`.
**How to avoid:** Define `handleFetchData` with `useCallback` and no changing dependencies. The `loadAvailableCoins` call inside it should also be stable. Alternatively, separate "check cache and auto-fetch" from "user-triggered fetch" to avoid circular dependencies.

---

## Code Examples

### Three-State Sort Toggle
```typescript
// Source: custom (Mantine v8 has no built-in sortable Table)
type SortDirection = 'asc' | 'desc' | null;
interface SortState { column: string | null; direction: SortDirection; }

const NATURAL: Record<string, SortDirection> = {
  p_value: 'asc', cointegration_score: 'desc', hedge_ratio: 'asc',
  half_life: 'asc', correlation: 'desc', observations: 'desc',
};

function handleHeaderClick(col: string, setCurrent: (s: SortState) => void, current: SortState) {
  if (current.column !== col) {
    setCurrent({ column: col, direction: NATURAL[col] ?? 'asc' });
  } else if (current.direction === NATURAL[col]) {
    setCurrent({ column: col, direction: current.direction === 'asc' ? 'desc' : 'asc' });
  } else {
    setCurrent({ column: null, direction: null });
  }
}
```

### Timeframe URL State (pair-analysis established pattern)
```typescript
// Source: frontend/src/app/(dashboard)/pair-analysis/page.tsx:44-51 [VERIFIED]
const searchParams = useSearchParams();
const pathname = usePathname();
const timeframe = searchParams.get('timeframe') ?? '1h';

function handleTimeframeChange(value: string) {
  const params = new URLSearchParams(searchParams.toString());
  params.set('timeframe', value);
  router.replace(pathname + '?' + params.toString());
}
```

### Completeness Formula Fix
```python
# Source: derived from api/routers/academy_scan.py:172-178 [VERIFIED]
TIMEFRAME_HOURS: dict[str, float] = {"1h": 1.0, "4h": 4.0, "1d": 24.0}

ts = df["timestamp"].sort().to_list()
total_hours = (ts[-1] - ts[0]) / 3_600_000
candle_hours = TIMEFRAME_HOURS.get(timeframe, 1.0)
expected_candles = max(int(total_hours / candle_hours), 1)
completeness = len(df) / expected_candles

if completeness < min_completeness:
    dropped_for_completeness.append(f"{base}/EUR")
    continue
```

### Row Click Navigation (preserve Phase 1 D-04)
```typescript
// Source: frontend/src/app/(dashboard)/scanner/page.tsx:320-327 [VERIFIED]
<Table.Tr
  key={`${pair.asset1}-${pair.asset2}`}
  onClick={() => {
    const base1 = pair.asset1.split('/')[0];
    const base2 = pair.asset2.split('/')[0];
    router.push(`/pair-analysis?asset1=${base1}&asset2=${base2}&timeframe=${timeframe}`);
  }}
  style={{ cursor: 'pointer' }}
>
```

### Suspense Wrapper for useSearchParams
```typescript
// Source: Next.js 16.2.1 bundled docs — use-search-params.md [VERIFIED]
import { Suspense } from 'react';

function ScannerContent() {
  const searchParams = useSearchParams();
  // ... all component logic
}

export default function ScannerPage() {
  return (
    <Suspense fallback={null}>
      <ScannerContent />
    </Suspense>
  );
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `export const dynamic = 'force-dynamic'` | `connection()` in Server Component | Next.js 15+ | Not relevant here (client page) but avoids confusion |
| `next/router` for App Router | `next/navigation` | Next.js 13+ | scanner page already uses `next/navigation` correctly |
| `router.query` for search params | `useSearchParams()` hook | Next.js 13+ | scanner page doesn't use search params yet — add correctly |
| All-in-one scan endpoint with auto-fetch | Separate fetch and scan endpoints | Phase 6 | D-17 removes `fresh` param; fetch and scan become explicit separate actions |

**Deprecated/outdated in this codebase:**
- `fresh=True` scan parameter: Was a convenience for the Academy demo; removed per D-17
- Chip filter for coin selection: Fictional (backend ignores it); removed per D-25
- Hard-coded `fetchLiveData('1h', 90, 20)`: Replaced by timeframe-aware call per D-19

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Frontend-side `daysBackForTimeframe` mapping is the intended location for smart defaults | Architecture Patterns (Pattern 4) | Low: D-28 says "frontend computes which days_back to send" — wording strongly implies frontend |
| A2 | Mantine v8 has no built-in sortable Table component | Don't Hand-Roll, Architecture Patterns | Low: verified Mantine v8.3.18 is in package.json; CLAUDE.md confirms Mantine v8; community pattern is custom sort state |
| A3 | The completeness formula bug (treats all timeframes as hourly) needs fixing for 1d to work | Common Pitfalls (Pitfall 3) | HIGH if ignored: daily timeframe will produce zero results with all coins in dropped list |

---

## Open Questions

1. **Academy cold-start after removing `fresh`**
   - What we know: `AcademyDataContext` passes `fresh=true`, which triggers an API data pull before scanning. Removing `fresh` from the backend endpoint means the Academy no longer auto-fetches on scan.
   - What's unclear: Is the Academy's data always warm enough (cache populated from previous scanner use), or does the Academy need its own fetch trigger?
   - Recommendation: Accept the limitation for Phase 6. The Academy is educational, not real-time. If cache is cold, Academy shows a loading error, which is already the existing `error` state. Document as known limitation.

2. **`max_pairs` parameter removal**
   - D-17 lists only `timeframe + days_back + max_pairs` as inputs. The current endpoint has `max_pairs` defaulting to 20. Is `max_pairs` configurable from the frontend, or is it always 20?
   - D-17 says "capped at max_pairs, default 20, hard cap 50 — same as today." Not user-facing.
   - Recommendation: Keep `max_pairs` as a backend query param with default 20, not exposed in the frontend. This is consistent with D-17.

---

## Environment Availability

Step 2.6: SKIPPED — this phase is pure code/config changes. All dependencies (Python 3.12, Node.js, Mantine v8, FastAPI) are already installed and verified working in Phases 1-5.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=7.4.0 + FastAPI TestClient (httpx) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` — `pythonpath = ["."]` |
| Quick run command | `uv run pytest tests/test_scanner_api.py -x` (Wave 0 gap) |
| Full suite command | `uv run pytest tests/ --ignore=tests/test_api.py --ignore=tests/test_backtest_api.py --ignore=tests/test_optimization_api.py --ignore=tests/test_research_api.py --ignore=tests/test_trading_api.py` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCAN-01 | Scan returns sortable pair data with all required columns | unit | `uv run pytest tests/test_scanner_api.py::TestScannerScan::test_scan_response_fields -x` | ❌ Wave 0 |
| SCAN-01 | Sortable header three-state cycle (asc→desc→none) | manual | Visual verification in browser | N/A |
| SCAN-02 | Response separates cointegrated vs not_cointegrated | unit | `uv run pytest tests/test_scanner_api.py::TestScannerScan::test_scan_categorizes_pairs -x` | ❌ Wave 0 |
| SCAN-03 | Loading state shows while scan runs | manual | Check for Loader component in JSX | N/A |
| SCAN-04 | Error state shows actionable message on scan failure | unit | `uv run pytest tests/test_scanner_api.py::TestScannerEndpoints::test_scan_wrong_endpoint_404 -x` | ❌ Wave 0 |
| D-16 | Old `/api/academy/scan` no longer exists | unit | `uv run pytest tests/test_scanner_api.py::TestScannerEndpoints::test_old_academy_endpoint_gone -x` | ❌ Wave 0 |
| D-16 | New `/api/scanner/scan` exists | unit | `uv run pytest tests/test_scanner_api.py::TestScannerEndpoints::test_new_scanner_endpoint -x` | ❌ Wave 0 |
| D-18 | Response includes dropped_for_completeness and cached_coin_count | unit | `uv run pytest tests/test_scanner_api.py::TestScannerScan::test_scan_new_fields -x` | ❌ Wave 0 |
| Pitfall 3 | Completeness formula is timeframe-aware | unit | `uv run pytest tests/test_scanner_api.py::TestCompletenessFormula -x` | ❌ Wave 0 |

### Test Pattern (from existing test_api.py, test_backtest_api.py)
```python
# tests/test_scanner_api.py  [Wave 0 gap]
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

class TestScannerEndpoints:
    def test_new_scanner_endpoint(self):
        # GET /api/scanner/scan should exist
        resp = client.get("/api/scanner/scan?timeframe=1h&days_back=90&max_pairs=5")
        assert resp.status_code == 200

    def test_old_academy_endpoint_gone(self):
        # GET /api/academy/scan should return 404 or 405 after rename
        resp = client.get("/api/academy/scan")
        assert resp.status_code in (404, 405)

class TestScannerScan:
    def test_scan_response_fields(self):
        resp = client.get("/api/scanner/scan?timeframe=1h&days_back=90&max_pairs=5")
        data = resp.json()
        assert "cointegrated" in data
        assert "not_cointegrated" in data
        assert "dropped_for_completeness" in data
        assert "cached_coin_count" in data
        assert isinstance(data["dropped_for_completeness"], list)
        assert isinstance(data["cached_coin_count"], int)
```

**Note:** These tests require cached data on disk (same condition as existing API tests — run with `uv run pytest tests/test_scanner_api.py`). They are integration tests, not unit tests. The existing test suite has the same constraint (`tests/test_api.py` uses `client.get("/api/health")` which reads from real cache).

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ --ignore=tests/test_api.py --ignore=tests/test_backtest_api.py --ignore=tests/test_optimization_api.py --ignore=tests/test_research_api.py --ignore=tests/test_trading_api.py -x`
- **Per wave merge:** `uv run pytest tests/test_scanner_api.py -v`
- **Phase gate:** Full suite green (with cached data available) before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_scanner_api.py` — covers SCAN-01, SCAN-02, SCAN-04, D-16, D-18, Pitfall 3
- [ ] No framework install needed — pytest + TestClient already present

---

## Security Domain

This phase has no authentication, user input validation beyond FastAPI query params, cryptography, or session management concerns. The scanner reads from a local file cache and returns aggregate statistics. ASVS categories V2, V3, V4, V6 do not apply.

V5 (Input Validation): FastAPI `Query(ge=7, le=365)` already validates `days_back`; `Query(ge=2, le=50)` validates `max_pairs`. The `timeframe` string is passed to `cache_manager.list_cached()` as a filter — no SQL injection risk (pure file system path). No user-supplied input reaches the database or OS commands.

[VERIFIED: `api/routers/academy_scan.py:43-48` — existing Query validators are adequate and carry forward to the renamed endpoint]

---

## Sources

### Primary (HIGH confidence)
- Live codebase — `api/routers/academy_scan.py` (full file read) — endpoint structure, cache logic, completeness filter, 100-candle minimum
- Live codebase — `frontend/src/app/(dashboard)/scanner/page.tsx` (full file read) — current state, row click handler location, chip state
- Live codebase — `frontend/src/lib/api.ts:843-912` — AcademyScanResponse, fetchAcademyScan, fetchLiveData
- Live codebase — `frontend/src/contexts/AcademyDataContext.tsx` (full file read) — line 137 call to fetchAcademyScan
- Live codebase — `frontend/src/contexts/PairContext.tsx` (full file read) — no changes needed
- Live codebase — `api/main.py` (full file read) — router registration
- Live codebase — `src/statistical_arbitrage/data/cache_manager.py` (full file read) — list_cached, get_cache_info, get_candles
- Live codebase — `frontend/src/app/(dashboard)/pair-analysis/page.tsx:1-120` — URL state pattern with useSearchParams + router.replace
- Next.js 16.2.1 bundled docs — `node_modules/next/dist/docs/01-app/03-api-reference/04-functions/use-search-params.md` — Suspense requirement, updateSearchParams pattern
- Next.js 16.2.1 bundled docs — `node_modules/next/dist/docs/01-app/03-api-reference/04-functions/use-router.md` — router.replace vs push
- Next.js 16.2.1 bundled docs — `node_modules/next/dist/docs/01-app/02-guides/preserving-ui-state.md` — Activity/Suspense patterns
- `frontend/package.json` — confirmed Next.js 16.2.1, React 19.2.4, Mantine 8.3.18

### Secondary (MEDIUM confidence)
- `tests/test_api.py`, `tests/test_backtest_api.py`, `tests/test_research_api.py` — test pattern (TestClient, class-based, cached-data dependency)
- `pyproject.toml` `[tool.pytest.ini_options]` — pytest config

### Tertiary (LOW confidence)
- None — all claims verified against live codebase or official Next.js 16 bundled docs.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified in package.json / pyproject.toml
- Architecture: HIGH — all patterns verified in live codebase or official bundled docs
- Pitfalls: HIGH for pitfalls 1/2/3/4 (verified in code); MEDIUM for 5/6 (standard React patterns)
- Test map: HIGH — test file path and class names follow established project convention

**Research date:** 2026-04-07
**Valid until:** 2026-05-07 (stable stack; Next.js 16 is pinned in package.json)
