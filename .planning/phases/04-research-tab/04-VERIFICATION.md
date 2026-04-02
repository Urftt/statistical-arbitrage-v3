---
phase: 04-research-tab
verified: 2026-04-02T19:48:00Z
status: human_needed
score: 9/9 must-haves verified
re_verification: false
human_verification:
  - test: "Open /pair-analysis with a pair selected, click the Research tab, expand Rolling Stability and click Run"
    expected: "Results load with a line chart of p-value over time, a dashed reference line at p=0.05, green markers on cointegrated windows, a severity-colored takeaway callout with backend text, and an Apply to Backtest button if recommended params exist"
    why_human: "Cannot verify Plotly rendering, color correctness, and chart interactivity without a running browser"
  - test: "Run Rolling Stability, then click Apply to Backtest"
    expected: "The Backtest tab becomes active and the strategy parameter form shows the module's recommended values pre-filled without the backtest running automatically"
    why_human: "Tab switching and form pre-fill are runtime UI behaviors requiring browser interaction"
  - test: "Select a different pair while module results are visible"
    expected: "All 8 module panels collapse and all result data clears — no stale charts or takeaways remain visible"
    why_human: "Pair-change reset involves remounting (Tabs key prop) and internal useEffect resets; must be confirmed visually"
  - test: "Click Run on two different modules (e.g., Lookback Sweep and Z-Score Threshold) in succession without waiting for each to complete"
    expected: "Both modules load and display independently — neither module's state interferes with the other"
    why_human: "Independent per-module state isolation requires visual confirmation at runtime"
  - test: "Run the Z-Score Threshold module and inspect the rendered chart"
    expected: "A heatmap is shown with entry threshold on the y-axis and exit threshold on the x-axis, with total_trades as cell color intensity using the Blues colorscale"
    why_human: "Heatmap pivot logic (IIFE) and colorscale rendering require visual verification"
---

# Phase 4: Research Tab Verification Report

