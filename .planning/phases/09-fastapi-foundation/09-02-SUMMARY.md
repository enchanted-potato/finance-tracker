---
phase: 09-fastapi-foundation
plan: "02"
subsystem: infra
tags: [fastapi, uvicorn, docker-compose, docker]

# Dependency graph
requires:
  - phase: 09-01
    provides: FastAPI app package (api/) with health endpoint, CORS, auth dependency
provides:
  - api service in docker-compose.yml on port 8000 with --host 0.0.0.0 --reload
affects: [10-core-data-api-routes, 11-react-scaffold-auth, 15-deployment]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - docker-compose api service shares build context with app service — no Dockerfile changes needed
    - uvicorn --host 0.0.0.0 required inside Docker (127.0.0.1 default is container-local only)

key-files:
  created: []
  modified:
    - docker-compose.yml

key-decisions:
  - "api service shares same Dockerfile/build context as app service — Dockerfile unchanged in Phase 9"
  - "uvicorn command uses --host 0.0.0.0 to bind on all interfaces, making port 8000 reachable from host"

patterns-established:
  - "Pattern: docker-compose api service mounts .:/app and /app/.venv — hot reload works without rebuild"

requirements-completed: [API-01, API-02]

# Metrics
duration: 2min
completed: 2026-04-29
---

# Phase 9 Plan 02: docker-compose api service added — awaiting human smoke test

**docker-compose.yml updated with FastAPI api service on port 8000 using --host 0.0.0.0; human smoke test pending before phase 9 closes**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-04-29T18:55:00Z
- **Completed:** 2026-04-29T18:58:53Z (checkpoint reached — human verify pending)
- **Tasks:** 1 of 2 complete (Task 2 is checkpoint:human-verify)
- **Files modified:** 1

## Accomplishments

- Added `api` service to `docker-compose.yml` — `docker-compose up` now starts db, app (Streamlit 8501), and api (FastAPI 8000) together
- Service uses the same build context and volume mounts as the existing `app` service — no Dockerfile changes required
- `uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload` command ensures port is reachable from host and hot reload works

## Task Commits

1. **Task 1: Add api service to docker-compose.yml** - `a2d7ea5` (feat)

**Plan metadata:** (see final commit below)

## Files Created/Modified

- `docker-compose.yml` — Added `api` service with port 8000, volumes, environment variables (DATABASE_URL, FIREBASE_CREDENTIALS_PATH, DEBUG, DEV_USER_ID, ALLOWED_FIREBASE_UID), depends_on db, and uvicorn command

## Decisions Made

- None — followed plan as specified. The api service definition exactly matches the specification in 09-02-PLAN.md and the docker-compose example in 09-RESEARCH.md.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

Human smoke test required before this plan is complete. See checkpoint section below.

### Smoke Test Steps

Run from the project root:

```bash
docker-compose up --build
```

Wait for both "Application startup complete." (FastAPI) and Streamlit to be ready, then run:

```bash
# 1. Health check — expect: 200
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health

# 2. Health body — expect: {"status":"ok"}
curl -s http://localhost:8000/api/health

# 3. CORS allowed origin — expect: access-control-allow-origin: http://localhost:5173
curl -s -I -X OPTIONS http://localhost:8000/api/health \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: GET"

# 4. CORS rejected origin — expect: NO access-control-allow-origin header
curl -s -I -X OPTIONS http://localhost:8000/api/health \
  -H "Origin: http://evil.example.com" \
  -H "Access-Control-Request-Method: GET"

# 5. Streamlit regression check — visit http://localhost:8501 in browser
```

## Next Phase Readiness

- Once smoke test passes: docker-compose environment is proven correct for Phase 10 feature route development
- Phase 10 can add domain routes targeting the running api service on port 8000

---
*Phase: 09-fastapi-foundation*
*Completed: 2026-04-29*
