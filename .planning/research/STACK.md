# Stack Research

**Domain:** Interactive financial backtesting UI (research & parameter tuning)
**Researched:** 2026-03-31
**Confidence:** HIGH for core stack (all locked in); MEDIUM for supporting libraries (verified current)

---

## Context: This Is a Brownfield Addition

The core stack is **locked in** from Phase 1 and must not change:

- Next.js 16.2.1 (App Router)
- React 19.2.4
- Mantine v8.3.18
- Plotly.js ^3.4.0 via react-plotly.js ^2.6.0
- TypeScript strict mode
- FastAPI backend at :8000

This research focuses on **what patterns and supporting libraries** to use within that locked stack to build the research & backtesting pages well.

---

## Recommended Stack

### Core Technologies (already installed — no new installs needed)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Mantine `Tabs` | v8.3.18 | Statistics / Research / Backtest / Optimize tab switching | Built-in controlled mode (`value`/`onChange`), `keepMounted={false}` per-tab isolation, WAI-ARIA keyboard navigation. No external router dependency needed for in-page tabs. |
| Mantine `Slider` + `onChangeEnd` | v8.3.18 | Z-score threshold, lookback window parameter tuning | `onChangeEnd` fires only when the user releases the thumb — ideal for expensive backend calls. `onChange` would trigger on every drag pixel. |
| Mantine `NumberInput` | v8.3.18 | Precise numeric parameter entry alongside sliders | `min`/`max`/`step`/`clampBehavior="strict"` prevent out-of-range values. `suffix` prop for units (e.g. "d" for days). Shares the same state with paired Slider. |
| Mantine `Grid` (12-col) | v8.3.18 | Parameter panel + chart panel side-by-side layout | `Grid.Col span={4}` / `span={8}` gives the classic sidebar-chart split. Use over `SimpleGrid` when column widths differ. |
| Plotly.js subplots | ^3.4.0 | Equity curve + drawdown stacked with shared x-axis | Stacked subplots via `yaxis.domain` ranges share x-axis automatically — linked zoom/pan requires no extra code. Already wrapped in `PlotlyChart`. |
| Plotly.js heatmap trace | ^3.4.0 | Grid search parameter heatmap (Optimize tab) | Native `type: 'heatmap'` with `colorscale: 'RdYlGn'` gives immediate visual of good/bad parameter regions. `text` + `texttemplate` overlays values on cells. |

### Supporting Libraries (new installs required)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `use-debounce` | ^10.1.1 | Debounce rapid input changes before triggering API calls | Use `useDebouncedCallback` on any input that should trigger a lightweight chart update (e.g. lookback window preview). Do NOT use for full backtest runs — use an explicit Run button instead. |
| `mantine-datatable` | ^8.3.13 | Sortable, formatted results table for top backtest runs | Use in the Optimize tab to display grid search results ranked by Sharpe. Built-in column sorting, custom cell rendering for colored metrics, row highlighting. Mantine v8 compatible. |

### Development Tools (already configured — no changes needed)

| Tool | Purpose | Notes |
|------|---------|-------|
| ESLint + eslint-config-next | TypeScript/React linting | Already configured in `frontend/eslint.config.mjs` |
| TypeScript strict mode | Catch parameter type errors at compile time | Already enabled in `frontend/tsconfig.json` |

---

## Installation

```bash
cd frontend

# Supporting libraries
npm install use-debounce mantine-datatable
```

All core libraries (Mantine, Plotly, React, Next.js) are already installed.

---

## Key Patterns

### Pattern 1: Slider + NumberInput paired parameter control

Share a single `useState` value. Slider uses `onChangeEnd` (not `onChange`) to avoid firing on every drag pixel. NumberInput uses `onChange` since keyboard input is already discrete.

```tsx
const [lookback, setLookback] = useState(60);

<Slider
  value={lookback}
  onChange={setLookback}          // update display immediately
  onChangeEnd={handleParamChange} // trigger expensive ops only on release
  min={20} max={200} step={5}
/>
<NumberInput
  value={lookback}
  onChange={(v) => { setLookback(Number(v)); handleParamChange(Number(v)); }}
  min={20} max={200} step={5}
  suffix="d"
  clampBehavior="strict"
/>
```

### Pattern 2: Run button for backtests, debounced preview for lightweight ops

Backtests are expensive (seconds). Never run them on every parameter change. Use:
- **Explicit "Run Backtest" button** — user must click to trigger `POST /api/backtest`
- `useTransition` from React 19 to track `isPending` and show a loading state on the button
- `useDebouncedCallback` (300–500ms) only for lightweight read-only previews (e.g. re-rendering a spread chart after lookback change)

```tsx
const [isPending, startTransition] = useTransition();

const runBacktest = () => {
  startTransition(async () => {
    const result = await postBacktest(params);
    setBacktestResult(result);
  });
};

<Button onClick={runBacktest} loading={isPending}>
  Run Backtest
</Button>
```

### Pattern 3: Stacked equity + drawdown chart with shared x-axis

A single Plotly figure with two y-axes using `domain` keeps zoom/pan linked automatically. Pass to the existing `PlotlyChart` wrapper.

```tsx
const layout = {
  yaxis:  { domain: [0.35, 1],    title: 'Equity (EUR)' },
  yaxis2: { domain: [0, 0.30],    title: 'Drawdown %' },
  // No xaxis reassignment on traces — sharing is automatic
  uirevision: 'backtest',  // preserves zoom state across data updates
};
```

Set `uirevision` to a constant string so user zoom is preserved when the chart re-renders after a new backtest run. Change `uirevision` only when you want to reset the view.

