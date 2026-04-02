---
phase: 4
slug: research-tab
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-02
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | jest (via Next.js) + manual browser verification |
| **Config file** | frontend/package.json |
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
| 4-01-01 | 01 | 1 | RSRCH-01 | build | `npm run build` | ✅ | ⬜ pending |
| 4-01-02 | 01 | 1 | RSRCH-02 | build | `npm run build` | ✅ | ⬜ pending |
| 4-01-03 | 01 | 1 | RSRCH-03 | build | `npm run build` | ✅ | ⬜ pending |
| 4-02-01 | 02 | 2 | RSRCH-04 | build+manual | `npm run build` | ✅ | ⬜ pending |
| 4-02-02 | 02 | 2 | RSRCH-05 | build+manual | `npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Accordion expand/collapse with independent Run buttons | RSRCH-01 | UI interaction | Open page, expand module, click Run, verify only that module loads |
| Takeaway callout colors match severity | RSRCH-02 | Visual verification | Run module, check Alert color matches green/yellow/red severity |
| Rolling stability chart has p-value reference line | RSRCH-03 | Chart visual | Run Rolling Stability, verify horizontal reference line at 0.05 |
| Apply to Backtest pre-fills form | RSRCH-04 | Cross-tab interaction | Click Apply, verify Backtest tab form fields match recommended params |
| Apply button hidden when recommended_backtest_params is null | RSRCH-05 | Conditional render | Run OOS Validation, verify no Apply button shown |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
