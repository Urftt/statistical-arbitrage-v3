# Phase 5: Optimize Tab - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-02
**Phase:** 05-optimize-tab
**Areas discussed:** Axis configuration, Heatmap interaction, Page layout & flow, Apply to Backtest

---

## Axis Configuration

### Parameter Selection UI

| Option | Description | Selected |
|--------|-------------|----------|
| Two dropdowns (Recommended) | Two Select dropdowns listing sweepable params, each with min/max/step inputs below | ✓ |
| Preset combos + custom | 3-4 common preset combinations with pre-filled ranges, plus Custom option | |
| Visual param cards | All 5 params as clickable cards, user clicks 2 to select, each expands with range inputs | |

**User's choice:** Two dropdowns (Recommended)
**Notes:** Clean, standard approach. Two Select dropdowns with NumberInput fields for min/max/step per axis.

### Base Strategy Parameters

| Option | Description | Selected |
|--------|-------------|----------|
| Backtest tab values (Recommended) | Use current Backtest tab parameter form values as base; fall back to defaults if not set | ✓ |
| Always use defaults | Always start from DEFAULT_STRATEGY_PARAMETERS regardless of Backtest tab state | |
| Editable base section | Show all non-swept params as editable fields, pre-filled from defaults | |

**User's choice:** Backtest tab values (Recommended)
**Notes:** Creates natural flow — tune in Backtest, then sweep in Optimize.

---

## Heatmap Interaction

### Cell Interaction

| Option | Description | Selected |
|--------|-------------|----------|
| Tooltip only (Recommended) | Hover shows Plotly tooltip with Sharpe, P&L, win rate, trade count. Best cell auto-highlighted with star. | ✓ |
| Click expands detail | Clicking opens detail panel below heatmap with full MetricSummary fields | |
| Click runs backtest | Clicking auto-runs a full backtest with those params (heavy, complex) | |

**User's choice:** Tooltip only (Recommended)
**Notes:** Simple, leverages Plotly built-in hover. Best cell marked with star annotation.

### Metric Coloring

| Option | Description | Selected |
|--------|-------------|----------|
| Sharpe only (Recommended) | Heatmap always colors by Sharpe ratio | |
| Selectable metric | Dropdown to switch between Sharpe, P&L, win rate, drawdown — re-colors without API call | ✓ |

**User's choice:** Selectable metric
**Notes:** User wants the flexibility to view the heatmap through different metric lenses. Data already available, no API call needed.

### Best Cell Display

| Option | Description | Selected |
|--------|-------------|----------|
| Card row above heatmap (Recommended) | Highlighted Paper card above heatmap with best params, Sharpe, P&L, robustness Badge, Apply button | ✓ |
| Sidebar to heatmap | Best cell panel beside the heatmap in side-by-side layout | |
| Below heatmap | Best cell card below the heatmap | |

**User's choice:** Card row above heatmap (Recommended)
**Notes:** Natural reading order — summary first, then explore the heatmap.

---

## Page Layout & Flow

### Grid Search / Walk-Forward Relationship

| Option | Description | Selected |
|--------|-------------|----------|
| Two sections, shared config (Recommended) | One axis config at top, two Run buttons side-by-side, separate result sections below | ✓ |
| Sequential workflow | Grid search first, "Validate with Walk-Forward" button appears after results | |
| Accordion sections | Two collapsible sections, each with own config and Run button | |

**User's choice:** Two sections, shared config (Recommended)
**Notes:** Shared axis configuration avoids duplication. Both operations use same axes and base params.

### Walk-Forward Controls Placement

| Option | Description | Selected |
|--------|-------------|----------|
| Inline above WF results (Recommended) | Fold count NumberInput + train % Slider between Run button and fold table | ✓ |
| In shared config area | Fold count and train % in the shared config section at top alongside axis dropdowns | |

**User's choice:** Inline above WF results (Recommended)
**Notes:** Keeps the shared config section focused on axes. WF-specific controls live near their results.

---

## Apply to Backtest

### Apply Button Placement

| Option | Description | Selected |
|--------|-------------|----------|
| Both sections get Apply button (Recommended) | Grid search best cell and walk-forward results both get Apply button. WF Apply only for stable/moderate verdict. | ✓ |
| Grid search only | Only grid search gets Apply. Walk-forward is validation-only. | |
| No Apply on Optimize | Results are display-only, user manually enters params in Backtest tab | |

**User's choice:** Both sections get Apply button (Recommended)
**Notes:** Reuses Phase 4 pendingBacktestParams mechanism. WF Apply hidden for fragile verdict.

---

## Claude's Discretion

- Exact min/max/step defaults per sweepable parameter
- Heatmap chart height, color scale, cell annotations
- Star/marker style for best cell highlight
- Loading state skeleton design
- Robustness score badge thresholds and labels
- Fold table column styling
- Walk-forward index-to-timestamp mapping strategy
- Execution time display

## Deferred Ideas

None — discussion stayed within phase scope.
