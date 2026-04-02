# Phase 5: Optimize Tab - Research

**Researched:** 2026-04-02
**Domain:** React/TypeScript frontend — optimization UI (Plotly heatmap, Mantine v8, cross-tab state, grid search + walk-forward)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01:** Two Mantine Select dropdowns (Parameter 1 / Parameter 2) for sweep axis selection. Below each, 3 NumberInput fields (min/max/step) with sensible defaults per parameter. Sweepable params: `entry_threshold`, `exit_threshold`, `lookback_window`, `stop_loss`, `position_size`.

**D-02:** Base strategy comes from BacktestTab's current parameter form state. Fall back to `DEFAULT_STRATEGY_PARAMETERS` when no backtest has been run. Requires lifting or sharing backtest param state from BacktestTab (similar to Phase 4's `pendingBacktestParams` pattern).

**D-03:** The 2 selected sweep axes override their corresponding values in the base strategy. All non-swept parameters stay at their base values.

**D-04:** Heatmap uses Plotly hover tooltip only (no click action). Tooltip shows: parameter values, Sharpe, total P&L, win rate, trade count.

**D-05:** Best cell highlighted with a star annotation on the heatmap.

**D-06:** A Select dropdown above the heatmap lets the user switch the coloring metric between Sharpe ratio, total P&L, win rate, and max drawdown. Re-colors heatmap client-side (no new API call).

**D-07:** Best cell summary displayed as a highlighted Paper card ABOVE the heatmap. Shows: best parameter values, Sharpe, P&L, robustness score Badge (Strong/Moderate/Weak). Includes "Apply to Backtest" button.

**D-08:** Shared axis configuration at the top of the tab. Below it, two Run buttons side-by-side: "Run Grid Search" and "Run Walk-Forward".

**D-09:** Grid Search results section: best cell card, then heatmap, then warnings/honest reporting Accordion (collapsed by default, Phase 3 pattern).

**D-10:** Walk-Forward results below Grid Search results. Walk-forward-specific controls (fold count NumberInput + train % Slider) are inline above fold table results. Defaults: 5 folds, 60% train.

**D-11:** Walk-forward fold table shows: fold index, train Sharpe, test Sharpe, train trade count, test trade count, status. Below: aggregate train/test Sharpe + stability verdict Badge (Stable=green, Moderate=yellow, Fragile=red).

**D-12:** Both operations run on explicit button click only (no auto-load), consistent with Phase 3.

**D-13:** Both best cell card and walk-forward results get "Apply to Backtest" button. Reuses Phase 4's `pendingBacktestParams` / `onApplyToBacktest` mechanism.

**D-14:** Walk-forward Apply button only appears when verdict is "stable" or "moderate". For "fragile" verdict, no Apply button.

**D-15:** Grid search warnings from `GridSearchResponse.warnings` displayed as Mantine Alert banners between Run buttons and results (Phase 3 three-tier pattern).

**D-16:** Walk-forward warnings displayed similarly above walk-forward results.

**D-17:** Honest reporting footers in collapsible Accordion sections at bottom of each result area.

### Claude's Discretion

- Exact min/max/step defaults per sweepable parameter (now resolved in UI-SPEC)
- Chart height and color scale for heatmap
- Heatmap cell annotation format
- Star/marker style for best cell highlight
- Loading state skeleton design
- Robustness score badge thresholds and labels (now resolved in UI-SPEC)
- Fold table column widths and styling
- Walk-forward index-to-timestamp mapping strategy (deferred per UI-SPEC)
- Whether to show execution time

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OPT-01 | User can configure a 2-axis grid search by selecting which two parameters to sweep and their ranges | Axis config section: two Select + three NumberInput per axis. API shape: `GridSearchRequest.axes: ParameterAxisPayload[]` already typed in `api.ts`. |
| OPT-02 | User can run grid search and view a parameter heatmap showing metric values across parameter combinations | `postGridSearch()` typed and implemented. Plotly `heatmap` trace type is supported. Client-side re-coloring by mapping `cells` array to selected metric z-values. |
| OPT-03 | User can view the best parameter combination with its metrics and robustness score | `GridSearchResponse.best_cell`, `robustness_score`, `recommended_backtest_params` already returned by API. |
| OPT-04 | User can run walk-forward validation and view a fold table with train/test Sharpe per fold | `postWalkForward()` typed and implemented. `WalkForwardFoldPayload` contains `train_metrics.sharpe_ratio`, `test_metrics.sharpe_ratio`, counts. |
| OPT-05 | User can see a stability verdict badge (stable/moderate/fragile) for walk-forward results | `WalkForwardResponse.stability_verdict: 'stable' \| 'moderate' \| 'fragile'` returned by API. |
</phase_requirements>

