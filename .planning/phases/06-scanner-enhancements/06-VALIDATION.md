---
phase: 6
slug: scanner-enhancements
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-07
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend) + manual UAT (frontend) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/test_scanner_api.py -x` |
| **Full suite command** | `uv run pytest tests/ --ignore=tests/test_api.py --ignore=tests/test_backtest_api.py --ignore=tests/test_optimization_api.py --ignore=tests/test_research_api.py --ignore=tests/test_trading_api.py` |
| **Estimated runtime** | ~30 seconds (unit suite) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_scanner_api.py -x`
- **After every plan wave:** Run full unit suite
- **Before `/gsd-verify-work`:** Full suite green + manual UAT for frontend changes
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

To be filled by planner — placeholder structure:

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 6-XX-XX | XX | X | SCAN-XX | T-6-XX / — | TBD | unit/manual | TBD | ✅ / ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_scanner_api.py` — new test file with stubs for SCAN-01..04 backend behavior (rename, response shape, completeness fix, dropped-coins exposure)
- [ ] No new framework install needed — pytest is already in pyproject.toml dev dependencies

*Frontend changes are validated manually — see Manual-Only Verifications below.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Sortable column headers cycle asc → desc → none on click | SCAN-01 | UI interaction, no automated frontend test infrastructure | 1. Navigate to /scanner. 2. Run a scan. 3. Click p-value header → expect IconChevronDown + ascending order. 4. Click again → expect IconChevronUp + descending. 5. Click again → expect IconArrowsSort dimmed + restored default order. |
| Two-section visual split with independent sort | SCAN-02 | UI interaction | 1. Run a scan with mixed cointegrated/non-cointegrated results. 2. Verify "Cointegrated (N)" section appears above "Not cointegrated (M)". 3. Sort cointegrated by Coint. Score desc. 4. Verify non-cointegrated section sort is unaffected. |
| Loading state during scan | SCAN-03 | UI interaction | 1. Click "Scan N pairs". 2. Verify Loader spinner appears in button. 3. Verify button disabled during scan. |
| Error state on scan failure | SCAN-04 | UI interaction (requires API down) | 1. Stop the API (`pkill -f run_api.py`). 2. Click Scan. 3. Verify red Alert with actionable message appears. |
| Auto-fetch on land with empty cache | D-20 | UI interaction (state-dependent) | 1. Clear cache: `rm -rf data/cache/*_4h.parquet`. 2. Navigate to /scanner?timeframe=4h. 3. Verify fetch fires automatically. 4. Verify cache status line updates after fetch. |
| URL timeframe param persistence | D-27 | URL routing | 1. Navigate to /scanner. 2. Change timeframe to 4h. 3. Verify URL becomes `/scanner?timeframe=4h`. 4. Refresh page. 5. Verify timeframe stays at 4h. |
| Daily timeframe scan no longer silently empty | D-29 + completeness fix | Bug-fix verification | 1. Select 1d timeframe. 2. Run scan. 3. Verify scan returns non-zero results (after completeness formula fix). |
| Pair Analysis row navigation still works (Phase 1 D-04 preserved) | NAV-02 (regression) | UI interaction | 1. Run a scan. 2. Click any row in either section. 3. Verify navigation to `/pair-analysis?asset1=...&asset2=...&timeframe=...`. 4. Verify Pair Analysis loads with the correct pair selected. |
| Dropped-coins Alert appears when completeness filter excludes coins | D-23/D-24 | UI + state-dependent | 1. Ensure cache contains some gappy coin (e.g., low-liquidity altcoin). 2. Run scan. 3. Verify inline Alert above results listing excluded coins with their symbols. |

---

## Validation Sign-Off

- [ ] All backend tasks have automated `pytest` verification or Wave 0 test stubs
- [ ] All frontend tasks have manual UAT instructions in this document
- [ ] Sampling continuity: no 3 consecutive backend tasks without automated verify
- [ ] Wave 0 covers all MISSING references (test_scanner_api.py)
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s for unit suite
- [ ] `nyquist_compliant: true` set in frontmatter after planning completes

**Approval:** pending
