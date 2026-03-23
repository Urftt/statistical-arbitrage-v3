# Progress Tracker

## Current Status
**Phase**: 0 (Port & Scaffold) — COMPLETE
**Branch**: `main`
**Next**: Phase 1 — Academy Chapter 1

## Completed

### Phase 0: Port & Scaffold
- [x] Python project setup (pyproject.toml, UV, Python 3.12)
- [x] Backend ported from v2 (src/, api/, config/, tests/)
- [x] 174 unit tests passing
- [x] Next.js 16 + React 19 + Mantine v8 + Plotly initialized
- [x] Dark theme + Plotly wrapper (SSR-safe)
- [x] App shell: 3-pillar sidebar, header with pair selectors
- [x] Typed API client (all v2 endpoints)
- [x] PairContext for global pair state
- [x] Glossary: 17 terms, searchable page, GlossaryLink component
- [x] All 10 routes scaffolded with placeholder content
- [x] Frontend build passing

## Decisions Log
- **Framework**: Next.js 16 + React 19 + Mantine v8 (stick with React, not switch to Nuxt)
- **Git strategy**: Branch per phase, conventional commits, merge commits to main
- **Testing**: Backend unit tests + `npm run build` as gate + visual verification
- **Academy design**: 5 chapters, ~18 lessons, Brilliant-style interactive, real crypto data from start
- **Target learner**: Data scientist who knows stats, learning finance/stat arb domain
- **Academy graduation**: Full pipeline understanding (pair selection → backtest interpretation)

## Session Notes
- API integration tests (43) need cached market data — expected, will pass once data is cached
- v2 had Dash frontend dependencies (dash, dash-bootstrap-components) — removed in v3