---

## Summary

Phase 5 is a pure frontend phase. The entire backend (grid search engine, walk-forward engine, optimization API router, all Pydantic schemas, and TypeScript API client functions) is already built and tested. The work is to replace the placeholder `<Text c="dimmed">Optimize — coming in Phase 5</Text>` in the Optimize tab panel with a new `OptimizeTab` component.

The key architectural challenge is sharing the current BacktestTab parameter state with OptimizeTab so the "base strategy" passed to the API reflects what the user has configured. The pattern established in Phase 4 (`pendingBacktestParams` / `onApplyToBacktest` as props on `page.tsx`) must be extended in the opposite direction: BacktestTab needs to expose its current `params` state up to `page.tsx`, which passes it down to OptimizeTab.

The second notable challenge is the Plotly heatmap construction. The `GridSearchResponse.cells` array is a flat 1D list ordered by the Cartesian product of axis 1 values × axis 2 values. The heatmap `z` matrix must be reconstructed from this flat array using `grid_shape` as dimensions — this pivot is the only non-trivial frontend computation in the phase.

**Primary recommendation:** Build `OptimizeTab.tsx` as a single self-contained `'use client'` component with independent loading/error/data states for grid search and walk-forward. Lift BacktestTab's `params` to `page.tsx` as `backtestParams` state and pass it down to OptimizeTab as a prop. This mirrors the existing Apply-to-Backtest pattern exactly.

---

## Standard Stack

### Core (all already installed and in use)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@mantine/core` | v8.3.18 | All UI components (Select, NumberInput, Slider, Table, Badge, Alert, Accordion, Paper, Button) | Project standard; all other tabs use it |
| `react-plotly.js` | ^2.6.0 | Heatmap chart | Project standard; accessed via `PlotlyChart` wrapper |
| `@tabler/icons-react` | ^3.40.0 | Icons (IconPlayerPlay, IconAlertTriangle) | Project standard |

### No New Dependencies

This phase introduces zero new npm packages. All needed components are already installed.

---

## Architecture Patterns

### Recommended File Structure

Only one new file is needed:

```
frontend/src/components/pair-analysis/
├── StatisticsTab.tsx      # existing
├── BacktestTab.tsx        # existing — needs one prop addition
├── ResearchTab.tsx        # existing
└── OptimizeTab.tsx        # NEW — this phase
```

The `page.tsx` file at `frontend/src/app/(dashboard)/pair-analysis/page.tsx` needs two small edits:
1. Add `backtestParams` state (lifted from BacktestTab) and pass it as prop
2. Replace the placeholder in the Optimize tab panel

### Pattern 1: Lifting BacktestTab Params to Page Level

**What:** BacktestTab currently owns `params` state internally. OptimizeTab needs these params as its "base strategy". The cleanest approach (consistent with the existing `pendingBacktestParams` pattern) is to lift `params` to `page.tsx`.

**When to use:** When two sibling components need to share state — the standard React lifting pattern.

**Implementation:**

In `page.tsx`, add alongside `pendingBacktestParams`:
```typescript
// Source: established Phase 4 pattern in this file
const [currentBacktestParams, setCurrentBacktestParams] = useState<StrategyParametersPayload>(
  DEFAULT_STRATEGY_PARAMETERS
);
```

Pass down to BacktestTab:
```typescript
<BacktestTab
  pendingParams={pendingBacktestParams}
  onParamsConsumed={() => setPendingBacktestParams(null)}
  onParamsChange={setCurrentBacktestParams}   // NEW
/>
```

Pass to OptimizeTab:
```typescript
<OptimizeTab
  baseStrategy={currentBacktestParams}
  onApplyToBacktest={handleApplyToBacktest}
/>
```

BacktestTab adds to its `updateParam` helper:
```typescript
function updateParam(key: keyof StrategyParametersPayload, value: number) {
  setParams((prev) => {
    const next = { ...prev, [key]: value };
    onParamsChange?.(next);
    return next;
  });
}
```

### Pattern 2: OptimizeTab Component State

