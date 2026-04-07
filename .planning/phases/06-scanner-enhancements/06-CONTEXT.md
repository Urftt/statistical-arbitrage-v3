# Phase 6: Scanner Enhancements - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the Pair Scanner a coherent discovery funnel that takes a user from "land on /scanner" to "I have 1-3 cointegrated pairs to dive into" with truthful UI, end-to-end timeframe awareness, and a fixed fetch flow — then add the original sortable table + cointegrated/non-cointegrated visual split on top.

**Why this scope expanded mid-discussion:** The original Phase 6 plan assumed the existing scanner basically worked and only needed UI polish. During discussion, the scanner was found to have substantial bugs: the chip filter is fictional (backend ignores it), the fetch button is hard-coded to 1h, the completeness filter silently drops gappy coins, the scan-count label is mathematically right but cognitively wrong, and the daily timeframe silently produces zero results because of an unrelated 100-candle minimum in the cointegration test. Polishing on top of that foundation would deliver a prettier liar. Phase 6 now means "make the scanner deliver on its promise" — bug fixes + the original UI work as one coherent feature.

**In scope:**
- Backend: rename `academy_scan.py` → `scanner.py`, add explicit input/output contract, expose dropped coins, smart history-horizon defaults per timeframe
- Frontend: rewire fetch to be timeframe-aware end-to-end, drop the fictional chip filter, add cache-status line, auto-fetch on empty cache, persist timeframe in URL
- Frontend: add per-column sortable headers (three-state cycle), default p-value asc, click-target separation between header and row
- Frontend: split results into stacked Cointegrated / Not cointegrated sections with independent sort
- Frontend: drop the Status column (redundant), drop Observations is kept, rename Score → Coint. Score, half-life shows bars + time conversion
- Both: surface dropped-for-completeness coins in an inline Alert above results
- Phase 1 contracts preserved: row click → /pair-analysis with URL params (D-03, D-04), URL query state pattern (D-08, D-09)

**Out of scope (deferred to v2 / SCAN-05/06):**
- Filtering visible results by p-value / half-life / correlation ranges
- Saved coin sets, named scans, scheduled scans
- Per-coin "scan only these" filter (the chip behavior, properly implemented)
- Multi-column sort, sort persistence across re-scans
- Configurable days_back input from the UI (smart defaults handle the v1 case)
- Configurable completeness threshold from the UI
- Cancel-during-scan, progress bar for long scans
- Per-row data completeness column or icon
- Exporting scan results

</domain>

<decisions>
## Implementation Decisions

### Sort Interaction Model
- **D-01:** Clickable column headers trigger sort. No separate sort dropdown.
- **D-02:** Three-state cycle: ascending → descending → none. The "none" state returns the section to its default order (D-03).
- **D-03:** Default sort on first scan results = **p-value ascending** (most cointegrated pairs surface first). This matches the existing hard-coded behavior and the discovery-funnel purpose.
- **D-04:** Click-target separation: header clicks live inside `<Table.Thead>`, row click-to-navigate stays inside `<Table.Tbody>`. They are different DOM subtrees, so no `stopPropagation` is needed. The Phase 1 D-04 contract (entire row click target → Pair Analysis) is preserved.

### Cointegrated vs Non-Cointegrated Split
- **D-05:** Two stacked sections, both visible by default. Top section: "Cointegrated (N)" with teal accent. Bottom section: "Not cointegrated (N)" with dimmed accent. Each is its own Mantine `Table`.
- **D-06:** Independent sort state per section — the user might want top cointegrated by p-value and non-cointegrated by half-life for an "almost there" survey.
- **D-07:** Keep the existing scan stats `Paper` cards (Pairs scanned / Cointegrated / Not cointegrated) above the tables. Section headings repeat the count for orientation when scrolled.
- **D-08:** Always render both section headings even when one is empty. Empty section shows "No pairs in this category" inside its frame for layout stability.

