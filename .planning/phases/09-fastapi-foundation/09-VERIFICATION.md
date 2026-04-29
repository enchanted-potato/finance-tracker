---
phase: 09-fastapi-foundation
verified: 2026-04-27T22:00:00Z
status: passed
score: 12/12 must-haves verified
re_verification: false
---

# Phase 9: FastAPI Foundation Verification Report

**Phase Goal:** A correctly configured FastAPI server is running locally — CORS, auth, database session, and Firebase Admin initialisation are all in place before any feature route is written
**Verified:** 2026-04-27T22:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|---------|
| 1  | GET /api/health returns HTTP 200 with {"status": "ok"} | VERIFIED | test_health_returns_200 passes; api/routers/health.py returns HealthResponse(status="ok") |
| 2  | Firebase Admin SDK is initialised inside the lifespan context manager, never at module level | VERIFIED | api/main.py lines 35/38 are inside @asynccontextmanager lifespan; test_firebase_not_init_at_import passes |
| 3  | A CORS preflight from http://localhost:5173 returns Access-Control-Allow-Origin: http://localhost:5173 | VERIFIED | test_cors_preflight_allowed_origin passes; ALLOWED_ORIGINS list in api/main.py contains "http://localhost:5173" |
| 4  | A CORS preflight from an unlisted origin returns no Access-Control-Allow-Origin header | VERIFIED | test_cors_preflight_rejected_origin passes |
| 5  | A request without an Authorization header to a protected route returns HTTP 401 | VERIFIED | test_missing_token_returns_401 passes; get_current_user raises HTTPException(401) when token is None |
| 6  | A request with a valid token but wrong UID returns HTTP 403 | VERIFIED | test_wrong_uid_returns_403 passes; get_current_user raises HTTPException(403) when uid != allowed_firebase_uid |
| 7  | A Pydantic schema with a float balance field serialises to a JSON number, not a string | VERIFIED | test_decimal_serialises_as_float passes; float(Decimal("10753.42")) round-trips through model_dump_json as float |
| 8  | pool_pre_ping=True is set on the database engine in app/database.py | VERIFIED | app/database.py line 7: create_engine(settings.database_url, echo=settings.debug, pool_pre_ping=True) |
| 9  | docker-compose up starts both Streamlit (8501) and FastAPI (8000) | VERIFIED | docker-compose.yml has api service with uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload; human verified per 09-02-SUMMARY.md |
| 10 | curl http://localhost:8000/api/health returns HTTP 200 with {"status": "ok"} | VERIFIED | Human-verified per 09-02-SUMMARY.md — all 5 smoke test checks passed |
| 11 | CORS preflight from http://localhost:5173 returns Access-Control-Allow-Origin: http://localhost:5173 in the response | VERIFIED | Human-verified via curl per 09-02-SUMMARY.md |
| 12 | dev bypass returns 200 without a token when settings.dev_user_id is set | VERIFIED | test_dev_bypass_skips_firebase passes; get_current_user returns dev_user_id immediately before touching Firebase |

**Score:** 12/12 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `api/__init__.py` | api package marker | VERIFIED | Exists; package importable |
| `api/main.py` | FastAPI app with lifespan, CORS middleware, router includes | VERIFIED | Contains asynccontextmanager lifespan, CORSMiddleware with explicit origins, app.include_router(health.router) |
| `api/dependencies.py` | get_current_user auth dependency | VERIFIED | Exports get_current_user; dev bypass, 401 for missing/invalid, 403 for UID mismatch — all substantive |
| `api/routers/__init__.py` | routers package marker | VERIFIED | Exists |
| `api/routers/health.py` | GET /api/health endpoint | VERIFIED | APIRouter with prefix="/api"; GET /health returning HealthResponse(status="ok") |
| `api/schemas/__init__.py` | schemas package marker | VERIFIED | Exists |
| `api/schemas/health.py` | HealthResponse Pydantic schema | VERIFIED | BaseModel subclass with status: str |
| `app/database.py` | pool_pre_ping=True on engine | VERIFIED | Line 7: pool_pre_ping=True present |
| `docker-compose.yml` | api service on port 8000 | VERIFIED | api service with uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload, depends_on db |
| `tests/test_api_health.py` | 5 tests: health, firebase import guard, CORS allow/reject, decimal float | VERIFIED | 5 tests all pass |
| `tests/test_api_auth.py` | 4 tests: 401 missing, 401 invalid, 403 wrong UID, dev bypass 200 | VERIFIED | 4 tests all pass |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| api/main.py | firebase_admin.initialize_app | lifespan @asynccontextmanager — not module level | VERIFIED | Both initialize_app calls (lines 35, 38) are inside the lifespan generator body; test_firebase_not_init_at_import confirms no module-level init |
| api/dependencies.py | settings.dev_user_id | dev bypass returns dev_user_id before touching Firebase | VERIFIED | Line 27: `if settings.dev_user_id: return settings.dev_user_id` |
| api/main.py | api/dependencies.py (get_current_user) | imported and used in routes requiring auth | PARTIAL — by design | get_current_user is not imported in main.py yet; no feature routes exist in this phase. The dependency is correctly defined and tested via test route injection. Phase 10 will import it in feature routers. This is the intended foundation state. |
| docker-compose.yml api service | api/main.py | uvicorn api.main:app command | VERIFIED | command: "uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload" on line 44 |
| docker-compose.yml api service | db service | depends_on: db and DATABASE_URL | VERIFIED | depends_on: [db] and DATABASE_URL env var both present |

