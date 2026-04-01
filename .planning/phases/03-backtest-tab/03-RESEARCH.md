# Phase 3: Backtest Tab - Research

**Researched:** 2026-04-01
**Domain:** Next.js 16 / React 19 / Mantine v8 frontend — wiring a parameter form + multi-chart results view to an existing FastAPI backtest endpoint
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** All 7 strategy parameters use Mantine Slider components, consistent with Phase 2 z-score threshold sliders. Each slider shows a label and current value.
- **D-02:** Sliders are grouped into 3 labeled sections: **Signal** (lookback window, entry threshold, exit threshold), **Risk Management** (stop-loss, position size), and **Execution** (initial capital, transaction fee).
- **D-03:** Parameter form stays always visible above results — no collapsing. Users can tweak and re-run immediately.
- **D-04:** Two buttons below the form: primary "Run Backtest" button and secondary "Reset to Defaults" button. Reset restores all sliders to `DEFAULT_STRATEGY_PARAMETERS` values from `api.ts`.
- **D-05:** Backtest does NOT auto-load on mount (unlike Statistics tab). User must click "Run Backtest" explicitly — per PROJECT.md "explicit run button for heavier compute".
- **D-06:** Results appear below the parameter form in this vertical order: (1) metric cards, (2) equity curve chart, (3) drawdown chart, (4) z-score chart with trade markers, (5) spread chart with trade markers, (6) trade log table, (7) collapsible Assumptions & Limitations section.
- **D-07:** 6 metric cards in a Mantine SimpleGrid row: Sharpe Ratio, Max Drawdown %, Win Rate, Total P&L (EUR), Total Trades, Final Equity. Use Paper + colored Badge pattern from Phase 2 stat cards. Remaining API metrics (Sortino, profit factor, avg trade return, avg holding period) available in expandable detail or tooltip — Claude's discretion.
- **D-08:** Results section includes a "generated for [PAIR]" context label (UX-04) to prevent misattribution.
- **D-09:** Trade entry/exit markers appear on BOTH the z-score chart and the spread chart. Z-score chart also shows entry/exit threshold horizontal lines (like Phase 2).
- **D-10:** Marker style: up-pointing triangles for entries (green = long, red = short), down-pointing triangles for exits. Stop-losses get an X marker. Standard trading chart convention.
- **D-11:** Preflight warnings (data quality) appear as Mantine Alert banners between the Run button and results. Yellow for warnings, red for blockers. Blockers prevent results from rendering — only the blocker alert shows.
- **D-12:** Overfitting warnings (Sharpe > 3.0, too few trades, etc.) appear as a yellow Mantine Alert positioned between the metric cards and the first chart. Persistent, not dismissable. Lists each flag with explanation.
- **D-13:** Assumptions & Limitations section (BT-09) uses Mantine Accordion/Collapse at the very bottom of results. Collapsed by default. Shows execution model, fee model, data basis, assumptions[], and limitations[] from the HonestReportingFooter.

### Claude's Discretion