**What:** Independent loading/error/data state for grid search and walk-forward, following the exact BacktestTab pattern.

```typescript
// Source: BacktestTab.tsx established pattern
const [gridLoading, setGridLoading] = useState(false);
const [gridError, setGridError] = useState<string | null>(null);
const [gridData, setGridData] = useState<GridSearchResponse | null>(null);

const [wfLoading, setWfLoading] = useState(false);
const [wfError, setWfError] = useState<string | null>(null);
const [wfData, setWfData] = useState<WalkForwardResponse | null>(null);
```

Pair-change clears both:
```typescript
useEffect(() => {
  setGridData(null);
  setWfData(null);
  setGridError(null);
  setWfError(null);
}, [asset1, asset2, timeframe]);
```

### Pattern 3: Heatmap Z-Matrix Construction

**What:** `GridSearchResponse.cells` is a flat array. The Plotly heatmap `z` property requires a 2D array `[y_values][x_values]`. The mapping uses `grid_shape` and axis values.

**Critical insight from API:** `grid_shape = [axis1_count, axis2_count]`. Cells are stored in row-major order (axis1 is the outer loop, axis2 is the inner loop). Axis1 values → Y-axis; axis2 values → X-axis.

**Example IIFE pattern (matching Phase 4 convention for inline derived computation):**
```typescript
// Source: Phase 4 IIFE pattern established in ResearchTab
const heatmapTraces = (() => {
  const [nRows, nCols] = gridData.grid_shape;  // [axis1_count, axis2_count]
  const zMatrix: (number | null)[][] = [];

  for (let r = 0; r < nRows; r++) {
    const row: (number | null)[] = [];
    for (let c = 0; c < nCols; c++) {
      const idx = r * nCols + c;
      const cell = gridData.cells[idx];
      if (cell.status !== 'ok') {
        row.push(null);
      } else {
        row.push(getMetricValue(cell, selectedMetric));
      }
    }
    zMatrix.push(row);
  }

  return [{
    type: 'heatmap' as const,
    x: gridData.axes[1].values,   // axis2 values on X
    y: gridData.axes[0].values,   // axis1 values on Y
    z: zMatrix,
    colorscale: colorscaleForMetric(selectedMetric),
    hovertemplate: '...%{customdata}...',
    customdata: buildCustomData(gridData.cells, nRows, nCols),
  }];
})();
```

**Note:** `ParameterAxisPayload` in `api.ts` has `min_value`, `max_value`, `step` — the actual axis value arrays must be computed client-side using `np.arange` equivalent. Use:
```typescript
function buildAxisValues(axis: ParameterAxisPayload): number[] {
  const values: number[] = [];
  for (let v = axis.min_value; v <= axis.max_value + axis.step / 2; v += axis.step) {
    values.push(Math.round(v * 1e10) / 1e10);  // match Python's rounding
  }
  return values;
}
```

### Pattern 4: Heatmap Best Cell Star Annotation

**What:** Plotly `layout.annotations` array places a star glyph at the best cell position.

```typescript
// Source: Plotly docs — annotations array in layout
const annotations = [];
if (gridData.best_cell_index !== null) {
  const nCols = gridData.grid_shape[1];
  const bestRow = Math.floor(gridData.best_cell_index / nCols);
  const bestCol = gridData.best_cell_index % nCols;
  const axis1Values = buildAxisValues(gridData.axes[0]);
  const axis2Values = buildAxisValues(gridData.axes[1]);
  annotations.push({
    x: axis2Values[bestCol],
    y: axis1Values[bestRow],
    text: '★',
    font: { size: 18, color: '#FCC419' },
    showarrow: false,
  });
}
```

### Pattern 5: Client-Side Metric Re-Coloring

**What:** When the user changes the "Color by" Select, update only `z` values and `colorscale` — no API call.

```typescript
const [selectedMetric, setSelectedMetric] = useState<string>('sharpe_ratio');

function getMetricValue(cell: GridSearchCellPayload, metric: string): number | null {
  switch (metric) {
    case 'sharpe_ratio': return cell.metrics.sharpe_ratio;
    case 'total_pnl': return cell.metrics.total_net_pnl;
    case 'win_rate': return cell.metrics.win_rate;
    case 'max_drawdown': return cell.metrics.max_drawdown_pct;
    default: return null;
  }
}

function colorscaleForMetric(metric: string): string {
  if (metric === 'win_rate') return 'Blues';
  if (metric === 'max_drawdown') return 'RdYlGn_r';  // reversed: lower drawdown = better
  return 'RdYlGn';
}
```

