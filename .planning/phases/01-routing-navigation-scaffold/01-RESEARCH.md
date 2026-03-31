# Phase 1: Routing & Navigation Scaffold - Research

**Researched:** 2026-03-31
**Domain:** Next.js 16 App Router navigation, Mantine v8 Tabs, React context state management
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Collapse sidebar "Research & Backtesting" to exactly 2 items: Scanner and Pair Analysis. Remove Pair Deep Dive, Research, Backtest, Optimize, and Summary entries.
- **D-02:** Pair Analysis sidebar item is a flat entry (no nested sub-items). Tab switching happens inside the page only.
- **D-03:** Clicking a scanner table row navigates to `/pair-analysis?asset1=ETH&asset2=BTC&timeframe=1h` via `router.push`. Pair Analysis page reads these params on mount and sets PairContext. Supports deep linking.
- **D-04:** Entire scanner table row is clickable (cursor: pointer on hover). No separate "Analyze" button.
- **D-05:** Use Mantine `Tabs` component with `variant="pills"` for the Pair Analysis page.
- **D-06:** Tab labels: Statistics, Research, Backtest, Optimize (4 tabs, in that order).
- **D-07:** Use React `key={`${asset1}-${asset2}`}` on the tabs container to clear all tab state on pair switch (NAV-05). Full remount discards stale results.
- **D-08:** Pair Analysis page lives at `/pair-analysis` (new route). Old stub pages (`/deep-dive`, `/research`, `/backtest`, `/optimize`, `/summary`) are removed.
- **D-09:** Active tab stored in URL as query param: `/pair-analysis?tab=backtest`. Tab state survives refresh. Default tab is Statistics when no `tab` param.

### Claude's Discretion

- Whether to add icons to tab labels (Tabler icons matching old sidebar items)
- Sidebar active state highlighting for Pair Analysis when on that route
- Whether to redirect old routes (/deep-dive, /research, etc.) or just remove them
- Pair Analysis page header design showing currently selected pair

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NAV-01 | User can navigate between Scanner and Pair Analysis pages from the sidebar | Sidebar restructure (D-01, D-02); Mantine NavLink + usePathname active state pattern verified in existing Sidebar.tsx |
| NAV-02 | User can click a pair in the Scanner to open Pair Analysis with that pair pre-selected | useRouter.push with query params (D-03, D-04); useSearchParams to read on mount; PairContext.setAsset1/setAsset2/setTimeframe already available |
| NAV-03 | User can change the selected pair from the Pair Analysis page header without returning to Scanner | Header.tsx already has working dropdowns bound to PairContext — no changes needed to Header |
| NAV-04 | Pair Analysis page uses tabbed interface (Statistics, Research, Backtest, Optimize) | Mantine Tabs with variant="pills" (D-05, D-06); tab value synced to URL via useSearchParams + router.replace (D-09) |
| NAV-05 | Tab state clears when user changes selected pair (prevents stale results) | React key remount pattern on tabs container (D-07) — verified Mantine Tabs supports controlled value prop |
</phase_requirements>

---

## Summary

Phase 1 is a pure frontend restructure with no backend changes. The goal is to collapse the current 6-item "Research & Backtesting" sidebar section to 2 items (Scanner + Pair Analysis), create a new `/pair-analysis` route with a 4-tab shell (Statistics, Research, Backtest, Optimize), and wire up drill-down navigation from the scanner table.

All required APIs and infrastructure already exist. `PairContext` already provides `setAsset1`, `setAsset2`, `setTimeframe`. The `Header` already has working dropdowns. The `Sidebar` uses the exact pattern needed (Mantine `NavLink` + `usePathname`). The scanner page already renders a `Table.Tr` per result — it just needs an `onClick` handler and `cursor: pointer`. Mantine `Tabs` with `variant="pills"` is available in the installed v8.3.18 package.

The most technically involved part is the dual URL param system: the `/pair-analysis` page reads both pair params (`asset1`, `asset2`, `timeframe`) on mount to hydrate PairContext, and separately manages the `tab` param for the active tab. Both must survive page refresh and direct URL access. The key technical constraint is that `useSearchParams` in Next.js 16 App Router requires a `Suspense` boundary in production builds when used in Client Components — the page is already `'use client'` but the Suspense wrapper must be present to prevent a build error.

