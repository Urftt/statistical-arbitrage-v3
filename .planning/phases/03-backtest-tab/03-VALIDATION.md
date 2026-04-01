---
phase: 03
slug: backtest-tab
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-01
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Next.js build (`npm run build`) + ESLint (`npm run lint`) |
| **Config file** | `frontend/next.config.ts`, `frontend/eslint.config.mjs` |
| **Quick run command** | `cd frontend && npm run lint` |
| **Full suite command** | `cd frontend && npm run build` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run lint`
- **After every plan wave:** Run `cd frontend && npm run build`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | BT-01 | build | `cd frontend && npm run build` | ✅ | ⬜ pending |
| 03-01-02 | 01 | 1 | BT-02, BT-03 | build | `cd frontend && npm run build` | ✅ | ⬜ pending |
| 03-01-03 | 01 | 1 | BT-04, BT-05 | build | `cd frontend && npm run build` | ✅ | ⬜ pending |
| 03-01-04 | 01 | 1 | BT-06, BT-07 | build | `cd frontend && npm run build` | ✅ | ⬜ pending |
| 03-01-05 | 01 | 1 | BT-08, BT-09, BT-10 | build | `cd frontend && npm run build` | ✅ | ⬜ pending |
| 03-01-06 | 01 | 1 | UX-02, UX-04 | build | `cd frontend && npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No new test framework or fixtures needed — this is a frontend-only phase validated by TypeScript build and lint.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Parameter sliders adjust values correctly | BT-01 | Visual interaction | Move each slider, verify label updates |
| Equity curve renders with correct data | BT-02 | Visual chart rendering | Run backtest, inspect equity curve matches API response |
| Trade markers appear on z-score/spread charts | BT-04 | Visual overlay | Run backtest, verify triangles at entry/exit points |
| Overfitting warnings appear when Sharpe > 3.0 | BT-08 | Conditional API response | Need a pair that produces high Sharpe |
| Preflight blockers prevent results display | BT-09 | Conditional API response | Need insufficient data scenario |
| Assumptions Accordion expands correctly | BT-10 | Visual interaction | Click accordion, verify content renders |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