### Pattern 6: API Request Construction

Grid search request:
```typescript
const req: GridSearchRequest = {
  asset1: `${asset1}/EUR`,
  asset2: `${asset2}/EUR`,
  timeframe,
  days_back: 365,
  axes: [
    { name: axis1Param, min_value: axis1Min, max_value: axis1Max, step: axis1Step },
    { name: axis2Param, min_value: axis2Min, max_value: axis2Max, step: axis2Step },
  ],
  base_strategy: {
    ...baseStrategy,
    min_trade_count_warning: 3,
  },
  optimize_metric: 'sharpe_ratio',
  max_combinations: 500,
};
```

Walk-forward request (same axes, adds fold params):
```typescript
const req: WalkForwardRequest = {
  asset1: `${asset1}/EUR`,
  asset2: `${asset2}/EUR`,
  timeframe,
  days_back: 365,
  axes: [/* same axis config */],
  base_strategy: { ...baseStrategy, min_trade_count_warning: 3 },
  fold_count: foldCount,         // from NumberInput, default 5
  train_pct: trainPct / 100,     // Slider gives 50–80, API expects 0.5–0.8
  optimize_metric: 'sharpe_ratio',
  max_combinations_per_fold: 500,
};
```

### Anti-Patterns to Avoid

- **Re-running grid search on metric selector change:** The metric Select only re-renders the z-values client-side. Never call `postGridSearch()` again just because the user changes the color metric.
- **Calling `buildAxisValues()` outside the grid_shape/axes from the response:** The response `axes` contain the definitive `min_value`, `max_value`, `step` that the engine actually used. Do not use the user's input form values for heatmap axis labels — use `gridData.axes[0]` and `gridData.axes[1]`.
- **Showing bar indices as dates:** STATE.md blocker acknowledged — walk-forward fold table omits date columns. Show fold index only (1-based: `fold.fold_index + 1`).
- **Both buttons sharing a single loading flag:** Grid search and walk-forward have independent loading states. Both buttons are disabled while either is loading, but Skeleton and loading copy are per-operation.
- **Forgetting the `'use client'` directive:** OptimizeTab.tsx must begin with `'use client'` like all other tab components.
- **Accessing `gridData.axes[n].values`:** `ParameterAxisPayload` does NOT have a `values` field — only `min_value`, `max_value`, `step`. Use `buildAxisValues()` to reconstruct.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Heatmap chart | Custom SVG/canvas grid | Plotly `heatmap` trace | Native hover, colorscale, annotations, zoom |
| Dark theme application | Manual Plotly layout dark overrides | `PlotlyChart` wrapper | Auto-merges `PLOTLY_DARK_TEMPLATE` |
| SSR-safe dynamic Plotly import | `React.lazy` or manual `useEffect` import | `PlotlyChart` wrapper | Already handles `next/dynamic ssr: false` |
| API error parsing | Custom response parsing | `apiFetch<T>()` in `api.ts` | Extracts `detail` from FastAPI error payloads |
| Pair change state clearing | URL param listeners | `useEffect([asset1, asset2, timeframe])` | Established pattern in BacktestTab, StatisticsTab |

---

## Common Pitfalls

### Pitfall 1: Flat cells array → 2D heatmap z-matrix mapping

**What goes wrong:** Using `cells.map(c => c.metrics.sharpe_ratio)` directly as `z` produces a 1D array, not a 2D matrix. Plotly renders a single row.

**Why it happens:** `GridSearchResponse.cells` is flat. Plotly `heatmap` requires `z` as `number[][]`.

**How to avoid:** Reshape using `grid_shape`: `z[row][col] = cells[row * nCols + col].metrics.sharpe_ratio`. See Pattern 3 above.

**Warning signs:** Heatmap renders as a single row instead of a grid.

### Pitfall 2: axis values must be computed, not read from ParameterAxisPayload

**What goes wrong:** Trying to access `gridData.axes[0].values` throws a TypeScript error because `ParameterAxisPayload` has no `values` field.

**Why it happens:** The API only returns `min_value`, `max_value`, `step`. Discrete values are implied.