### Sortable Column Scope & Defaults
- **D-09:** Sortable columns: p-value, Coint. Score, Hedge Ratio, Half-Life, Correlation, Observations. **Pair label is not sortable.** Status column is gone (D-13).
- **D-10:** Natural-direction defaults per column on first click: p-value asc, Coint. Score desc, Hedge Ratio asc, Half-Life asc, Correlation desc, Observations desc.
- **D-11:** Null `half_life` values always sort last regardless of direction (standard data-table convention — nulls aren't "better" or "worse," they're missing).
- **D-12:** Sort indicator = `IconChevronUp` / `IconChevronDown` from `@tabler/icons-react` next to active header label; `IconArrowsSort` dimmed when inactive. Matches the existing IconTabler family in the page.

### Column Set & Labelling Cleanup
- **D-13:** Drop the **Status** column. Section split (D-05) makes the badge redundant. Remaining 7 columns: Pair, p-value, Coint. Score, Hedge Ratio, Half-Life, Correlation, Observations.
- **D-14:** Rename **Score** → **Coint. Score** to disambiguate the `cointegration_score` field.
- **D-15:** Half-life shown as `"X bars (Yh)"` or `"X bars (Yd)"` — bars remain authoritative (matches the backend), time conversion in parentheses computed from the selected timeframe (1h → "h", 4h → "h", 1d → "d"). Null still renders as "N/A" with dimmed text.

### Backend Endpoint Strategy
- **D-16:** Rename `api/routers/academy_scan.py` → `api/routers/scanner.py` with prefix `/api/scanner`. Update `frontend/src/contexts/AcademyDataContext.tsx:137` to call the new path so the Academy continues to work. One canonical scanner endpoint, no duplication.
- **D-17:** Endpoint inputs: `timeframe` + `days_back` + `max_pairs` only. **No `coins[]` parameter.** Backend reads all cached coins for that timeframe (capped at `max_pairs`, default 20, hard cap 50 — same as today). Honest, simple, matches "scan everything in cache" model.
- **D-18:** Endpoint response gains: `dropped_for_completeness: list[str]` (coins that failed the 90% completeness check), `cached_coin_count: int` (how many coins existed in cache before filtering), in addition to the existing `cointegrated[]`, `not_cointegrated[]`, `scanned`, `timeframe`. New TypeScript interface in `frontend/src/lib/api.ts`.

### Fetch Flow Redesign
- **D-19:** "Fetch fresh data" button pulls top N coins from Bitvavo **for the currently selected timeframe** (frontend passes timeframe to the backend). Default N = 20 (matches `academy_scan.py:47` default). Currently the only call is `fetchLiveData('1h', 90, 20)` — that becomes `fetchLiveData(timeframe, dayBackForTimeframe, 20)`.
- **D-20:** **Auto-fetch on first land when cache is empty for the selected timeframe.** No manual click required, no Alert prompt. The user explicitly chose this over the recommended "show prompt." Page mount logic: read cache state via existing API → if empty for current timeframe, immediately fire fetch. *(This is a slight departure from the standard "never auto-call external APIs without user gesture" — accepted because the scanner exists to surface cached data and an empty cache is useless. Reconsider if Bitvavo rate limits become an issue.)*
- **D-21:** Fetch invalidates the in-memory scan cache. Already the case in `academy_scan.py:79-80` (`_scan_cache.clear(); _scan_cache_ts.clear()`). Keep this behavior.
- **D-22:** Show a small "Cache status" text line near the controls: `"32 coins cached for 1h, last updated 2h ago"`. Built from cache metadata. Cheap to render — refresh after every fetch and every scan.

### Completeness Filter Handling
- **D-23:** Keep the 90% data-completeness threshold in the backend (it protects chart quality downstream in Statistics/Backtest/Optimize tabs). But return the dropped coins to the frontend instead of silently filtering them. Backend change: collect dropped coins into a list during the loop in `academy_scan.py:164-186` and add to the response.
- **D-24:** Frontend displays dropped coins in an **inline Mantine `Alert`** above the results, neutral color, dismissible. Format: `"Scanned X pairs from Y coins. Excluded Z coins for incomplete data."` with an expandable detail listing the dropped coin symbols. Only render the Alert when `dropped_for_completeness.length > 0`.

