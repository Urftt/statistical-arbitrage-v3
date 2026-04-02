# Phase 4: Research Tab - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-02
**Phase:** 04-research-tab
**Areas discussed:** Module layout & sections, Apply to Backtest mechanism, Chart types per module, Takeaway callout design

---

## Module Layout & Sections

### How should the 8 research modules be presented?

| Option | Description | Selected |
|--------|-------------|----------|
| Accordion sections | Mantine Accordion — each module is a collapsible section with title and Run button in the header. Matches Phase 3 Assumptions & Limitations pattern. | ✓ |
| Stacked cards | All 8 modules visible as Paper cards in a vertical stack. More scrolling but everything visible at a glance. | |
| Two-column grid | 8 modules in a 2x4 grid of cards. Compact but charts may be cramped at half-width. | |

**User's choice:** Accordion sections
**Notes:** None

### Expand behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Multiple at once | Users can expand several modules and scroll between results. Useful for comparing. | ✓ |
| One at a time | Opening a new module auto-closes the previous one. | |

**User's choice:** Multiple at once
**Notes:** None

### Module grouping

| Option | Description | Selected |
|--------|-------------|----------|
| Flat list with natural ordering | All 8 at the same level, ordered by research workflow. | |
| Grouped with section headers | 2-3 categories with labeled dividers (Pair Stability, Parameter Tuning, Method Comparison). | ✓ |

**User's choice:** Grouped with section headers
**Notes:** None

### Run behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Per-module Run only | Each module has its own Run button. Matches RSRCH-01. | ✓ |
| Per-module + Run All | Individual Run buttons plus a "Run All" at the top. | |

**User's choice:** Per-module Run only
**Notes:** None

### Run button placement

| Option | Description | Selected |
|--------|-------------|----------|
| In the accordion header | Visible when collapsed. Auto-expands on results. | ✓ |
| Inside expanded section | Must expand first, then click Run. | |

**User's choice:** In the accordion header
**Notes:** None

---

## Apply to Backtest Mechanism

### Cross-tab state approach

| Option | Description | Selected |
|--------|-------------|----------|
| Lift state to page level | page.tsx holds pendingBacktestParams state. Research calls setter, Backtest reads on mount. | ✓ |
| Shared context (new provider) | CrossTabContext wrapping tabs. More extensible but more indirection. | |
| URL query params | Encode params in URL on tab switch. Bookmarkable but messy. | |

**User's choice:** Lift state to page level
**Notes:** Resolves STATE.md blocker about cross-tab state design.

### Auto-switch tab on Apply

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-switch to Backtest tab | Clicking Apply navigates to Backtest tab with params pre-filled. | ✓ |
| Stay on Research tab with confirmation | Show toast and stay. User switches manually. | |

**User's choice:** Auto-switch to Backtest tab
**Notes:** None

### Auto-run backtest on Apply

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-fill only | Form pre-filled, user reviews and clicks Run manually. | ✓ |
| Pre-fill and auto-run | Form fills and backtest starts immediately. | |

**User's choice:** Pre-fill only
**Notes:** Consistent with Phase 3 decision that backtests require explicit Run click.

---

## Chart Types Per Module

| Option | Description | Selected |
|--------|-------------|----------|
| Claude's discretion | Pick best chart type per module based on data structure. | ✓ |
| Discuss each module | Go through all 8 one by one. | |
| Show proposed types first | List proposals for approval/adjustment. | |

**User's choice:** Claude's discretion
**Notes:** None

---

## Takeaway Callout Design

| Option | Description | Selected |
|--------|-------------|----------|
| Mantine Alert below chart | Colored Alert banner (green/yellow/red) between chart and Apply button. Consistent with Phase 3 warning pattern. | ✓ |
| Inline badge + text | Colored Badge next to text. More subtle. | |
| Card-style callout | Paper with colored left border. Visually distinct but less heavy. | |

**User's choice:** Mantine Alert below chart
**Notes:** None

---

## Claude's Discretion

- Chart types per module (bar, line, heatmap, table, grouped bars)
- Chart sizing, axis labels, hover tooltips, reference lines
- Module ordering within groups
- Loading state skeleton design
- Handling of null `recommended_backtest_params` (hide or disable Apply button)
- Section header styling for the 3 groups

## Deferred Ideas

None — discussion stayed within phase scope.
