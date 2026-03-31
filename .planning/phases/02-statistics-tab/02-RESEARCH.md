# Phase 2: Statistics Tab — Research

**Researched:** 2026-03-31
**Domain:** React/TypeScript frontend — Mantine v8 components, Plotly.js chart shapes, data-driven stat cards
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Use a Mantine `SimpleGrid` with Paper cards in a 4-column row (collapses to 2x2 on smaller screens). Five cards total: p-value, half-life, hedge ratio, correlation, and cointegration score (0-100).
- **D-02:** Each card includes a colored `Badge` below the value with an interpretive label. Color coding: green for strong/good values, yellow for moderate, red for weak/concerning. Examples: p-value < 0.01 = green "Strong", p-value > 0.05 = red "Weak"; half-life < 20 = green "Fast", etc.
- **D-03:** Cointegration score (0-100) shown as a 5th card. The API already returns `cointegration_score` in `CointegrationResponse`.
- **D-04:** Use Mantine `Slider` components for entry and exit threshold values. Two sliders: one for entry threshold, one for exit threshold. Chart threshold lines update as the user drags.
- **D-05:** Thresholds are symmetric — entry slider draws lines at +value and -value, exit slider draws lines at +value and -value. Two sliders total, four lines drawn.
- **D-06:** Auto-load cointegration data when the Statistics tab opens and a pair is selected. `useEffect` fires `postCointegration()` immediately. Show skeleton/loading state while fetching.
- **D-07:** Lookback period (`days_back`) is user-adjustable via a dropdown with presets (e.g., 90d, 180d, 365d, 730d).
- **D-08:** Changing the lookback dropdown auto-reloads data immediately (no separate refresh button needed).
- **D-09:** Two stacked charts with shared x-axis: spread chart on top, z-score chart below. Time axes aligned vertically.
- **D-10:** Charts are interactive — Plotly zoom (drag-select), pan, and reset-zoom supported.
- **D-11:** Hover tooltips enabled showing date + value on both charts.

### Claude's Discretion

- Exact slider range/step values for entry (e.g., 0.5-4.0) and exit (e.g., 0.0-2.0) thresholds
- Default values for entry (2.0) and exit (0.5) thresholds
- Default lookback period preset selection
- Skeleton loading component design
- Exact color thresholds for interpretive badges (what counts as "strong" vs "moderate")
- Whether to show `interpretation` text from the API response (already returned by backend)
- Chart height ratios (spread vs z-score)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| STAT-01 | User can view cointegration stat cards (p-value, half-life, hedge ratio, correlation) for the selected pair | `CointegrationResponse` already returns all four fields plus `cointegration_score`; Mantine `SimpleGrid` + `Paper` + `Badge` pattern confirmed in codebase |
| STAT-02 | User can view a spread chart showing the price relationship between the two coins | `CointegrationResponse.spread[]` + `timestamps[]` arrays ready; `PlotlyChart` wrapper handles dark theme and SSR-safety |
| STAT-03 | User can view a z-score chart with entry/exit threshold lines drawn at configurable levels | `CointegrationResponse.zscore[]` ready; Plotly `shapes` array with `type: 'line'` draws horizontal threshold lines; Mantine `Slider` drives values |
| UX-01 | All charts use the existing dark Plotly template consistent with the Academy | `PLOTLY_DARK_TEMPLATE` from `frontend/src/lib/theme.ts` auto-merged by `PlotlyChart` wrapper — no extra work needed |
| UX-03 | API errors display inline with actionable messages (not silent failures) | `apiFetch<T>()` throws `Error` with status + detail; component catches in `useEffect` and renders `Alert color="red"` |
</phase_requirements>

---

## Summary

Phase 2 is a pure frontend addition. No backend work is required — `POST /api/analysis/cointegration` exists and returns all needed fields (`p_value`, `half_life`, `hedge_ratio`, `correlation`, `cointegration_score`, `spread[]`, `zscore[]`, `timestamps[]`). The UI-SPEC (approved 2026-03-31) has already resolved all discretion items, making the design fully specified.