### Control Surface After Dropping Chips
- **D-25:** Final control surface: **Timeframe `Select`** + **"Fetch top 20 from Bitvavo" `Button`** + **cache status line** + **"Scan N pairs" `Button`**. Drop the entire chip filter (`Chip` components, `selectAll`, `deselectAll`, `toggleCoin`, `selectedCoins` state). Drop the Divider labelled "Scan Controls."
- **D-26:** "Scan N pairs" label math = `C(coins-currently-in-cache-for-timeframe, 2)`. Honest, predictable, computable client-side from cache state. Any delta from completeness drops gets explained in the post-scan Alert (D-24).
- **D-27:** Persist timeframe in URL query param: `/scanner?timeframe=4h`. Bookmarkable, shareable, deep-linkable. Matches Phase 1 D-08/D-09 pattern for tab state.

### History Horizon (days_back)
- **D-28:** **Smart per-timeframe defaults**, frontend computes which `days_back` to send based on selected timeframe: `1h → 90`, `4h → 180`, `1d → 365`. Each clears the 100-candle cointegration minimum (`academy_scan.py:208`) with comfortable margin. No user-facing input — this is hidden complexity the scanner handles for them.
- **D-29:** Auto-bump means the 1d case always works without warnings. The current bug ("daily timeframe silently produces zero results" because `90d × 1d = 90 candles < 100 minimum`) goes away because 1d defaults to 365 days now.

### Claude's Discretion
- Exact copy text in section headings (e.g., "Cointegrated (4)" vs "✓ Cointegrated (4)" vs "Cointegrated · 4")
- Exact copy in the dropped-coins Alert (template: "Scanned X pairs from Y coins. Excluded Z coins for incomplete data.")
- Exact copy in the cache status line (template: "N coins cached for [timeframe], last updated [relative time]")
- Hover state styling on sortable headers (cursor pointer, subtle bg change)
- Whether to show a distinct "Fetching..." vs "Scanning..." button label/spinner
- Whether fetch and scan buttons sit side-by-side or stacked vertically
- Loading skeleton vs Loader spinner for the cache status line during initial mount
- Exact bottom-of-section "No pairs in this category" empty-state copy
- Whether the dropped-coins Alert is dismissible across re-scans or always re-renders
- Number formatting precision per metric column (current: p_value 4dp, others 3dp — discretion to keep or adjust)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frontend — Existing Scanner & Related State
- `frontend/src/app/(dashboard)/scanner/page.tsx` — Current scanner page (substantial rewrite); contains all the UX issues being fixed. Note: row click handler at lines 320-327 must be preserved (Phase 1 D-04).
- `frontend/src/lib/api.ts` lines 843-895 — Existing `AcademyScanPair`, `AcademyScanResponse`, `fetchAcademyScan`, `FetchLiveDataResponse`, `fetchLiveData`. Need new `ScanResponse` interface (extends with `dropped_for_completeness`, `cached_coin_count`) and new `fetchScan` function.
- `frontend/src/contexts/AcademyDataContext.tsx:137` — Calls `fetchAcademyScan('1h', 90, true)`; **must update** when endpoint renames (D-16).
- `frontend/src/contexts/PairContext.tsx` — Global pair selection (asset1/asset2/timeframe); row click → Pair Analysis flows through this.
- `frontend/AGENTS.md` — Reminder that Next.js 16 has breaking changes from training data; consult `node_modules/next/dist/docs/` before using new APIs (sorting hooks, headers helpers, etc.).
- `frontend/src/lib/theme.ts` — Mantine theme + Plotly dark template; not directly touched but referenced for consistent component styling.