**Primary recommendation:** Create `/pair-analysis/page.tsx` as a `'use client'` component that wraps its search-param-reading logic in `<Suspense>`, reads pair + tab params on mount, and renders Mantine `Tabs` with a `key` prop derived from `${asset1}-${asset2}`.

---

## Standard Stack

### Core (all already installed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 16.2.1 | App Router, routing, `useRouter`, `useSearchParams` | Project-locked |
| React | 19.2.4 | Component model, `key` remount, `useState`, `useEffect` | Project-locked |
| @mantine/core | 8.3.18 | `Tabs`, `NavLink`, `Container`, `Stack`, `Paper` | Project-locked |
| @tabler/icons-react | 3.40.0 | Optional tab icons (Claude's discretion) | Already used in Sidebar.tsx |

### No new dependencies needed

This phase requires zero new npm packages. All required building blocks are installed.

---

## Architecture Patterns

### Recommended File Structure (additions only)

```
frontend/src/app/(dashboard)/
├── pair-analysis/
│   └── page.tsx          # NEW — tabbed Pair Analysis shell
├── scanner/
│   └── page.tsx          # MODIFY — add onClick to Table.Tr
├── deep-dive/            # DELETE — stub page removed
├── research/             # DELETE — stub page removed
├── backtest/             # DELETE — stub page removed
├── optimize/             # DELETE — stub page removed
└── summary/              # DELETE — stub page removed

frontend/src/components/layout/
└── Sidebar.tsx           # MODIFY — replace RESEARCH_ITEMS array
```

### Pattern 1: Scanner Row Click — Navigate with URL Params

**What:** `Table.Tr` gets `onClick` that calls `router.push` with pair params encoded as query string.
**When to use:** D-03, D-04 — entire row is the navigation trigger.

```tsx
// Source: verified from Next.js 16 node_modules docs (use-router.md)
'use client'

import { useRouter } from 'next/navigation'

// Inside the Table.Tbody map:
<Table.Tr
  key={`${pair.asset1}-${pair.asset2}`}
  onClick={() => {
    const base1 = pair.asset1.split('/')[0];
    const base2 = pair.asset2.split('/')[0];
    router.push(
      `/pair-analysis?asset1=${base1}&asset2=${base2}&timeframe=${timeframe}`
    );
  }}
  style={{ cursor: 'pointer' }}
>
```

### Pattern 2: Pair Analysis Page — Read URL Params on Mount

**What:** On mount, read `asset1`, `asset2`, `timeframe` from `useSearchParams()` and call `setAsset1`/`setAsset2`/`setTimeframe` from PairContext.
**When to use:** NAV-02, NAV-03 — supports deep linking and bookmarking (D-03).

**Critical constraint from Next.js 16 docs:** Any Client Component using `useSearchParams` must be wrapped in a `<Suspense>` boundary or the production build will fail with "Missing Suspense boundary with useSearchParams".

```tsx
// Source: verified from Next.js 16 node_modules docs (use-search-params.md)
'use client'

import { Suspense } from 'react'
import { useSearchParams, useRouter, usePathname } from 'next/navigation'
import { usePairContext } from '@/contexts/PairContext'

function PairAnalysisContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()
  const { asset1, asset2, setAsset1, setAsset2, setTimeframe } = usePairContext()

  // On mount: hydrate PairContext from URL params
  useEffect(() => {
    const a1 = searchParams.get('asset1')
    const a2 = searchParams.get('asset2')
    const tf = searchParams.get('timeframe')
    if (a1) setAsset1(a1)
    if (a2) setAsset2(a2)
    if (tf) setTimeframe(tf)
  }, []) // intentionally empty — only on initial mount

  // Tab param
  const tab = searchParams.get('tab') ?? 'statistics'

  const handleTabChange = (value: string | null) => {
    if (!value) return
    const params = new URLSearchParams(searchParams.toString())
    params.set('tab', value)
    router.replace(pathname + '?' + params.toString())
  }

  return (
    <Tabs
      key={`${asset1}-${asset2}`}   // D-07: remount on pair change
      value={tab}
      onChange={handleTabChange}
      variant="pills"
    >
      <Tabs.List>
        <Tabs.Tab value="statistics">Statistics</Tabs.Tab>
        <Tabs.Tab value="research">Research</Tabs.Tab>
        <Tabs.Tab value="backtest">Backtest</Tabs.Tab>
        <Tabs.Tab value="optimize">Optimize</Tabs.Tab>
      </Tabs.List>
      <Tabs.Panel value="statistics"><Text c="dimmed">Statistics — coming in Phase 2</Text></Tabs.Panel>
      <Tabs.Panel value="research"><Text c="dimmed">Research — coming in Phase 4</Text></Tabs.Panel>
      <Tabs.Panel value="backtest"><Text c="dimmed">Backtest — coming in Phase 3</Text></Tabs.Panel>
      <Tabs.Panel value="optimize"><Text c="dimmed">Optimize — coming in Phase 5</Text></Tabs.Panel>
    </Tabs>
  )
}

export default function PairAnalysisPage() {
  return (
    <Container size="xl" py="md">
      <Suspense fallback={<Text c="dimmed">Loading...</Text>}>
        <PairAnalysisContent />
      </Suspense>
    </Container>
  )
}
```

### Pattern 3: Sidebar Restructure

**What:** Replace the 6-item `RESEARCH_ITEMS` array with 2 items. Active state for Pair Analysis uses `pathname.startsWith('/pair-analysis')` to stay highlighted across all tab states.

```tsx
// Source: verified from existing Sidebar.tsx + Next.js 16 docs (use-pathname)
const RESEARCH_ITEMS = [
  {
    label: 'Scanner',
    href: '/scanner',
    icon: IconSearch,
    description: 'Batch cointegration scan',
  },
  {
    label: 'Pair Analysis',
    href: '/pair-analysis',
    icon: IconMicroscope,
    description: 'Statistics, research, backtest',
  },
] as const;

// In the NavLink render:
active={pathname.startsWith(item.href)}
```

Note: Using `startsWith` instead of `===` keeps "Pair Analysis" highlighted when the URL is `/pair-analysis?tab=backtest&asset1=ETH&asset2=BTC`.

### Pattern 4: Tab Sync — Using router.replace, Not router.push

**What:** Tab changes use `router.replace` (not `router.push`) so the browser history stack doesn't accumulate a new entry for every tab click.
**When to use:** D-09 — tab is a view state, not a navigation destination. Back button should return to Scanner, not cycle through tabs.

### Anti-Patterns to Avoid

- **Using `router.push` for tab changes:** Pollutes browser history; back button becomes unusable. Use `router.replace` instead.
- **Reading searchParams in layout.tsx:** Next.js 16 docs explicitly state layouts do NOT receive `searchParams` prop and should not read them (can lead to stale values). Read in the page component only.
- **Omitting Suspense around `useSearchParams`:** Production builds fail. Development mode works without it, creating a false sense of safety.
- **Setting PairContext in a `useEffect` with all deps:** Including `setAsset1` etc. in the dependency array causes an infinite re-render loop (the setters are already `useCallback`-stabilized but the effect still runs on every render if you include `searchParams`). Use an empty dep array or a `mounted` ref.
- **Leaving old route directories in place without redirects:** Next.js will still serve the old pages. Either delete the directories or add redirect entries in `next.config.ts`. Deleting is cleaner for this scaffold phase.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| URL query string building | Custom string concatenation | `new URLSearchParams(searchParams.toString()); params.set(key, val)` | Handles encoding, merges existing params safely |
| Tab state persistence | localStorage or cookie | URL query param `?tab=value` via `router.replace` | Already decided (D-09); survives refresh, enables deep linking |
| Pair-change state clearing | Manual `setState(null)` calls in each tab | `key={`${asset1}-${asset2}`}` on `<Tabs>` container | Automatic remount via React reconciliation; zero coordination overhead |
| Active sidebar detection | Manual URL comparison logic | `usePathname().startsWith(href)` | Built into Next.js navigation hooks |

---

## Common Pitfalls

### Pitfall 1: Missing Suspense Boundary Breaks Production Build

**What goes wrong:** Page builds fine in `npm run dev` but `npm run build` fails with error: `Missing Suspense boundary with useSearchParams`.
**Why it happens:** Next.js 16 requires a `Suspense` wrapper for any Client Component using `useSearchParams` during static prerendering. Dev mode skips this check.
**How to avoid:** Always wrap the component that calls `useSearchParams` in `<Suspense fallback={...}>`. Put the Suspense boundary in the outer page component, not inside the content component.
**Warning signs:** `npm run build` output mentions "Missing Suspense boundary with useSearchParams" or the route being marked as `(SSR)` unexpectedly.

### Pitfall 2: Infinite Re-render Loop from useEffect Deps

**What goes wrong:** `useEffect` that reads `searchParams` and calls `setAsset1()`/`setAsset2()` fires on every render, causing a loop.
**Why it happens:** If `searchParams` is in the dependency array, any URL change (including tab changes) re-runs the effect, which calls setters, which may trigger re-renders.
**How to avoid:** Run the mount hydration effect with an empty dependency array `[]`. The pair params from URL are only needed on initial mount — subsequent pair changes come from the Header dropdowns. Alternatively use a `hasMounted` ref.
**Warning signs:** Browser tab freezes or console shows rapid re-render warnings after navigating to `/pair-analysis`.

### Pitfall 3: import from 'next/router' Instead of 'next/navigation'

**What goes wrong:** Runtime error "useRouter is not a function" or "Cannot read properties of undefined".
**Why it happens:** `useRouter`, `usePathname`, `useSearchParams` must all come from `next/navigation` in the App Router. The old Pages Router used `next/router`. Both exist in the package.
**How to avoid:** Always `import { useRouter, usePathname, useSearchParams } from 'next/navigation'`.
**Warning signs:** TypeScript may not catch this immediately if types overlap.

### Pitfall 4: Stale PairContext Values in Tab Key

**What goes wrong:** The `key={`${asset1}-${asset2}`}` on the Tabs container uses the PairContext values, but PairContext is updated asynchronously after the URL params are set on mount. If the key is evaluated before PairContext hydrates, all tabs remount unnecessarily on first render.
**Why it happens:** PairContext starts with `asset1 = ''`, `asset2 = ''`. The mount effect sets real values. The Tabs container remounts once as values change from empty to real.
**How to avoid:** This one-time remount on first load is acceptable — it happens before any API calls in tab content. Document this in code comments so future developers understand the intentional double-render.
**Warning signs:** Console shows two renders of PairAnalysisContent on first page load.

### Pitfall 5: Old Route Directories Still Served

**What goes wrong:** Navigating to `/research` still loads the old stub page after "removal".
**Why it happens:** In Next.js App Router, the route exists as long as the directory exists. Simply not linking to it doesn't remove it.
**How to avoid:** Delete the directories (`deep-dive/`, `research/`, `backtest/`, `optimize/`, `summary/`) or add `redirects` in `next.config.ts`. For this phase, deletion is the correct approach — these are stub pages with no users.
**Warning signs:** `npm run dev` still resolves old URLs after supposedly removing them.

---

## Code Examples

### Verified Pattern: Mantine Tabs with pills variant and controlled value

```tsx
// Source: verified from @mantine/core 8.3.18 Tabs.mjs — keepMounted default is true
// This means all tab panels are mounted; only display is toggled. Safe for our use case.
<Tabs
  value={activeTab}
  onChange={setActiveTab}
  variant="pills"
  keepMounted    // default true — panels stay mounted when switching tabs
>
  <Tabs.List>
    <Tabs.Tab value="statistics">Statistics</Tabs.Tab>
    <Tabs.Tab value="research">Research</Tabs.Tab>
    <Tabs.Tab value="backtest">Backtest</Tabs.Tab>
    <Tabs.Tab value="optimize">Optimize</Tabs.Tab>
  </Tabs.List>

  <Tabs.Panel value="statistics" pt="md">
    {/* content */}
  </Tabs.Panel>
  {/* ... other panels */}
</Tabs>
```

**Important:** `keepMounted: true` is the default. This means all four panels are mounted in the DOM even when inactive. For Phase 1 (placeholder content only) this is fine. Later phases building tab content should be aware that lazy loading will require explicitly setting `keepMounted={false}` or using conditional rendering inside panels (see RSRCH-04).

### Verified Pattern: URLSearchParams merging for tab updates

```tsx
// Source: verified from Next.js 16 docs (use-search-params.md — "Updating searchParams" section)
const params = new URLSearchParams(searchParams.toString())
params.set('tab', newTab)
router.replace(pathname + '?' + params.toString())
```

This preserves existing params (asset1, asset2, timeframe) while updating just the tab param.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `import { useRouter } from 'next/router'` | `import { useRouter } from 'next/navigation'` | Next.js 13 (App Router) | All routing hooks now come from `next/navigation` |
| `router.query` for URL params | `useSearchParams()` + `.get(key)` | Next.js 13 | `query` object removed; use URLSearchParams interface |
| `pathname` from `useRouter()` | `usePathname()` separate hook | Next.js 13 | Separate import required |
| Static export with `getStaticProps` | Client-side data fetching in `useEffect` | App Router migration | All pages in this project are already `'use client'` |

**Deprecated/outdated:**
- `next/router`: Still exists in the package for Pages Router compatibility but must NOT be used in App Router (`app/` directory). The project has no `pages/` directory so this is not a concern, but import mistakes will fail silently or with confusing errors.

---

## Open Questions

1. **Redirect vs. delete for old routes**
   - What we know: Stub pages exist at `/deep-dive`, `/research`, `/backtest`, `/optimize`, `/summary`. All have placeholder content only. Claude's discretion (CONTEXT.md).
   - What's unclear: Whether any bookmarked URLs or internal links point to the old routes.
   - Recommendation: Delete the directories. Stubs have no real users, no external links, and no SEO value. Adding redirects adds configuration noise for zero benefit at this stage.

2. **Tab icon inclusion**
   - What we know: Claude's discretion per CONTEXT.md. Tabler icons matching old sidebar items are already imported in Sidebar.tsx.
   - Recommendation: Add icons to tab labels. `IconChartHistogram` (Statistics), `IconMicroscope` (Research), `IconChartLine` (Backtest), `IconAdjustments` (Optimize). Consistent with existing sidebar style. Low effort, improves scannability.

3. **Pair Analysis header display**
   - What we know: Claude's discretion per CONTEXT.md. Header.tsx already shows pair dropdowns globally.
   - Recommendation: Add a `Title` showing "ETH / BTC" prominently at the top of the Pair Analysis page, pulled from PairContext. The global Header dropdowns remain for changing the pair (NAV-03 is already satisfied by Header). No additional header design needed.

---

## Environment Availability

Step 2.6: SKIPPED — Phase 1 is purely frontend code changes with no external service dependencies beyond the already-running Next.js dev server. No new CLI tools, databases, or runtime services are introduced.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | No frontend test framework installed (no jest.config, no vitest.config, no test scripts in package.json) |
| Config file | None — Wave 0 gap |
| Quick run command | `npm run lint` (ESLint only) |
| Full suite command | `npm run build` (TypeScript + build validation) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NAV-01 | Sidebar shows exactly Scanner + Pair Analysis in Research section | manual | Navigate sidebar in browser | N/A |
| NAV-02 | Scanner row click navigates to /pair-analysis with correct params | manual | Click row, verify URL + header | N/A |
| NAV-03 | Header dropdowns change pair without leaving /pair-analysis | manual | Change dropdown on /pair-analysis | N/A |
| NAV-04 | Four tabs render; switching tabs does not re-fetch | manual | Click through all 4 tabs | N/A |
| NAV-05 | Changing pair in header clears tab content (remount) | manual | Select new pair, verify stale data gone | N/A |
| Build integrity | TypeScript compiles, no missing Suspense errors | automated | `npm run build` | ✅ (existing) |
| Lint | No ESLint violations in new/modified files | automated | `npm run lint` | ✅ (existing) |

### Sampling Rate

- **Per task commit:** `cd frontend && npm run lint`
- **Per wave merge:** `cd frontend && npm run build`
- **Phase gate:** `npm run build` green before `/gsd:verify-work`

### Wave 0 Gaps

No frontend test framework is installed. For Phase 1 (navigation scaffold), all verification is manual browser testing + build success. This is acceptable — no business logic to unit test in this phase.

- [ ] Consider adding a frontend test framework (Jest + React Testing Library or Vitest) in a future phase before tab content is implemented.

*(NAV-01 through NAV-05 are all interaction/navigation behaviors best verified manually for this phase.)*

---

## Project Constraints (from CLAUDE.md)

All directives below are mandatory for this phase:

| Directive | Impact on Phase 1 |
|-----------|-------------------|
| Next.js 16 App Router | Use `next/navigation` for all routing hooks (not `next/router`) |
| React 19 | `key` remount pattern is standard React behavior — fully supported |
| Mantine v8 | Use `Tabs`, `NavLink`, `Container`, `Stack`, `Paper`, `Title`, `Text` — no custom CSS |
| Dark mode only | No light-mode variants; no conditional color scheme logic |
| All pages `'use client'` | Pair Analysis page must have `'use client'` directive at top |
| `usePathname()` for sidebar active state | Already used in Sidebar.tsx — continue the pattern |
| TypeScript strict mode | All props, state, and handler types must be explicitly typed |
| ESLint via `eslint-config-next` | Run `npm run lint` before committing |
| No Pandas / Polars | Not applicable (frontend-only phase) |
| Charts via PlotlyChart wrapper | Not applicable (no charts in Phase 1 scaffold) |
| PairContext for global pair state | Phase 1 must read from and write to PairContext — never duplicate state |
| API client via `frontend/src/lib/api.ts` | Not applicable (no API calls in Phase 1 scaffold) |
| GSD workflow enforcement | All changes via GSD execute-phase, not direct edits |

---

## Sources

### Primary (HIGH confidence)
- `frontend/node_modules/next/dist/docs/01-app/03-api-reference/04-functions/use-router.md` — useRouter API, router.push/replace signatures, `next/navigation` import
- `frontend/node_modules/next/dist/docs/01-app/03-api-reference/04-functions/use-search-params.md` — useSearchParams API, Suspense requirement, URLSearchParams merging pattern
- `frontend/src/components/layout/Sidebar.tsx` — Existing NavLink + usePathname pattern
- `frontend/src/contexts/PairContext.tsx` — Available setters (setAsset1, setAsset2, setTimeframe)
- `frontend/src/components/layout/Header.tsx` — NAV-03 already satisfied by existing Header
- `frontend/src/app/(dashboard)/scanner/page.tsx` — Table.Tr structure to receive onClick
- `frontend/node_modules/@mantine/core/esm/components/Tabs/Tabs.mjs` — Mantine Tabs props (variant, value, onChange, keepMounted default=true)

### Secondary (MEDIUM confidence)
- `frontend/package.json` — Confirmed installed versions: Next.js 16.2.1, React 19.2.4, @mantine/core 8.3.18
- `frontend/AGENTS.md` — Warning that Next.js 16 has breaking changes from training data; verified APIs against local node_modules docs

### Tertiary (LOW confidence)
- None — all critical claims verified against local source files and node_modules documentation.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified in package.json and node_modules
- Architecture: HIGH — patterns verified against existing codebase files + Next.js 16 local docs
- Pitfalls: HIGH — Suspense requirement verified in Next.js 16 local docs; others derived from code analysis
- Mantine Tabs behavior: HIGH — verified keepMounted default from Tabs.mjs source

**Research date:** 2026-03-31
**Valid until:** 2026-06-01 (stable framework versions; Mantine and Next.js are pinned in package.json)
