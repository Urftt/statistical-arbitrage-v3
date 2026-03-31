# Phase 2: Statistics Tab - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-31
**Phase:** 02-statistics-tab
**Areas discussed:** Stat cards presentation, Z-score threshold controls, Data loading & parameters, Chart layout & interaction

---

## Stat Cards Presentation

### Card Layout

| Option | Description | Selected |
|--------|-------------|----------|
| 4-column grid | Mantine SimpleGrid with 4 Paper cards in a row. Collapses to 2x2 on smaller screens. | ✓ |
| Horizontal stat strip | Compact single-row strip using Mantine Group with minimal styling. | |
| 2x2 card grid | Two rows of two cards with more detail per card. | |

**User's choice:** 4-column grid
**Notes:** None

### Interpretive Labels

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, colored badges | Each card shows a Badge below the value: green/yellow/red based on quality. | ✓ |
| Values only, no interpretation | Just the raw numbers. | |
| You decide | Claude picks the best approach. | |

**User's choice:** Yes, colored badges
**Notes:** None

### Cointegration Score

| Option | Description | Selected |
|--------|-------------|----------|
| Just the 4 required metrics | P-value, half-life, hedge ratio, correlation only. | |
| Add cointegration score as 5th card | Show the 0-100 score alongside individual metrics. | ✓ |
| You decide | Claude picks based on layout. | |

**User's choice:** Add cointegration score as 5th card
**Notes:** None

---

## Z-Score Threshold Controls

### Control Type

| Option | Description | Selected |
|--------|-------------|----------|
| Number inputs | Two NumberInput fields for entry/exit thresholds. | |
| Sliders | Mantine Slider components for each threshold. Visual and tactile. | ✓ |
| Preset buttons + custom | Common presets as chip buttons with custom entry option. | |

**User's choice:** Sliders
**Notes:** None

### Symmetry

| Option | Description | Selected |
|--------|-------------|----------|
| Symmetric | One entry slider draws at +/- value, one exit slider draws at +/- value. | ✓ |
| Independent upper/lower | Four sliders for independent control. | |

**User's choice:** Symmetric
**Notes:** None

---

## Data Loading & Parameters

### Auto-load Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-load on tab open | useEffect fires postCointegration() when pair is available. | ✓ |
| Manual 'Analyze' button | User clicks to trigger the API call. | |

**User's choice:** Auto-load on tab open
**Notes:** None

### Lookback Period

| Option | Description | Selected |
|--------|-------------|----------|
| Sensible default, no control | Use 365 days with no user control. | |
| Dropdown with presets | Select from 90d / 180d / 365d / 730d. | ✓ |
| You decide | Claude picks. | |

**User's choice:** Dropdown with presets
**Notes:** None

### Reload on Change

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-reload on change | Changing dropdown immediately fires new API call. | ✓ |
| Require 'Refresh' click | Dropdown sets value only; user clicks to re-fetch. | |

**User's choice:** Auto-reload on change
**Notes:** None

---

## Chart Layout & Interaction

### Chart Arrangement

| Option | Description | Selected |
|--------|-------------|----------|
| Two stacked, shared x-axis | Spread on top, z-score below, time axes aligned. | ✓ |
| Two separate charts | Independent charts with own x-axes. | |
| Combined single chart | Both on one chart with dual y-axes. | |

**User's choice:** Two stacked, shared x-axis
**Notes:** None

### Zoom/Pan

| Option | Description | Selected |
|--------|-------------|----------|
| Interactive with zoom/pan | Plotly built-in zoom and pan with reset button. | ✓ |
| Static view only | No zoom/pan interaction. | |

**User's choice:** Interactive with zoom/pan
**Notes:** None

### Hover Tooltips

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, hover tooltips | Plotly default hover showing date + value. | ✓ |
| No tooltips | Clean chart without hover data. | |

**User's choice:** Yes, hover tooltips
**Notes:** None

---

## Claude's Discretion

- Exact slider range/step values for thresholds
- Default threshold values
- Default lookback period preset
- Skeleton loading design
- Color threshold boundaries for interpretive badges
- Whether to show API interpretation text
- Chart height ratios

## Deferred Ideas

None — discussion stayed within phase scope.