The implementation creates one new file: `frontend/src/components/pair-analysis/StatisticsTab.tsx`. This component is inserted into the existing `pair-analysis/page.tsx` at line 97, replacing the placeholder `<Text c="dimmed">Statistics — coming in Phase 2</Text>`. All required Mantine components (`SimpleGrid`, `Paper`, `Badge`, `Select`, `Slider`, `Skeleton`, `Alert`) are already installed. No new npm packages are needed.

The principal technical decisions to understand are: (1) how Mantine `Slider` works in controlled vs uncontrolled mode, (2) how Plotly `shapes` render horizontal threshold lines inside the `PlotlyChart` wrapper, and (3) the cleanup-flag `useEffect` fetch pattern required by the codebase.

**Primary recommendation:** Build `StatisticsTab.tsx` as a single self-contained `'use client'` component that reads `PairContext`, fetches once on mount (and on lookback change), drives threshold lines via local `useState` sliders, and delegates all rendering to existing Mantine + `PlotlyChart` primitives.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @mantine/core | 8.3.18 | `SimpleGrid`, `Paper`, `Badge`, `Slider`, `Select`, `Skeleton`, `Alert`, `Stack`, `Group`, `Text` | Project-locked; all components already installed |
| react-plotly.js | 2.6.0 | Chart rendering via `PlotlyChart` wrapper | Project-locked; SSR-safe dynamic import already wired |
| plotly.js | 3.4.0 | Underlying Plotly engine — `shapes` API for horizontal threshold lines | Project-locked |
| @tabler/icons-react | 3.40.0 | `IconAlertCircle` for error Alert | Project-locked |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `postCointegration()` (internal) | — | Typed fetch to `POST /api/analysis/cointegration` | Called in `useEffect` on mount and on lookback change |
| `PLOTLY_DARK_TEMPLATE` (internal) | — | Dark chart theme, auto-merged by `PlotlyChart` | Referenced by `PlotlyChart` automatically — no explicit usage in `StatisticsTab` |
| `usePairContext()` (internal) | — | Reads `asset1`, `asset2`, `timeframe` | Called at top of `StatisticsTab` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Mantine `Slider` | `<input type="range">` | Mantine Slider has proper dark theme integration; raw input would need custom styling |
| Two separate `PlotlyChart` instances | Single Plotly subplot | Subplots require direct `react-plotly.js` props bypassing `PlotlyChart` wrapper; two separate charts are simpler and consistent with the wrapper |

**Installation:** No new packages needed. All dependencies are already installed.

---

## Architecture Patterns

### Recommended Project Structure

```
frontend/src/
├── app/(dashboard)/pair-analysis/page.tsx    # EDIT: replace placeholder at line 97
└── components/pair-analysis/
    └── StatisticsTab.tsx                     # NEW: entire Statistics tab content
```

No barrel file (`index.ts`) needed for a single component. Direct import from `pair-analysis/page.tsx`.

### Pattern 1: Controlled Mantine Slider

**What:** Use `value` + `onChange` props (controlled mode) so the slider value can drive chart `shapes` reactively.

**When to use:** Any time slider value must synchronize with another UI element (here: Plotly shape lines).

**Example:**
```typescript
// Source: @mantine/core Slider component (node_modules inspected)
const [entryThreshold, setEntryThreshold] = useState<number>(2.0);

<Slider
  min={0.5}
  max={4.0}
  step={0.1}
  value={entryThreshold}
  onChange={setEntryThreshold}
/>
```

Key props confirmed from source inspection: `min`, `max`, `step`, `value`, `onChange`, `defaultValue`. `onChange` fires on every drag tick — no debouncing needed since updating chart shapes is cheap (no re-fetch).

### Pattern 2: Plotly Horizontal Threshold Lines via `shapes`

**What:** Pass a `shapes` array in the Plotly `layout` prop to draw horizontal lines across the full chart width.

**When to use:** Any time a horizontal reference line must be drawn without adding a scatter trace.

