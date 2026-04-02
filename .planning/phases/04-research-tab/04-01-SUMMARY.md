---
phase: 04-research-tab
plan: 01
subsystem: frontend
tags: [research-tab, accordion, cross-tab-state, plotly, mantine]
requires: [03-backtest-tab]
provides: [research-tab-component, cross-tab-apply-to-backtest]
affects: [pair-analysis-page, backtest-tab]
tech-stack-added: []
tech-stack-patterns: [controlled-accordion-shared-state, cross-tab-param-passing, click-triggered-fetch]
key-files-created:
  - frontend/src/components/pair-analysis/ResearchTab.tsx
key-files-modified:
  - frontend/src/app/(dashboard)/pair-analysis/page.tsx
  - frontend/src/components/pair-analysis/BacktestTab.tsx
decisions:
  - "Shared openPanels state across all 3 Accordion groups for unified panel management"
  - "eslint-disable inside useEffect body (not above) for accurate suppression targeting"
  - "5 placeholder modules retain full run/state/takeaway/apply infrastructure with chart stub only"
duration: 4 min
completed: 2026-04-02
tasks-completed: 2
files-changed: 3
---

# Phase 04 Plan 01: Research Tab Scaffold and Pair Stability Modules Summary

ResearchTab with 8-module Mantine Accordion scaffold and 3 Pair Stability charts, plus cross-tab Apply to Backtest state wiring through page.tsx lifting pattern.

## What Was Built

### Task 1: Cross-tab state wiring (page.tsx + BacktestTab.tsx)

`page.tsx` now holds `pendingBacktestParams: BacktestRequest | null` state. A `handleApplyToBacktest` callback sets params and programmatically switches to the backtest tab. `ResearchTab` receives this callback as `onApplyToBacktest`. `BacktestTab` receives `pendingParams` and `onParamsConsumed` props. A `useEffect` in `BacktestTab` pre-fills the strategy form without auto-running when params arrive.

### Task 2: ResearchTab component

`frontend/src/components/pair-analysis/ResearchTab.tsx` — 822 lines, `'use client'`, fully implemented:

- 8 Accordion.Item elements across 3 section groups: Pair Stability, Parameter Tuning, Method Comparison
- Per-module state: 3 `useState` tuples (loading/error/data) × 8 modules = 24 state declarations
- Controlled Accordion: single `openPanels: string[]` shared across all 3 Accordions
- Auto-expand on run (success or error) via `setOpenPanels(prev => prev.includes(key) ? prev : [...prev, key])`
- Pair-change reset clears all state and collapses all panels
- No auto-load on mount (RSRCH-04 satisfied)

**3 Pair Stability modules with full chart implementations:**
- Rolling Stability: line chart of p-value over time + green cointegrated markers + dashed reference line at p=0.05
- OOS Validation: grouped bar chart (Formation vs Trading p-value per split ratio)
- Cointegration Method: bar chart colored green/red by cointegration result

**5 placeholder modules (Parameter Tuning + Method Comparison):**
All have full run handlers, takeaway Alerts, Apply to Backtest buttons — only the chart body contains "Chart implementation in Plan 02" placeholder text.

## Commits

- `582b7e4` — feat(04-01): wire cross-tab state in page.tsx and BacktestTab.tsx
- `6c556c0` — feat(04-01): create ResearchTab with 8-module accordion and 3 Pair Stability modules

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

The following 5 modules have stub chart content (intentional — Plan 02 will implement them):

| Module | File | Stub |
|--------|------|------|
| Lookback Window Sweep | ResearchTab.tsx ~L327 | `<Text>Chart implementation in Plan 02</Text>` |
| Z-Score Threshold | ResearchTab.tsx ~L376 | `<Text>Chart implementation in Plan 02</Text>` |
| Transaction Cost | ResearchTab.tsx ~L425 | `<Text>Chart implementation in Plan 02</Text>` |
| Spread Method | ResearchTab.tsx ~L474 | `<Text>Chart implementation in Plan 02</Text>` |
| Timeframe Comparison | ResearchTab.tsx ~L523 | `<Text>Chart implementation in Plan 02</Text>` |

These stubs do not prevent Plan 01's goals — all infrastructure (run handlers, state, takeaways, apply buttons) is wired. Plan 02 will replace just the chart placeholder text with actual `<PlotlyChart>` calls.

## Self-Check: PASSED

Files exist:
- frontend/src/components/pair-analysis/ResearchTab.tsx — FOUND
- frontend/src/app/(dashboard)/pair-analysis/page.tsx — FOUND (modified)
- frontend/src/components/pair-analysis/BacktestTab.tsx — FOUND (modified)

Commits exist:
- 582b7e4 — FOUND
- 6c556c0 — FOUND
