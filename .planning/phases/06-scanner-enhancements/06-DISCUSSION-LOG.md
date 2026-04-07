# Phase 6: Scanner Enhancements - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-07
**Phase:** 06-scanner-enhancements
**Areas discussed:** Sort interaction model, Cointegrated vs non-cointegrated split, Sortable column scope & defaults, Column set & labelling cleanup, Backend endpoint strategy, Fetch flow redesign, Completeness filter handling, Control surface after dropping chips, History horizon (days_back)

---

## Sort Interaction Model

| Option | Description | Selected |
|--------|-------------|----------|
| Clickable column headers | Standard table UX, click a header cell to sort. Lowest learning curve. | ✓ |
| Explicit sort dropdown | Two Select inputs above the table for column + direction. More obvious for non-technical users. | |
| Both header clicks AND dropdown | Headers for power users, dropdown for discoverability. More UI surface. | |

**User's choice:** Clickable column headers

| Option | Description | Selected |
|--------|-------------|----------|
| Two-state: asc ↔ desc | First click on a column = its natural direction, subsequent clicks toggle. Always exactly one active sort. | |
| Three-state: asc → desc → none | Click cycles through asc, desc, then unsorted (returns to default). More flexible. | ✓ |

**User's choice:** Three-state cycle

| Option | Description | Selected |
|--------|-------------|----------|
| p-value ascending | Matches current behavior, most cointegrated pairs first. | ✓ |
| Cointegration score descending | Highest score first. | |
| Half-life ascending | Fastest mean-reverting pairs first. | |

**User's choice:** p-value ascending

| Option | Description | Selected |
|--------|-------------|----------|
| Headers handle their own clicks; row click only on Tbody | Header cells in Thead intercept clicks. Row navigation only fires from Tbody Tr. | ✓ |
| stopPropagation on header clicks | Defensive but redundant if structured per option 1. | |

**User's choice:** Headers handle their own clicks (Thead/Tbody separation)

---

## Cointegrated vs Non-Cointegrated Split

| Option | Description | Selected |
|--------|-------------|----------|
| Two stacked sections, both visible | Cointegrated table on top, Not cointegrated below. Each independently sortable. Strongest visual signal. | ✓ |
| Single sortable table with stronger badge + tint | Keep one table, strengthen the existing tint. Sort applies globally. | |
| Two sections, non-cointegrated collapsed by default | Cointegrated visible, non-cointegrated wrapped in Accordion. Cleanest first view but hides data. | |

**User's choice:** Two stacked sections, both visible

| Option | Description | Selected |
|--------|-------------|----------|
| Independent sort per section | Each section has its own sort state. | ✓ |
| Single sort state shared by both sections | One column/direction applies to both tables. | |
| N/A | Single table option. | |

**User's choice:** Independent sort per section

| Option | Description | Selected |
|--------|-------------|----------|
| Keep both — stats above tables, counts in section headings | Stats Paper cards stay above; section headings repeat counts for orientation. | ✓ |
| Drop existing stats Paper cards | Counts only in section headings. | |

**User's choice:** Keep both

---

## Sortable Column Scope & Defaults

| Option | Description | Selected |
|--------|-------------|----------|
| All numeric/metric columns | p-value, Score, Hedge Ratio, Half-Life, Correlation, Observations sortable. Pair and Status not. | ✓ |
| Only the 4 'core' metrics named in SCAN-01 | p-value, Score, Half-Life, Correlation. | |
| Every column including Pair (alphabetical) | Maximum flexibility. | |

**User's choice:** All numeric/metric columns

| Option | Description | Selected |
|--------|-------------|----------|
| Lower-is-better asc, higher-is-better desc | p-value asc, Half-Life asc, Score desc, Correlation desc, Observations desc. | ✓ |
| All columns default to ascending | Simple and predictable. | |

**User's choice:** Smart natural defaults per column

| Option | Description | Selected |
|--------|-------------|----------|
| Always last regardless of direction | Nulls sink to the bottom whether sorting asc or desc. Standard convention. | ✓ |
| Treat null as Infinity | Nulls cluster at top when desc, bottom when asc. | |

**User's choice:** Nulls always last

| Option | Description | Selected |
|--------|-------------|----------|
| Tabler chevron icon next to header label | IconChevronUp/Down active, IconArrowsSort dimmed inactive. | ✓ |
| Mantine Center + ThemeIcon group | More component scaffolding. | |
| Plain text arrow characters | Lightest weight, less consistent. | |

**User's choice:** Tabler chevron icon

---

## Column Set & Labelling Cleanup

