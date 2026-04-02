# Phase 4: Research Tab - Research

**Researched:** 2026-04-02
**Domain:** React/TypeScript frontend — Mantine v8 Accordion, Plotly.js chart variants, cross-tab state lifting
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Use Mantine Accordion for the 8 research modules. Each module is a collapsible section with title and Run button visible in the accordion header.
- **D-02:** Multiple modules can be expanded simultaneously (`multiple` prop on Accordion). Users can compare findings across modules.
- **D-03:** Modules are grouped under 3 labeled section headers: Pair Stability (Rolling Stability, OOS Validation, Cointegration Method), Parameter Tuning (Lookback Window Sweep, Z-Score Threshold, Transaction Cost), Method Comparison (Spread Method, Timeframe Comparison).
- **D-04:** Per-module Run buttons only — no "Run All" button.
- **D-05:** Run button is in the accordion header, visible when collapsed. Clicking Run on a collapsed section auto-expands it when results arrive.
- **D-06:** Lift backtest parameter state to pair-analysis page level. `page.tsx` holds `pendingBacktestParams` state via `useState<BacktestRequest | null>(null)`. ResearchTab receives `onApplyToBacktest` callback; BacktestTab receives `pendingParams` prop and `onParamsConsumed` callback.
- **D-07:** Clicking "Apply to Backtest" auto-switches to the Backtest tab with params pre-filled in the form.
- **D-08:** Apply does NOT auto-run the backtest — only pre-fills the form.
- **D-09:** Claude's discretion on chart type per module based on data structure.
- **D-10:** Mantine Alert for takeaway callouts: `color="green"` / `color="yellow"` / `color="red"`. Between chart and Apply button.
- **D-11:** Takeaway text rendered verbatim from `takeaway.text` — no frontend interpretation.

### Claude's Discretion
- Exact chart heights and sizing per module (defined in UI-SPEC: 260px rolling, 240px OOS/lookback, 220px coint/tx/spread/timeframe, 280px heatmap)
- Chart configuration details (axis labels, hover tooltips, reference lines)
- Module ordering within each group
- Loading state skeleton design
- Whether to show "recommended" badge on best result row/bar
- How to handle null `recommended_backtest_params` (hide Apply button — resolved: hide)
- Exact section header styling for the 3 groups

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RSRCH-01 | User can run each of the 8 research modules independently for the selected pair | Each module gets isolated useState (loading/error/data). Run button triggers single API call. Accordion `multiple` prop allows any combination to be open simultaneously. |
| RSRCH-02 | Each research module displays chart results and contextual takeaway callout (info/warning/error severity) | Mantine Alert with `color` from `takeaway.severity`. Text from `takeaway.text` verbatim. Chart types per module defined in UI-SPEC. |
| RSRCH-03 | User can click "Apply to Backtest" to pre-fill the Backtest tab with recommended parameters | State lifted to page.tsx. `onApplyToBacktest` callback → `pendingBacktestParams` state + tab switch. BacktestTab receives `pendingParams` prop. |
| RSRCH-04 | Research modules load lazily (not all at once) to prevent chart initialization performance issues | Click-triggered fetch pattern (no useEffect auto-load). Each module independent. PlotlyChart SSR-safe via `next/dynamic`. |
| RSRCH-05 | User can view rolling cointegration stability chart showing p-value over time with significance reference line | `postRollingStability` → line chart of `p_value` over `timestamp`. Reference line shape at y=0.05 with `dash: 'dash'`. Cointegrated windows as green markers. |
</phase_requirements>

---

## Summary

Phase 4 builds the ResearchTab component that replaces the "coming in Phase 4" placeholder in `pair-analysis/page.tsx`. The tab displays 8 research modules inside a Mantine Accordion with independent run/load/error state per module. Each module fetches one of the 8 existing backend endpoints (`/api/research/*`), renders a chart appropriate to its data shape, and shows a severity-colored takeaway callout. A cross-tab "Apply to Backtest" mechanism requires lifting parameter state to page level and adding props to BacktestTab.

