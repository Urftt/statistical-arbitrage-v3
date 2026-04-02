---
phase: 05-optimize-tab
plan: "01"
subsystem: frontend
tags: [optimize-tab, grid-search, heatmap, backtest-params, react, mantine]
dependency_graph:
  requires: [03-01, 04-01]
  provides: [optimize-tab-grid-search]
  affects: [pair-analysis-page]
tech_stack:
  added: []
  patterns:
    - Lifted state pattern (backtest params from BacktestTab to page.tsx)
    - IIFE pattern for derived computation in JSX (heatmap pivot)
    - Click-triggered async fetch with cancelRef pattern
    - Accordion variant="separated" for honest reporting
key_files:
  created:
    - frontend/src/components/pair-analysis/OptimizeTab.tsx
  modified:
    - frontend/src/app/(dashboard)/pair-analysis/page.tsx
    - frontend/src/components/pair-analysis/BacktestTab.tsx
decisions:
  - "Heatmap colorscale: RdYlGn for Sharpe/P&L (higher=green), Blues for win rate, RdYlGn_r for max drawdown (lower=green since lower drawdown is better)"
  - "Walk-forward state managed in OptimizeTab now, UI rendered in Plan 02 — prevents state loss between plans"
  - "OptimizeTab.tsx created in same commit as Task 1 because build verification requires the file to exist"
metrics:
  duration: 3min
  completed: "2026-04-02"
  tasks_completed: 2
  files_changed: 3
---

# Phase 05 Plan 01: Grid Search & Heatmap Summary

**One-liner:** Plotly heatmap grid search optimizer with axis config form, best cell card, robustness badge, and Apply-to-Backtest wiring via lifted page-level param state.

## What Was Built

### Task 1: Lift backtest params to page level and wire OptimizeTab into tab shell

Updated `page.tsx` to add `currentBacktestParams` state (lifted from BacktestTab), pass `onParamsChange={setCurrentBacktestParams}` to BacktestTab, and replace the "Optimize — coming in Phase 5" placeholder with the real `OptimizeTab` component receiving `baseStrategy` and `onApplyToBacktest` props.

Updated `BacktestTab.tsx` to expose an `onParamsChange` callback that fires whenever any parameter changes (via `updateParam`, `handleReset`, or pending params applied from Research tab).

### Task 2: Create OptimizeTab component

Created `frontend/src/components/pair-analysis/OptimizeTab.tsx` (~350 lines) with:

- **Axis configuration form:** Two-column layout with `Select` dropdown for parameter choice and `NumberInput` triplets (min/max/step) per axis, with defaults auto-populated from `PARAM_DEFAULTS` on param change
- **Grid search handler:** `postGridSearch()` call with axes config, base strategy (spread from page-level state), `max_combinations: 500`
- **Walk-forward handler:** `postWalkForward()` call with same axes config, fold_count=5, train_pct sent as `trainPct/100` (60 → 0.60)
- **Loading skeletons:** Separate skeletons for grid search and walk-forward
- **Best cell card:** Displays best parameter values, Sharpe ratio, total P&L, robustness Badge (Strong/Moderate/Weak) with "Apply to Backtest" button wired to `onApplyToBacktest`
- **Plotly heatmap:** 2D z-matrix built from flat `cells` array using `grid_shape`, star annotation (U+2605 in gold) on best cell, client-side metric re-coloring without re-running search
- **Honest reporting:** `Accordion variant="separated"` with assumptions and limitations from `footer`
- **Walk-forward stub:** State managed, placeholder Paper shown while Plan 02 renders real UI

## Deviations from Plan

None — plan executed exactly as written. OptimizeTab.tsx was committed together with Task 1 changes (both tasks in single commit) because the build verification for Task 1 requires the imported OptimizeTab file to exist.

## Known Stubs

- `wfData` walk-forward results rendered as placeholder Paper: "Walk-forward results will be rendered in Plan 02." — intentional per plan spec, Plan 02 will replace this.

## Self-Check: PASSED

- [x] frontend/src/components/pair-analysis/OptimizeTab.tsx exists
- [x] frontend/src/app/(dashboard)/pair-analysis/page.tsx modified
- [x] frontend/src/components/pair-analysis/BacktestTab.tsx modified
- [x] Commit 88e9ff6 exists
- [x] `npm run build` exits 0
- [x] OptimizeTab.tsx starts with 'use client'
- [x] No "Optimize — coming in Phase 5" in page.tsx
- [x] All acceptance criteria satisfied