- Exact slider min/max/step ranges for each parameter
- Default slider values (use `DEFAULT_STRATEGY_PARAMETERS` from api.ts)
- Chart heights and relative sizing
- Trade log table columns and sorting (API provides: trade_id, direction, entry/exit timestamps, prices, net_pnl, return_pct, exit_reason, bars_held, equity_after_trade)
- How secondary metrics (Sortino, profit factor, etc.) are accessible beyond the 6 main cards
- Badge color thresholds for metric cards (e.g., what Sharpe is "good" vs "poor")
- Loading state skeleton design during backtest computation
- Whether drawdown chart uses filled area or line

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BT-01 | User can configure all strategy parameters: entry threshold, exit threshold, lookback window, stop-loss, position size, transaction fee | `DEFAULT_STRATEGY_PARAMETERS` and `StrategyParametersPayload` already typed in `api.ts`; slider ranges resolved in UI-SPEC |
| BT-02 | User can run a backtest with a "Run Backtest" button and see a loading state during computation | `postBacktest()` already exists in `api.ts`; Skeleton layout defined in UI-SPEC |
| BT-03 | User can view an equity curve chart showing portfolio value over time | `equity_curve[].equity` + `equity_curve[].timestamp` from `BacktestResponse`; PlotlyChart wrapper ready |
| BT-04 | User can view trade entry/exit markers overlaid on the spread or z-score chart | `signal_overlay[]` from `BacktestResponse`; marker symbols defined in UI-SPEC (triangle-up/down, x for stop-loss) |
| BT-05 | User can view a drawdown chart showing how deep underwater the strategy went | Derived from `equity_curve`; fill-to-zero pattern confirmed in UI-SPEC |
| BT-06 | User can view key metric cards: Sharpe, max drawdown, win rate, total P&L in EUR | `metrics` object from `BacktestResponse`; 6-card grid with badge thresholds defined in UI-SPEC |
| BT-07 | User can view a trade log table with entry/exit timestamps, direction, net P&L, and exit reason | `trade_log[]` from `BacktestResponse`; column mapping defined in UI-SPEC |
| BT-08 | User sees data quality preflight warnings before results if engine detects issues | `data_quality.blockers[]` and `data_quality.warnings[]` from `BacktestResponse`; Alert component pattern documented |
| BT-09 | User can expand an "Assumptions & Limitations" section showing the honest reporting footer | `footer` object from `BacktestResponse`; Mantine Accordion pattern confirmed |
| BT-10 | User sees overfitting warning banners when engine detects them | `warnings[]` from `BacktestResponse` (engine-level, not preflight); Alert positioned between metric cards and charts |
| UX-02 | Heavy computations show loading states with appropriate feedback | Skeleton stack layout specified in UI-SPEC; disabled button with Loader during flight |
| UX-04 | Results display includes a "generated for [pair]" context label | `Text` component above metric cards, sourced from `PairContext` values |

</phase_requirements>

---

## Summary

Phase 3 is a pure frontend implementation phase. The backend API endpoint (`POST /api/backtest`), all Pydantic schemas, all engine logic, and all TypeScript API types are already in place and tested. The task is to build `BacktestTab.tsx` and wire it into the existing `pair-analysis/page.tsx` tab panel.

The component follows the same `useState`/`useEffect`/cancellation-flag pattern as `StatisticsTab.tsx`, with one key difference: computation is triggered by a button click (`handleRun`), not by a dependency change. All seven slider values live in local state; the form is always visible; results render below only when a successful run has been completed.

The most technically involved parts are: (1) building four Plotly traces with the correct marker symbols and threshold shape annotations, (2) computing the drawdown series from the equity curve (not returned directly by the API), and (3) implementing the three-tier warning display hierarchy (preflight blockers → preflight warnings → overfitting warnings).

**Primary recommendation:** Implement `BacktestTab.tsx` as a single file following the `StatisticsTab.tsx` pattern. Extract the four chart builders and the badge-threshold helpers as top-level pure functions within the file.

---

## Standard Stack

### Core (all already installed — no new packages required)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 19.2.4 | Component framework | Project-locked |
| Next.js | 16.2.1 | App Router, `'use client'` directive | Project-locked |
| Mantine core | ^8.3.18 | Slider, SimpleGrid, Paper, Badge, Alert, Accordion, Table, Skeleton, Tooltip | Project-locked |
| react-plotly.js | ^2.6.0 | Chart rendering via PlotlyChart wrapper | Project-locked |
| @tabler/icons-react | ^3.40.0 | IconPlayerPlay, IconRefresh, IconAlertTriangle | Project-locked |

**No new npm packages are needed for this phase.**

### Mantine Components Used (verified in existing code)

