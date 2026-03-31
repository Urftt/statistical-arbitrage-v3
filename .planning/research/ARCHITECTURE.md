# Architecture Research

**Domain:** Interactive backtesting / research UI on top of existing FastAPI + Next.js 16 app
**Researched:** 2026-03-31
**Confidence:** HIGH — based on direct inspection of the live codebase (all files read), Next.js 16 local docs, and established React patterns

---

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│  Browser (Next.js 16, React 19, Mantine v8)                          │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │  Dashboard Shell  (app/(dashboard)/layout.tsx)               │     │
│  │  AppShell + PairProvider                                      │     │
│  │                                                              │     │
│  │  ┌──────────────┐    ┌─────────────────────────────────┐    │     │
│  │  │ Header.tsx   │    │  Page content (AppShell.Main)   │    │     │
│  │  │ Pair select  │    │                                 │    │     │
│  │  │ Timeframe    │    │  ┌───────────────────────────┐  │    │     │
│  │  └──────────────┘    │  │  Scanner page             │  │    │     │
│  │                      │  │  - Coin chip selector     │  │    │     │
│  │  ┌──────────────┐    │  │  - Scan results table     │  │    │     │
│  │  │ Sidebar.tsx  │    │  │  - "Analyze" row action   │  │    │     │
│  │  │ Nav links    │    │  └───────────────────────────┘  │    │     │
│  │  └──────────────┘    │  ┌───────────────────────────┐  │    │     │
│  │                      │  │  Pair Analysis page        │  │    │     │
│  │                      │  │  ┌─────────────────────┐  │  │    │     │
│  │                      │  │  │ Mantine Tabs         │  │  │    │     │
│  │                      │  │  │ Statistics│Research  │  │  │    │     │
│  │                      │  │  │ Backtest │Optimize   │  │  │    │     │
│  │                      │  │  └──────────────────────┘  │  │    │     │
│  │                      │  │  Tab panels (lazy-loaded   │  │    │     │
│  │                      │  │  data per tab)             │  │    │     │
│  │                      │  └───────────────────────────┘  │    │     │
│  │                      └─────────────────────────────────┘    │     │
│  └─────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
                               │  HTTP fetch (typed via api.ts)
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│  FastAPI :8000                                                        │
│                                                                      │
│  /api/analysis/*   /api/research/*   /api/backtest   /api/optimization│
│       │                 │                 │                 │        │
│       └─────────────────┴─────────────────┴─────────────────┘        │
│                                    │                                 │
│                          Core Python library                          │
│                 (cointegration, research, engine, grid search)        │
│                                    │                                 │
│                         DataCacheManager (parquet)                    │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Location |
|-----------|---------------|----------|
| `PairContext` | Global pair selection (asset1, asset2, timeframe, coins list) | `contexts/PairContext.tsx` |
| `Header` | Pair and timeframe picker — updates `PairContext` | `components/layout/Header.tsx` |
| `Sidebar` | Navigation between pages, updated nav items for merged structure | `components/layout/Sidebar.tsx` |
| `PlotlyChart` | Renders any Plotly figure with dark theme; SSR-safe via `next/dynamic` | `components/charts/PlotlyChart.tsx` |
| `ScannerPage` | Fetch data, select coins, run scan, display results table with row action to Pair Analysis | `app/(dashboard)/scanner/page.tsx` |
| `PairAnalysisPage` | Tabbed shell — receives pair from `PairContext`, owns tab state in local `useState` | `app/(dashboard)/pair-analysis/page.tsx` (new) |
| `StatisticsTab` | Cointegration results, spread chart, z-score chart, half-life stats | component under `pair-analysis/` |
| `ResearchTab` | 8 research module sub-sections, each independently fetched on demand | component under `pair-analysis/` |
| `BacktestTab` | Parameter form + "Run Backtest" button + equity curve + metrics | component under `pair-analysis/` |
| `OptimizeTab` | Parameter axis config + "Run Optimize" button + heatmap + results table | component under `pair-analysis/` |
| `api.ts` | Typed fetch wrappers and TypeScript interfaces for all backend endpoints | `lib/api.ts` |

---

## Recommended Project Structure

The Pair Analysis page is the structural centerpiece. Organize it as a folder of focused components:

```
frontend/src/
├── app/(dashboard)/
│   ├── scanner/
│   │   └── page.tsx              # Existing — scanner (add "Analyze" row action)
│   └── pair-analysis/
│       └── page.tsx              # New — tabbed shell
│
├── components/
│   ├── layout/                   # Existing — no changes needed
│   ├── charts/                   # Existing — PlotlyChart unchanged
│   └── pair-analysis/            # New folder
│       ├── StatisticsTab.tsx     # Cointegration stats + spread/zscore charts
│       ├── ResearchTab.tsx       # 8-module research panel
│       ├── BacktestTab.tsx       # Parameter form + results
│       ├── OptimizeTab.tsx       # Grid/walk-forward config + results
│       ├── PairHeader.tsx        # Pair name + timeframe display at top of page
│       ├── RunButton.tsx         # Reusable "Run / loading / error" button
│       └── MetricCard.tsx        # Small stat card (Sharpe, drawdown, etc.)
│
└── lib/
    └── api.ts                    # Existing — all endpoints already typed
```

### Structure Rationale

- **`pair-analysis/` component folder**: All four tab bodies are non-trivial. Co-locating them under a named folder keeps them findable and prevents polluting the top-level `components/` directory.
- **No new contexts needed**: `PairContext` already provides `asset1`, `asset2`, `timeframe`. Tab-local data (backtest result, research responses) stays in the tab component's own `useState` — it does not need to be global.
- **`RunButton.tsx`**: Backtest and Optimize both have an identical "run expensive computation, show loading, show error" pattern. Extract once.
- **`MetricCard.tsx`**: The backtest metrics summary repeats the same pattern (label + value + optional color coding). Extract for consistency with the Academy style.

---

## Architectural Patterns

### Pattern 1: Fetch-on-Tab-Activate (Lazy Tab Data)

**What:** Each tab owns its own `useState` for `{ data, loading, error }`. Data is fetched the first time the tab becomes active (tracked with a `hasFetched` ref or `data !== null` check), not on page mount.

**When to use:** Statistics, Research. These computations take 1-5 seconds. Fetching all four tabs on mount would block the page and waste API calls if the user only wants Statistics.

**Trade-offs:** First tab activation has latency; subsequent visits to the same tab are instant (data persists in component state for the session). Tab state resets on page navigation (no `cacheComponents` is enabled in `next.config.ts`, confirmed by inspection).

**Example:**

```typescript
// Inside StatisticsTab.tsx
const { asset1, asset2, timeframe } = usePairContext();
const [result, setResult] = useState<CointegrationResponse | null>(null);
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

// Fetch when the tab first becomes visible and pair is set
useEffect(() => {
  if (!asset1 || !asset2 || result !== null || loading) return;
  let cancelled = false;
  setLoading(true);
  postCointegration({ asset1: toEurSymbol(asset1), asset2: toEurSymbol(asset2), timeframe })
    .then((r) => { if (!cancelled) setResult(r); })
    .catch((e) => { if (!cancelled) setError(e.message); })
    .finally(() => { if (!cancelled) setLoading(false); });
  return () => { cancelled = true; };
}, [asset1, asset2, timeframe, result, loading]);
```

The `result !== null` guard means the fetch only runs once per pair selection per session.

### Pattern 2: Explicit Run Button for Heavy Computations

**What:** Backtest and Optimize do not auto-fetch. The user configures parameters in a form, then clicks "Run Backtest" or "Run Grid Search". The button becomes a loading spinner during execution; the previous result stays visible until the new one arrives.

**When to use:** Any computation that takes >3 seconds, or where the user controls parameters that must be finalized before running (backtest strategy params, grid search axes).

**Trade-offs:** Requires an intentional user action; avoids accidental expensive re-computations on every parameter change. Consistent with the Academy pattern where "see real data" is opt-in.

**Example:**

```typescript
// BacktestTab.tsx
const [params, setParams] = useState<StrategyParametersPayload>(DEFAULT_STRATEGY_PARAMETERS);
const [result, setResult] = useState<BacktestResponse | null>(null);
const [running, setRunning] = useState(false);
const [error, setError] = useState<string | null>(null);

const handleRun = useCallback(async () => {
  setRunning(true);
  setError(null);
  try {
    const r = await postBacktest({ asset1: toEurSymbol(asset1), asset2: toEurSymbol(asset2),
                                   timeframe, days_back: 180, strategy: params });
    setResult(r);
  } catch (e) {
    setError(e instanceof Error ? e.message : 'Backtest failed');
  } finally {
    setRunning(false);
  }
}, [asset1, asset2, timeframe, params]);
```

### Pattern 3: Pair Change Invalidation

**What:** When `asset1`, `asset2`, or `timeframe` changes in `PairContext`, all tab results must be cleared so stale data from the previous pair is not displayed.

**When to use:** Every tab component must implement this. Without it, a user switching from BTC/ETH to ETH/SOL would see BTC/ETH results with an ETH/SOL label.

**Trade-offs:** Slight UX friction (re-fetching Statistics on every pair change), but necessary for correctness. The alternative — persisting results across pair changes — is a correctness bug.

**Example:**

```typescript
// Clear stale results when the pair changes
const prevPairRef = useRef<string>('');
const currentPair = `${asset1}|${asset2}|${timeframe}`;

useEffect(() => {
  if (prevPairRef.current && prevPairRef.current !== currentPair) {
    setResult(null);
    setError(null);
  }
  prevPairRef.current = currentPair;
}, [currentPair]);
```

### Pattern 4: Scanner-to-Pair-Analysis Navigation

**What:** The Scanner table has a clickable row (or an "Analyze" button per row). Clicking it updates `PairContext` (setAsset1, setAsset2) and navigates to `/pair-analysis` via `router.push('/pair-analysis')`. The Pair Analysis page then reads from `PairContext` and auto-fetches Statistics.

**When to use:** The primary user flow: scan many pairs, pick one that looks promising, investigate it.

**Trade-offs:** Uses the global context as a communication channel between pages, which is already established. The alternative (URL query params for pair selection) would duplicate the existing context mechanism and require parsing on the analysis page.

**Example (Scanner row click):**

```typescript
const { setAsset1, setAsset2 } = usePairContext();
const router = useRouter();

const handleAnalyze = (pair: AcademyScanPair) => {
  setAsset1(pair.asset1.split('/')[0]);  // strip /EUR suffix
  setAsset2(pair.asset2.split('/')[0]);
  router.push('/pair-analysis');
};
```

### Pattern 5: Research Module Sub-Sections

**What:** The Research tab contains 8 independent modules. Each module has its own fetch, loading state, and result display. They are stacked vertically in a single scrollable column, not a second level of tabs. Each module has a "Run" button (same as Pattern 2) since research modules can take 3-10 seconds each.

**When to use:** The Research tab only. Eight nested tabs would be too deep and confusing.

**Trade-offs:** The page becomes long when all 8 modules are run. Mitigate with collapsed/expanded sections (Mantine `Accordion` or the same collapsed-card pattern from `RealDataSection.tsx`). Results from each module are independent; running one does not require another.

---

## Data Flow

### Request Flow: Statistics Tab

```
User lands on /pair-analysis (or switches pair in Header)
    |
    v
PairContext provides { asset1, asset2, timeframe }
    |
    v
StatisticsTab useEffect fires (pair changed or first load)
    |
    v
postCointegration({ asset1: 'BTC/EUR', asset2: 'ETH/EUR', timeframe: '1h' })
    |
    v
FastAPI POST /api/analysis/cointegration
  -> DataCacheManager.get_candles() (parquet cache or Bitvavo fetch)
  -> PairAnalysis.test_cointegration()
  -> BacktestResult serialized as JSON
    |
    v
CointegrationResponse returned to StatisticsTab
    |
    v
setResult(response) -> React re-render
    |
    v
PlotlyChart renders spread, z-score, price comparison
Mantine components render stats (p-value, half-life, correlation)
```

### Request Flow: Backtest Tab

```
User opens Backtest tab
    |
    v
BacktestTab renders with DEFAULT_STRATEGY_PARAMETERS in form
No fetch — waiting for user action
    |
    v
User adjusts params (z-score entry: 1.5 → 2.0, etc.)
All changes are local useState in the form — no API calls
    |
    v
User clicks "Run Backtest"
    |
    v
postBacktest({ asset1, asset2, timeframe, days_back, strategy: params })
    |
    v
FastAPI POST /api/backtest
  -> run_backtest() -> equity_curve, trade_log, metrics, warnings
    |
    v
BacktestResponse returned
    |
    v
setResult(response) -> re-render
    |
    v
PlotlyChart renders equity curve
PlotlyChart renders drawdown
Mantine Table renders trade log
MetricCards render Sharpe, win rate, max drawdown, P&L
```

### State Management

```
PairContext (global, cross-page)
  asset1, asset2, timeframe, coins
  Set by: Header selectors, Scanner row click
  Read by: All tab components, PairHeader display

Tab-local state (reset on pair change, persists across tab switches)
  StatisticsTab: { result: CointegrationResponse | null, loading, error }
  ResearchTab:   { results: Map<module, Response | null>, loading per module }
  BacktestTab:   { params: StrategyParams, result: BacktestResponse | null, running, error }
  OptimizeTab:   { axes: ParameterAxis[], result: GridSearchResponse | null, running, error }

No shared state between tabs.
No new context providers needed.
No external state library (Zustand, etc.) needed — useState is sufficient.
```

---

## Component Boundaries

| Boundary | What crosses it | Notes |
|----------|----------------|-------|
| `PairContext` → Tab components | `asset1`, `asset2`, `timeframe` read via `usePairContext()` | Read-only in tabs; only Header and Scanner write to it |
| `api.ts` → Tab components | All fetch functions are imported directly into tab components | No intermediary service layer needed at this scale |
| `PlotlyChart` → Tab components | `data: Data[]`, `layout: ChartLayout` props | Chart data transformation (raw API response → Plotly traces) happens inside the tab component, not in PlotlyChart |
| Tab components → `PairAnalysisPage` | Only mount/unmount (which tab is active) | Tabs do not pass data up to the page; no callbacks between page and tabs |
| `ScannerPage` → `PairContext` | Writes `asset1`, `asset2` on row click | The only cross-page state mutation pattern |

---

## Build Order (Dependencies)

Build in this order — each step unblocks the next:

**Step 1 — Routing and navigation scaffold**
- Rename `/deep-dive` → `/pair-analysis` (update page.tsx, Sidebar.tsx nav items)
- Remove stub pages: `/research`, `/backtest`, `/optimize` (their content moves into tabs)
- Verify Scanner "Analyze" row action updates PairContext and navigates to `/pair-analysis`
- No API calls yet; just routing works correctly

**Step 2 — Statistics tab (auto-fetch, read-only display)**
- Implement `StatisticsTab.tsx` with fetch-on-activate pattern (Pattern 1)
- Add `PairHeader.tsx` showing selected pair + timeframe above the tabs
- This exercises the full loop: PairContext → API call → Plotly charts
- Unblocks visual validation of the chart patterns for remaining tabs

**Step 3 — Backtest tab (parameter form + run button + results)**
- Implement `BacktestTab.tsx` with parameter form and explicit run pattern (Pattern 2)
- Add `MetricCard.tsx` and `RunButton.tsx` shared components
- Equity curve chart, drawdown chart, trade log table
- This is the most user-visible feature and most likely to surface API issues early

**Step 4 — Research tab (8 modules, accordion layout)**
- Implement `ResearchTab.tsx` with 8 accordion sections
- Each section: run button → fetch → chart/table result
- The individual module types are already fully typed in `api.ts`

**Step 5 — Optimize tab (grid search + walk-forward)**
- Implement `OptimizeTab.tsx` with axis configuration and run button
- Heatmap chart (Plotly heatmap) for grid search results
- Walk-forward fold table
- Most complex UI; correct to do last when shared patterns are settled

**Step 6 — Scanner enhancements**
- Add "Analyze this pair" button/action to each scanner result row (wires PairContext + navigation)
- This step is last because it depends on the Pair Analysis page being built

---

## Anti-Patterns

### Anti-Pattern 1: Fetching All Tabs on Page Mount

**What people do:** Fire all four API calls in the page-level `useEffect` when `PairAnalysisPage` mounts.

**Why it is wrong:** Backtest and grid search can take 10+ seconds. A user who opens the Statistics tab would wait through all four computations. The grid search in particular can run hundreds of backtests. This would also thrash the FastAPI process.

**Do this instead:** Each tab component fetches its own data. Statistics tab auto-fetches on activation. Backtest and Optimize require an explicit "Run" click. Research modules use per-module run buttons.

### Anti-Pattern 2: Storing Tab Results in PairContext

**What people do:** Add `backtestResult`, `researchResults`, `statsResult` to the global PairContext so results persist across tab switches.

**Why it is wrong:** PairContext is already used by the Header and Sidebar — it is a layout-level concern. Adding computation results to it mixes concerns, makes the context fat, and complicates clearing stale results on pair change. Tab results are page-scoped, not app-scoped.

**Do this instead:** Keep results in tab-local `useState`. Results persist for the lifetime of the page component (i.e., as long as the user is on `/pair-analysis`). When the user navigates away and back, state resets — which is acceptable and matches user expectations.

### Anti-Pattern 3: Directly Mutating PairContext from a Tab Component

**What people do:** A tab sees "recommended_backtest_params" in a research module response and calls `setTimeframe()` or `setAsset1()` from within the tab to apply the recommendation.

**Why it is wrong:** The recommendation is a suggestion, not an imperative. Silently changing the global pair selection from within a sub-component breaks the user's mental model. The pair selector in the Header changes, other tabs get invalidated, and the user has no idea why.

**Do this instead:** Show a "Use these parameters" button that visibly communicates the action. For backtest params, pre-populate the Backtest tab form rather than mutating global context. Only `Header` and `ScannerPage` should ever write to PairContext.

### Anti-Pattern 4: Inline Chart Data Transformation Inside PlotlyChart

**What people do:** Pass raw API response data directly into `PlotlyChart` and do the transformation (timestamps → Date objects, response fields → Plotly trace objects) inside the `PlotlyChart` component via extra props.

**Why it is wrong:** `PlotlyChart` is a pure rendering wrapper. Adding transformation logic inside it would require it to know about domain types (`CointegrationResponse`, `BacktestResponse`, etc.), creating tight coupling.

**Do this instead:** Each tab component owns the transformation from API response to Plotly `Data[]` and `Layout`. Keep `PlotlyChart` generic — it only accepts `data`, `layout`, `config`, and `style`. This pattern is already established in the codebase (`PlotlyChart.tsx` confirmed by inspection).

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| FastAPI :8000 | Direct HTTP fetch via `apiFetch()` in `lib/api.ts` | No proxy — frontend calls backend directly. CORS allows all origins. |
| Bitvavo (via backend) | Triggered by backend cache-miss path | Frontend never calls Bitvavo; only the backend DataCacheManager does. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `Scanner` → `PairAnalysis` | PairContext write + `router.push()` | The canonical cross-page flow |
| `Header` → all pages | PairContext write | Pair changes broadcast to any page that reads context |
| Tab components → `api.ts` | Direct import, typed function calls | No abstraction layer between tabs and API client |
| `PairAnalysisPage` → tabs | React children / conditional render | The page renders the active tab's component; no prop drilling of data |

---

## Scaling Considerations

This is a single-user local tool. Scaling is not a concern. The relevant scaling axis is UI complexity as more features are added.

| Concern | Current Scale | If 3+ more tabs added |
|---------|--------------|----------------------|
| Tab state management | `useState` per tab in page component is sufficient | Consider a `useReducer` in the page or a lightweight context scoped to `PairAnalysisPage` |
| Number of Plotly charts rendered | 2-4 charts per tab, only one tab visible | Each `PlotlyChart` is SSR-safe via `next/dynamic`; no perf issue |
| Research tab length | 8 modules stacked | Mantine `Accordion` keeps page manageable; no pagination needed |
| Parameter form complexity | ~8 fields for backtest | Mantine `NumberInput` + `Slider` handles this; no form library needed |

---

## Sources

- Live codebase inspection (2026-03-31):
  - `frontend/src/contexts/PairContext.tsx`
  - `frontend/src/components/academy/real-data/RealDataSection.tsx`
  - `frontend/src/components/charts/PlotlyChart.tsx`
  - `frontend/src/lib/api.ts` (all endpoint types)
  - `frontend/src/app/(dashboard)/scanner/page.tsx`
  - `frontend/src/components/layout/Header.tsx`, `Sidebar.tsx`
  - `frontend/src/app/(dashboard)/layout.tsx`
  - `frontend/next.config.ts` (cacheComponents not enabled)
- Next.js 16 local docs (`node_modules/next/dist/docs/`):
  - `01-app/02-guides/preserving-ui-state.md` — Activity component, state preservation patterns
- `.planning/codebase/ARCHITECTURE.md` — existing system architecture
- `.planning/codebase/STRUCTURE.md` — existing project structure
- `.planning/PROJECT.md` — milestone requirements

---

*Architecture research for: interactive backtesting/research UI, statistical-arbitrage-v3*
*Researched: 2026-03-31*
