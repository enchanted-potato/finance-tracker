---
phase: 06-dashboard-and-navigation-polish
plan: "01"
subsystem: testing
tags: [pytest, plotly, streamlit, tdd, dashboard]

# Dependency graph
requires:
  - phase: 05-deployment
    provides: Deployed app with dashboard.py including _render_line_chart
provides:
  - RED-state test scaffold for DASH-02 (negative delta color) and DASH-03 (chart tick format)
  - tests/test_dashboard_helpers.py with 4 failing tests for plan 02 to fix
affects: [06-dashboard-and-navigation-polish]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Deferred imports inside test functions allow pytest to collect tests even when the imported symbol doesn't exist yet (ImportError surfaces at runtime, not collection time)"
    - "_MockSt helper class stubs streamlit module so chart helper functions can be tested without a running Streamlit server"

key-files:
  created:
    - tests/test_dashboard_helpers.py
  modified: []

key-decisions:
  - "Deferred imports inside each test body (not module-level) so pytest can collect all 4 tests even before _build_net_worth_card_html exists — avoids collection error while preserving ImportError RED state"
  - "Mock st module via monkeypatch on the dashboard module attribute rather than sys.modules to avoid side-effects on other imports"

patterns-established:
  - "TDD scaffold pattern: import inside test body for symbols that don't exist yet"

requirements-completed: [DASH-02, DASH-03]

# Metrics
duration: 2min
completed: 2026-03-07
---

# Phase 6 Plan 01: Dashboard Helper Tests Summary

**Pytest-collectable RED-state test scaffold for DASH-02 (negative delta HTML color) and DASH-03 (Plotly chart tick format split into tickprefix/tickformat)**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-07T18:25:15Z
- **Completed:** 2026-03-07T18:27:39Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Created `tests/test_dashboard_helpers.py` with 4 tests all collected by pytest without collection errors
- DASH-02 tests fail with ImportError (correct RED — `_build_net_worth_card_html` not yet in dashboard.py)
- DASH-03 tests fail with AssertionError (correct RED — dashboard still uses broken combined `yaxis_tickformat="£,.0f"`)
- Identified the key structural issue: module-level imports would cause collection errors, so imports were deferred into test function bodies

## Task Commits

Each task was committed atomically:

1. **Task 1: Create dashboard helper tests (RED state)** - `4a866e6` (test)

**Plan metadata:** _(docs commit follows)_

## Files Created/Modified
- `tests/test_dashboard_helpers.py` - 4 RED-state tests for DASH-02 and DASH-03; uses deferred imports and _MockSt helper class

## Decisions Made
- Deferred imports inside each test function rather than module-level: plan specified ImportError as acceptable RED state, but module-level ImportError causes a pytest collection error (which the done criteria explicitly rules out). Moving the import inside the test body lets pytest collect all 4 tests while still producing ImportError at run time.
- Monkeypatching `frontend.pages.dashboard.st` (the module-level st reference) rather than patching `streamlit` globally, which avoids polluting other tests.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Moved imports inside test bodies to avoid collection errors**
- **Found during:** Task 1 (Create dashboard helper tests)
- **Issue:** Plan's code sample placed `from frontend.pages.dashboard import _build_net_worth_card_html` at module level. This causes a pytest collection error (not just a test failure), which violates the done criteria ("not a collection error").
- **Fix:** Moved all dashboard imports inside each test function body so pytest can collect 4 tests while the symbol is still missing.
- **Files modified:** tests/test_dashboard_helpers.py
- **Verification:** `uv run pytest tests/test_dashboard_helpers.py -v` — 4 tests collected, 4 FAILED (2 ImportError, 2 AssertionError)
- **Committed in:** 4a866e6 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug in plan's sample code caused collection error)
**Impact on plan:** Required adjustment to test structure; RED state and intent preserved exactly.

## Issues Encountered
None beyond the import-structure deviation noted above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan 02 can immediately implement `_build_net_worth_card_html` and fix the chart axis format; tests are waiting in RED state
- The `_MockSt` helper class in the test file provides the monkeypatch pattern plan 02 can extend

## Self-Check: PASSED
- tests/test_dashboard_helpers.py: FOUND
- 06-01-SUMMARY.md: FOUND
- Commit 4a866e6: FOUND

---
*Phase: 06-dashboard-and-navigation-polish*
*Completed: 2026-03-07*