| Component | Import | Usage in this phase |
|-----------|--------|---------------------|
| `Slider` | `@mantine/core` | 7 strategy parameter sliders |
| `SimpleGrid` | `@mantine/core` | 6-column metric card grid |
| `Paper` | `@mantine/core` | Card containers |
| `Badge` | `@mantine/core` | Metric interpretive labels |
| `Alert` | `@mantine/core` | Preflight + overfitting warnings |
| `Accordion` | `@mantine/core` | Assumptions & Limitations section |
| `Table` | `@mantine/core` | Trade log |
| `Skeleton` | `@mantine/core` | Loading placeholders |
| `Tooltip` | `@mantine/core` | Secondary metric access on cards |
| `Button` | `@mantine/core` | Run Backtest, Reset to Defaults |
| `Loader` | `@mantine/core` | Inline in Run Backtest button during flight |
| `Stack`, `Group`, `Text` | `@mantine/core` | Layout |

All confirmed present in `StatisticsTab.tsx` and the project's `package.json`.

---

## Architecture Patterns

### Recommended Project Structure

```
frontend/src/
├── components/
│   └── pair-analysis/
│       ├── StatisticsTab.tsx        # existing — reference pattern
│       └── BacktestTab.tsx          # NEW — this phase's single new file
└── app/(dashboard)/pair-analysis/
    └── page.tsx                     # existing — replace placeholder with <BacktestTab />
```

One new component file. The page.tsx change is a 2-line import + replace.

### Pattern 1: Click-Triggered Fetch (not auto-fetch)

**What:** `postBacktest()` called inside a `handleRun` event handler, not a `useEffect`. Loading state set on click.

**When to use:** Any heavy computation where the user must explicitly initiate it (per D-05 and CLAUDE.md project constraint).

**Example:**
```typescript
// Source: StatisticsTab.tsx cancellation pattern adapted for click trigger
const [loading, setLoading] = useState(false);
const [data, setData] = useState<BacktestResponse | null>(null);
const cancelRef = useRef<boolean>(false);

function handleRun() {
  cancelRef.current = false;
  setLoading(true);
  setError(null);
  postBacktest({ asset1: `${asset1}/EUR`, asset2: `${asset2}/EUR`, timeframe, days_back: 365, strategy: params })
    .then((res) => { if (!cancelRef.current) setData(res); })
    .catch((err: unknown) => { if (!cancelRef.current) setError(err instanceof Error ? err.message : 'Backtest failed'); })
    .finally(() => { if (!cancelRef.current) setLoading(false); });
}
```

Note: A `useRef` for cancellation is preferred over a local `let cancelled` variable here because `handleRun` is not inside a `useEffect` cleanup scope.

### Pattern 2: Pair-Change State Clear

**What:** A `useEffect` keyed on `[asset1, asset2, timeframe]` that clears results and resets sliders to defaults when the pair changes.

**When to use:** Whenever stale results must not persist across pair switches (NAV-05 requirement).

**Example:**
```typescript
// Source: Phase 2 StatisticsTab behavior, NAV-05 requirement
useEffect(() => {
  setData(null);
  setError(null);
  setParams(DEFAULT_STRATEGY_PARAMETERS);
}, [asset1, asset2, timeframe]);
```

### Pattern 3: Plotly Marker Traces for Signal Overlay

**What:** Separate Plotly scatter traces for each signal type, using Plotly marker symbols.

**Signal type → Plotly marker symbol mapping:**
```typescript
// Source: Plotly.js marker.symbol documentation + UI-SPEC D-10
const MARKER_MAP = {
  long_entry:  { symbol: 'triangle-up',   color: '#51CF66', name: 'Long Entry' },
  short_entry: { symbol: 'triangle-up',   color: '#FF6B6B', name: 'Short Entry' },
  long_exit:   { symbol: 'triangle-down', color: '#51CF66', name: 'Long Exit' },
  short_exit:  { symbol: 'triangle-down', color: '#FF6B6B', name: 'Short Exit' },
  stop_loss:   { symbol: 'x',             color: '#FF922B', name: 'Stop Loss' },
};
```

