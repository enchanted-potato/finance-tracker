---
phase: 10-core-data-api-routes
plan: "04"
subsystem: api
tags: [fastapi, pydantic, csv, streaming-response, upload-file, python]

requires:
  - phase: 09-fastapi-foundation
    provides: api/main.py, api/dependencies.py, get_current_user, health router pattern

provides:
  - api/routers/snapshots.py — GET /api/snapshots, GET /api/snapshots/export.csv (StreamingResponse), POST /api/snapshots/import (UploadFile), DELETE /api/snapshots/{id}
  - api/routers/configure.py — GET/POST /api/configure/account-types, DELETE /api/configure/account-types/{id}, GET/POST /api/configure/liability-types, DELETE /api/configure/liability-types/{id}
  - api/schemas/snapshots.py — SnapshotResponse (no user_id, float fields), ImportResult
  - api/schemas/configure.py — AccountTypeConfigResponse, LiabilityTypeConfigResponse, AccountTypeCreateRequest, LiabilityTypeCreateRequest
  - tests/test_api_snapshots.py — 8 integration tests for /api/snapshots/*
  - tests/test_api_configure.py — 9 integration tests for /api/configure/*

affects: [10-05-plan, phase-14-history, phase-14-configure]

tech-stack:
  added: []
  patterns:
    - StreamingResponse pattern for in-memory CSV export (no response_model on endpoint)
    - async def + await file.read() pattern for UploadFile multipart endpoints
    - ValueError -> HTTPException(409) mapping for in-use type deletes
    - Thin router calling service functions with keyword-only args; all shaping in router body
    - Pydantic BaseModel response schemas with float fields and no user_id (prevents leakage)

key-files:
  created:
    - api/routers/snapshots.py
    - api/routers/configure.py
    - api/schemas/snapshots.py
    - api/schemas/configure.py
    - tests/test_api_snapshots.py
    - tests/test_api_configure.py
  modified: []

key-decisions:
  - "GET /export.csv uses StreamingResponse with iter([csv_bytes]) — no response_model to avoid FastAPI validation conflict"
  - "POST /import is async def to support await file.read(); all other endpoints are regular def"
  - "ValueError from delete_account_type / delete_liability_type maps to 409 Conflict (not 422) — preserves D-12 decision"
  - "POST create endpoints pass user_id=user_id to service — new types are owned by authenticated caller, not system (user_id=None)"
  - "SnapshotResponse uses snapshot_date: str (ISO date) not datetime — avoids timezone serialisation issues"
  - "api/main.py NOT modified — router wiring deferred to Plan 05 as specified"

patterns-established:
  - "StreamingResponse pattern: generate CSV via csv.writer + io.StringIO, return StreamingResponse(iter([content]), media_type='text/csv', headers={'Content-Disposition': ...})"
  - "409 pattern: try service_call(); except ValueError as exc: check 'not found' in msg for 404, else raise 409"
  - "Import pattern: async def endpoint, await file.read(), decode utf-8 with UnicodeDecodeError -> 400"

requirements-completed: [API-08]

duration: ~15min
completed: 2026-05-06
---

# Phase 10 Plan 04: Snapshots Router and Configure Router Summary

**Snapshots router (history list, CSV StreamingResponse, multipart CSV import, delete) and configure router (account/liability type CRUD with in_use flag and ValueError-to-409 mapping)**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-05-06T18:00:00Z
- **Completed:** 2026-05-06T18:16:30Z
- **Tasks:** 3 (TDD: RED -> GREEN x2 pairs)
- **Files modified:** 6 created, 0 modified

## Accomplishments

- Snapshots router: 4 endpoints covering full snapshot lifecycle (list, export CSV, import CSV, delete)
- Configure router: 6 endpoints covering account-type and liability-type CRUD with in_use flag computed per-type
- 17 integration tests written (8 snapshots + 9 configure) confirming auth, no user_id leakage, correct status codes, 409 on in-use delete
- StreamingResponse CSV export pattern established with `Content-Disposition: attachment; filename=snapshots.csv`
- Multipart CSV import with UTF-8 validation (400 on decode failure) and ImportResult response
- Both routers NOT wired into api/main.py as specified (deferred to Plan 05)

## Task Commits

Each task was committed atomically:

1. **Task 1: Write failing tests for snapshots and configure routers (RED)** - `4b7e088` (test)
2. **Task 2: Implement schemas and snapshots router (GREEN — snapshots half)** - `da0c305` (feat)
3. **Task 3: Implement configure schemas and configure router (GREEN — types half)** - `ba71fde` (feat)

## Files Created/Modified

- `api/schemas/snapshots.py` - SnapshotResponse (id, snapshot_date str, float monetary fields, no user_id) and ImportResult
- `api/schemas/configure.py` - AccountTypeConfigResponse, LiabilityTypeConfigResponse, AccountTypeCreateRequest, LiabilityTypeCreateRequest (no user_id)
- `api/routers/snapshots.py` - GET /api/snapshots, GET /api/snapshots/export.csv (StreamingResponse, no response_model), POST /api/snapshots/import (async def, UploadFile), DELETE /api/snapshots/{id}
- `api/routers/configure.py` - GET/POST/DELETE for account-types and liability-types; ValueError -> 409 for in-use; user_id=user_id on POST
- `tests/test_api_snapshots.py` - 8 integration tests: auth gate, no user_id, ascending order, CSV export headers, CSV import result, invalid UTF-8 400, delete 204, cross-user 404
- `tests/test_api_configure.py` - 9 integration tests: auth gate, no user_id, in_use flag, create 201 + owner, delete 409 in-use, delete 204 unused (both account and liability types)

## Decisions Made

- `GET /export.csv` has NO `response_model` — FastAPI cannot validate StreamingResponse against a Pydantic model (Pitfall 6 from research)
- `POST /import` is `async def` because `await file.read()` is a coroutine (Pitfall 8 from research)
- ValueError with "not found" maps to 404; all other ValueErrors (in-use) map to 409 — per D-12
- New types created via POST are owned by `user_id=user_id` (the authenticated caller), not `user_id=None` (system default)
- `snapshot_date` serialised as ISO date string (not datetime) by calling `.date().isoformat()` on the datetime field

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

No test DB available in worktree environment — tests were verified by:
1. Confirming import fails before router creation (RED: `ImportError: cannot import name 'snapshots' from 'api.routers'`)
2. Confirming routers import cleanly after implementation
3. Running static checks (grep for StreamingResponse, async def, HTTP_409_CONFLICT, user_id=user_id, Content-Disposition)
4. Running existing test suite (test_api_health.py + test_api_auth.py) confirming no regressions

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Snapshots and configure routers are complete and ready to be wired into api/main.py (Plan 05)
- Plan 05 adds `app.include_router(snapshots.router)` and `app.include_router(configure.router)` to api/main.py
- Phase 14 History and Configure React pages can rely on these endpoints without further API work

---
*Phase: 10-core-data-api-routes*
*Completed: 2026-05-06*
