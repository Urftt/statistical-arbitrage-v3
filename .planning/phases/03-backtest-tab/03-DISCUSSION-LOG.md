# Phase 3: Backtest Tab - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-01
**Phase:** 03-backtest-tab
**Areas discussed:** Parameter form design, Results layout & charts, Signal overlay style, Warning presentation

---

## Parameter Form Design

### Input style

| Option | Description | Selected |
|--------|-------------|----------|
| Sliders for all (Recommended) | Consistent with Phase 2. Each parameter gets a Mantine Slider grouped into Signal/Risk/Execution sections. | ✓ |
| Number inputs | Mantine NumberInput fields. More precise but less visual. | |
| Mixed approach | Sliders for continuous, NumberInput for discrete/large-range values. | |

**User's choice:** Sliders for all
**Notes:** Preview showed 3-section layout (Signal, Risk Management, Execution) which user confirmed.

### Form persistence after run

| Option | Description | Selected |
|--------|-------------|----------|
| Always visible (Recommended) | Form stays above results for fast iteration. | ✓ |
| Collapse into accordion | Form collapses after run, click to re-expand. | |
| Side-by-side | Form in narrow left column, results in wider right. | |

**User's choice:** Always visible

### Reset button

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, reset button | Secondary button next to Run Backtest, resets all sliders to defaults. | ✓ |
| No, just Run Backtest | Minimal — defaults are initial state on mount. | |

**User's choice:** Yes, reset button

---

## Results Layout & Charts

### Vertical arrangement

| Option | Description | Selected |
|--------|-------------|----------|
| Metrics -> Charts -> Trade log (Recommended) | Top: 6 metric cards. Middle: equity, drawdown, signal overlay charts stacked. Bottom: trade log table. | ✓ |
| Charts -> Metrics -> Trade log | Lead with visual story, metrics below. | |
| Two-column layout | Charts left 60%, metrics+log right 40%. | |

**User's choice:** Metrics -> Charts -> Trade log

### Metric card selection

| Option | Description | Selected |
|--------|-------------|----------|
| 6 key cards (Recommended) | Sharpe, Max Drawdown, Win Rate, Total P&L, Total Trades, Final Equity. Other metrics in expandable detail. | ✓ |
| 4 essential cards | Sharpe, Max Drawdown, Win Rate, Total P&L only. | |
| All metrics as cards | All 12+ metrics in a grid. | |

**User's choice:** 6 key cards

---

## Signal Overlay Style

### Which chart for markers

| Option | Description | Selected |
|--------|-------------|----------|
| Z-score chart (Recommended) | Entries at threshold crossings, most intuitive. | |
| Spread chart | Markers on raw spread, harder to see trigger reason. | |
| Both charts | Markers on both z-score and spread charts. | ✓ |

**User's choice:** Both charts

### Marker style

| Option | Description | Selected |
|--------|-------------|----------|
| Triangles (Recommended) | Up triangles for entries (green=long, red=short), down for exits, X for stop-loss. Standard convention. | ✓ |
| Dots with labels | Colored dots with tiny text labels. | |
| Vertical lines + regions | Colored lines at entry/exit with shaded regions. | |

**User's choice:** Triangles

---

## Warning Presentation

### Preflight warnings

| Option | Description | Selected |
|--------|-------------|----------|
| Alert banner above results (Recommended) | Mantine Alert (yellow=warning, red=blocker) between Run button and results. Blockers prevent results. | ✓ |
| Inline on metric cards | Warning badges on affected cards. | |
| Modal before results | Pop-up forcing acknowledgment. | |

**User's choice:** Alert banner above results

### Overfitting warnings

| Option | Description | Selected |
|--------|-------------|----------|
| Yellow alert below metrics (Recommended) | Mantine Alert between metric cards and charts. Lists each flag. Persistent, not dismissable. | ✓ |
| Badges on affected cards | Yellow "Suspect" badge on triggered metric card. | |
| Red border on results section | Red-bordered container wrapping all results. | |

**User's choice:** Yellow alert below metrics

### Assumptions & Limitations

| Option | Description | Selected |
|--------|-------------|----------|
| Collapsible at bottom (Recommended) | Mantine Accordion at bottom of results. Collapsed by default. | ✓ |
| Always visible footer | Always shown, no click needed. | |
| Info icon tooltip | Popover from info icon near Run button. | |

**User's choice:** Collapsible at bottom

---

## Claude's Discretion

- Exact slider min/max/step ranges for each parameter
- Chart heights and relative sizing
- Trade log table columns and sorting
- Badge color thresholds for metric cards
- Loading state skeleton design
- How secondary metrics are accessible (tooltip vs expandable row)
- Drawdown chart style (filled area vs line)

## Deferred Ideas

None — discussion stayed within phase scope.