**How to avoid:** Use `buildAxisValues(axis)` helper (Pattern 3) to generate the array. Verify step rounding matches Python's `np.arange` logic.

**Warning signs:** TypeScript compile error on `.values` access; or X/Y axis labels being index numbers instead of parameter values.

### Pitfall 3: Train % Slider value vs API expected value

**What goes wrong:** Slider runs 50–80 (integer percent), but `WalkForwardRequest.train_pct` expects a float 0.5–0.8. Sending `60` instead of `0.6` returns a 422 validation error.

**Why it happens:** UI uses integer percent for readability. API uses decimal fraction.

**How to avoid:** Convert before sending: `train_pct: trainPct / 100`.

**Warning signs:** API returns 422 with detail about `train_pct` out of range.

### Pitfall 4: base_strategy missing min_trade_count_warning

**What goes wrong:** Sending `base_strategy` without `min_trade_count_warning` causes a Pydantic validation error since `StrategyParametersPayload` requires it.

**Why it happens:** `DEFAULT_STRATEGY_PARAMETERS` includes it, but if `baseStrategy` prop comes from a partially-constructed object, the field might be missing.

**How to avoid:** Always spread and add: `base_strategy: { ...baseStrategy, min_trade_count_warning: 3 }`.

### Pitfall 5: Both Run buttons should disable while EITHER operation is loading

**What goes wrong:** Only the active operation's button is disabled. User clicks the second button mid-computation, creating two concurrent requests that may corrupt results display.

**Why it happens:** Naive per-button `disabled={ownLoading}` check.

**How to avoid:** `disabled={gridLoading || wfLoading}` on both buttons.

### Pitfall 6: Plotly Accordion variant mismatch with Phase 3

**What goes wrong:** Using `variant="contained"` (Phase 3 backtest) vs `variant="separated"` (UI-SPEC requirement for optimize).

**Why it happens:** BacktestTab uses `variant="contained"`. UI-SPEC specifies `variant="separated"` for the honest reporting Accordion in this phase.

**How to avoid:** Use `<Accordion variant="separated">` in OptimizeTab.

### Pitfall 7: NumberInput onChange type mismatch

**What goes wrong:** Mantine v8 `NumberInput.onChange` fires with `string | number` (not just `number`). Directly using the value as a number fails.

**Why it happens:** NumberInput allows intermediate string states during typing (e.g., empty string, "-", "1.").

**How to avoid:**
```typescript
onChange={(v) => setAxis1Min(typeof v === 'number' ? v : parseFloat(String(v)) || 0)}
```
Or use `onBlur` for committed numeric values. The `value` prop should stay as `number` type since we initialize with known valid numbers.

---

## Code Examples

### Heatmap Trace Construction (full pattern)

```typescript
// Source: pattern synthesized from GridSearchResponse type in api.ts + Plotly heatmap docs
function buildAxisValues(axis: ParameterAxisPayload): number[] {
  const values: number[] = [];
  for (let v = axis.min_value; v <= axis.max_value + axis.step / 2; v += axis.step) {
    values.push(Math.round(v * 1e10) / 1e10);
  }
  return values;
}

// Inside render with gridData non-null:
const [nRows, nCols] = gridData.grid_shape;
const axis1Values = buildAxisValues(gridData.axes[0]);
const axis2Values = buildAxisValues(gridData.axes[1]);

const zMatrix: (number | null)[][] = Array.from({ length: nRows }, (_, r) =>
  Array.from({ length: nCols }, (_, c) => {
    const cell = gridData.cells[r * nCols + c];
    return cell.status === 'ok' ? getMetricValue(cell, selectedMetric) : null;
  })
);

const annotations = gridData.best_cell_index !== null ? [{
  x: axis2Values[gridData.best_cell_index % nCols],
  y: axis1Values[Math.floor(gridData.best_cell_index / nCols)],
  text: '★',
  font: { size: 18, color: '#FCC419' },
  showarrow: false,
}] : [];

const heatmapData: Data[] = [{
  type: 'heatmap' as const,
  x: axis2Values,
  y: axis1Values,
  z: zMatrix,
  colorscale: colorscaleForMetric(selectedMetric),
  hovertemplate:
    `${gridData.axes[1].name}: %{x}<br>` +
    `${gridData.axes[0].name}: %{y}<br>` +
    `${selectedMetric}: %{z:.3f}<extra></extra>`,
}];
```

### Walk-Forward Fold Table Row

