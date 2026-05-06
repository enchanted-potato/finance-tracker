---
phase: 10-core-data-api-routes
plan: "01"
subsystem: api
tags: [fastapi, pydantic, sqlmodel, accounts, float-schemas, auto-snapshot]

# Dependency graph
requires:
  - phase: 09-fastapi-foundation
    provides: api/main.py, api/dependencies.py, get_current_user, health router pattern
  - phase: app-services
    provides: account_service.list_account_types, list_non_pension_entries, upsert_account_entry, delete_account_entry; type_service.account_type_usage_count; snapshot_service.capture_snapshot
provides:
  - api/schemas/accounts.py — AccountTypeResponse, AccountEntryRequest, AccountEntryResponse, EntryItemResponse, HistoryDayResponse (all float, no user_id)
  - api/routers/accounts.py — GET /api/accounts/types, POST /api/accounts/entries, DELETE /api/accounts/entries/{id}, GET /api/accounts/history
  - Thin-router + Pydantic-float-schema + capture_snapshot pattern established for liabilities/pension/configure/dashboard routers to mirror
affects: [10-02-liabilities, 10-03-pension, 10-04-snapshots-configure, 10-05-wiring, 12-data-pages]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Thin router: service call -> Pydantic schema construction -> return; no business logic in handlers"
    - "Decimal(str(body.balance)) for float-to-Decimal precision-safe conversion"
    - "capture_snapshot imported at module level (from app.services.snapshot_service import capture_snapshot) enabling mocker.patch('api.routers.accounts.capture_snapshot')"
    - "date-grouping with defaultdict(list) + defaultdict(float) + sorted(keys, reverse=True)"
    - "client_with_db fixture: app.dependency_overrides[get_session] = rollback-scoped session"

key-files:
  created:
    - api/schemas/accounts.py
    - api/routers/accounts.py
    - tests/test_api_accounts.py
  modified: []

key-decisions:
  - "Router not wired into api/main.py in this plan — Plan 05 handles wiring to avoid file conflicts in parallel wave"
  - "capture_snapshot imported directly (not via module) so mocker.patch works at api.routers.accounts.capture_snapshot"
  - "Tests use client_with_db fixture that overrides get_session with rollback-scoped db_session from conftest"
  - "balance field in EntryItemResponse is float(e.balance * e.exchange_rate) — GBP-equivalent value per entry"

patterns-established:
  - "Thin router pattern: router imports service module, calls service functions, maps results to BaseModel, returns"
  - "Float schema pattern: all monetary Pydantic fields are float; convert from Decimal via float(entry.balance)"
  - "Auto-snapshot pattern: every POST /entries calls capture_snapshot(session, user_id, snapshot_date=entry.entry_date)"
  - "No user_id in any response schema — confirmed by grep returning 0 hits"

requirements-completed: [API-05]

# Metrics
duration: 4min
completed: 2026-05-06
---

# Phase 10 Plan 01: Accounts Router Summary

**FastAPI accounts router with float schemas, in-use type flag, auto-snapshot on balance write, and date-grouped history — thin-router pattern established for all subsequent routers**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-06T12:53:23Z
- **Completed:** 2026-05-06T12:56:44Z
- **Tasks:** 2 (TDD RED + GREEN)
- **Files modified:** 3

## Accomplishments

- Created `api/schemas/accounts.py` with 5 Pydantic BaseModel classes (float-typed, no user_id exposure)
- Created `api/routers/accounts.py` with 4 endpoints under `/api/accounts` prefix; all require `Depends(get_current_user)`
- All 10 tests in `tests/test_api_accounts.py` pass; no regressions in previously-green tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Write failing tests for accounts router (RED)** - `da7f63f` (test)
2. **Task 2: Implement api/schemas/accounts.py and api/routers/accounts.py (GREEN)** - `2c7d4d6` (feat)

_Note: TDD plan — RED commit then GREEN commit_

## Files Created/Modified

- `tests/test_api_accounts.py` — 10 integration tests: auth gate, types in-use flag, no user_id in responses, entry create/persist, auto-snapshot trigger, decimal precision, user_id enforcement, delete 204, history shape (grouped by date newest first), float-not-string
- `api/schemas/accounts.py` — AccountTypeResponse (id, name, is_pension, in_use), AccountEntryRequest (account_type_id, entry_date, balance, currency, exchange_rate), AccountEntryResponse (id, account_type_id, entry_date, balance, currency), EntryItemResponse (entry_id, type_id, type_name, balance), HistoryDayResponse (date, total, entries)
- `api/routers/accounts.py` — GET /types (in_use via account_type_usage_count), POST /entries (auto-snapshot at line 60), DELETE /entries/{entry_id} (ValueError -> 404), GET /history (date-grouped defaultdict, newest first)

## Decisions Made

- Router not wired into `api/main.py` in this plan (Plan 05 handles wiring to avoid file conflicts with parallel wave agents)
- `capture_snapshot` imported directly at module level — enables `mocker.patch("api.routers.accounts.capture_snapshot")` in tests
- `client_with_db` fixture overrides `get_session` dependency with conftest's rollback-scoped `db_session` — ensures test isolation
- `balance` in `EntryItemResponse` represents GBP-equivalent value: `float(e.balance * e.exchange_rate)`

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Test database `finance_tracker_test` did not exist on local machine. Created it with `psql -c "CREATE DATABASE finance_tracker_test"` using `finance/finance` credentials (docker-compose DB user). Tests then ran successfully.
- 9 pre-existing test failures found in `test_account_service.py`, `test_type_service.py`, `test_snapshot_service.py`, `test_dashboard_helpers.py` — all confirmed pre-existing at base commit (759b0e8), not caused by this plan. Logged to deferred-items.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Thin-router + float-schema + auto-snapshot pattern established and tested
- `api/routers/accounts.py` ready to be wired into `api/main.py` (Plan 05)
- Plan 02 (liabilities router) and Plan 03 (pension router) can mirror this pattern directly
- No blockers for subsequent wave-1 parallel plans

---
*Phase: 10-core-data-api-routes*
*Completed: 2026-05-06*
