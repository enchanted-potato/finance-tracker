# Phase 9: FastAPI Foundation - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Stand up a correctly configured FastAPI server locally — CORS, auth dependency, Firebase Admin SDK initialisation via lifespan, pool_pre_ping, and a health endpoint. No feature routes. The API contract infrastructure is proven correct before Phase 10 adds any domain endpoints.

</domain>

<decisions>
## Implementation Decisions

### Directory structure
- Top-level `api/` directory (not nested under `app/`)
- Layout: `api/main.py`, `api/dependencies.py`, `api/routers/`, `api/schemas/`
- `api/schemas/` is flat — one file per domain: `health.py` now, `accounts.py`, `liabilities.py`, `snapshots.py` in Phase 10
- API tests go in the existing `tests/` directory alongside service tests (`tests/test_api_health.py`, `tests/test_api_auth.py`)

### Streamlit coexistence
- Add an `api` service to `docker-compose.yml` on port 8000; Streamlit service is unchanged
- Both services share the same build context; both run with `docker-compose up`
- Dockerfile is NOT touched in Phase 9 — deferred to Phase 15 when Streamlit is replaced on Cloud Run

### Database engine
- Add `pool_pre_ping=True` to the existing `create_engine()` call in `app/database.py` (shared change — Streamlit benefits too)
- FastAPI route handlers use `Depends(get_session)` from `app/database.py` directly — no wrapper in `api/dependencies.py`

### Auth dependency
- `GET /api/health` is public — no auth required (used by Cloud Run health checks)
- Auth dependency (`get_current_user`) verifies the Firebase ID token from `Authorization: Bearer` header
- After token verification, UID is checked against `settings.allowed_firebase_uid` — returns HTTP 403 if a different Firebase account presents a valid token
- Dev bypass: if `settings.dev_user_id` is set (non-empty), the dependency returns it immediately without calling Firebase — skips token verification entirely
- Returns HTTP 401 if token is missing or invalid; HTTP 403 if UID doesn't match

### Claude's Discretion
- Firebase Admin SDK initialisation details within the lifespan context manager
- Exact CORS middleware configuration (allowed headers, methods)
- Health response schema shape (beyond returning HTTP 200)
- Test fixtures for API tests (how to mock Firebase in tests)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/database.py` — `get_session()` generator used directly as `Depends(get_session)` in FastAPI routes; `engine` will have `pool_pre_ping=True` added
- `app/config.py` — `Settings` already has `dev_user_id`, `allowed_firebase_uid`, and `firebase_credentials_path` fields — ready to use in the auth dependency without any config changes
- `app/services/` — Pure functions accepting `session` parameter; FastAPI route handlers call these identically to how Streamlit pages do

### Established Patterns
- Import order: stdlib → third-party → local (`from app.xxx import ...`)
- Service functions are keyword-only and stateless — no changes needed to wire into FastAPI
- All business logic stays in `app/services/` — FastAPI route handlers are thin translation layers only

### Integration Points
- `app/database.py`: Add `pool_pre_ping=True` to `create_engine()` — one-line change
- `docker-compose.yml`: Add `api` service pointing to `uvicorn api.main:app --reload --port 8000`
- `tests/conftest.py`: API tests will add fixtures here (or create test-specific conftest)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard FastAPI patterns for lifespan, CORS, and auth dependencies.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 09-fastapi-foundation*
*Context gathered: 2026-04-08*