**Example:**
```typescript
// Source: Plotly.js documentation (verified against plotly.js 3.4.0 installed)
const zscoreLayout = {
  title: 'Z-Score',
  shapes: [
    { type: 'line', x0: 0, x1: 1, xref: 'paper', y0: entryThreshold, y1: entryThreshold,
      line: { color: '#FF6B6B', width: 1, dash: 'dash' } },
    { type: 'line', x0: 0, x1: 1, xref: 'paper', y0: -entryThreshold, y1: -entryThreshold,
      line: { color: '#FF6B6B', width: 1, dash: 'dash' } },
    { type: 'line', x0: 0, x1: 1, xref: 'paper', y0: exitThreshold, y1: exitThreshold,
      line: { color: '#FCC419', width: 1, dash: 'dot' } },
    { type: 'line', x0: 0, x1: 1, xref: 'paper', y0: -exitThreshold, y1: -exitThreshold,
      line: { color: '#FCC419', width: 1, dash: 'dot' } },
  ],
};
```

`xref: 'paper'` spans the full plot width from 0 to 1 regardless of x-axis data range. This is the correct approach when threshold lines must span the entire chart.

**CRITICAL:** The `PlotlyChart` wrapper in this codebase merges layout with `PLOTLY_DARK_TEMPLATE` but does NOT merge `shapes`. Passing `shapes` in the `layout` prop will work correctly because the spread merge only touches: `font`, `title`, `xaxis`, `yaxis`, `margin`, `legend`, `colorway`. The `shapes` key passes through untouched.

### Pattern 3: useEffect Cleanup-Flag Data Fetch

**What:** Standard project data-fetch pattern with a `cancelled` flag to avoid setting state after unmount.

**When to use:** All `useEffect` data fetches in this codebase — mandatory per CLAUDE.md and CONVENTIONS.md.

**Example:**
```typescript
// Source: frontend/src/contexts/PairContext.tsx (codebase pattern)
useEffect(() => {
  let cancelled = false;
  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await postCointegration({ asset1, asset2, timeframe, days_back: Number(daysBack) });
      if (cancelled) return;
      setData(res);
    } catch (err) {
      if (cancelled) return;
      setError(err instanceof Error ? err.message : 'Failed to load statistics');
    } finally {
      if (!cancelled) setLoading(false);
    }
  }
  load();
  return () => { cancelled = true; };
}, [asset1, asset2, timeframe, daysBack]);
```

Note: `daysBack` as a string state (Select value) must be converted to `Number(daysBack)` before passing to `postCointegration()`.

### Pattern 4: Timestamp-to-Date Conversion for Plotly x-axis

**What:** `CointegrationResponse.timestamps[]` is epoch milliseconds (integers). Plotly requires ISO string dates or JavaScript Date objects for time-axis charts.

**When to use:** Whenever rendering any chart with timestamp data from this API.

**Example:**
```typescript
// Source: api/schemas.py comment ("Timestamps are epoch milliseconds"), CLAUDE.md
const dates = data.timestamps.map((ts) => new Date(ts).toISOString());
```

Pass `dates` as the `x` array for both spread and z-score traces. This produces correctly formatted hover tooltips with human-readable dates.

### Anti-Patterns to Avoid

- **Uncontrolled Slider for chart sync:** Using `defaultValue` without `value`/`onChange` means the chart shapes won't update on drag. Always use controlled mode when slider value drives other UI.
- **Plotly subplot API:** Do not use `make_subplots` or Plotly's built-in subplot rows/cols. Use two separate `PlotlyChart` instances stacked in a `Stack`. The wrapper was built for single-chart use.
- **Bypassing PlotlyChart wrapper:** Never import `react-plotly.js` directly in components. All charts go through `PlotlyChart` per CLAUDE.md.
- **Non-null spread/zscore values without filtering:** `CointegrationResponse.spread` and `zscore` are typed as `(number | null)[]`. Pass null values directly as the Plotly `y` array — Plotly handles null by breaking the line, which is correct behavior for gaps.
- **Pandas import in backend:** Not applicable — backend is already written. But if any backend modifications are needed: use Polars only.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dark chart theme | Custom CSS overrides on Plotly | `PlotlyChart` wrapper + `PLOTLY_DARK_TEMPLATE` | Already implemented; manual overrides break consistency |
| Horizontal reference lines | Scatter traces with constant y | Plotly `shapes` in layout | Shapes don't appear in legend, don't affect y-axis autoscale, no extra trace overhead |
| Loading skeleton | Custom spinner/overlay | Mantine `Skeleton` | Matches existing pattern in `PlotlyChart` wrapper and Scanner page |
| API error display | `console.error` + empty state | Mantine `Alert color="red" variant="light"` | Required by UX-03; matches Scanner page error pattern |
| Slider color coding | Custom CSS | Mantine `Slider color` prop | Mantine handles dark-mode slider track color natively |