The entire API client layer, backend endpoints, TypeScript interfaces, and UI design contract already exist. This phase is a pure frontend implementation task — no new backend work needed. All API functions and response interfaces are in `frontend/src/lib/api.ts`. All chart types and dimensions are specified in `04-UI-SPEC.md`. The main complexity is correct Accordion controlled-state management (to auto-expand on run), and the cross-tab param-passing integration.

**Primary recommendation:** Create `ResearchTab.tsx` with 8 per-module state tuples, controlled Mantine Accordion with `multiple` and `value` as `string[]`, then modify `page.tsx` and `BacktestTab.tsx` for cross-tab state passing.

---

## Standard Stack

### Core (all already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@mantine/core` | 8.3.18 | Accordion, Alert, Badge, Button, Skeleton, Stack, Group, Text, Paper, Loader | Project-locked component library (CLAUDE.md) |
| `react-plotly.js` | ^2.6.0 | Chart rendering inside PlotlyChart wrapper | Project-locked charting library (CLAUDE.md) |
| `next` | 16.2.1 | App Router, `next/dynamic` for SSR-safe Plotly | Project-locked framework (CLAUDE.md) |
| `@tabler/icons-react` | ^3.40.0 | IconPlayerPlay, IconArrowRight, IconAlertTriangle | Project-locked icon library (CLAUDE.md) |

**No new packages needed.** All dependencies are already installed.

### API Functions (already in api.ts)
| Function | Endpoint | Has `recommended_backtest_params` |
|----------|----------|----------------------------------|
| `postRollingStability` | POST /api/research/rolling-stability | null (always) |
| `postOOSValidation` | POST /api/research/oos-validation | null (always) |
| `postCointMethodComparison` | POST /api/research/coint-method | null (always) |
| `postLookbackSweep` | POST /api/research/lookback-window | BacktestRequest (always non-null) |
| `postZScoreThreshold` | POST /api/research/zscore-threshold | BacktestRequest or null |
| `postTxCost` | POST /api/research/tx-cost | BacktestRequest (always non-null — Bitvavo 0.25%) |
| `postSpreadMethodComparison` | POST /api/research/spread-method | null (always) |
| `postTimeframeComparison` | POST /api/research/timeframe-comparison | null (always) |

---

## Architecture Patterns

### Recommended Project Structure

New files created in this phase:
```
frontend/src/
├── app/(dashboard)/pair-analysis/
│   └── page.tsx                          # MODIFY: add pendingBacktestParams state, controlled tab value, pass props
└── components/pair-analysis/
    ├── StatisticsTab.tsx                 # NO CHANGE
    ├── BacktestTab.tsx                   # MODIFY: accept pendingParams + onParamsConsumed props
    └── ResearchTab.tsx                   # CREATE: 8-module accordion component
```

### Pattern 1: Controlled Accordion with Auto-Expand on Run

The Mantine v8 Accordion with `multiple` uses `value: string[]` (not `string | null`) and `onChange: (value: string[]) => void`. To auto-expand a panel when results arrive, hold the open-panel set in state and push to it on successful API response.

```typescript
// Source: verified from @mantine/core 8.3.18 Accordion.mjs source
const [openPanels, setOpenPanels] = useState<string[]>([]);

function handleRun(moduleKey: string) {
  setModuleLoading(prev => ({ ...prev, [moduleKey]: true }));
  postSomeModule(req)
    .then(res => {
      setModuleData(prev => ({ ...prev, [moduleKey]: res }));
      // Auto-expand: add moduleKey if not already in the list
      setOpenPanels(prev => prev.includes(moduleKey) ? prev : [...prev, moduleKey]);
    })
    .catch(/* ... */)
    .finally(() => setModuleLoading(prev => ({ ...prev, [moduleKey]: false })));
}

<Accordion multiple value={openPanels} onChange={setOpenPanels}>
  <Accordion.Item value="rolling_stability">
    <Accordion.Control>
      <Group justify="space-between">
        <Text>Rolling Stability</Text>
        <Button size="xs" onClick={(e) => { e.stopPropagation(); handleRun('rolling_stability'); }}>
          Run
        </Button>
      </Group>
    </Accordion.Control>
    <Accordion.Panel>...</Accordion.Panel>
  </Accordion.Item>
</Accordion>
```