The `signal_overlay` array from `BacktestResponse` provides `execution_timestamp`, `zscore_at_signal`, and `signal_type`. The spread value at each signal point must be looked up from the spread data returned by a prior cointegration call — OR derived from the equity_curve's position field. However, this creates a dependency problem.

**Resolution:** The BacktestTab gets the spread series from `PairContext` or re-uses the cointegration data that StatisticsTab already fetched. The cleanest approach is to call `postCointegration` inside BacktestTab's `handleRun` callback using the same parameters, store both responses, then use `cointegration.spread` for the spread chart overlay. This avoids cross-tab state coupling (Phase 4 blocker noted in STATE.md).

**Alternative (simpler):** Display trade markers on the equity curve and z-score chart only, skipping spread markers. But D-09 explicitly requires spread chart markers. The cointegration call approach is necessary.

**Actual simplest approach:** The backtest response contains the `signal_overlay` with `execution_timestamp` values. The spread chart data must come from somewhere. Looking at what the API returns: the backtest engine uses `build_rolling_strategy_data` which computes the spread internally, but `BacktestResponse` does not return the spread series — it returns `spread_summary` (mean + std only, not the full series). Therefore BacktestTab MUST make a parallel `postCointegration` call to get `spread[]` and `zscore[]` arrays for overlay charts. This is a known pattern (StatisticsTab already does it) and is the right approach.

### Pattern 4: Drawdown Computation from Equity Curve

**What:** Drawdown % is not returned directly by the API. Must be computed from `equity_curve[].equity`.

**Formula:**
```typescript
// Source: standard drawdown formula
function computeDrawdown(equityCurve: EquityCurvePointPayload[]): number[] {
  let runningMax = equityCurve[0]?.equity ?? 0;
  return equityCurve.map((point) => {
    if (point.equity > runningMax) runningMax = point.equity;
    return runningMax > 0 ? ((point.equity - runningMax) / runningMax) * 100 : 0;
  });
}
```

Rendered as a filled-area Plotly trace: `fill: 'tozeroy'`, `fillcolor: 'rgba(255, 107, 107, 0.3)'`, line color `#FF6B6B`.

### Pattern 5: Three-Tier Warning Display Hierarchy

**What:** Strict render order for warning banners per D-11 and D-12.

```typescript
// Tier 1: Preflight blockers — render ONLY these, block all results
if (data.data_quality.status === 'blocked') {
  return blockerAlerts; // no results, no charts
}

// Tier 2: Preflight warnings — render above results
preflight_warnings = data.data_quality.warnings; // yellow Alerts

// Tier 3: Overfitting warnings — render between metric cards and charts
overfit_warnings = data.warnings; // yellow Alert with bullet list
```

### Anti-Patterns to Avoid

- **Auto-running on mount:** BacktestTab must NOT call `postBacktest` in `useEffect`. It is triggered by button click only (D-05).
- **Showing results when status is 'blocked':** If `data_quality.status === 'blocked'`, render only blocker alerts, no charts or metrics.
- **Using Pandas:** All backend code uses Polars. Frontend does not touch dataframes. No Python changes in this phase.
- **Adding `height` as a layout prop directly:** The `PlotlyChart` wrapper expects a `style` prop for height: `style={{ height: '280px' }}`. Setting `layout.height` also works but `style` is more reliable with the resize handler.
- **Forgetting `useRef` for in-flight cancel:** Since `handleRun` is called from a button (not a `useEffect`), the local `let cancelled` pattern from `StatisticsTab` does not apply cleanly. Use `useRef<boolean>(false)` set to `true` in cleanup.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Slider input | Custom range input | Mantine `Slider` | Already in use in StatisticsTab; matches Phase 2 visual pattern |
| Collapsible section | Custom show/hide | Mantine `Accordion` | Built-in animation, keyboard accessible, matches Mantine patterns |
| Warning banners | Custom styled divs | Mantine `Alert` | Color variants (yellow, red) map exactly to warning/blocker semantics |
| Tooltip on metric cards | Custom hover state | Mantine `Tooltip` | One-liner, accessible, dark theme compatible |
| Loading placeholders | Custom shimmer CSS | Mantine `Skeleton` | Already used in StatisticsTab; consistent appearance |
| Date formatting | Custom date format | `new Date(ts).toLocaleDateString()` or ISO slice | No date library needed; timestamps are ISO strings from the API |
| Chart rendering | Custom SVG | PlotlyChart wrapper | Project-locked; handles dark theme, SSR, resize |