**Key insight:** This phase is assembly work, not invention. Every primitive needed already exists in the codebase — the task is wiring them together correctly.

---

## Common Pitfalls

### Pitfall 1: PlotlyChart Layout Merge Behavior

**What goes wrong:** Developer expects all layout keys to be deep-merged by the wrapper, then is surprised that `shapes` disappears or custom `xaxis2` keys are lost.

**Why it happens:** `PlotlyChart.tsx` explicitly merges only the keys it knows about: `font`, `title`, `xaxis`, `yaxis`, `margin`, `legend`, `colorway`. All other keys (including `shapes`) pass through from the caller's `layout` prop unmodified.

**How to avoid:** Pass `shapes` directly in the `layout` prop. It will not be clobbered. Do not rely on deep-merge for keys not listed in the wrapper's `mergedLayout` object.

**Warning signs:** Charts render without threshold lines despite the `shapes` array being in state.

### Pitfall 2: Slider onChange Fires Extremely Frequently

**What goes wrong:** Slider `onChange` fires on every pixel of drag movement, potentially causing React re-renders for every tiny slider movement.

**Why it happens:** Mantine `Slider` fires `onChange` continuously during drag, not just on release. Chart shapes are derived from slider state, so every change triggers a chart re-render.

**How to avoid:** This is acceptable for `shapes`-based updates — Plotly handles shape updates efficiently without a full chart re-render. Do not debounce; the responsiveness is a feature (D-04 says "Chart threshold lines update as the user drags"). Only re-fetch from the API on `daysBack` change, not on slider change.

**Warning signs:** Sluggish slider if the chart is re-created from scratch on every drag; profile first before optimizing.

### Pitfall 3: Stale PairContext After Pair Change

**What goes wrong:** User changes pair; `StatisticsTab` shows old data while new data loads.

**Why it happens:** Without proper key-based remounting, `useState` for data persists across pair changes.

**How to avoid:** Already handled by the parent — `page.tsx` uses `key={\`${asset1}-${asset2}\`}` on the `<Tabs>` container (line 64), which causes `StatisticsTab` to fully unmount and remount on pair change. No explicit reset logic is needed inside `StatisticsTab`.

**Warning signs:** If you see old pair's data flash before new data arrives, the parent key prop may have been removed accidentally.

### Pitfall 4: days_back Type Mismatch

**What goes wrong:** `postCointegration()` expects `days_back?: number`, but Mantine `Select` returns `string | null`. Passing the string "365" causes TypeScript to error or sends a string to the API.

**Why it happens:** Mantine Select `value` is always a string. `CointegrationRequest.days_back` is typed as `number`.

**How to avoid:** Convert explicitly: `days_back: Number(daysBack)`. Guard against null: `days_back: daysBack ? Number(daysBack) : 365`.

**Warning signs:** TypeScript strict mode will catch this at compile time if types are correct.

### Pitfall 5: null Values in spread/zscore Arrays

**What goes wrong:** Attempting to compute statistics or display values from `spread[i]` without null-checking crashes at runtime.

**Why it happens:** `CointegrationResponse.spread` is typed `(number | null)[]`. Null values appear at the beginning of rolling-window calculations (warmup bars).

**How to avoid:** Pass the array directly to Plotly `y` — Plotly renders gaps for null values correctly. Do not filter nulls before passing to Plotly. Do not perform arithmetic on these arrays without null guards.