**Critical:** `e.stopPropagation()` on the Run button prevents the Accordion from toggling collapsed/expanded when the user clicks Run. Without it, clicking Run collapses the panel instead of triggering the fetch.

### Pattern 2: Per-Module State Tuples

Each of the 8 modules gets its own loading/error/data state. Use separate `useState` calls — not a single object state — to avoid unnecessary re-renders across unrelated modules.

```typescript
// 8 × 3 = 24 useState calls total (loading, error, data per module)
const [rollingLoading, setRollingLoading] = useState(false);
const [rollingError, setRollingError] = useState<string | null>(null);
const [rollingData, setRollingData] = useState<RollingStabilityResponse | null>(null);
// ... repeat for each module
```

Alternatively, use an object keyed by module name — but then ALL modules re-render on any module state change. For 8 modules with Plotly charts this is a performance concern. Separate `useState` calls are preferred (Confidence: MEDIUM — this is a judgment call; either works at this scale).

### Pattern 3: Cross-Tab Param Passing (D-06/D-07)

The page holds a controlled tab value and a pending params state. This requires converting from the current URL-driven tab to a hybrid approach: URL still controls tab on manual click, but programmatic switch on Apply goes through the router.

```typescript
// In page.tsx — add to PairAnalysisContent:
const [pendingBacktestParams, setPendingBacktestParams] = useState<BacktestRequest | null>(null);

function handleApplyToBacktest(params: BacktestRequest) {
  setPendingBacktestParams(params);
  handleTabChange('backtest'); // existing function — sets URL param
}

// Pass down:
<ResearchTab onApplyToBacktest={handleApplyToBacktest} />
<BacktestTab pendingParams={pendingBacktestParams} onParamsConsumed={() => setPendingBacktestParams(null)} />
```

```typescript
// In BacktestTab.tsx — add props interface:
interface BacktestTabProps {
  pendingParams?: BacktestRequest | null;
  onParamsConsumed?: () => void;
}

// Consume in useEffect:
useEffect(() => {
  if (pendingParams) {
    setParams({ ...pendingParams.strategy });
    onParamsConsumed?.();
  }
}, [pendingParams]); // eslint-disable-line react-hooks/exhaustive-deps
```

The `BacktestRequest` interface in `api.ts` has a `strategy: StrategyParametersPayload` field. The BacktestTab `params` state is typed as `StrategyParametersPayload`. So `pendingParams.strategy` maps directly to `setParams`.

### Pattern 4: Pair-Change Reset

When asset1/asset2/timeframe changes, reset ALL 8 modules' state to clear stale results. Use `useEffect` with the pair deps — same pattern as BacktestTab's existing pair-change clear.

```typescript
useEffect(() => {
  // Clear all 8 module states
  setRollingLoading(false); setRollingError(null); setRollingData(null);
  // ... repeat for all 7 other modules
  setOpenPanels([]); // collapse all panels
}, [asset1, asset2, timeframe]);
```

### Pattern 5: Rolling Stability Chart with Reference Line

RSRCH-05 requires a significance reference line at p=0.05. Plotly shapes with `xref: 'paper'` span the full chart width regardless of data range.

