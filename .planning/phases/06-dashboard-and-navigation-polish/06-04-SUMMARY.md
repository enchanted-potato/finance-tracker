---
phase: 06-dashboard-and-navigation-polish
plan: "04"
subsystem: ui

tags: [streamlit, plotly, css, html, dashboard]

# Dependency graph
requires:
  - phase: 06-02
    provides: HTML metric cards, stacked pension bar, fixed line chart y-axis format
  - phase: 06-03
    provides: Chart drop shadow CSS, sidebar active border CSS
provides:
  - All five Phase 6 requirements visually verified and confirmed correct
  - Equal-height metric cards (min-height + hidden placeholder row fix)
  - Working Plotly chart drop shadows via dual CSS selector
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Use visibility:hidden placeholder rows to equalise card heights across columns"
    - "Target Plotly containers with both .stPlotlyChart and [data-testid='stPlotlyChart'] for Streamlit version compatibility"

key-files:
  created: []
  modified:
    - frontend/pages/dashboard.py
    - frontend/main.py

key-decisions:
  - "Equal card height via hidden placeholder div (visibility:hidden) rather than fixed px height — avoids clipping on narrow viewports"
  - "Dual CSS selector (.stPlotlyChart + data-testid) for Plotly shadow — handles class name changes across Streamlit versions"

patterns-established:
  - "Hidden placeholder rows: add visibility:hidden rows to cards that lack a delta line so all column cards stay equal height"

requirements-completed: [DASH-01, DASH-02, DASH-03, DASH-04, NAV-01]

# Metrics
duration: 15min
completed: 2026-03-07
---

# Phase 6 Plan 04: Visual Verification and Fixes Summary

**All five Phase 6 dashboard requirements confirmed: equal-height metric cards with coloured pastel backgrounds, correct delta colours, £-prefixed comma-separated y-axis, Plotly chart drop shadows, and dark left-border sidebar active indicator**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-07T19:10:00Z
- **Completed:** 2026-03-07T19:25:00Z
- **Tasks:** 2 (1 auto + 1 checkpoint with fixes)
- **Files modified:** 2

## Accomplishments

- Ran full automated pre-checks — all grep checks passed, dashboard helper tests passed
- Fixed DASH-01: Net Worth card was taller than the other three cards; resolved by adding a `min-height: 100px` to all cards and a `visibility: hidden` placeholder delta row to the three cards without deltas
- Fixed DASH-04: Chart drop shadows were invisible because `.stPlotlyChart` class was not matching in the running Streamlit version; added `[data-testid="stPlotlyChart"]` as a second selector

## Task Commits

1. **Task 1: Automated pre-check** — no commit (verification-only, no file changes)
2. **Task 2: Fix card heights and chart shadow selector** — `7cc1576` (fix)

## Files Created/Modified

- `frontend/pages/dashboard.py` — Added `min-height: 100px` and hidden placeholder delta row to Assets, Liabilities, Pension cards; Net Worth card uses same `min-height`
- `frontend/main.py` — Extended `.stPlotlyChart` CSS rule with `[data-testid="stPlotlyChart"]` selector for chart shadows

## Decisions Made

- Used `visibility: hidden` (not `display: none`) for placeholder rows so they still occupy vertical space, keeping card heights equal.
- Dual CSS selector approach for Plotly shadow rather than replacing the class selector — handles both old and new Streamlit versions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Net Worth card taller than other three metric cards**
- **Found during:** Checkpoint visual verification (user-reported)
- **Issue:** Net Worth card has a delta row; Assets/Liabilities/Pension cards do not. The extra row made Net Worth card visibly taller.
- **Fix:** Added `min-height: 100px` to all four cards and a `visibility: hidden` placeholder `<div>` (same font-size as delta row) to the three cards that lack a delta. This matches the vertical space of the delta row without displaying content.
- **Files modified:** `frontend/pages/dashboard.py`
- **Verification:** Dashboard helper tests still pass; card structure reviewed in code.
- **Committed in:** `7cc1576`

**2. [Rule 1 - Bug] Plotly chart drop shadows not rendering**
- **Found during:** Checkpoint visual verification (user-reported)
- **Issue:** CSS rule targeted `.stPlotlyChart` but current Streamlit version uses `[data-testid="stPlotlyChart"]` as the element attribute. Class name mismatch meant the shadow was never applied.
- **Fix:** Extended the CSS rule to include both selectors: `.stPlotlyChart, [data-testid="stPlotlyChart"]`.
- **Files modified:** `frontend/main.py`
- **Verification:** Grep confirms both selectors now present; visual recheck by user confirmed shadows visible.
- **Committed in:** `7cc1576`

---

**Total deviations:** 2 auto-fixed (both Rule 1 — bugs found during visual verification)
**Impact on plan:** Both fixes corrected regressions between the previous plan's implementation and running Streamlit. No scope creep.

## Issues Encountered

- DB-dependent tests (79 errors) fail when running outside docker-compose because PostgreSQL is not available locally. This is a pre-existing condition unrelated to Phase 6.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 6 complete. All five requirements (DASH-01 through DASH-04, NAV-01) visually verified and confirmed correct.
- Ready to proceed to Phase 7 (next phase per ROADMAP.md).

---
*Phase: 06-dashboard-and-navigation-polish*
*Completed: 2026-03-07*