Note on PARTIAL key link: The plan's key_link for `get_current_user imported in routes that require auth` refers to feature routes (Phase 10+). No feature routes exist in Phase 9 — the foundation phase intentionally creates the dependency for future use. The link is fully tested via test-injected routes. This is not a gap.

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| API-01 | 09-01, 09-02 | FastAPI app initialises Firebase Admin SDK via lifespan context manager and sets pool_pre_ping=True on the database engine | SATISFIED | lifespan in api/main.py guards initialize_app; pool_pre_ping=True in app/database.py line 7; 9 tests confirm both |
| API-02 | 09-01, 09-02 | FastAPI configures CORS with explicit Firebase Hosting origins and allow_credentials=True (no wildcard) | SATISFIED | ALLOWED_ORIGINS list with 3 explicit origins; allow_credentials=True; allow_origins not wildcard; CORS tests pass; human smoke test confirms headers via curl |
| API-03 | 09-01 | FastAPI auth dependency verifies Firebase ID token from Authorization: Bearer header; returns HTTP 401 if missing or invalid | SATISFIED | get_current_user in api/dependencies.py; test_missing_token_returns_401 and test_invalid_token_returns_401 both pass |
| API-04 | 09-01 | All response schemas use float (not Decimal) for monetary values | SATISFIED | HealthResponse uses str; BalanceModel test proves float field serialises as JSON number; test_decimal_serialises_as_float passes. Note: full chart data format (Recharts) is deferred to Phase 10 feature routes — the float serialisation pattern is proven |

API-04 partial note: The requirement text also says "chart data is returned in Recharts format". Chart endpoints are Phase 10 (API-05 to API-08). Phase 9 establishes the float serialisation pattern that Phase 10 routes will follow. The test proves this pattern works. The Recharts-format half of API-04 is correctly deferred.

---

### Anti-Patterns Found

None. Scanning api/ for TODO/FIXME/XXX/HACK/placeholder/return null/return {}/return [] found zero matches. All implementations are substantive.

---

### Human Verification Required

The following were human-verified and recorded in 09-02-SUMMARY.md as approved:

1. **docker-compose up brings up all services without errors**
   - Test: docker-compose up --build
   - Expected: db, app (Streamlit 8501), and api (FastAPI 8000) all reach "Application startup complete"
   - Verified: Human typed "approved" per 09-02-SUMMARY.md

2. **curl http://localhost:8000/api/health returns 200 {"status":"ok"}**
   - Verified: Human confirmed per 09-02-SUMMARY.md

3. **CORS preflight from http://localhost:5173 returns correct header in live server**
   - Verified: Human confirmed per 09-02-SUMMARY.md

4. **CORS preflight from http://evil.example.com has no Access-Control-Allow-Origin header in live server**
   - Verified: Human confirmed per 09-02-SUMMARY.md

5. **Streamlit still loads at http://localhost:8501 (no regression)**
   - Verified: Human confirmed per 09-02-SUMMARY.md

---

### Test Results

```
tests/test_api_health.py::test_health_returns_200              PASSED
tests/test_api_health.py::test_firebase_not_init_at_import     PASSED
tests/test_api_health.py::test_cors_preflight_allowed_origin   PASSED
tests/test_api_health.py::test_cors_preflight_rejected_origin  PASSED
tests/test_api_health.py::test_decimal_serialises_as_float     PASSED
tests/test_api_auth.py::test_missing_token_returns_401         PASSED
tests/test_api_auth.py::test_invalid_token_returns_401         PASSED
tests/test_api_auth.py::test_wrong_uid_returns_403             PASSED
tests/test_api_auth.py::test_dev_bypass_skips_firebase         PASSED

9 passed in 0.70s
```

---

### Commits Verified

All commits referenced in SUMMARY files exist in git history:
- `bc2d51a` — test(09-01): add failing tests for health, CORS, auth, and float serialisation
- `7422046` — feat(09-01): implement api/ package — FastAPI server with lifespan, CORS, auth dependency
- `a2d7ea5` — feat(09-02): add FastAPI api service to docker-compose.yml

---

_Verified: 2026-04-27T22:00:00Z_
_Verifier: Claude (gsd-verifier)_