```typescript
// Source: verified from BacktestTab.tsx pattern (buildZScoreShapes) and UI-SPEC
const rollingStabilityLayout = {
  shapes: [
    {
      type: 'line' as const,
      x0: 0, x1: 1, xref: 'paper' as const,
      y0: 0.05, y1: 0.05,
      line: { color: '#339AF0', width: 1, dash: 'dash' as const },
    },
  ],
  xaxis: { type: 'date' as const },
  yaxis: { title: { text: 'p-value' }, range: [0, 1] },
  annotations: [{ xref: 'paper' as const, yref: 'y' as const, x: 0.02, y: 0.05, text: 'p=0.05', showarrow: false, font: { color: '#339AF0', size: 10 } }],
};

// Two traces: main line + green markers for cointegrated windows
const rollingTraces = [
  {
    type: 'scatter' as const,
    mode: 'lines' as const,
    x: results.map(r => new Date(r.timestamp).toISOString()),
    y: results.map(r => r.p_value),
    line: { color: '#339AF0', width: 1.5 },
    name: 'p-value',
    connectgaps: false, // p_value can be null
  },
  {
    type: 'scatter' as const,
    mode: 'markers' as const,
    x: results.filter(r => r.is_cointegrated).map(r => new Date(r.timestamp).toISOString()),
    y: results.filter(r => r.is_cointegrated).map(r => r.p_value),
    marker: { color: '#51CF66', size: 6 },
    name: 'Cointegrated',
  },
];
```

Note: `RollingStabilityResultPayload.p_value` is typed as `number | null` in api.ts. Plotly handles null as a gap in lines when `connectgaps: false`. Filter nulls for the green markers to avoid NaN in the y array.

### Pattern 6: Heatmap for Z-Score Threshold Module

The ZScoreThreshold module returns a flat array of `ThresholdResultPayload` with `entry`, `exit`, and `total_trades`. Convert to a 2D heatmap by pivoting.

```typescript
// Pivot flat results to 2D z-matrix for heatmap
const entryValues = [...new Set(results.map(r => r.entry))].sort((a, b) => a - b);
const exitValues = [...new Set(results.map(r => r.exit))].sort((a, b) => a - b);
const zMatrix = entryValues.map(entry =>
  exitValues.map(exit => {
    const row = results.find(r => r.entry === entry && r.exit === exit);
    return row?.total_trades ?? 0;
  })
);

const heatmapTrace = {
  type: 'heatmap' as const,
  x: exitValues,
  y: entryValues,
  z: zMatrix,
  colorscale: 'Blues',
  colorbar: { title: 'Trades' },
};
```

### Anti-Patterns to Avoid
- **Single shared loading state for all modules:** Each module must be independently runnable (RSRCH-01). A shared `loading` boolean blocks all other modules while one is computing.
- **useEffect auto-load on mount:** This triggers all 8 modules simultaneously and defeats RSRCH-04 (lazy loading). Only user click triggers a fetch.
- **Not stopping propagation on Run button in Accordion.Control:** Without `e.stopPropagation()`, clicking Run collapses/expands the Accordion item instead of triggering the API call.
- **Forgetting to handle null p_value in rolling stability:** `p_value: number | null` — filter out nulls before computing marker y values, else Plotly renders NaN as 0.
- **Using `type` prop as `string` instead of `as const`:** TypeScript strict mode requires literal types for Plotly trace/shape type fields. Use `'scatter' as const`, `'heatmap' as const`, etc.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dark theme for Plotly charts | Custom theme merge | `PlotlyChart` wrapper (already exists) | Auto-merges `PLOTLY_DARK_TEMPLATE`, handles SSR-safe dynamic import |
| Responsive chart sizing | Manual width calculation | `PlotlyChart` with `style={{ height: 'Xpx' }}` | Wrapper sets `responsive: true` and `useResizeHandler` |
| API request/response types | Manual fetch + parse | `api.ts` typed functions (already exist) | All 8 research functions fully typed, error handling via `apiFetch<T>` |
| Accordion controlled state for multi-open | Manual visibility toggle with CSS | Mantine `Accordion` with `multiple` and `value: string[]` | Built-in animation, keyboard navigation, accessibility |
| Tab switching on Apply to Backtest | Custom event emitter, Ref | State lift + `handleTabChange('backtest')` via existing URL router | page.tsx already has `handleTabChange` that writes to URL params |