**Warning signs:** Runtime TypeError in the browser console when accessing properties of `null`.

---

## Code Examples

Verified patterns from existing codebase files:

### StatisticsTab Component Skeleton

```typescript
// StatisticsTab.tsx — named export, 'use client' not needed (parent page is already client)
import { useState, useEffect } from 'react';
import { Alert, Badge, Group, Paper, Select, SimpleGrid, Skeleton, Slider, Stack, Text } from '@mantine/core';
import { IconAlertCircle } from '@tabler/icons-react';
import PlotlyChart from '@/components/charts/PlotlyChart';
import { postCointegration, type CointegrationResponse } from '@/lib/api';
import { usePairContext } from '@/contexts/PairContext';

const LOOKBACK_OPTIONS = [
  { value: '90', label: '90 days' },
  { value: '180', label: '180 days' },
  { value: '365', label: '1 year' },
  { value: '730', label: '2 years' },
];

export default function StatisticsTab() {
  const { asset1, asset2, timeframe } = usePairContext();
  const [daysBack, setDaysBack] = useState<string>('365');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<CointegrationResponse | null>(null);
  const [entryThreshold, setEntryThreshold] = useState<number>(2.0);
  const [exitThreshold, setExitThreshold] = useState<number>(0.5);

  useEffect(() => {
    if (!asset1 || !asset2) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    async function load() {
      try {
        const res = await postCointegration({ asset1, asset2, timeframe, days_back: Number(daysBack) });
        if (cancelled) return;
        setData(res);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Failed to load statistics');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [asset1, asset2, timeframe, daysBack]);

  // ... render
}
```

### Plotly Shapes for Threshold Lines

```typescript
// Source: Plotly.js Layout API — shapes with xref: 'paper'
function buildZScoreShapes(entry: number, exit: number) {
  return [
    { type: 'line' as const, x0: 0, x1: 1, xref: 'paper' as const,
      y0: entry, y1: entry, line: { color: '#FF6B6B', width: 1, dash: 'dash' as const } },
    { type: 'line' as const, x0: 0, x1: 1, xref: 'paper' as const,
      y0: -entry, y1: -entry, line: { color: '#FF6B6B', width: 1, dash: 'dash' as const } },
    { type: 'line' as const, x0: 0, x1: 1, xref: 'paper' as const,
      y0: exit, y1: exit, line: { color: '#FCC419', width: 1, dash: 'dot' as const } },
    { type: 'line' as const, x0: 0, x1: 1, xref: 'paper' as const,
      y0: -exit, y1: -exit, line: { color: '#FCC419', width: 1, dash: 'dot' as const } },
  ];
}
```

### Badge Color Helper

```typescript
// Badge thresholds from UI-SPEC (approved 2026-03-31)
function pValueBadge(v: number): { color: string; label: string } {
  if (v < 0.01) return { color: 'green', label: 'Strong' };
  if (v <= 0.05) return { color: 'yellow', label: 'Moderate' };
  return { color: 'red', label: 'Weak' };
}

function halfLifeBadge(v: number | null): { color: string; label: string } {
  if (v === null) return { color: 'gray', label: 'N/A' };
  if (v < 20) return { color: 'green', label: 'Fast' };
  if (v <= 50) return { color: 'yellow', label: 'Medium' };
  return { color: 'red', label: 'Slow' };
}

function correlationBadge(v: number): { color: string; label: string } {
  if (v > 0.7) return { color: 'green', label: 'High' };
  if (v >= 0.4) return { color: 'yellow', label: 'Moderate' };
  return { color: 'red', label: 'Low' };
}

function hedgeRatioBadge(v: number): { color: string; label: string } {
  if (v >= 0.5 && v <= 2.0) return { color: 'green', label: 'Balanced' };
  return { color: 'yellow', label: 'Skewed' };
}

function cointScoreBadge(v: number): { color: string; label: string } {
  if (v > 70) return { color: 'green', label: 'Strong' };
  if (v >= 40) return { color: 'yellow', label: 'Moderate' };
  return { color: 'red', label: 'Weak' };
}
```