```typescript
// Source: WalkForwardFoldPayload interface in api.ts + BacktestTab.tsx Table pattern
<Table.Tr key={fold.fold_index}>
  <Table.Td>{fold.fold_index + 1}</Table.Td>
  <Table.Td>{fold.train_metrics.sharpe_ratio?.toFixed(2) ?? 'N/A'}</Table.Td>
  <Table.Td>{fold.test_metrics.sharpe_ratio?.toFixed(2) ?? 'N/A'}</Table.Td>
  <Table.Td>{fold.train_trade_count}</Table.Td>
  <Table.Td>{fold.test_trade_count}</Table.Td>
  <Table.Td>
    <Badge size="sm" variant="light" color={foldStatusColor(fold.status)}>
      {foldStatusLabel(fold.status)}
    </Badge>
  </Table.Td>
</Table.Tr>
```

### Stability Verdict Badge

```typescript
// Source: WalkForwardResponse.stability_verdict: 'stable' | 'moderate' | 'fragile'
function verdictColor(v: 'stable' | 'moderate' | 'fragile'): string {
  return v === 'stable' ? 'green' : v === 'moderate' ? 'yellow' : 'red';
}
```

### Apply to Backtest (both sources)

```typescript
// Grid search best cell
<Button
  variant="light"
  color="blue"
  size="sm"
  onClick={() => {
    if (gridData.recommended_backtest_params) {
      onApplyToBacktest(gridData.recommended_backtest_params);
    }
  }}
>
  Apply to Backtest
</Button>

// Walk-forward (hidden when fragile)
{wfData.stability_verdict !== 'fragile' && wfData.recommended_backtest_params && (
  <Button
    variant="light"
    color="blue"
    size="sm"
    onClick={() => onApplyToBacktest(wfData.recommended_backtest_params!)}
  >
    Apply to Backtest
  </Button>
)}
```

---

## Runtime State Inventory

> Omitted — this is a greenfield frontend component phase. No renames, migrations, or stored-data mutations.

---

## Environment Availability

Step 2.6: SKIPPED — this phase is purely frontend TypeScript code. No external tools, services, CLIs, or databases are introduced. All dependencies are already installed npm packages.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 7.4+ (backend) |
| Config file | `pyproject.toml` |
| Quick run command | `uv run pytest tests/test_optimization.py -x` |
| Full suite command | `uv run pytest tests/ --ignore=tests/test_api.py --ignore=tests/test_backtest_api.py --ignore=tests/test_optimization_api.py --ignore=tests/test_research_api.py --ignore=tests/test_trading_api.py` |
| Frontend lint | `cd frontend && npm run lint` |
| Frontend build | `cd frontend && npm run build` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| OPT-01 | Axis config form renders and accepts valid ranges | manual | — | N/A |
| OPT-02 | Grid search returns a 2D heatmap from flat cells | unit (backend) | `uv run pytest tests/test_optimization.py -x` | Yes |
| OPT-02 | Heatmap renders without error in browser | manual | — | N/A |
| OPT-03 | Best cell card shows correct values from response | manual | — | N/A |
| OPT-04 | Walk-forward fold table shows correct Sharpe values | manual | — | N/A |
| OPT-05 | Stability verdict badge color matches verdict string | manual | — | N/A |

**Note:** Frontend component behavior is validated manually — no Jest/RTL is configured in this project (no `jest.config.*` found). The build check `npm run build` will catch TypeScript type errors.

### Sampling Rate

- Per task commit: `cd frontend && npm run lint && npm run build` (catches type errors and lint)
- Per wave merge: `uv run pytest tests/test_optimization.py tests/test_optimization_api.py` (verify backend not broken)
- Phase gate: Full suite + manual browser smoke test before `/gsd:verify-work`

### Wave 0 Gaps

None — existing test infrastructure is sufficient. No new test files needed for this frontend-only phase. Backend optimization tests already exist at `tests/test_optimization.py` and `tests/test_optimization_api.py`.

---

## Open Questions

1. **`ParameterAxisPayload` response does not return computed values array**
   - What we know: The response axes contain `min_value`, `max_value`, `step` only. The engine uses `np.arange` to compute discrete values.
   - What's unclear: Floating-point rounding edge cases between Python `np.arange` and JavaScript `for` loop. Example: `step=0.1` for exit_threshold may produce 0.10000000000000001 in JS.
   - Recommendation: Use `Math.round(v * 1e10) / 1e10` in `buildAxisValues()` to match Python's 10-decimal precision rounding (verified in `optimization.py` line 48: `round(float(v), 10)`).