**Key insight:** No new dependencies. Every problem in this phase has a solution already installed and in use elsewhere in the codebase.

---

## Common Pitfalls

### Pitfall 1: Stale Signal Overlay When Cointegration Not Fetched

**What goes wrong:** Developer renders the spread + z-score charts from the backtest response alone, but `BacktestResponse` does not include the spread/zscore series — only `spread_summary` (mean + std). Charts appear without the underlying series.

**Why it happens:** The backend engine computes the spread internally for execution purposes but does not echo it back in the response.

**How to avoid:** Call `postCointegration` in parallel with `postBacktest` inside `handleRun`. Use `Promise.all([postBacktest(req), postCointegration(cointReq)])`. Store both results. Use `cointegration.spread` and `cointegration.zscore` for chart series; use `backtest.signal_overlay` for marker positions.

**Warning signs:** Z-score chart shows threshold lines but no underlying series. Spread chart is empty.

### Pitfall 2: Disabled Button Not Reflecting Loading State

**What goes wrong:** The Run Backtest button remains clickable during a fetch. User clicks twice, second response races the first, stale data overwrites fresh data.

**Why it happens:** Forgetting `disabled={loading}` on the Button component.

**How to avoid:** `<Button disabled={loading} leftSection={loading ? <Loader size="xs" /> : undefined}>Run Backtest</Button>`. Also set `cancelRef.current = false` at start of `handleRun` so the previous in-flight cancels cleanly.

### Pitfall 3: Blocked Status Renders Partial Results

**What goes wrong:** When `data_quality.status === 'blocked'`, the component still renders metric cards (with zero values) and empty charts below the blocker alert.

**Why it happens:** Not checking status before the results render block.

**How to avoid:** After setting `data`, check `data.data_quality.status === 'blocked'` in the render path and return only the blocker `Alert` banners with no results.

### Pitfall 4: Pair Change Leaves Stale Results Visible

**What goes wrong:** User switches from ETH/BTC to XRP/ADA. The previous backtest results (still in state) remain visible under the new pair's headers, with the wrong "generated for" label appearing to update but chart data still belonging to old pair.

**Why it happens:** Forgetting to clear `data` state on pair context change.

**How to avoid:** `useEffect(() => { setData(null); setParams({...DEFAULT_STRATEGY_PARAMETERS}); }, [asset1, asset2, timeframe])`. This is NAV-05 compliance.

### Pitfall 5: Drawdown Chart Shows Positive Values

**What goes wrong:** Drawdown chart shows values above zero or is inverted.

**Why it happens:** Not multiplying by -1 or using `tozeroy` fill on wrong axis.

**How to avoid:** Drawdown values are negative percentages (e.g., -15 means 15% underwater). `fill: 'tozeroy'` with `fillcolor: 'rgba(255, 107, 107, 0.3)'` on negative values fills correctly. The running-max formula in Pattern 4 produces values ≤ 0.

### Pitfall 6: `min_trade_count_warning` Exposed as a Slider

**What goes wrong:** Developer sees `min_trade_count_warning` in `StrategyParametersPayload` and adds it as an 8th slider.

**Why it happens:** The interface has 8 fields but only 7 should be exposed (UI-SPEC specifies this explicitly).

