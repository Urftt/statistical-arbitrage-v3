# Pitfalls Research

**Domain:** Interactive financial backtesting and research UI — crypto statistical arbitrage
**Researched:** 2026-03-31
**Confidence:** HIGH (grounded in codebase analysis + verified patterns)

---

## Critical Pitfalls

### Pitfall 1: Synchronous API Calls Block the UI During Heavy Computation

**What goes wrong:**
The frontend fires a `POST /api/optimization/grid-search` or `POST /api/optimization/walk-forward` and awaits the response inline. The request takes 5–60 seconds depending on grid size. During that time the page is frozen — no spinner updates, no cancel option, no way to know if it's still running. Users click "Run" again, creating duplicate requests; or they navigate away and lose results silently.

**Why it happens:**
The default pattern for form submission in React is fire-and-wait. When computation is fast (< 500ms) this is invisible. When it's slow, the same pattern produces a terrible experience. Developers don't feel the pain until the grid is populated with real parameters.

The backend currently runs grid search and walk-forward synchronously in FastAPI thread pool workers (`api/routers/optimization.py` — both handlers are `def`, not `async def`). This means the HTTP connection stays open for the full duration.

**How to avoid:**
- Show a progress indicator immediately on button click (disable the run button, show "Running..." state)
- For grid search: display estimated combinations count before running — `max_combinations=500` is the guard, so surface this to the user pre-run
- Use `execution_time_ms` from the response to show "completed in X seconds" — the backend already returns this
- Do NOT implement background task polling for v1 of this milestone; the synchronous pattern is acceptable for a single-user tool as long as loading state is wired correctly
- If walk-forward exceeds 30 seconds in practice, escalate to background task with polling as a phase follow-up

**Warning signs:**
- "Run" button triggers no immediate visual feedback
- Browser network tab shows a single hanging request for >10 seconds
- User can click "Run" again while first request is in flight

**Phase to address:**
Pair Analysis page implementation — wire loading state before wiring any computation endpoint.

---

### Pitfall 2: Overfitting Presented as Success in the Grid Search UI

**What goes wrong:**
The optimize tab shows a heatmap of Sharpe ratios across parameter combinations. The highest-Sharpe cell glows. The user selects it, runs a backtest, sees great metrics, and believes they have found a working strategy. They have not — they found the best in-sample parameters from a brute-force search over 500 combinations. This is textbook data snooping / p-hacking.

The backend already emits `warnings` and `footer.limitations` in `GridSearchResponse` that call this out explicitly. If the UI buries these or renders them as small footnote text, they will be ignored.