2. **BacktestTab `onParamsChange` callback stability**
   - What we know: `useCallback` is not used on `setCurrentBacktestParams` passed as prop.
   - What's unclear: Whether omitting `useCallback` causes unnecessary re-renders.
   - Recommendation: This is low-stakes. The `setCurrentBacktestParams` setter from `useState` is stable by React contract; no `useCallback` wrapper needed.

---

## Project Constraints (from CLAUDE.md)

- **Polars (not Pandas):** Not relevant to this frontend phase. Backend core library already uses Polars.
- **Two-process architecture:** Unchanged. OptimizeTab calls existing `/api/optimization/grid-search` and `/api/optimization/walk-forward` endpoints.
- **Dark mode only:** All Mantine components inherit dark scheme. All Plotly charts go through `PlotlyChart` wrapper which auto-merges `PLOTLY_DARK_TEMPLATE`.
- **All charts via PlotlyChart wrapper:** The heatmap must be wrapped in `<PlotlyChart data={...} layout={...} style={{ height: 360 }} />`. No direct `react-plotly.js` imports in OptimizeTab.
- **TypeScript strict mode:** All props interfaces, state types, and return types must be fully annotated. No implicit `any`.
- **`'use client'` directive:** Required at top of `OptimizeTab.tsx` and in updated `page.tsx`.
- **Mantine v8:** Use `<Select>`, `<NumberInput>`, `<Slider>`, `<Table>` (with `Table.Thead`, `Table.Tr`, etc.), `<Accordion variant="separated">`. All from `@mantine/core`.
- **GSD Workflow:** Changes must go through GSD execute-phase, not direct edits.
- **API timestamps are epoch milliseconds:** Walk-forward indices are bar indices (not timestamps) per STATE.md blocker. Do not attempt to display them as dates.

---

## Sources

### Primary (HIGH confidence)

- `api/routers/optimization.py` — Full grid search and walk-forward endpoint implementations, response shapes, recommended_backtest_params logic
- `frontend/src/lib/api.ts` (lines 497–582) — `GridSearchRequest`, `GridSearchResponse`, `GridSearchCellPayload`, `WalkForwardRequest`, `WalkForwardResponse`, `WalkForwardFoldPayload`, `ParameterAxisPayload` — all verified from source
- `frontend/src/components/pair-analysis/BacktestTab.tsx` — Full component pattern (state management, click-triggered fetch, cancellation ref, pair-change effect, warning display, honest reporting Accordion, Apply pattern)
- `frontend/src/app/(dashboard)/pair-analysis/page.tsx` — Current tab shell, `pendingBacktestParams` / `handleApplyToBacktest` pattern
- `frontend/src/components/charts/PlotlyChart.tsx` — Wrapper API and dark template merge logic
- `.planning/phases/05-optimize-tab/05-CONTEXT.md` — All locked decisions D-01 through D-17
- `.planning/phases/05-optimize-tab/05-UI-SPEC.md` — Component inventory, color specs, layout structure, defaults, copywriting contract
- `src/statistical_arbitrage/backtesting/optimization.py` — `_build_axis_values()` rounding logic (line 48: `round(float(v), 10)`)

### Secondary (MEDIUM confidence)

- `frontend/node_modules/@mantine/core/esm/components/NumberInput/NumberInput.mjs` — Confirmed `onChange` fires with `string | number`; `value`, `min`, `max`, `step` props all present in v8.3.18
- `frontend/node_modules/@mantine/core/esm/components/Select/Select.mjs` — Confirmed `onChange` receives `string | null` as first argument

---

## Metadata

**Confidence breakdown:**
- API contract (request/response shapes): HIGH — verified from source files
- Component patterns: HIGH — verified from existing BacktestTab.tsx, ResearchTab.tsx
- Mantine v8 component props: HIGH — verified from installed node_modules source
- Plotly heatmap construction: HIGH — standard Plotly trace type, axis array reconstruction is deterministic
- Backend behavior: HIGH — backend fully implemented, tested, and reviewed

**Research date:** 2026-04-02
**Valid until:** 2026-05-02 (stable stack; Mantine/Plotly APIs unlikely to change within 30 days)