**Key insight:** Every required UI primitive and API binding already exists in the codebase. The planner's task is composition, not invention.

---

## Common Pitfalls

### Pitfall 1: Accordion `multiple` value type mismatch
**What goes wrong:** With `multiple` prop, Mantine v8 Accordion's `value` is `string[]`, not `string | null`. Passing `string | null` causes TypeScript error and incorrect behavior.
**Why it happens:** Mantine v7 used a different API. Training data may reflect old patterns.
**How to avoid:** Initialize `const [openPanels, setOpenPanels] = useState<string[]>([])`. Pass `value={openPanels}` and `onChange={setOpenPanels}`. Verified from `Accordion.mjs` source: `finalValue: multiple ? [] : null`.
**Warning signs:** TypeScript error on `value` prop — "Type 'string | null' is not assignable to type 'string[]'".

### Pitfall 2: Run button click propagates to Accordion toggle
**What goes wrong:** Clicking Run in the Accordion.Control header toggles the panel open/closed instead of triggering the API call.
**Why it happens:** `Accordion.Control` is a button element; nested buttons cause propagation.
**How to avoid:** Add `onClick={(e) => { e.stopPropagation(); handleRun(moduleKey); }}` to the Run Button. Use `variant="light"` or `size="xs"` to visually distinguish from the expand affordance.
**Warning signs:** Panel collapses when Run is clicked; API call not triggered.

### Pitfall 3: BacktestRequest asset format mismatch
**What goes wrong:** Research API functions require `asset1: 'ETH/EUR'` (slash format). BacktestTab uses the same slash format. But `PairContext` provides `asset1: 'ETH'` (no `/EUR`).
**Why it happens:** PairContext stores the base symbol; the API layer appends `/EUR`.
**How to avoid:** When calling research API functions, use `` `${asset1}/EUR` `` — same as BacktestTab's `handleRun`. All existing research function calls in api.ts expect full symbols.
**Warning signs:** 422 or 404 from backend; error message mentions unrecognized symbol format.

### Pitfall 4: Null p_value in rolling stability data
**What goes wrong:** Plotly renders NaN as 0, creating visual artifacts at the bottom of the chart.
**Why it happens:** `RollingStabilityResultPayload.p_value: number | null` — early windows may be null before the rolling window fills.
**How to avoid:** Filter nulls for marker traces: `results.filter(r => r.p_value !== null)`. For the main line trace, Plotly handles null as a gap with `connectgaps: false` (no extra filtering needed for the line).
**Warning signs:** Spiky dips to 0 at the start of the rolling stability chart.

### Pitfall 5: pendingParams consumed before BacktestTab mounts
**What goes wrong:** If user clicks Apply to Backtest and the Backtest tab hasn't mounted yet, the `useEffect` in BacktestTab that consumes `pendingParams` runs on mount and sees the non-null value — this is actually the correct behavior. But if `onParamsConsumed` clears the state before the tab renders, the params are lost.
**Why it happens:** React renders the new tab panel after the state update that switches tabs. The order is: (1) `setPendingBacktestParams(params)`, (2) `handleTabChange('backtest')`, (3) BacktestTab mounts, (4) useEffect fires and sees pendingParams.
**How to avoid:** Call `onParamsConsumed()` inside the `useEffect` in BacktestTab (after consuming), not in the page-level Apply handler. The sequence is safe because setState batching ensures the tab renders with the correct pendingParams value.
**Warning signs:** Backtest form not pre-filled after Apply to Backtest click.

