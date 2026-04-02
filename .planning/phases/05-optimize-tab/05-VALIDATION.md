---
phase: 5
slug: optimize-tab
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-02
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.4+ (backend), ESLint + TypeScript build (frontend) |
| **Config file** | `pyproject.toml` (pytest), `frontend/tsconfig.json` (TS), `frontend/eslint.config.mjs` (ESLint) |
| **Quick run command** | `cd frontend && npm run lint && npm run build` |
| **Full suite command** | `uv run pytest tests/ --ignore=tests/test_api.py --ignore=tests/test_backtest_api.py --ignore=tests/test_optimization_api.py --ignore=tests/test_research_api.py --ignore=tests/test_trading_api.py && cd frontend && npm run lint && npm run build` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run lint && npm run build`
- **After every plan wave:** Run full suite command above
- **Before `/gsd:verify-work`:** Full suite must be green + manual browser smoke test
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | OPT-01 | build + lint | `cd frontend && npm run build` | Yes | ⬜ pending |
| 05-01-02 | 01 | 1 | OPT-02 | build + lint | `cd frontend && npm run build` | Yes | ⬜ pending |
| 05-01-03 | 01 | 1 | OPT-03 | build + lint | `cd frontend && npm run build` | Yes | ⬜ pending |
| 05-02-01 | 02 | 2 | OPT-04 | build + lint | `cd frontend && npm run build` | Yes | ⬜ pending |
| 05-02-02 | 02 | 2 | OPT-05 | build + lint | `cd frontend && npm run build` | Yes | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No new test files needed for this frontend-only phase. Backend optimization tests already exist at `tests/test_optimization.py` and `tests/test_optimization_api.py`.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Axis config form renders with 2 Select dropdowns and 3 NumberInputs per axis | OPT-01 | No Jest/RTL configured in project | Navigate to Pair Analysis > Optimize tab, verify 2 param selectors + min/max/step fields render |
| Heatmap renders with correct colors and star annotation on best cell | OPT-02 | Visual verification needed | Run grid search, verify heatmap shows RdYlGn color scale with star on best cell |
| Best cell card shows correct param values, Sharpe, P&L, and robustness badge | OPT-03 | Visual verification needed | Run grid search, compare best cell card values against heatmap tooltip for same cell |
| Fold table shows correct per-fold train/test Sharpe and trade counts | OPT-04 | Visual verification needed | Run walk-forward, verify fold table rows match expected fold count |
| Stability verdict badge shows correct color (green/yellow/red) matching verdict | OPT-05 | Visual verification needed | Run walk-forward, verify badge color matches verdict text |
| Apply to Backtest pre-fills Backtest tab with recommended params | OPT-03 | Cross-tab interaction | Click Apply to Backtest on best cell card, verify Backtest tab params update |
| Metric selector re-colors heatmap without API call | OPT-02 | Visual + no-network verification | Change Color by dropdown, verify heatmap updates without network request in devtools |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
