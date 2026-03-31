---
phase: 2
slug: statistics-tab
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | No frontend test framework (no jest/vitest configured) |
| **Config file** | `frontend/tsconfig.json` (TypeScript strict), `frontend/eslint.config.mjs` |
| **Quick run command** | `cd frontend && npm run lint` |
| **Full suite command** | `cd frontend && npm run build` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run lint`
- **After every plan wave:** Run `cd frontend && npm run build`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | STAT-01 | lint+build | `cd frontend && npm run lint && npm run build` | ✅ | ⬜ pending |
| 02-01-02 | 01 | 1 | STAT-02 | lint+build | `cd frontend && npm run lint && npm run build` | ✅ | ⬜ pending |
| 02-01-03 | 01 | 1 | STAT-03 | lint+build | `cd frontend && npm run lint && npm run build` | ✅ | ⬜ pending |
| 02-01-04 | 01 | 1 | UX-01 | lint+build | `cd frontend && npm run lint && npm run build` | ✅ | ⬜ pending |
| 02-01-05 | 01 | 1 | UX-03 | lint+build | `cd frontend && npm run lint && npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No frontend test framework installation needed — ESLint + TypeScript strict mode via `npm run build` is the automated gate.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Stat cards render with correct values from API | STAT-01 | Visual UI — no frontend test framework | 1. Start API + frontend. 2. Navigate to Pair Analysis. 3. Select a pair. 4. Verify 5 stat cards show p-value, half-life, hedge ratio, correlation, cointegration score with colored badges. |
| Spread chart renders with timestamps | STAT-02 | Visual chart rendering | 1. With pair selected, verify spread chart appears with time series x-axis. 2. Confirm dark Plotly template applied. |
| Z-score chart with threshold lines | STAT-03 | Visual chart + interactive sliders | 1. Verify z-score chart appears below spread chart. 2. Drag entry/exit sliders. 3. Confirm 4 threshold lines (±entry, ±exit) update in real-time. |
| Dark Plotly template consistent with Academy | UX-01 | Visual consistency check | 1. Open Academy page, note chart styling. 2. Open Statistics tab, compare chart backgrounds, fonts, colors. |
| API error shows inline Alert | UX-03 | Requires error triggering | 1. Stop backend API. 2. Select a pair on Statistics tab. 3. Verify red Alert appears with actionable message (not blank page). |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