| Option | Description | Selected |
|--------|-------------|----------|
| Drop Status (now redundant with sections), keep rest | 7 columns. | ✓ |
| Keep all 8 columns including Status badge | Belt and suspenders. | |
| Drop Status AND Observations | 6 columns. | |

**User's choice:** Drop Status, keep 7 columns

| Option | Description | Selected |
|--------|-------------|----------|
| Keep 'Score' | Short, fits the table. | |
| Rename to 'Coint. Score' | More precise, takes a bit more horizontal space. | ✓ |
| Rename to 'Strength' | Plain English, slightly inaccurate. | |

**User's choice:** Rename to 'Coint. Score'

| Option | Description | Selected |
|--------|-------------|----------|
| Keep 'X bars' | Timeframe-agnostic, matches backend unit. | |
| Convert to hours/days based on selected timeframe | More human-readable, introduces conversion layer. | |
| Show both: 'X bars (Yh)' | Bars stay authoritative, time in parentheses. | ✓ (chose "Convert" but documented as bars + time per CONTEXT clarification) |

**User's choice:** Convert to hours/days based on selected timeframe (CONTEXT.md D-15 documents the bars + time hybrid as the implementation form)

| Option | Description | Selected |
|--------|-------------|----------|
| Hide empty section entirely | Zero results in a category → don't render that section. | |
| Always show both section headings, with 'No pairs' message inside empty ones | Both sections always visible. | ✓ |

**User's choice:** Always show both sections

---

## *Mid-discussion scope expansion*

After Area 4, the user raised concerns that the scanner had broader functional issues — "what does this thing have to do, and how are we going to solve that really?" They described concrete bugs:
- "Fetch top 20" but chip list shows 25 (cache accumulation)
- "Scan 300 pairs" but result shows scanned 10 (chip selection ignored by backend, completeness filter dropping coins silently)
- Switch timeframe → 0 pairs (fetch button hard-coded to 1h)

A backend code review of `api/routers/academy_scan.py` confirmed:
- The chip filter is completely ignored by the backend (no `coins[]` parameter)
- The 90% completeness filter at lines 162-182 silently drops gappy coins
- The endpoint is named `academy/scan` and is also called by `AcademyDataContext.tsx:137`
- The endpoint accepts any timeframe — frontend just doesn't pass it
- Backend `days_back` range: 7-365 days, default 90
- Cointegration test requires 100+ candles (line 208) — at 1d × 90d = 90 candles, every daily scan silently produces zero results

User and Claude agreed on **Path A: widen Phase 6 to "make the scanner actually work."** The original sort + visual split work continues, plus bug fixes and a coherent fetch/scan flow.

Four new gray areas were identified and all four selected for discussion: Backend endpoint strategy, Fetch flow redesign, Completeness filter handling, Control surface after dropping chips. A fifth (History horizon) emerged from the user's question about how far back the scanner queries.

---

## Backend Endpoint Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Rename to /api/scanner/scan, update Academy too | Move file, update AcademyDataContext.tsx. One canonical endpoint. | ✓ |
| New /api/scanner/scan endpoint, leave academy alone | Two endpoints, code duplication. | |
| Fix academy/scan in place, don't rename | Lowest churn, the name remains a lie. | |

**User's choice:** Rename to /api/scanner/scan, update Academy

| Option | Description | Selected |
|--------|-------------|----------|
| timeframe + days_back + max_pairs only | No coin list parameter. Backend reads all cached coins. | ✓ |
| timeframe + days_back + max_pairs + optional coins[] | Future-proof for SCAN-05 filtering. | |

**User's choice:** Timeframe + days_back + max_pairs only

| Option | Description | Selected |
|--------|-------------|----------|
| Add dropped_for_completeness[] + cached_coin_count + timeframe | Honest metadata for UI. | ✓ |
| Keep response shape unchanged | Strongly recommended against. | |

**User's choice:** Add dropped_for_completeness + cached_coin_count

---

## Fetch Flow Redesign

| Option | Description | Selected |
|--------|-------------|----------|
| Pulls top N coins for the SELECTED timeframe | Single button, single side effect, timeframe-aware. | ✓ |
| Pulls top N for ALL timeframes at once | One click, ~3x API calls. | |
| Two buttons: 'Fetch top 20' and 'Fetch top 50' | Hard-coded counts. | |

**User's choice:** Pulls top N for selected timeframe

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-prompt with a 'Cache empty' Alert + 'Fetch now' button | Don't auto-fetch, make next action obvious. | |
| Auto-fetch on first land | Page loads, fires fetch immediately. Risk: surprises users. | ✓ |
| Show empty state with current behavior | User has to look up. | |

