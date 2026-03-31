---
phase: 1
slug: routing-navigation-scaffold
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | jest (via Next.js) for unit; manual browser for navigation |
| **Config file** | frontend/package.json (scripts section) |
| **Quick run command** | `cd frontend && npm run build` |
| **Full suite command** | `cd frontend && npm run build && npm run lint` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run build`
- **After every plan wave:** Run `cd frontend && npm run build && npm run lint`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | NAV-01 | build | `npm run build` | ✅ | ⬜ pending |
| 1-01-02 | 01 | 1 | NAV-02 | build | `npm run build` | ✅ | ⬜ pending |
| 1-01-03 | 01 | 1 | NAV-03 | build | `npm run build` | ✅ | ⬜ pending |
| 1-01-04 | 01 | 1 | NAV-04 | build | `npm run build` | ✅ | ⬜ pending |
| 1-01-05 | 01 | 1 | NAV-05 | build | `npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Sidebar links navigate to correct pages | NAV-01 | Navigation routing requires browser | Click Scanner and Pair Analysis sidebar links, verify correct page loads |
| Scanner row click navigates to Pair Analysis | NAV-02 | Click interaction requires browser | Click a pair row in Scanner, verify Pair Analysis loads with that pair |
| Pair selection from header works | NAV-03 | Dropdown interaction requires browser | Change pair from Pair Analysis header dropdowns, verify header updates |
| Tab switching works without re-fetch | NAV-04 | Tab interaction requires browser | Switch between 4 tabs, verify no loading states on revisit |
| Pair change clears tab state | NAV-05 | State clearing requires browser | Load data in a tab, change pair, verify tab shows fresh/empty state |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