**How to avoid:** Always send `min_trade_count_warning: 3` as a hardcoded constant in the request body. Do not render a slider for it.

---

## Code Examples

Verified patterns from the existing codebase:

### Mantine Accordion (for Assumptions & Limitations)

```typescript
// Source: Mantine v8 docs pattern, consistent with project's Mantine usage
import { Accordion } from '@mantine/core';

<Accordion variant="contained" radius="sm">
  <Accordion.Item value="assumptions">
    <Accordion.Control>Assumptions & Limitations</Accordion.Control>
    <Accordion.Panel>
      <Stack gap="xs">
        <Text size="sm" fw={600}>Execution Model</Text>
        <Text size="sm">{data.footer.execution_model}</Text>
        {/* ... */}
      </Stack>
    </Accordion.Panel>
  </Accordion.Item>
</Accordion>
```

### Mantine Alert for Warnings

```typescript
// Source: existing Alert usage pattern in StatisticsTab error state
import { Alert } from '@mantine/core';
import { IconAlertTriangle } from '@tabler/icons-react';

// Preflight warning (yellow)
<Alert color="yellow" icon={<IconAlertTriangle size={16} />}>
  {warning.message}
</Alert>

// Preflight blocker (red)
<Alert color="red" icon={<IconAlertTriangle size={16} />} title="Blocked:">
  {blocker.message}
</Alert>
```

### Plotly Signal Overlay Trace

```typescript
// Source: Plotly.js scatter marker documentation + UI-SPEC D-10
const signalTrace = (signals: SignalOverlayPointPayload[], type: string, yValues: (number | null)[]) => ({
  type: 'scatter' as const,
  mode: 'markers' as const,
  x: signals.filter(s => s.signal_type === type).map(s => s.execution_timestamp),
  y: signals.filter(s => s.signal_type === type).map(s => {
    // find matching y value from series by timestamp lookup
    const idx = allTimestamps.indexOf(s.execution_timestamp);
    return idx >= 0 ? yValues[idx] : null;
  }),
  marker: { symbol: MARKER_MAP[type].symbol, color: MARKER_MAP[type].color, size: 10 },
  name: MARKER_MAP[type].name,
  showlegend: true,
});
```

### Z-Score Threshold Shapes (reuse from StatisticsTab)

```typescript
// Source: StatisticsTab.tsx buildZScoreShapes() — copy directly
function buildZScoreShapes(entry: number, exit: number) {
  return [
    { type: 'line' as const, x0: 0, x1: 1, xref: 'paper' as const, y0:  entry, y1:  entry, line: { color: '#FF6B6B', width: 1, dash: 'dash' as const } },
    { type: 'line' as const, x0: 0, x1: 1, xref: 'paper' as const, y0: -entry, y1: -entry, line: { color: '#FF6B6B', width: 1, dash: 'dash' as const } },
    { type: 'line' as const, x0: 0, x1: 1, xref: 'paper' as const, y0:  exit,  y1:  exit,  line: { color: '#FCC419', width: 1, dash: 'dot'  as const } },
    { type: 'line' as const, x0: 0, x1: 1, xref: 'paper' as const, y0: -exit,  y1: -exit,  line: { color: '#FCC419', width: 1, dash: 'dot'  as const } },
  ];
}
```

### Equity Curve Background Shading (position state)

```typescript
// Source: Plotly.js shapes + UI-SPEC chart spec
// Build vrect shapes from equity_curve position field transitions
function buildPositionShapes(equityCurve: EquityCurvePointPayload[]) {
  const shapes = [];
  // Group consecutive bars with same non-flat position into rectangles
  // long_spread = rgba(81, 207, 102, 0.08), short_spread = rgba(255, 107, 107, 0.08)
  // Implementation: iterate, track start of each position segment, emit shape on change
  return shapes;
}
```

---

## Environment Availability