**User's choice:** Auto-fetch on first land *(user explicitly chose this over the recommended prompt option — documented as a deliberate departure from "no auto-API-calls without gesture")*

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — fetch invalidates scan cache | Backend already does this; keep it. | ✓ |
| No — keep separate, let user manually re-scan | Risks stale results. | |

**User's choice:** Yes, fetch invalidates scan cache

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — small text line: 'N coins cached for [tf], last updated [time]' | Builds trust by surfacing invisible state. | ✓ |
| No — keep the page minimal | Less clutter. | |

**User's choice:** Yes, show cache status line

---

## Completeness Filter Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Keep threshold but expose dropped coins in response | Backend still drops, but UI explains. | ✓ |
| Lift the filter — scan everything, mark gappy results in the row | No silent drops, but bad data leads to misleading results. | |
| Make threshold configurable from the UI | Power-user knob, overkill for v1. | |

**User's choice:** Keep threshold, expose dropped coins

| Option | Description | Selected |
|--------|-------------|----------|
| Inline Alert above results: 'Scanned X from Y. Excluded Z coins...' | One Mantine Alert, expandable details. | ✓ |
| Add a 'Data Quality' tab or accordion below results | Out of the way, harder to discover. | |
| Tooltip on the scan stat card | Single line, doesn't explain why. | |

**User's choice:** Inline Alert above results

---

## Control Surface After Dropping Chips

| Option | Description | Selected |
|--------|-------------|----------|
| Timeframe + Fetch button + Scan button + cache status line | Three controls, one status line. | ✓ |
| Add a 'Number of coins to fetch' input next to fetch button | Power users get control. | |
| Add timeframe AND days_back inputs | Both configurable. | |

**User's choice:** Timeframe + Fetch + Scan + cache status line

| Option | Description | Selected |
|--------|-------------|----------|
| C(coins-currently-in-cache, 2) for the selected timeframe | Honest math. | ✓ |
| Show a range: 'Scan up to N pairs (some may be excluded for data quality)' | Sets expectations upfront. | |

**User's choice:** Honest C(coins-in-cache, 2) math

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — persist timeframe in URL query param: ?timeframe=4h | Bookmarkable, shareable. Matches Phase 1. | ✓ |
| Yes — persist in localStorage | Survives refresh, not shareable. | |
| No persistence — always default to 1h | Simplest. | |

**User's choice:** Persist in URL query param

---

## History Horizon (days_back)

| Option | Description | Selected |
|--------|-------------|----------|
| Smart defaults per timeframe | 1h → 90d, 4h → 180d, 1d → 365d. No user knob. | ✓ |
| Single configurable input + sensible default | NumberInput, default 90, range 7-365. | |
| Always 365 days regardless of timeframe | Maximum data, simplest mental model. | |

**User's choice:** Smart per-timeframe defaults

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-bump days_back so the scan succeeds | With smart defaults, just works. | ✓ |
| Show a warning Alert: 'Daily timeframe with 90 days will exclude all pairs...' | Educational, requires user action. | |
| Silently produce empty results | Current behavior. | |

**User's choice:** Auto-bump (handled by smart defaults)

---

## Claude's Discretion

The following implementation details were left to Claude's judgment during planning/execution:
- Exact section heading copy ("Cointegrated (4)" formatting)
- Exact dropped-coins Alert copy (template provided)
- Exact cache status line copy (template provided)
- Hover state styling on sortable headers
- Whether to show distinct "Fetching..." vs "Scanning..." button labels
- Whether fetch and scan buttons sit side-by-side or stacked
- Loading skeleton vs Loader spinner for cache status during initial mount
- Empty-state copy inside empty section frames
- Whether the dropped-coins Alert is dismissible across re-scans
- Number formatting precision per metric column (current: p_value 4dp, others 3dp)

## Deferred Ideas

- SCAN-05: Filter visible results by p-value range, half-life range, min correlation — v2
- SCAN-06: Standalone refresh+rescan combo button — partially absorbed by D-19/D-20, full version v2
- Per-coin filter (chip behavior, properly implemented) — v2 if needed
- Saved coin sets, named scans, scheduled scans — v2
- Multi-column sort, sort persistence across re-scans — v2
- Cancel-during-scan, progress bar — v2
- Per-row data completeness column or icon — v2
- Configurable days_back from the UI — v2
- Configurable completeness threshold from the UI — v2
- Exporting scan results — v2
- Hover tooltip explaining "Coint. Score" — nice-to-have
