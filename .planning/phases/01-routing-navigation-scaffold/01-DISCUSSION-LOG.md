# Phase 1: Routing & Navigation Scaffold - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-31
**Phase:** 01-routing-navigation-scaffold
**Areas discussed:** Sidebar restructure, Scanner drill-down, Tab design & behavior, URL routing

---

## Sidebar Restructure

| Option | Description | Selected |
|--------|-------------|----------|
| Scanner + Pair Analysis only | Collapse all 6 items into just 2 entries. Summary page removed (out of scope per PROJECT.md). Clean and minimal. | ✓ |
| Scanner + Pair Analysis + Summary | Keep Summary as a separate nav item for later. Three entries in the section. | |
| You decide | Claude picks the cleanest approach based on the PROJECT.md scope decisions | |

**User's choice:** Scanner + Pair Analysis only
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| No nesting — flat entry | Just 'Pair Analysis' as a single nav item. Tab switching happens inside the page, not the sidebar. | |
| Nested sub-items | Expandable 'Pair Analysis' with 4 sub-links for each tab. | |
| You decide | Claude picks based on existing sidebar patterns | ✓ |

**User's choice:** You decide (Claude's discretion)
**Notes:** Claude will determine nesting approach based on existing sidebar patterns

---

## Scanner Drill-Down

| Option | Description | Selected |
|--------|-------------|----------|
| Click row → set context + navigate | Clicking a row sets asset1/asset2 in PairContext, then router.push to /pair-analysis. Simple. | |
| Click row → navigate with URL params | Router.push to /pair-analysis?asset1=ETH&asset2=BTC. Page reads params on mount and sets context. Supports deep linking. | ✓ |
| You decide | Claude picks the approach that works best with existing PairContext patterns | |

**User's choice:** Click row → navigate with URL params
**Notes:** Supports deep linking and bookmarking

| Option | Description | Selected |
|--------|-------------|----------|
| Entire row clickable | Click anywhere on the row to drill down. Cursor changes to pointer on hover. | ✓ |
| Explicit 'Analyze' button per row | Add a small button or icon in a new column. | |
| You decide | Claude picks based on the scanner table's current design | |

**User's choice:** Entire row clickable
**Notes:** None

---

## Tab Design & Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Default (underline) | Standard underline tabs. Clean, works well in dark theme. | |
| Outline | Bordered tab style. Slightly more prominent visual separation. | |
| Pills | Rounded pill-shaped tabs. More modern feel. | ✓ |
| You decide | Claude picks the variant that fits the dark theme best | |

**User's choice:** Pills
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Key-based remount | Use React key={asset1-asset2} on tabs container. Switching pairs remounts all tab content. | ✓ |
| Manual state reset via useEffect | Each tab watches asset1/asset2 and resets its own state on change. | |
| You decide | Claude picks the most maintainable approach | |

**User's choice:** Key-based remount
**Notes:** Simple and reliable — automatic cleanup

---

## URL Routing

| Option | Description | Selected |
|--------|-------------|----------|
| /pair-analysis | New clean route. Matches the page name. Old stubs removed. | ✓ |
| /analysis | Shorter path. Less verbose but slightly ambiguous. | |
| You decide | Claude picks based on existing route naming conventions | |

**User's choice:** /pair-analysis
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — query param | /pair-analysis?tab=backtest. Supports deep linking. Tab state survives refresh. | ✓ |
| No — tab state is local only | Always opens on first tab. Simpler URL. | |
| You decide | Claude picks the approach that best supports the user flow | |

**User's choice:** Yes — query param
**Notes:** Tab selection persists on page refresh

## Claude's Discretion

- Tab icons (whether to add Tabler icons to tab labels)
- Sidebar active state highlighting for Pair Analysis
- Whether to redirect old routes or just remove them
- Pair Analysis page header design
- Sidebar nesting approach (flat entry vs nested sub-items)

## Deferred Ideas

None — discussion stayed within phase scope.