Step 2.6: SKIPPED — this phase is frontend-only code changes. All dependencies are already installed in `frontend/node_modules`. No external services, CLIs, or databases are introduced. The FastAPI backend with `POST /api/backtest` is an existing, tested endpoint.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 7.4+ (Python backend) |
| Frontend | No Jest/Vitest configured — frontend testing is manual/visual in this project |
| Config file | `pyproject.toml` (pytest section) |
| Quick run command | `uv run pytest tests/test_backtest_engine.py -x` |
| Full suite command | `uv run pytest tests/ --ignore=tests/test_api.py --ignore=tests/test_backtest_api.py --ignore=tests/test_optimization_api.py --ignore=tests/test_research_api.py --ignore=tests/test_trading_api.py` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BT-01 | Parameter form renders 7 sliders with correct defaults | manual-only | visual verification | N/A |
| BT-02 | Run button triggers API call, loading skeleton appears | manual-only | visual verification | N/A |
| BT-03 | Equity curve chart renders with correct data | manual-only | visual verification | N/A |
| BT-04 | Trade markers appear on z-score and spread charts | manual-only | visual verification | N/A |
| BT-05 | Drawdown chart derived correctly from equity curve | unit (Python helper) | n/a (frontend logic) | N/A |
| BT-06 | Metric cards show correct values from API response | manual-only | visual verification | N/A |
| BT-07 | Trade log table shows all required columns | manual-only | visual verification | N/A |
| BT-08 | Blocker alerts prevent results; warning alerts show above results | manual-only | visual verification | N/A |
| BT-09 | Accordion collapsed by default, expands to show footer | manual-only | visual verification | N/A |
| BT-10 | Overfitting warnings render between metric cards and charts | manual-only | visual verification | N/A |
| UX-02 | Skeleton shown during loading; button disabled during flight | manual-only | visual verification | N/A |
| UX-04 | Context label shows correct pair above metric cards | manual-only | visual verification | N/A |

**Backend coverage note:** The backtest engine is already well-tested:
- `tests/test_backtest_engine.py` — 4 tests covering look-ahead safety, fee accounting, preflight blocking, and warning surfacing (all passing as of Phase 2)
- `tests/test_overfitting.py` — overfitting detection tests
- No new backend tests are needed for this phase.

### Sampling Rate

- **Per task commit:** `uv run pytest tests/test_backtest_engine.py -x` (ensures backend unchanged)
- **Per wave merge:** `uv run pytest tests/ --ignore=tests/test_api.py --ignore=tests/test_backtest_api.py --ignore=tests/test_optimization_api.py --ignore=tests/test_research_api.py --ignore=tests/test_trading_api.py`
- **Phase gate:** Full backend suite green + manual visual verification of all 12 requirements before `/gsd:verify-work`

### Wave 0 Gaps

None — existing test infrastructure covers all backend requirements. Frontend testing is manual-visual only (no Jest/Vitest in project).

---

## Project Constraints (from CLAUDE.md)

These directives apply to all implementation work in this phase:

| Directive | Implication for Phase 3 |
|-----------|------------------------|
| Use Polars, never Pandas | No Python changes in this phase — not applicable |
| Ruff for Python linting | No Python changes in this phase — not applicable |
| All Plotly charts go through `PlotlyChart` wrapper | All 4 charts must use `<PlotlyChart data={...} layout={...} style={{ height: 'Xpx' }} />` |
| TypeScript strict mode | No `any` types without justification; all `BacktestResponse` fields are already typed in `api.ts` |
| Mantine v8 component library | Slider, SimpleGrid, Alert, Accordion, Table, Badge, Tooltip — all from `@mantine/core` |
| Dark mode only | No light mode variants; use `PLOTLY_DARK_TEMPLATE` via PlotlyChart wrapper (auto-applied) |
| `'use client'` on all pages/tabs | `BacktestTab.tsx` must have `'use client'` as first line |
| `apiFetch<T>()` for all API calls | Use existing `postBacktest()` and `postCointegration()` from `api.ts` — do not write raw fetch calls |
| API timestamps are epoch milliseconds | `signal_overlay[].execution_timestamp` is an ISO string (from `BacktestResponse`); `equity_curve[].timestamp` is also ISO string — use directly as Plotly x values |
| Components in `components/pair-analysis/` | `BacktestTab.tsx` goes in `frontend/src/components/pair-analysis/BacktestTab.tsx` |
| GSD workflow enforcement | All file changes go through GSD execute-phase |