### Pattern 4: Tabs with keepMounted={false}

Use `keepMounted={false}` on `Tabs` so inactive panels unmount. This means each tab fetches its data lazily when first activated — avoids loading all 8 research modules at page load.

```tsx
<Tabs defaultValue="statistics" keepMounted={false}>
  <Tabs.List>
    <Tabs.Tab value="statistics">Statistics</Tabs.Tab>
    <Tabs.Tab value="research">Research</Tabs.Tab>
    <Tabs.Tab value="backtest">Backtest</Tabs.Tab>
    <Tabs.Tab value="optimize">Optimize</Tabs.Tab>
  </Tabs.List>
  <Tabs.Panel value="statistics"><StatisticsTab /></Tabs.Panel>
  <Tabs.Panel value="backtest"><BacktestTab /></Tabs.Panel>
  ...
</Tabs>
```

### Pattern 5: Parameter heatmap for grid search results

Grid search returns a 2D array of Sharpe ratios indexed by two parameters (e.g. entry threshold vs lookback). Pass directly to Plotly heatmap:

```tsx
const data = [{
  type: 'heatmap',
  z: sharpeMatrix,       // 2D array [[sharpe, ...], ...]
  x: entryThresholds,    // x-axis labels
  y: lookbackDays,       // y-axis labels
  colorscale: 'RdYlGn',  // red = bad, green = good
  text: sharpeMatrix,    // show values in cells
  texttemplate: '%{text:.2f}',
  hoverongaps: false,
}];
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `mantine-datatable` | Native Mantine `Table` | Use native `Table` only for static, non-sortable data under ~20 rows. For sortable backtest results, `mantine-datatable` saves significant implementation time. |
| `use-debounce` | Inline `setTimeout` / `lodash.debounce` | Lodash is fine if already in the bundle. `use-debounce` is preferred because it handles cleanup on unmount automatically, avoiding stale closure bugs. |
| `onChangeEnd` for Slider | `onChange` with debounce | `onChangeEnd` is semantically correct (fires on release) and zero-dependency. Debouncing `onChange` introduces a delay even for keyboard inputs. |
| `useTransition` for loading state | `useState(isLoading)` boolean | Both work. `useTransition` is React 19 idiomatic, marks the state update as non-urgent, and integrates with React's concurrent rendering. Available since React 18. |
| Plotly subplots for equity+drawdown | Two separate `PlotlyChart` components | Separate charts don't share zoom/pan. Subplots give linked interaction for free with no extra code. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `onChange` on Slider for API calls | Fires 50–100 times per second during drag; will hammer the backend | `onChangeEnd` for expensive ops; `onChange` only for instant UI updates |
| `keepMounted={true}` (default) on Tabs | All 4 tabs fetch data on page load simultaneously — 4+ API calls before user interacts | `keepMounted={false}` for lazy per-tab loading |
| `Plotly.newPlot` / full figure replace on every update | Destroys and recreates DOM — slow, loses zoom state | Set `uirevision` in layout so `react-plotly.js` uses `Plotly.react` internally for diff-based updates |
| `mantine-react-table` | Wraps TanStack Table — far more complex API than needed for displaying ~50 backtest results | `mantine-datatable` for simple sortable results; native `Table` for static data |
| Adding a separate state management library (Zustand, Redux) | Overkill — the existing `PairContext` already provides global pair selection; backtest state is local to the Backtest tab | `useState` / `useReducer` at the page level; `PairContext` for pair selection |
| `react-query` / `SWR` for data fetching | Adds complexity and cache invalidation logic; backtest results are deterministic per parameter set — no background refetch needed | Direct `fetch` + `useState` + `useTransition` pattern; matches existing `api.ts` typed client |

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `mantine-datatable` ^8.3.13 | Mantine ^8.x | Version major tracks Mantine major. Do not install mantine-datatable v6 or v7. |
| `use-debounce` ^10.1.1 | React ^18 and ^19 | Peer dep is React >=16.8. Fully compatible with React 19.2.4. |
| `react-plotly.js` ^2.6.0 | Plotly.js ^3.x | react-plotly.js 2.6 works with Plotly 3.x; already in package.json. |

---

## Sources

- [Mantine Tabs docs (v9/v8)](https://mantine.dev/core/tabs/) — controlled mode, keepMounted prop — HIGH confidence
- [Mantine NumberInput docs](https://mantine.dev/core/number-input/) — clampBehavior, suffix, step — HIGH confidence
- [Mantine Slider docs](https://mantine.dev/core/slider/) — onChangeEnd vs onChange, marks, step — HIGH confidence
- [Mantine v8.1.0 changelog](https://mantine.dev/changelog/8-1-0/) — RangeSlider domain prop, Slider domain — HIGH confidence
- [mantine-datatable GitHub](https://github.com/icflorescu/mantine-datatable) — v8.3.13 Mantine v8 compatible — HIGH confidence
- [use-debounce npm](https://www.npmjs.com/package/use-debounce) — v10.1.1, 4.9M weekly downloads, React 19 compatible — HIGH confidence
- [Plotly.js subplots docs](https://plotly.com/javascript/subplots/) — shared x-axis via yaxis.domain — HIGH confidence
- [react-plotly.js uirevision issue #90](https://github.com/plotly/react-plotly.js/issues/90) — uirevision for zoom state preservation — MEDIUM confidence (GitHub issue thread, not official docs)
- [useTransition React docs](https://react.dev/reference/react/useTransition) — isPending pattern for async operations — HIGH confidence

---
*Stack research for: interactive financial backtesting UI (research & backtesting milestone)*
*Researched: 2026-03-31*