**Why it happens:**
UI designers default to showing the "best" result prominently (that's what the user asked for). Warnings are styled as disclaimers rather than action items. The distinction between in-sample optimized metrics and out-of-sample validated metrics is subtle and easy to omit.

**How to avoid:**
- Render the `footer.limitations` array and `warnings` from the API response as visible, styled callouts — not as fine print
- Label all grid search metrics explicitly as "in-sample" in the UI
- Place a "Validate with Walk-Forward" action button adjacent to grid search results — make the validation step feel like the natural next step, not an optional advanced feature
- If the stability verdict from walk-forward is "unstable", show that prominently near any recommended parameter set

**Warning signs:**
- Grid search results shown without any in-sample label
- Backend `warnings` array silently ignored in the frontend response handler
- Walk-forward tab exists but nothing in the grid search results points to it

**Phase to address:**
Optimize tab implementation — design the results display before writing any rendering code.

---

### Pitfall 3: Multiple Plotly Charts Initialized Simultaneously Causing Page Freeze

**What goes wrong:**
The Research tab renders all 8 research module results at once, each containing 1–3 Plotly charts. On first load or after running all modules, 10–20 Plotly instances initialize simultaneously in the DOM. Initialization time scales non-linearly — 10 charts at ~250ms each means 2–5 seconds of main thread blocking, producing a visible freeze or stutter.

The Academy page avoids this because lessons are shown one at a time. The Research tab shows everything together.

**Why it happens:**
Developers build the layout with all chart slots rendered, populate data, and call it done. The freeze only appears on full data load — local development with empty states looks fine.

**How to avoid:**
- Render Research module sections lazily: only mount a chart's `PlotlyChart` component when the section is visible (use Intersection Observer or keep-mounted tabs pattern)
- Run research modules one at a time rather than all in parallel — show each result as it completes instead of waiting for all 8 and rendering simultaneously
- Alternatively, trigger each research module independently (separate "Run" buttons per section) — aligns with "explicit run for heavy compute" requirement in PROJECT.md
- The existing `PlotlyChart` wrapper already uses `next/dynamic` with `ssr: false` — do not bypass this pattern

**Warning signs:**
- Browser DevTools Performance tab shows >1 second scripting on Research tab mount
- Page becomes unresponsive for 2–3 seconds after data loads
- All 8 research sections initialized at the same time in React DevTools

**Phase to address:**
Research tab implementation — decide on lazy vs. eager rendering strategy before building the tab layout.

---

### Pitfall 4: Stale Results After Pair Changes

**What goes wrong:**
User selects BTC/ETH, runs a backtest, sees results. Then changes pair selection to SOL/ADA via the global `PairContext`. The backtest results remain displayed on screen for the old pair. The parameters form still shows values from the previous run. User sees "SOL/ADA" in the pair selector but BTC/ETH results in the metrics panel. They trust the wrong numbers.

This is especially dangerous across tabs — user runs backtest on tab 3 (Backtest), switches to tab 4 (Optimize) with a different pair selected, the optimize results from the previous run are still visible.

**Why it happens:**
Results state is local to the component/tab. Pair context changes don't automatically clear result state. This is the standard stale closure / disconnected state problem in tab-based UIs.

**How to avoid:**
- Use a `useEffect` keyed on the selected pair to clear all result state when the pair changes: `useEffect(() => { clearResults(); }, [selectedPair])`
- Display the pair that was used to generate results directly in the results header ("Results for BTC/ETH — 1h — 365 days"), not just in the global selector
- The `BacktestRequest` (and all research request types) already include `asset1` and `asset2` — surface these from the response, not from current context state
- Consider a banner: "Pair changed — results below are from [old pair]. Run again for [new pair]."

**Warning signs:**
- Results header doesn't show which pair was analyzed
- PairContext selector and displayed results can show different pairs simultaneously
- No `useEffect` clearing results on pair change

**Phase to address:**
Pair Analysis page architecture — define result state lifecycle and pair-change behavior before implementing any single tab.

---

### Pitfall 5: Parameter Form Re-runs Computation on Every Input Change

**What goes wrong:**
The backtest parameter form has 8 inputs (lookback window, entry threshold, exit threshold, stop-loss, capital, position size, fee, min trade count). If any input change immediately triggers an API call, the user gets 8+ requests while typing a lookback window value from 60 to 120. This hammers the synchronous backend and produces out-of-order responses.

**Why it happens:**
React controlled inputs fire `onChange` on every keystroke. Developers wire `onChange` directly to the fetch function for "live preview" feedback. This is reasonable for cheap operations (local chart updates) but catastrophic for server round-trips.

**How to avoid:**
- Use an explicit "Run Backtest" button for all server-triggered computation — PROJECT.md already mandates this: "explicit 'run' button for heavier compute"
- Keep parameter form state local (uncontrolled or React Hook Form) and only send to the server on submit
- Local state changes can update lightweight UI elements (estimated combination count for grid search preview) without triggering API calls
- Use `react-hook-form` to manage the 8-field parameter form — avoids per-keystroke re-renders on all sibling fields

**Warning signs:**
- Network tab shows requests firing while typing in a parameter field
- Results flash/flicker as parameters change
- No "Run" button — computation is triggered by onChange or useEffect on form values

**Phase to address:**
Backtest tab implementation — establish the form-to-submit pattern first, before wiring any API call.

---

### Pitfall 6: Look-Ahead Bias Introduced via Frontend Parameter Display

**What goes wrong:**
The research modules (lookback sweep, z-score threshold sweep, OOS validation) produce recommendations — "use lookback 60", "entry threshold 2.1 is optimal". The UI surfaces these prominently and the user copies them into the backtest parameters. If the user then runs a full-history backtest using these parameters, and the parameters were chosen by looking at the full history results, the backtest is contaminated. The look-ahead comes from the parameter selection workflow, not the engine.

The backend engine is already look-ahead safe (`execute_backtest` docstring: "look-ahead-safe backtest"). The UX layer can reintroduce bias by how it presents recommendations.

**Why it happens:**
Presenting "recommended" parameters from research results is helpful. The problem is not showing them — it's not contextualizing them. "Best parameters from full-history sweep" reads as "use these" when it should read as "these worked historically on the data you just swept."

**How to avoid:**
- Label all research-derived recommendations as "in-sample recommendation" — never just "recommended"
- When pre-populating backtest form from research results, show a contextual note: "Parameters filled from full-history lookback sweep. This backtest uses the same data used to select these parameters."
- Treat the walk-forward / OOS validation results as the authoritative validation — make this clear in the tab flow
- The `ResearchTakeaway` objects returned by the API already contain honest framing — render their text rather than writing custom summary copy

**Warning signs:**
- "Recommended" label appears without "in-sample" qualifier
- Clicking "Apply to Backtest" from research results shows no explanation of what was transferred
- Academy lessons cover look-ahead bias but the research tab workflow doesn't reference it

**Phase to address:**
Research tab implementation and the "apply parameters to backtest" cross-tab action.

---

### Pitfall 7: No Error Boundary Causes Full Page Crash on Chart Data Anomaly

**What goes wrong:**
A research module returns an edge-case response (empty trade list, null spread, a cointegration test that failed silently). The Plotly chart component tries to render empty or malformed data and throws. Without a React error boundary, the entire Pair Analysis page unmounts, showing a blank page or the generic Next.js error screen. The user loses all other tab results.

The codebase already has this gap documented: "No error boundaries in Frontend" in CONCERNS.md. The research module backend also silently swallows some errors and returns empty results (`analysis/research.py` lines 77, 193, 202, 579).

**How to avoid:**
- Wrap each Research module section, each chart panel, and each results block in a granular error boundary
- Add `error.tsx` at the `(dashboard)` layout level as a last-resort catch (per CONCERNS.md recommendation)
- In `PlotlyChart.tsx`, add a guard: if `data` is empty or all series have zero points, render a "No data to display" placeholder instead of passing empty arrays to Plotly
- Treat null/undefined fields in API responses defensively — the API sometimes returns `null` for metrics that couldn't be computed (e.g., `sharpe_ratio: null`)

**Warning signs:**
- PlotlyChart receives `data=[]` and renders without error in development, but crashes with specific data shapes in production
- `sharpe_ratio: null` from the API causes a NaN display or crash in a metric card
- Research module section disappears completely when one request fails

**Phase to address:**
Research tab implementation — add error boundaries at the section level before populating charts.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| All research modules triggered in one batch request | Simpler frontend code | 8 sequential heavy computations, UI blocks for full duration | Never — use per-section triggering |
| Global result state stored in PairContext | Survives tab switches | Pair change logic becomes complex; stale results persist | Acceptable only for lightweight data (pair metadata), not backtest results |
| Inline loading state per component (8 separate booleans) | Simple local state | No unified loading/error UX; impossible to cancel all pending requests at once | Acceptable for MVP but plan a unified request manager |
| Hardcoded default strategy parameters in frontend (`api.ts` `DEFAULT_STRATEGY_PARAMETERS`) | Convenient starting point | Drifts from backend defaults if backend changes | Acceptable if `DEFAULT_STRATEGY_PARAMETERS` is derived from a `/api/backtest/defaults` endpoint call on mount |
| No debounce on parameter inputs | Simplest form wiring | Accidental request spam if onChange is ever connected to fetch | Never skip — always gate computation behind an explicit Run button |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| FastAPI `execution_time_ms` field | Ignored or not displayed | Always show to user — it calibrates expectations and helps debug slow grids |
| `warnings` array in all response types | Rendered as console.log only, or ignored | Render every warning as a visible `Alert` component adjacent to results |
| `footer.limitations` in optimization responses | Buried in a collapsed "details" section | Show at least one sentence from limitations inline with results, not hidden |
| `recommended_backtest_params` from grid search | Silently pre-populates backtest form | Show a notification: "Optimize tab filled your backtest parameters with the best in-sample result" |
| Research `takeaway` objects | Custom summary text written in frontend instead | Use the `takeaway.headline` and `takeaway.body` from the API response — it is purpose-built for this |
| Null metrics from failed backtest cells | Rendered as `null` string or crash | Treat null Sharpe, null win rate, etc. as "—" (em dash) in metric displays |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Mounting all 8 Research module chart panels simultaneously | 3–5 second main-thread freeze on data load | Lazy mount: only render `PlotlyChart` when section is visible or manually triggered | With 8+ modules and 2+ charts each, i.e., from day one of Research tab |
| No memoization on Plotly data objects in results components | Chart re-renders on every parent state change (e.g., loading spinner update) | `useMemo` on data/layout props passed to `PlotlyChart` | Noticeable with 3+ charts on screen during active loading |
| Large equity curve payloads (1 point per candle, 365 days of 1h data = 8760 points) | Slow JSON parse, slow Plotly render | Accept the full payload but downsample display to ~2000 points using Plotly's built-in decimation or a frontend thin function | With 1h timeframe over 365 days |
| Grid search heatmap with 500 cells as a Plotly heatmap | Acceptable render time (~200ms) | No special action needed; 500 cells is within Plotly's comfortable range | Only becomes a problem if max_combinations is raised to 5000+ |
| Scanner page fetching all pairs on mount | Slow initial load if cache requires incremental Bitvavo fetches | Show loading state per pair; do not block the scanner table render on all pairs completing | From first open if data is not yet cached |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| CORS `allow_origins=["*"]` with `allow_credentials=True` | Any website can make authenticated requests to the API | Restrict to `["http://localhost:3000"]` — already flagged in CONCERNS.md, fix before any non-localhost deployment |
| No rate limiting on compute-heavy endpoints | Grid search endpoint spammable; 500 combinations x repeated calls exhausts CPU | `max_combinations=500` guard exists in engine; add `slowapi` rate limiting middleware to `/api/optimization/*` routes if this is ever accessible on a network |
| Strategy parameters accepted directly from frontend without bounds validation | Malformed parameters (negative lookback, entry_threshold=0) cause backend exceptions or silent wrong results | Pydantic models in `api/schemas.py` should include `ge`/`le` validators on all numeric fields |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing Sharpe ratio without trade count context | User trusts a Sharpe of 2.5 from 3 trades as meaningful | Always show trade count next to Sharpe; show the `min_trade_count_warning` threshold |
| No visual indication which pair generated displayed results | User changes pair, old results stay visible, decisions are made on wrong pair | Show pair + timeframe + date range in every results header |
| Optimize tab shows "best parameters" without surfacing walk-forward stability | User applies over-fit parameters to live trading | Place walk-forward verdict ("Stable / Moderate / Unstable") prominently in optimize results, not as a separate tab action |
| Research module results shown without the Academy concept they relate to | User sees "rolling cointegration window: 30d best" without understanding what that means | Link each research module header to the relevant Academy lesson (the glossary linking pattern already exists) |
| Parameter form resets when switching tabs | User configures backtest, switches to Research tab, returns to Backtest with defaults | Persist parameter form state across tab switches — lift form state to the Pair Analysis page level, not the tab component level |
| Equity curve without drawdown overlay | User sees profit but not the pain of the path | Always show max drawdown period as a shaded region on the equity curve, not just as a metric number |

---

## "Looks Done But Isn't" Checklist

- [ ] **Backtest results panel:** Verify all null-able metric fields (`sharpe_ratio`, `max_drawdown`, `win_rate`) render as "—" when null, not as "null" string or crash
- [ ] **Grid search heatmap:** Verify the heatmap correctly maps the 2D grid shape — a 1D grid (single axis) must degrade gracefully to a bar chart or flat heatmap
- [ ] **Walk-forward results:** Verify fold timestamps are displayed in human-readable dates, not raw bar indices (`train_start_idx`, `test_start_idx` are bar indices, not timestamps)
- [ ] **Research takeaways:** Verify `takeaway.headline` and `takeaway.body` are rendered for every module response, not just the charts
- [ ] **Scanner page:** Verify the pair list loads even when some pairs have insufficient data (the backend scanner may return partial results or errors per pair)
- [ ] **Parameter form:** Verify the form shows validation errors for out-of-range values (e.g., entry_threshold < exit_threshold) before the request is sent
- [ ] **Pair change:** Verify all result panels are cleared when the global pair selection changes
- [ ] **Loading state:** Verify the "Run" button is disabled and shows a spinner for the full duration of all compute requests, not just the first 100ms
- [ ] **Backend warnings:** Verify every `warnings` array from every API response is rendered — not console-logged-and-discarded

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Stale results on pair change | LOW | Add `useEffect` keyed on selectedPair that resets all result state; 1–2 hour fix |
| Overfitting misrepresented in UI | LOW | Add "in-sample" labels and limitations callouts; visual-only changes, no logic changes |
| Page freeze from simultaneous Plotly mounts | MEDIUM | Refactor Research tab to lazy-mount sections; requires restructuring the data fetch flow |
| Full-page crash on bad chart data | MEDIUM | Add error boundaries at section level; requires wrapping ~10 components |
| Compute request spam from form onChange | LOW | Replace onChange-triggered fetch with explicit Run button; straightforward if caught early |
| Walk-forward bar indices in results | LOW | Map indices to timestamps using the timestamps array already in the response context |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| UI freeze during heavy computation | Pair Analysis page skeleton — wire loading state first | Run grid search with 500 combos; verify button is disabled and spinner visible for full duration |
| Overfitting presented as success | Optimize tab design — before rendering grid results | Check that "in-sample" label and limitations callout appear in every grid search result view |
| Multiple Plotly simultaneous mount | Research tab implementation — lazy rendering decision upfront | Open Research tab with all 8 modules populated; DevTools Performance should show no >500ms scripting block |
| Stale results on pair change | Pair Analysis page architecture — before implementing any single tab | Change pair while backtest results are displayed; verify results clear immediately |
| Parameter form re-run on change | Backtest tab implementation — establish form-submit pattern first | Type into lookback window field; verify no network request fires until Run button is clicked |
| Look-ahead in parameter recommendations | Research tab + cross-tab actions — when "Apply to Backtest" is built | Apply research recommendation to backtest form; verify contextual "in-sample" note is shown |
| No error boundary on chart crash | Research tab implementation — add before populating any charts | Pass empty data array to PlotlyChart; verify "No data" placeholder renders, not a crash |

---

## Sources

- Codebase audit: `/Users/luckleineschaars/repos/statistical-arbitrage-v3/.planning/codebase/CONCERNS.md` — synchronous handlers, no error boundaries, no frontend tests (HIGH confidence, direct code inspection)
- Backend code: `api/routers/optimization.py`, `api/routers/backtest.py` — synchronous handlers, `execution_time_ms` already returned, `warnings` and `footer` already present in responses
- Backend code: `src/statistical_arbitrage/backtesting/optimization.py` — `max_combinations=500` guard confirmed
- Plotly.js GitHub issue #3416: initialization time scales with chart count — 10 charts ~250ms, 50 charts ~1500ms each (MEDIUM confidence)
- Plotly.js GitHub issue #97 (angular-plotly): "Performance with initializing multiple plot components at once"
- Backtesting overfitting literature: "Why 90% of Backtests Lie" (targethit.ai), "The critical pitfalls of backtesting trading strategies" (starqube.com), "Backtesting Biases" (auquan/Medium) — p-hacking and data snooping are universal backtesting UI problems (HIGH confidence, multiple sources agree)
- FastAPI background tasks patterns: leapcell.io, unfoldai.com, betterstack.com — synchronous handler with loading state is acceptable for single-user tools; task queue only needed for multi-user (MEDIUM confidence)
- React state management pitfalls: logicloom.in, evilmartians.com — stale state on context change is a well-documented React pattern problem (HIGH confidence)

---
*Pitfalls research for: interactive financial backtesting and research UI (crypto stat arb)*
*Researched: 2026-03-31*
