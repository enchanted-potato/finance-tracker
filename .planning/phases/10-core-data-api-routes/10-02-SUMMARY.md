---
phase: 10-core-data-api-routes
plan: 02
subsystem: api
tags: [fastapi, pydantic, liabilities, tdd, python]

# Dependency graph
requires:
  - phase: 09-fastapi-foundation
    provides: api/main.py, api/dependencies.py, get_current_user auth pattern, get_session dependency

provides:
  - api/schemas/liabilities.py — Pydantic response schemas (LiabilityTypeResponse, LiabilityEntryRequest, LiabilityEntryResponse, LiabilityHistoryItemResponse, LiabilityHistoryDayResponse)
  - api/routers/liabilities.py — FastAPI router prefix /api/liabilities with GET /types, POST /entries, DELETE /entries/{id}, GET /history
  - tests/test_api_liabilities.py — 10 integration tests covering all endpoints, auth, precision, history shape

affects:
  - 10-05 (router wiring — will include_router(liabilities.router) in main.py)
  - 11-react-scaffold (API contract for liabilities endpoints)
  - 12-data-pages (liabilities page consumes these endpoints)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Thin router: service call + Pydantic schema mapping, no business logic in route handler
    - Decimal(str(body.amount)) for safe float-to-Decimal conversion in request handling
    - Auto-snapshot via capture_snapshot() after every balance write (D-04 pattern)
    - history endpoint: defaultdict grouping of flat service results by ISO date string, newest-first sort
    - LiabilityHistoryItemResponse uses "balance" key (not "amount") for unified D-01 history shape

key-files:
  created:
    - api/schemas/liabilities.py
    - api/routers/liabilities.py
    - tests/test_api_liabilities.py
  modified: []

key-decisions:
  - "History items use 'balance' key (not 'amount') matching unified D-01 history shape from CONTEXT.md — consistent across accounts, liabilities, and pension history endpoints"
  - "Router not wired into api/main.py — Plan 05 owns all include_router() calls"
  - "capture_snapshot imported directly (from app.services.snapshot_service import capture_snapshot) so test patch path api.routers.liabilities.capture_snapshot works correctly"

patterns-established:
  - "Decimal(str(body.amount)) for request body float-to-Decimal conversion — prevents float binary representation precision loss"
  - "ValueError from delete service mapped to HTTP 404 (not 400) for not-found/wrong-user cases"
  - "client_with_db fixture: idempotent router include + dependency_overrides[get_session] per test function"

requirements-completed:
  - API-06

# Metrics
duration: 3min
completed: 2026-05-06
---

# Phase 10 Plan 02: Liabilities Router Summary

**FastAPI liabilities router with 4 endpoints (types+in_use, entry upsert+auto-snapshot, entry delete, date-grouped history) and Pydantic schemas using float serialisation and unified D-01 history shape**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-05-06T09:53:23Z
- **Completed:** 2026-05-06T09:56:12Z
- **Tasks:** 2 (TDD: RED then GREEN)
- **Files modified:** 3 created

## Accomplishments
- 10 integration tests written first (RED phase), all covering auth, precision, history shape, snapshot trigger
- Liabilities router implementing GET /api/liabilities/types with in_use flag, POST /entries with Decimal precision, DELETE /entries/{id} with ValueError->404 mapping, GET /history with date grouping
- All 10 tests pass (GREEN phase); no regressions in existing API test suite (test_api_health.py, test_api_auth.py)

## Task Commits

Each task was committed atomically:

1. **Task 1: Write failing tests for liabilities router (RED)** - `65b62bf` (test)
2. **Task 2: Implement api/schemas/liabilities.py and api/routers/liabilities.py (GREEN)** - `bafa5fd` (feat)

**Plan metadata:** (committed with SUMMARY.md)

_Note: TDD tasks — test commit (RED) then feat commit (GREEN)_

## Files Created/Modified
- `api/schemas/liabilities.py` — Pydantic BaseModel schemas: LiabilityTypeResponse, LiabilityEntryRequest, LiabilityEntryResponse, LiabilityHistoryItemResponse, LiabilityHistoryDayResponse; all float fields, no user_id
- `api/routers/liabilities.py` — APIRouter(prefix="/api/liabilities"): 4 endpoints with full auth dependencies, Decimal(str()) conversion, capture_snapshot integration, history date-grouping via defaultdict
- `tests/test_api_liabilities.py` — 10 integration tests covering all endpoints plus auth bypass, precision preservation, cross-user delete 404, history shape validation, float serialisation

## Decisions Made
- History item key is "balance" (not "amount") — unified D-01 history shape from CONTEXT.md; liabilities model uses `amount` field but router translates to `balance` key for consistency with accounts/pension history
- Router is NOT wired into api/main.py — Plan 05 owns all router registration; confirmed api/main.py unchanged
- capture_snapshot is imported directly at module level so mocker.patch("api.routers.liabilities.capture_snapshot") works in tests

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

Pre-existing test failures in test_account_service.py, test_type_service.py, test_snapshot_service.py, and test_dashboard_helpers.py were present before this plan's changes (verified with git stash). These are out of scope for this plan.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Liabilities API contract complete: 4 endpoints with correct shapes for React consumption
- Router ready for include_router() wiring in Plan 05
- Mirrors accounts router pattern — React data page can reuse same client code shape

---
*Phase: 10-core-data-api-routes*
*Completed: 2026-05-06*