### Backend — Scanner Endpoint & Dependencies
- `api/routers/academy_scan.py` — Source of truth for current scanner backend; **renames to `api/routers/scanner.py`** (D-16). Key code paths: fetch endpoint (lines 43-94), scan endpoint (lines 102-247), in-memory cache (lines 25-27), completeness filter (lines 162-182), 100-candle minimum check (line 208).
- `api/main.py` — App factory and `app.include_router` calls; new `scanner.py` router needs to be wired here (and `academy_scan` removed).
- `api/routers/__init__.py` — Router exports.
- `api/schemas.py` — Pydantic request/response schemas; new `ScanRequest`, `ScanResponse`, `ScanPair`, plus `numpy_to_python` helper used during serialization.
- `src/statistical_arbitrage/data/cache_manager.py` — `get_candles` (line 189, the `days_back` parameter), `list_cached`, `get_available_pairs`, `_cache_path`, `get_cache_info`. The `refresh()` helper at line 272 uses `days_back=365` — relevant precedent for D-28.
- `src/statistical_arbitrage/analysis/cointegration.py` — `PairAnalysis` class used in the scan loop (`test_cointegration`, `calculate_half_life`, `get_correlation`).

### Prior Phase Decisions to Preserve
- `.planning/phases/01-routing-navigation-scaffold/01-CONTEXT.md` — **D-03** (URL query params for navigation: `/pair-analysis?asset1=ETH&asset2=BTC&timeframe=1h`), **D-04** (entire row is click target, no Analyze button), **D-08/D-09** (URL query param state pattern). Phase 6 must not break any of these.

### Codebase Conventions
- `.planning/codebase/CONVENTIONS.md` — Naming, imports, component patterns (e.g., snake_case Python, PascalCase React, `@tabler/icons-react` icon family).
- `.planning/codebase/STRUCTURE.md` — Where to add new code; backend routers under `api/routers/`, frontend pages under `frontend/src/app/(dashboard)/`.
- `.planning/codebase/STACK.md` — Tech stack constraints (Polars not Pandas, Mantine v8, Plotly via PlotlyChart wrapper).

### Project Documents
- `.planning/PROJECT.md` — Vision, tech-stack constraints, three-pillar value statement.
- `.planning/REQUIREMENTS.md` — SCAN-01..04 (Phase 6 in scope, all currently `Pending`); SCAN-05/SCAN-06 (v2 deferred — do not pull in).
- `.planning/ROADMAP.md` Phase 6 entry (lines 101-110) — Goal, requirements, success criteria, "Depends on Phase 1."

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Mantine `Table` with `Thead` / `Tbody`** — Already used in `scanner/page.tsx`. Two instances needed (one per section) instead of one. Sortable header logic is a small custom wrapper — Mantine v8 has no built-in sortable table.
- **`@tabler/icons-react`** — `IconSearch`, `IconRefresh`, `IconDownload`, `IconCheck` already imported in scanner page; add `IconChevronUp`, `IconChevronDown`, `IconArrowsSort` for sort indicators.
- **Mantine `Alert`** — Already used for fetch result/error in scanner page (lines 186-200); reuse pattern for the dropped-coins Alert.
- **`DataCacheManager` singleton** — `get_cache_manager()` in `src/statistical_arbitrage/data/cache_manager.py`. Methods used: `get_candles`, `list_cached`, `get_available_pairs`, `get_cache_info`. New: scanner backend may need a `cached_coin_count` helper or compute inline from `list_cached`.
- **`PairAnalysis` class** — Already wired into the scan loop; no changes needed to the cointegration math itself.
- **`numpy_to_python` helper** — `api/schemas.py`, used in scan response serialization; already handles numpy → JSON conversion.
- **5-minute in-memory scan cache** — `_scan_cache` / `_scan_cache_ts` in `academy_scan.py:25-27`; preserve in renamed file.
- **`useRouter` from `next/navigation`** — Already imported in scanner page for row navigation; reuse for URL query param updates.

### Established Patterns
- **`'use client'` + `useState` + `useEffect` cancellation flag** for data fetching (existing pattern in scanner/page.tsx, statistics/backtest/research/optimize tabs)
- **`useCallback` for handlers passed to children**
- **Mantine `Container size="xl" py="md"` + `Stack gap="lg"`** for page layout
- **`Paper p="md" radius="sm" withBorder` + `Stack`** for control sections
- **URL query params for shareable state** — Phase 1 D-08/D-09 for tab state; D-27 here for timeframe state
- **Inline `Alert`** for warnings/errors near the affected control (not toast)
- **Polars `.join` + `.sort` + `.select`** in backend, never Pandas
- **Pydantic `Field()` with descriptions** for all schemas
- **Incremental delta fetching in `cache_manager.get_candles`** — first fetch hits API, subsequent fetches only pull deltas; never throws data away