---

## Open Questions

1. **Parallel vs sequential cointegration call in `handleRun`**
   - What we know: `BacktestResponse` lacks the spread and zscore series needed for overlay charts. `postCointegration` returns them.
   - What's unclear: Should `handleRun` call both in parallel (`Promise.all`) or sequentially? Parallel is faster but requires both to succeed.
   - Recommendation: Use `Promise.all([postBacktest(req), postCointegration(cointReq)])`. If cointegration fails, still show backtest results but render the z-score and spread charts without the overlay series (degrade gracefully). However, given the same pair data must be cached for both, a joint failure is unlikely.

2. **`days_back` parameter for the backtest request**
   - What we know: `BacktestRequest` requires `days_back`. `StatisticsTab` exposes a lookback dropdown (90/180/365/730 days).
   - What's unclear: Should BacktestTab also expose a `days_back` selector, or hardcode it?
   - Recommendation: Hardcode `days_back: 365` matching `DEFAULT_STRATEGY_PARAMETERS` intent. The slider for `lookback_window` controls the rolling window within that dataset. A `days_back` dropdown adds complexity not required by any BT-XX requirement and is not in the decisions list. Planner should confirm this or add a selector if desired.

---

## Sources

### Primary (HIGH confidence)

- `frontend/src/components/pair-analysis/StatisticsTab.tsx` — direct code inspection of established tab pattern, Slider usage, Badge helpers, PlotlyChart usage
- `frontend/src/lib/api.ts` lines 22-244 — all TypeScript interfaces for BacktestRequest/Response verified by direct read
- `api/routers/backtest.py` — POST /api/backtest endpoint verified by direct read; confirmed returns `BacktestResponse` with all fields
- `src/statistical_arbitrage/backtesting/engine.py` — footer content, run_backtest signature verified
- `src/statistical_arbitrage/backtesting/preflight.py` — all blocker codes verified (length_mismatch, insufficient_observations, null_timestamps, null_price_gaps, non_finite_prices, impossible_prices, non_monotonic_timestamps, limited_post_warmup_sample)
- `src/statistical_arbitrage/backtesting/overfitting.py` — all overfit warning codes verified (overfit_high_sharpe threshold=3.0, overfit_high_profit_factor, overfit_high_winrate, overfit_smooth_equity)
- `.planning/phases/03-backtest-tab/03-UI-SPEC.md` — slider ranges, chart heights, badge thresholds, component inventory, trade log column spec, copywriting contract

### Secondary (MEDIUM confidence)

- Mantine v8 Accordion, Alert, Table, Tooltip — usage patterns inferred from Mantine v8 conventions; consistent with components already in use in the codebase

### Tertiary (LOW confidence)

- Plotly.js marker symbol names (`triangle-up`, `triangle-down`, `x`) — from Plotly documentation knowledge; should be verified against `node_modules/plotly.js` type definitions if any doubt

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified in package.json and node_modules
- Architecture: HIGH — pattern directly derived from StatisticsTab.tsx source code
- Pitfalls: HIGH — derived from direct API contract inspection (BacktestResponse shape, status field, preflight blocker behavior)
- Chart markers: MEDIUM — Plotly symbol names are standard but should be spot-checked against installed version

**Research date:** 2026-04-01
**Valid until:** 2026-05-01 (stable stack — Next.js 16, Mantine v8 not changing)
