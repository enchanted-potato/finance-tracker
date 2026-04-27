---
phase: 09-fastapi-foundation
plan: "01"
subsystem: api
tags: [fastapi, firebase-admin, cors, pydantic, sqlalchemy, uvicorn, httpx]

# Dependency graph
requires: []
provides:
  - FastAPI app with lifespan-managed Firebase Admin SDK init
  - CORSMiddleware configured for React dev origin and Firebase Hosting origins
  - get_current_user auth dependency with dev bypass, 401/403 handling
  - GET /api/health public endpoint returning {"status": "ok"}
  - HealthResponse Pydantic schema (float-safe BaseModel)
  - pool_pre_ping=True on database engine
  - Full test suite for health, CORS, auth (9 tests)
affects: [10-core-data-api-routes, 11-react-scaffold-auth, 15-deployment]

# Tech tracking
tech-stack:
  added: [fastapi[standard], uvicorn, httpx]
  patterns:
    - Lifespan context manager for Firebase Admin SDK init (not module-level)
    - CORSMiddleware with explicit origin list (allow_credentials=True requires no wildcard)
    - HTTPBearer(auto_error=False) + dev bypass pattern for auth dependency
    - Pydantic BaseModel with float fields (never Decimal) for API response schemas
    - firebase_admin.get_app() try/except for checking initialisation state

key-files:
  created:
    - api/__init__.py
    - api/main.py
    - api/dependencies.py
    - api/routers/__init__.py
    - api/routers/health.py
    - api/schemas/__init__.py
    - api/schemas/health.py
    - tests/test_api_health.py
    - tests/test_api_auth.py
  modified:
    - app/database.py
    - pyproject.toml
    - uv.lock

key-decisions:
  - "firebase_admin has no public .apps attribute — use get_app() with try/except ValueError to check init state"
  - "lifespan skips Firebase init when settings.dev_user_id is truthy — keeps tests fast without credentials"
  - "pool_pre_ping=True added to shared app/database.py engine — benefits both Streamlit and FastAPI"

patterns-established:
  - "Pattern: Lifespan async context manager for one-time SDK init — do not init at module level"
  - "Pattern: HTTPBearer(auto_error=False) + dev_user_id bypass — allows local dev without Firebase"
  - "Pattern: Pydantic BaseModel with float fields — avoids Pydantic v2 Decimal-as-string serialisation"
  - "Pattern: CORSMiddleware with explicit origin list — required with allow_credentials=True"

requirements-completed: [API-01, API-02, API-03, API-04]

# Metrics
duration: 3min
completed: 2026-04-27
---

# Phase 9 Plan 01: FastAPI Foundation Summary

**FastAPI server scaffolded with lifespan Firebase init, explicit CORS for localhost:5173 and Firebase Hosting, Bearer-token auth dependency with dev bypass, and GET /api/health endpoint — all 9 tests green**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-27T21:21:57Z
- **Completed:** 2026-04-27T21:24:15Z
- **Tasks:** 2 (TDD: RED + GREEN)
- **Files modified:** 12

## Accomplishments

- Installed `fastapi[standard]` (FastAPI + uvicorn + httpx) and scaffolded the full `api/` package
- Implemented `api/main.py` with `@asynccontextmanager` lifespan, CORS middleware (explicit origins, no wildcard), and health router; Firebase Admin SDK init is guarded behind `if not settings.dev_user_id` to keep tests fast
- Implemented `api/dependencies.py` — `get_current_user` with dev bypass (returns `settings.dev_user_id`), 401 for missing/invalid token, 403 for UID mismatch
- Added `pool_pre_ping=True` to `app/database.py` engine — shared improvement for both Streamlit and FastAPI

## Task Commits

Each task was committed atomically:

1. **Task 1: Write failing tests (RED) and install fastapi[standard]** - `bc2d51a` (test)
2. **Task 2: Implement api/ package (GREEN)** - `7422046` (feat)

**Plan metadata:** (see final commit below)

_Note: TDD tasks — test commit (RED) then implementation commit (GREEN)_

## Files Created/Modified

- `api/__init__.py` — Package marker
- `api/main.py` — FastAPI app, lifespan, CORSMiddleware, router includes
- `api/dependencies.py` — get_current_user auth dependency
- `api/routers/__init__.py` — Package marker
- `api/routers/health.py` — GET /api/health endpoint
- `api/schemas/__init__.py` — Package marker
- `api/schemas/health.py` — HealthResponse Pydantic schema
- `app/database.py` — Added pool_pre_ping=True to create_engine()
- `tests/test_api_health.py` — 5 tests: health 200, firebase import guard, CORS allow/reject, decimal float
- `tests/test_api_auth.py` — 4 tests: 401 missing, 401 invalid, 403 wrong UID, dev bypass 200
- `pyproject.toml` — Added fastapi[standard]
- `uv.lock` — Updated lockfile

## Decisions Made

- Used `firebase_admin.get_app()` with `try/except ValueError` rather than `firebase_admin._apps` private dict to check initialisation state — the public `apps` attribute does not exist in the installed version
- Lifespan guards Firebase init with `if not settings.dev_user_id:` — when dev bypass is active, Firebase is never called, keeping all tests fast and credential-free
- `pool_pre_ping=True` added to shared `app/database.py` engine (not a separate API engine) — Streamlit benefits too

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] firebase_admin.apps attribute does not exist**
- **Found during:** Task 2 (GREEN — running tests)
- **Issue:** `test_firebase_not_init_at_import` used `firebase_admin.apps` but the installed `firebase-admin` SDK exposes no public `apps` attribute (only private `_apps` dict)
- **Fix:** Replaced with helper function using `firebase_admin.get_app()` wrapped in `try/except ValueError` — the documented safe approach from RESEARCH.md
- **Files modified:** tests/test_api_health.py
- **Verification:** test_firebase_not_init_at_import passes (9/9 green)
- **Committed in:** `7422046` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Single fix to test — matched the RESEARCH.md recommendation to use `get_app()` not `_apps`. No scope creep.

## Issues Encountered

- Pre-existing service tests (`test_account_service.py` etc.) fail with `OperationalError` — no local PostgreSQL running. This is environment-only, not caused by changes in this plan. API tests (`test_api_health.py`, `test_api_auth.py`) all pass: 9/9.

## User Setup Required

None - no external service configuration required beyond what is already in `.env`.

Note: `docker-compose.yml` will need an `api` service added (per CONTEXT.md decision), but that is deferred to a later task in Phase 9.

## Next Phase Readiness

- FastAPI server infrastructure is fully established: CORS, auth dependency, Firebase lifespan, pool_pre_ping
- Phase 10 can add domain routes (`api/routers/accounts.py` etc.) using `Depends(get_current_user)` and `Depends(get_session)` directly
- Phase 11 React scaffold can target `http://localhost:5173` — CORS is already configured for that origin

---
*Phase: 09-fastapi-foundation*
*Completed: 2026-04-27*