### Pitfall 6: ZScoreThreshold heatmap pivot assumes complete grid
**What goes wrong:** If the backend returns fewer results than the full entry × exit grid (some combos filtered), the pivot produces missing cells.
**Why it happens:** The backend may skip threshold combos where exit >= entry (invalid). The frontend pivot must handle missing cells gracefully.
**How to avoid:** Use `results.find(r => r.entry === entry && r.exit === exit)?.total_trades ?? 0` (null-coalescing to 0) when building the z-matrix.
**Warning signs:** Heatmap has unexpected blank cells or JavaScript errors on undefined access.

---

## Code Examples

### Module Accordion Structure (verified pattern)
```typescript
// Source: Verified from @mantine/core 8.3.18 Accordion.mjs + BacktestTab.tsx Accordion pattern
'use client';

import { useState } from 'react';
import { Accordion, Button, Group, Loader, Text } from '@mantine/core';
import { IconPlayerPlay } from '@tabler/icons-react';

export default function ResearchTab({ onApplyToBacktest }: { onApplyToBacktest: (params: BacktestRequest) => void }) {
  const [openPanels, setOpenPanels] = useState<string[]>([]);

  // Per-module state (example for one module)
  const [rollingLoading, setRollingLoading] = useState(false);
  const [rollingData, setRollingData] = useState<RollingStabilityResponse | null>(null);

  async function handleRunRolling() {
    setRollingLoading(true);
    try {
      const res = await postRollingStability({ asset1: `${asset1}/EUR`, asset2: `${asset2}/EUR`, timeframe, days_back: 365 });
      setRollingData(res);
      setOpenPanels(prev => prev.includes('rolling') ? prev : [...prev, 'rolling']);
    } catch (err) {
      setRollingError(err instanceof Error ? err.message : 'Unknown error');
      setOpenPanels(prev => prev.includes('rolling') ? prev : [...prev, 'rolling']); // show error in panel
    } finally {
      setRollingLoading(false);
    }
  }

  return (
    <Accordion multiple value={openPanels} onChange={setOpenPanels}>
      <Accordion.Item value="rolling">
        <Accordion.Control>
          <Group justify="space-between" pr="sm">
            <Text size="sm" fw={500}>Rolling Stability</Text>
            <Button
              size="xs"
              variant="filled"
              color="blue"
              disabled={rollingLoading}
              leftSection={rollingLoading ? <Loader size="xs" /> : <IconPlayerPlay size={14} />}
              onClick={(e) => { e.stopPropagation(); handleRunRolling(); }}
            >
              Run
            </Button>
          </Group>
        </Accordion.Control>
        <Accordion.Panel>
          {/* chart + takeaway + apply button */}
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
```

### Takeaway Alert (from UI-SPEC + CONTEXT.md D-10/D-11)
```typescript
// Source: BacktestTab.tsx Alert pattern + CONTEXT.md D-10
import { Alert } from '@mantine/core';
import { IconAlertTriangle } from '@tabler/icons-react';

// severity: 'green' | 'yellow' | 'red' from ResearchTakeawayPayload
<Alert color={data.takeaway.severity} icon={<IconAlertTriangle size={16} />}>
  {data.takeaway.text}
</Alert>
```

### Apply to Backtest Button (null-safe, from UI-SPEC)
```typescript
// Source: CONTEXT.md D-06/D-07/D-08 + UI-SPEC null handling
import { IconArrowRight } from '@tabler/icons-react';

// Only render if recommended_backtest_params is non-null
{data.recommended_backtest_params && (
  <Button
    variant="filled"
    color="blue"
    size="xs"
    leftSection={<IconArrowRight size={16} />}
    onClick={() => onApplyToBacktest(data.recommended_backtest_params!)}
  >
    Apply to Backtest
  </Button>
)}
```

### Skeleton Loading State (from UI-SPEC)
```typescript
// Source: BacktestTab.tsx Skeleton pattern + UI-SPEC chart heights
import { Skeleton, Text } from '@mantine/core';

{moduleLoading && (
  <>
    <Skeleton height={260} /> {/* height matches module's chart height */}
    <Text size="sm" c="dimmed" ta="center">Running module...</Text>
  </>
)}
```