### Integration Points
- **New endpoint location:** `api/routers/scanner.py` (renamed from `academy_scan.py`)
- **Router registration:** `api/main.py` `app.include_router(scanner.router)`; remove the old `academy_scan` include
- **Frontend client wiring:** `frontend/src/contexts/AcademyDataContext.tsx:137` updated to call new scanner endpoint or a renamed function
- **Phase 1 row click target:** `frontend/src/app/(dashboard)/scanner/page.tsx:320-327` — `<Table.Tr onClick>` navigating to `/pair-analysis?asset1=...&asset2=...&timeframe=...`. Must remain functional after Tbody/Thead split for sort.
- **PairContext:** No changes required; URL params populate it on the Pair Analysis page mount.
- **`frontend/src/lib/api.ts`** — Replace `AcademyScanResponse` / `fetchAcademyScan` with new `ScanResponse` / `fetchScan` (or extend in place if academy still uses the same types). New `dropped_for_completeness: string[]` and `cached_coin_count: number` fields.

</code_context>

<specifics>
## Specific Ideas

- **Section heading style preview chosen by user:**
  ```
  Cointegrated (4)
    ETH / BTC    p=0.012  ...
    SOL / BTC    p=0.034  ...

  Not cointegrated (12)
    ADA / DOT    p=0.21   ...
    XRP / LINK   p=0.34   ...
  ```
- **The user explicitly framed the scanner's purpose as a "discovery funnel":** "Find the cointegrated pairs that I can dive into and perform further analysis on." Every UX trade-off should optimize for that 30-second journey, not for power-user configurability.
- **Honest reporting principle:** No silent drops. Anything the backend filters out gets surfaced to the UI. This matches the Phase 3 honest-reporting precedent (preflight warnings, overfitting banners) and the project's learning-first ethos.
- **Trust the cache.** The user was uncertain whether the cache was earning its keep — confirmed it is (Statistics, Backtest, Research, Optimize all read from it). Phase 6 should reinforce that trust by surfacing cache state visibly (D-22), not hiding it.
- **Match Phase 1-5 visual language:** Mantine v8 components, dark theme, IconTabler icons, the same `Paper p="md" radius="sm" withBorder` blocks the rest of the dashboard uses.

</specifics>

<deferred>
## Deferred Ideas

These came up during discussion or are explicitly v2-tagged in REQUIREMENTS.md. Not part of Phase 6 — captured here so they're not lost.

- **SCAN-05** Filter visible results by p-value range, half-life range, min correlation — v2. Better as a post-scan client-side filter than a pre-scan input filter.
- **SCAN-06** Refresh data before re-scanning as a separate action — partially absorbed by D-19/D-20 (timeframe-aware fetch + auto-fetch on empty cache); the explicit "refresh and re-scan" combo button is v2.
- **Per-coin "scan only these" filter** (the chip behavior, properly implemented in the backend) — v2 if a clear use case emerges; the discovery-funnel purpose argues against it.
- **Saved coin sets, named scans, scheduled scans** — v2.
- **Multi-column sort** — v2.
- **Sort persistence across re-scans** — could be added later if users complain; v1 resets sort to default on each re-scan.
- **Cancel-during-scan, progress bar for long scans** — v2; current scan is fast enough at default `max_pairs=20` to not need it.
- **Per-row data completeness column or icon** — v2; the dropped-coins Alert (D-24) covers the v1 honesty requirement without per-row clutter.
- **Configurable `days_back` input from the UI** — v2; smart per-timeframe defaults (D-28) cover the v1 case.
- **Configurable completeness threshold from the UI** — v2; backend keeps the 90% default.
- **Exporting scan results** (CSV/JSON) — v2 (matches REQUIREMENTS.md EXP-01 pattern for backtest exports).
- **Hover tooltip explaining "Coint. Score" as the cointegration test statistic** — nice-to-have, not blocking.

</deferred>

---

*Phase: 06-scanner-enhancements*
*Context gathered: 2026-04-07*
