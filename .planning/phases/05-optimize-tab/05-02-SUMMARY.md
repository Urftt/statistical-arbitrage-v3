---
phase: 05-optimize-tab
plan: "02"
subsystem: frontend
tags: [optimize-tab, walk-forward, fold-table, verdict-badge, react, mantine]
dependency_graph:
  requires: [05-01]
  provides: [optimize-tab-walk-forward]
  affects: [pair-analysis-page]
tech_stack:
  added: []
  patterns:
    - Walk-forward fold table with per-fold Sharpe and trade count columns
    - Stability verdict Badge with green/yellow/red color mapping
    - Conditional Apply to Backtest button (hidden for fragile verdict)
    - Accordion variant="separated" for honest reporting (walk-forward footer)
key_files:
  created: []
  modified:
    - frontend/src/components/pair-analysis/OptimizeTab.tsx
decisions:
  - "Walk-forward controls (Folds NumberInput + Train% Slider) rendered inside results section so user can tweak and re-run after seeing initial results"
  - "foldStatusBadge helper maps all four status values (ok/no_train_trades/no_test_trades/blocked) via single function rather than two separate helpers for color and label"
  - "Pre-existing lint errors in unrelated files (AcademyWizard, Lesson1_3, scanner) are out of scope per deviation rules — OptimizeTab.tsx has zero lint errors"
metrics:
  duration: 2min
  completed: "2026-04-02"
  tasks_completed: 1
  files_changed: 1
---

# Phase 05 Plan 02: Walk-Forward Validation UI Summary

**One-liner:** Walk-forward fold table with per-fold train/test Sharpe, stability verdict Badge (Stable=green/Moderate=yellow/Fragile=red), and conditional Apply to Backtest button completing the full OptimizeTab.

## What Was Built

### Task 1: Replace walk-forward stub with full fold table, verdict badge, and controls

Replaced the placeholder `Paper` block ("Walk-forward results will be rendered in Plan 02") in `OptimizeTab.tsx` with the complete walk-forward validation UI.

**New helper functions added (outside component):**

- `verdictColor(v: 'stable' | 'moderate' | 'fragile'): string` — returns `'green'`, `'yellow'`, or `'red'` for Mantine Badge color prop
- `foldStatusBadge(status: string): { label: string; color: string }` — maps `ok`/`no_train_trades`/`no_test_trades`/`blocked` to badge label and color

**Walk-forward results section renders:**

1. **Section heading** — "Walk-Forward Validation"
2. **Controls (D-10)** — `NumberInput` (label="Folds", min=2, max=10) and `Slider` (Train %, min=50, max=80, step=5 with marks) in a `Group gap="md"` row above the fold table; both disabled while loading
3. **Warning Alerts (D-16)** — Mantine `Alert` banners for each `wfData.warnings` entry; red for blocking, yellow otherwise
4. **Fold Table (D-11)** — `Table striped highlightOnHover` inside `Paper withBorder p="md"` with columns: Fold (1-based), Train Sharpe (2dp), Test Sharpe (2dp), Train Trades (int), Test Trades (int), Status (Badge)
5. **Aggregate metrics + verdict** — `Group gap="xl"` showing Avg Train Sharpe, Avg Test Sharpe, and stability verdict `Badge size="lg"`
6. **Fragile warning (D-14)** — Red `Alert` with copywriting contract text when `stability_verdict === 'fragile'`
7. **Apply to Backtest (D-13)** — `Button variant="light" color="blue"` in `Group justify="flex-end"`, conditionally rendered only when verdict is not `'fragile'` AND `recommended_backtest_params` is not null
8. **Honest Reporting Accordion (D-17)** — `Accordion variant="separated"` with `footer.assumptions` and `footer.limitations` as `List` items

**Imports added:** `Slider`, `Table` from `@mantine/core`

**State wired:** `foldCount` and `trainPct` state setters (previously unused `const` destructuring) now properly destructured with setters enabling two-way binding.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all walk-forward UI is fully wired to `wfData` from `postWalkForward()`. The stub from Plan 01 has been completely replaced.

## Self-Check: PASSED

- [x] `frontend/src/components/pair-analysis/OptimizeTab.tsx` modified (162 net insertions)
- [x] Commit 878238d exists
- [x] `npm run build` exits 0
- [x] `npm run lint` (scoped to OptimizeTab.tsx) exits 0
- [x] OptimizeTab.tsx no longer contains "Walk-forward results will be rendered in Plan 02"
- [x] `function verdictColor(` present at line 105
- [x] `function foldStatusBadge(` present at line 109
- [x] "Walk-Forward Validation" text present
- [x] `<Table striped highlightOnHover>` present
- [x] All 6 Table.Th columns present (Fold, Train Sharpe, Test Sharpe, Train Trades, Test Trades, Status)
- [x] `fold.fold_index + 1` (1-based display) present
- [x] `fold.train_metrics.sharpe_ratio?.toFixed(2)` present
- [x] `fold.test_metrics.sharpe_ratio?.toFixed(2)` present
- [x] `fold.train_trade_count` and `fold.test_trade_count` present
- [x] `foldStatusBadge(fold.status)` present
- [x] `wfData.aggregate_train_sharpe` and `wfData.aggregate_test_sharpe` present
- [x] `verdictColor(wfData.stability_verdict)` present
- [x] `wfData.stability_verdict !== 'fragile'` (conditional Apply) present
- [x] `wfData.recommended_backtest_params` present
- [x] "Results are fragile" text present
- [x] Two `Accordion variant="separated"` instances (grid search + walk-forward)
- [x] `NumberInput` with `label="Folds"`, `min={2}`, `max={10}` present
- [x] `Slider` with `min={50}`, `max={80}` present