### Timestamp Conversion for Plotly

```typescript
// Convert epoch-ms timestamps to ISO strings for Plotly x-axis
// Source: CLAUDE.md ("API timestamps are epoch milliseconds")
const dates = data.timestamps.map((ts) => new Date(ts).toISOString());
```

### Chart Configuration for Interactivity (D-10, D-11)

```typescript
// displayModeBar: 'hover' shows reset-zoom button on hover; scrollZoom enables pan/scroll
// Source: PlotlyChart wrapper (config defaults are overridable)
const chartConfig = { displayModeBar: 'hover' as const, scrollZoom: true };

<PlotlyChart
  data={[{ type: 'scatter', x: dates, y: data.spread, mode: 'lines', name: 'Spread' }]}
  layout={{ title: 'Spread', height: 260 }}
  config={chartConfig}
/>
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Plotly `layout.yaxis.range` fixed bounds for threshold lines | Plotly `shapes` with `xref: 'paper'` | Long-standing Plotly best practice | Shapes don't interfere with y-axis autoscale; threshold stays visible when user zooms |
| Uncontrolled Slider (`defaultValue`) | Controlled Slider (`value` + `onChange`) | Mantine v6+ | Required for reactive chart updates |

**Deprecated/outdated:**
- `react-plotly.js` `revision` prop: Old pattern for forcing Plotly re-renders; not needed in Plotly.js 3.x which detects prop changes automatically.

---

## Open Questions

1. **`displayModeBar: 'hover'` TypeScript type**
   - What we know: Plotly.js accepts `'hover'` as a valid value for `displayModeBar`
   - What's unclear: The `@types/react-plotly.js` type definitions may type `displayModeBar` as `boolean` only, causing a TypeScript strict-mode error
   - Recommendation: Use `displayModeBar: 'hover' as const` or cast as `Partial<Config>` to suppress. If type error occurs, fall back to `displayModeBar: false` (hides permanently) — interactive zoom via drag still works without the mode bar.

2. **CointegrationResponse half_life null handling**
   - What we know: `half_life` is typed `number | null`; `half_life_note` explains why when null
   - What's unclear: Whether to show `half_life_note` in the Half-Life stat card when null
   - Recommendation: Show "N/A" as the card value and a gray "N/A" badge. Optionally show `half_life_note` as a `Text size="xs" c="dimmed"` tooltip or beneath the badge — use Claude's discretion.

---

## Environment Availability

Step 2.6: SKIPPED — This phase is purely frontend code changes. No external CLI tools, services, runtimes, or databases beyond the project's existing Node.js + npm setup are required.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 7.4.0+ (backend only) — no frontend test framework configured |
| Config file | `pyproject.toml` (pytest section) |
| Quick run command | `uv run pytest tests/ --ignore=tests/test_api.py --ignore=tests/test_backtest_api.py --ignore=tests/test_optimization_api.py --ignore=tests/test_research_api.py --ignore=tests/test_trading_api.py` |
| Full suite command | `uv run pytest tests/` |
| Frontend tests | `npm run lint` (ESLint + TypeScript type check) — no jest/vitest configured |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STAT-01 | Stat cards render with API data | manual-only | — visual verification | ❌ no frontend test framework |
| STAT-02 | Spread chart renders with timestamps | manual-only | — visual verification | ❌ no frontend test framework |
| STAT-03 | Z-score chart with configurable threshold lines | manual-only | — visual verification | ❌ no frontend test framework |
| UX-01 | Dark Plotly template applied | manual-only | — visual verification | ❌ no frontend test framework |
| UX-03 | API error shows Alert inline | manual-only | — trigger error by stopping API | ❌ no frontend test framework |

**Frontend test justification:** No jest/vitest is configured in `frontend/package.json`. The project has no frontend test infrastructure. All five requirements are UI/visual — they require a running browser. The validation gate for this phase is: (1) ESLint passes (`npm run lint`), (2) TypeScript compiles without errors (`npm run build`), (3) manual smoke test in browser.

### Sampling Rate

- **Per task commit:** `cd /Users/luckleineschaars/repos/statistical-arbitrage-v3/frontend && npm run lint`
- **Per wave merge:** `cd /Users/luckleineschaars/repos/statistical-arbitrage-v3/frontend && npm run build`
- **Phase gate:** ESLint clean + build succeeds + manual browser verification before `/gsd:verify-work`

### Wave 0 Gaps

None — no backend changes, no new test files required. ESLint + TypeScript strict mode via `npm run build` is the automated gate.

---

## Project Constraints (from CLAUDE.md)

Directives the planner must verify compliance with:

| Directive | Impact on This Phase |
|-----------|---------------------|
| Use Polars, never Pandas | Not applicable — no backend changes in this phase |
| All Plotly charts through `PlotlyChart` wrapper | Both spread and z-score charts MUST use `PlotlyChart`, not raw `react-plotly.js` |
| Dark mode only | No light-mode color values; Mantine Badge colors must be from semantic palette |
| `'use client'` on all pages | `StatisticsTab.tsx` is used inside a `'use client'` page; it does not need its own directive but must not use server-only APIs |
| TypeScript strict mode | No `any` types; `displayModeBar: 'hover'` may need casting |
| `@/` path alias for imports | Use `@/components/charts/PlotlyChart`, `@/lib/api`, `@/contexts/PairContext` |
| Named export for reusable components | `StatisticsTab` is reusable → `export default function StatisticsTab()` (default for component files per codebase pattern) |
| `useCallback` for stable refs passed as props | Not required here — no props are passed from `StatisticsTab` to children that need stable references |
| `useState<string | null>(null)` for error | Use `useState<string | null>(null)` for the error state |
| ruff linting (backend) | Not applicable — no backend changes |
| API timestamps are epoch milliseconds | Convert with `new Date(ts).toISOString()` before passing to Plotly x-axis |
| GSD workflow enforcement | All file changes go through `/gsd:execute-phase` |

---

## Sources

### Primary (HIGH confidence)

- `frontend/src/components/charts/PlotlyChart.tsx` — full source read; confirmed layout merge behavior, wrapper props
- `frontend/src/lib/api.ts` lines 75-124, 686-697 — `CointegrationResponse` interface and `postCointegration()` function
- `frontend/src/lib/theme.ts` — full source read; `PLOTLY_DARK_TEMPLATE` colorway values confirmed
- `frontend/src/contexts/PairContext.tsx` — full source read; cleanup-flag pattern, context shape
- `frontend/src/app/(dashboard)/pair-analysis/page.tsx` — full source read; placeholder location (line 97), `key` remount prop (line 64)
- `frontend/src/app/(dashboard)/scanner/page.tsx` — full source read; established page patterns (error Alert, loading state, Badge color usage)
- `.planning/phases/02-statistics-tab/02-UI-SPEC.md` — full source read; all discretion items resolved, copy contract, layout spec
- `.planning/phases/02-statistics-tab/02-CONTEXT.md` — full source read; locked decisions D-01 through D-11
- `frontend/node_modules/@mantine/core/esm/components/Slider/Slider/Slider.mjs` — Slider props confirmed: `min`, `max`, `step`, `value`, `onChange`, `defaultValue`
- `frontend/package.json` — dependency versions confirmed

### Secondary (MEDIUM confidence)

- Plotly.js `shapes` API — `xref: 'paper'` behavior for full-width horizontal lines; confirmed against installed plotly.js 3.4.0 source (not full docs read, but pattern well-established in Plotly ecosystem)

### Tertiary (LOW confidence)

- `displayModeBar: 'hover'` TypeScript type compatibility — flagged as Open Question; `@types/react-plotly.js` 2.6.4 type definitions not deeply inspected

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages installed, versions confirmed from package.json
- Architecture: HIGH — patterns read directly from existing source files
- Pitfalls: HIGH — derived from direct source inspection (PlotlyChart merge behavior, Slider API, null types)
- Validation: HIGH — no frontend test framework exists; confirmed from package.json

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (stable stack, low churn expected)