**Phase Goal:** Users can run any of the 8 research modules independently, read contextual takeaways, and carry recommended parameters directly into the Backtest tab
**Verified:** 2026-04-02T19:48:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can expand any of the 8 research module sections and press that section's Run button to load results without triggering other sections | VERIFIED | All 8 Accordion.Item elements exist (values: rolling, oos, coint, lookback, zscore, txcost, spread, timeframe). Each has independent 3-tuple state (loading/error/data) and a dedicated async run handler. No cross-module state sharing. |
| 2 | Each completed module shows its chart results and a contextual takeaway callout using backend text verbatim | VERIFIED | All 8 modules render `<PlotlyChart>` when data is loaded, followed by `<Alert color={moduleData.takeaway.severity}>` with `{moduleData.takeaway.text}` — backend text is rendered verbatim without transformation. |
| 3 | User can view rolling cointegration stability chart with p-value over time and significance reference line | VERIFIED | Rolling Stability chart: scatter line + cointegrated markers + layout shape `y0: 0.05, y1: 0.05` with `dash: 'dash'` and `p=0.05` annotation. Lines 317-365 of ResearchTab.tsx. |
| 4 | User can click Apply to Backtest and see Backtest tab's form pre-filled with recommended parameters | VERIFIED | `onApplyToBacktest` callback present in all 8 modules guarded by `recommended_backtest_params &&`. page.tsx `handleApplyToBacktest` calls `setPendingBacktestParams` + `handleTabChange('backtest')`. BacktestTab `useEffect` on `pendingParams` calls `setParams({ ...pendingParams.strategy })` without auto-running. |
| 5 | Switching pairs clears all module results and collapses all accordion panels | VERIFIED | Two mechanisms: (1) `Tabs key={asset1-asset2}` in page.tsx remounts all tab content on pair change; (2) ResearchTab's internal `useEffect([asset1, asset2, timeframe])` explicitly resets all 24 state variables and calls `setOpenPanels([])`. |
| 6 | Modules do not auto-load on tab mount — only user click triggers fetch | VERIFIED | No `useEffect` in ResearchTab that calls any run handler. All 8 handlers are only wired to `onClick` of the Run buttons. `useEffect` only handles pair-change reset. |
| 7 | Cross-tab state wiring: ResearchTab → page.tsx → BacktestTab | VERIFIED | `onApplyToBacktest` prop on ResearchTab; `handleApplyToBacktest` in page.tsx sets `pendingBacktestParams` state and calls `handleTabChange`; BacktestTab accepts `pendingParams` and `onParamsConsumed` props. |
| 8 | All 5 remaining module charts are fully implemented (no Plan 02 placeholder text) | VERIFIED | No "Plan 02" placeholder text found in ResearchTab.tsx (937 lines). All 8 `<PlotlyChart>` calls confirmed: lines 285, 388, 467, 547, 623, 707, 786, 860. |
| 9 | TypeScript compiles clean, no lint errors in Phase 4 files | VERIFIED | `npx tsc --noEmit` exits 0. `npm run lint` shows 6 errors and 12 warnings, none in ResearchTab.tsx, page.tsx, or BacktestTab.tsx — all are pre-existing issues in unrelated academy/context files. |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/src/components/pair-analysis/ResearchTab.tsx` | Research tab with 8 modules, min 400 lines | VERIFIED | 937 lines. Contains all 8 Accordion.Item elements, 24 state tuples, 8 run handlers, 8 PlotlyChart calls, pair-change reset useEffect, and onApplyToBacktest callback. |
| `frontend/src/app/(dashboard)/pair-analysis/page.tsx` | Contains `pendingBacktestParams` | VERIFIED | Line 38: `useState<BacktestRequest | null>(null)`. Line 49: `handleApplyToBacktest`. Line 111: `<ResearchTab onApplyToBacktest={handleApplyToBacktest} />`. Lines 114-117: BacktestTab with pendingParams/onParamsConsumed. |
| `frontend/src/components/pair-analysis/BacktestTab.tsx` | Contains `pendingParams` prop | VERIFIED | Lines 249-252: `interface BacktestTabProps` with `pendingParams?: BacktestRequest | null` and `onParamsConsumed?: () => void`. Lines 276-283: useEffect consuming pendingParams. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| ResearchTab.tsx | /api/research/* | postRollingStability, postOOSValidation, postCointMethodComparison | WIRED | All 3 functions imported from `@/lib/api`, called with `${asset1}/EUR` format, response stored in module-specific state. |
| ResearchTab.tsx | /api/research/* | postLookbackSweep, postZScoreThreshold, postTxCost, postSpreadMethodComparison, postTimeframeComparison | WIRED | All 5 functions imported and called. postTimeframeComparison correctly omits `timeframe` field (line 259: only asset1, asset2, days_back). |
| ResearchTab.tsx | page.tsx | onApplyToBacktest callback prop | WIRED | Prop declared in `ResearchTabProps`, used in all 8 module conditional Apply buttons. |
| page.tsx | BacktestTab.tsx | pendingParams + onParamsConsumed | WIRED | BacktestTab receives props at lines 114-117. useEffect at lines 276-283 consumes and clears them. |
| api.ts functions | /api/research/* endpoints | apiFetch POST calls | WIRED | All 8 research API functions call `apiFetch` with correct backend endpoint paths (rolling-stability, oos-validation, lookback-window, zscore-threshold, tx-cost, spread-method, timeframe-comparison, coint-method). |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| ResearchTab.tsx (rolling module) | `rollingData` | `postRollingStability` → `apiFetch` → `fetch` to `/api/research/rolling-stability` | Yes — calls real FastAPI endpoint, stores full response | FLOWING |
| ResearchTab.tsx (all 7 other modules) | `{module}Data` | Corresponding `post*` function → `apiFetch` → `fetch` to real endpoint | Yes — same pattern, all call real FastAPI endpoints | FLOWING |
| BacktestTab.tsx (params pre-fill) | `params` state | `pendingParams.strategy` from ResearchTab recommended_backtest_params | Yes — comes from backend API response | FLOWING |

### Behavioral Spot-Checks

Step 7b: SKIPPED (requires running browser — frontend-only chart rendering, no CLI-testable behavior).

TypeScript compilation passes as behavioral proxy: `npx tsc --noEmit` exits 0.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| RSRCH-01 | 04-01-PLAN.md, 04-02-PLAN.md | User can run each of the 8 research modules independently | SATISFIED | 8 independent Accordion.Item elements, each with dedicated run handler, state tuple, and no cross-module state sharing |
| RSRCH-02 | 04-01-PLAN.md, 04-02-PLAN.md | Each module displays chart results and a contextual takeaway callout | SATISFIED | All 8 modules render PlotlyChart + Alert with `takeaway.severity` color and `takeaway.text` verbatim |
| RSRCH-03 | 04-01-PLAN.md | User can Apply to Backtest to pre-fill Backtest tab | SATISFIED | onApplyToBacktest callback chain: ResearchTab → page.tsx → BacktestTab useEffect pre-fills form |
| RSRCH-04 | 04-01-PLAN.md, 04-02-PLAN.md | Research modules load lazily (not all at once) | SATISFIED | No auto-loading useEffect; all handlers are onClick-only |
| RSRCH-05 | 04-01-PLAN.md | Rolling cointegration stability chart with p-value over time and significance reference line | SATISFIED | Scatter chart with dashed reference line shape at y=0.05, p=0.05 annotation, green cointegrated markers |

**Orphaned requirements from REQUIREMENTS.md for Phase 4:** None. All 5 RSRCH-* requirements are claimed and satisfied.

**Note on REQUIREMENTS.md status:** The traceability table marks all RSRCH-01 through RSRCH-05 as `[x] Complete`. This matches the verification findings.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| ResearchTab.tsx | — | `e.stopPropagation()` is absent from Run button onClick | Info | The plan's acceptance criterion required `e.stopPropagation()`, but a subsequent fix commit (d010b87) legitimately moved buttons outside `Accordion.Control` to fix invalid nested `<button>` HTML. Buttons are now siblings, so `stopPropagation` is no longer needed. This is a correct improvement, not a regression. |
| ResearchTab.tsx | — | No "Plan 02" placeholder text remains | Info (positive) | `grep` confirmed zero matches for "Plan 02", "placeholder", "TODO", or "coming soon" in ResearchTab.tsx. All 8 modules are fully implemented. |

No blocker or warning-level anti-patterns found in Phase 4 files.

### Human Verification Required

The automated checks all pass. The following items require human browser verification:

#### 1. Rolling Stability Chart Renders Correctly

**Test:** Select a pair with cached data, open Research tab, expand Rolling Stability, click Run.
**Expected:** Line chart of p-value over time appears with a dashed blue reference line at p=0.05, green dot markers on cointegrated windows, dark theme applied.
**Why human:** Plotly chart rendering and dark theme cannot be verified without a browser.

#### 2. Apply to Backtest Cross-Tab Flow

**Test:** Run any module that returns `recommended_backtest_params` (Rolling Stability, Lookback Sweep, OOS Validation). Click the Apply to Backtest button.
**Expected:** Browser switches to the Backtest tab and the strategy form shows the recommended values pre-filled. The backtest does NOT auto-run — only the form is populated.
**Why human:** Tab switching and form pre-fill are runtime behaviors.

#### 3. Pair-Change Reset

**Test:** Run two or three research modules, see their results. Then select a different pair from the header dropdowns.
**Expected:** All module panels collapse, all charts and takeaways disappear — no stale data from the previous pair remains visible.
**Why human:** Involves both Tabs key remount and internal useEffect resets; must be confirmed visually.

#### 4. Independent Module Execution

**Test:** Click Run on Lookback Sweep, then immediately click Run on Z-Score Threshold before Lookback finishes.
**Expected:** Both modules show their own loading skeletons independently, and both eventually show their own results without interfering with each other.
**Why human:** Async state isolation requires runtime observation.

#### 5. Z-Score Heatmap Chart

**Test:** Run the Z-Score Threshold Sweep module.
**Expected:** A heatmap appears with entry threshold (y-axis), exit threshold (x-axis), and total_trades as color intensity using the Blues colorscale.
**Why human:** 2D heatmap pivot rendering requires visual verification.

### Gaps Summary

No gaps found. All automated checks pass:

- All 9 observable truths are VERIFIED against the actual codebase.
- All 3 required artifacts exist, are substantive (no stubs), and are wired to each other and to the backend API.
- All 5 RSRCH-* requirements are satisfied.
- TypeScript compiles clean with exit 0.
- No lint errors in Phase 4 files.
- No placeholder text or stub patterns remain in ResearchTab.tsx.

The only outstanding items are visual/behavioral verifications that require a running browser (listed above in Human Verification Required). These are expected for a UI phase and do not indicate implementation gaps.

---

_Verified: 2026-04-02T19:48:00Z_
_Verifier: Claude (gsd-verifier)_