### Section Group Headers (from UI-SPEC)
```typescript
// Source: UI-SPEC Section Group Headers + BacktestTab.tsx section header pattern
<Text size="xs" fw={600} c="dimmed" tt="uppercase" mb="xs">
  Pair Stability
</Text>
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Mantine v7 Accordion `value: string \| null` for single, array for multiple | Mantine v8 always uses `string[]` for `multiple=true` | Mantine v8 release | Must initialize `useState<string[]>([])` not `useState<string | null>(null)` |
| Plotly axis titles as plain strings (`yaxis: { title: 'EUR' }`) | Plotly v3: title must be object form (`yaxis: { title: { text: 'EUR' } }`) | Plotly v3 | Already documented in STATE.md Phase 3 decision — PlotlyChart wrapper handles string conversion via `ChartLayout` type |

**Deprecated/outdated:**
- Mantine v7 Accordion `defaultValue` string: replaced by array in v8 multiple mode. Confirmed from source.
- Plotly string axis titles: deprecated in types but the PlotlyChart wrapper's `ChartLayout` type already handles the conversion transparently (src verified from PlotlyChart.tsx lines 43-46).

---

## Open Questions

1. **ZScoreThreshold recommended params may use stale lookback_window**
   - What we know: The backend's `/api/research/zscore-threshold` endpoint accepts `lookback_window` as an optional parameter with a default. The recommended BacktestRequest sets `lookback_window` to whatever was passed in the request.
   - What's unclear: Should the frontend send the user's currently-active lookback window (e.g., from a prior Lookback Sweep result) or always use the default?
   - Recommendation: Use `DEFAULT_STRATEGY_PARAMETERS.lookback_window` (60) for the initial call — the same value BacktestTab uses as its default. This keeps the research tab self-contained with no dependency on prior module results.

2. **TimeframeComparison request omits `timeframe` field**
   - What we know: `TimeframeRequest` interface in api.ts has `asset1`, `asset2`, `days_back`, and optional `timeframes[]` — but no `timeframe` field. The backend's response sets `timeframe: "multi"`.
   - What's unclear: Nothing — the API is clear. The frontend should not pass `timeframe` from PairContext to this endpoint.
   - Recommendation: Construct `TimeframeRequest` without the `timeframe` field. This is already correct per the TypeScript interface.

---

## Environment Availability

Step 2.6: SKIPPED (no external dependencies identified — phase is pure frontend code changes, all required packages already installed, backend APIs already implemented).

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.4.0+ (backend) |
| Config file | `pyproject.toml` [tool.pytest] |
| Quick run command | `uv run pytest tests/test_research_api.py tests/test_research_modules.py -x` |
| Full suite command | `uv run pytest tests/ --ignore=tests/test_api.py --ignore=tests/test_backtest_api.py --ignore=tests/test_optimization_api.py --ignore=tests/test_research_api.py --ignore=tests/test_trading_api.py` |

Note: No frontend test framework is configured (no jest.config.*, no vitest.config.*, no `__tests__/` directory). All validation for this phase is manual smoke-testing of the UI.

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RSRCH-01 | Each module runs independently without triggering others | manual | — | N/A |
| RSRCH-02 | Chart + takeaway callout renders with correct severity color | manual | — | N/A |
| RSRCH-03 | Apply to Backtest pre-fills BacktestTab form and switches tab | manual | — | N/A |
| RSRCH-04 | No modules load on tab mount (lazy) | manual | — | N/A |
| RSRCH-05 | Rolling stability chart shows p-value line + p=0.05 reference | manual | — | N/A |
| Backend contracts | All 8 research endpoints return correct envelope | `uv run pytest tests/test_research_api.py -x` | ✅ exists |
| Backend logic | Research module computations correct | `uv run pytest tests/test_research_modules.py -x` | ✅ exists |

### Sampling Rate
- **Per task:** Run `uv run pytest tests/test_research_api.py -x` to verify backend contracts unchanged
- **Per wave merge:** `uv run pytest tests/ --ignore=tests/test_api.py --ignore=tests/test_backtest_api.py --ignore=tests/test_optimization_api.py --ignore=tests/test_research_api.py --ignore=tests/test_trading_api.py`
- **Phase gate:** All backend tests green + manual UI walkthrough of all 8 modules before `/gsd:verify-work`

### Wave 0 Gaps
None — existing backend test infrastructure covers all research API contracts. No new test files are needed for this frontend-only phase.

---

## Project Constraints (from CLAUDE.md)

Directives the planner MUST verify compliance with:

| Directive | Impact on This Phase |
|-----------|---------------------|
| **Polars, never Pandas** | No impact — pure frontend phase |
| **All charts via PlotlyChart wrapper** | Every chart in ResearchTab MUST use `PlotlyChart` component — no direct `<Plot>` |
| **Dark mode only** | No light-mode variants, no conditional color scheme |
| **All pages `'use client'`** | `ResearchTab.tsx` is a client component — must include `'use client'` directive |
| **PlotlyChart loaded via `next/dynamic` with `ssr: false`** | Already handled by PlotlyChart wrapper — do not import `react-plotly.js` directly |
| **TypeScript strict mode** | All props interfaces required, `as const` for Plotly literal types, no implicit any |
| **API timestamps are epoch milliseconds** | Convert timestamps via `new Date(Number(timestamp)).toISOString()` — same as BacktestTab pattern |
| **PairContext via `usePairContext()` hook** | Use `usePairContext()`, not `useContext(PairContext)` directly |
| **Components in `components/pair-analysis/`** | `ResearchTab.tsx` goes in `frontend/src/components/pair-analysis/` |
| **No GSD bypasses** | All file changes go through GSD workflow (CLAUDE.md) |

---

## Sources

### Primary (HIGH confidence)
- `frontend/src/lib/api.ts` lines 246-811 — All 8 research TypeScript interfaces and API functions, verified directly
- `frontend/node_modules/@mantine/core/esm/components/Accordion/Accordion.mjs` — Verified Mantine v8 Accordion `multiple` uses `string[]` for value, not `string | null`
- `api/routers/research.py` — Backend endpoints verified; confirmed which modules return non-null `recommended_backtest_params`
- `frontend/src/components/pair-analysis/BacktestTab.tsx` — Verified existing Accordion, Alert, Skeleton, PlotlyChart patterns
- `frontend/src/components/charts/PlotlyChart.tsx` — Verified wrapper API, `ChartLayout` type handles string→object title conversion
- `.planning/phases/04-research-tab/04-UI-SPEC.md` — Verified chart heights, colors, component inventory, interaction contracts
- `.planning/phases/04-research-tab/04-CONTEXT.md` — Locked decisions D-01 through D-11
- `frontend/package.json` + `node_modules/@mantine/core/package.json` — Verified actual installed versions: Mantine 8.3.18, Next.js 16.2.1

### Secondary (MEDIUM confidence)
- `tests/test_research_api.py` — Confirmed all 8 research endpoints are tested; test file exists and is structured
- `.planning/STATE.md` — Confirmed Phase 3 decision: Plotly v3 axis titles use object form (already handled by PlotlyChart wrapper)

### Tertiary (LOW confidence)
None — all findings verified against source files directly.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified from `node_modules`, all API functions verified from source
- Architecture: HIGH — Accordion behavior verified from Mantine source, cross-tab pattern verified from existing BacktestTab code
- Pitfalls: HIGH — stopPropagation pitfall verified from Mantine Accordion.Control DOM structure; null p_value verified from TypeScript interface; BacktestRequest format verified from api.ts

**Research date:** 2026-04-02
**Valid until:** 2026-05-02 (stable stack — Mantine, Next.js, Plotly all pinned in package.json)
