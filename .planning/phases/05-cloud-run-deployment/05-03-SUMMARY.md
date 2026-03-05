---
phase: 05-cloud-run-deployment
plan: 03
subsystem: infra
tags: [cloud-run, docker, gcr, firebase, cloud-sql, unix-socket, secret-manager]

# Dependency graph
requires:
  - phase: 05-cloud-run-deployment/05-01
    provides: Dockerfile with PORT support, .dockerignore
  - phase: 05-cloud-run-deployment/05-02
    provides: Cloud SQL schema initialized, Secret Manager firebase-creds secret
  - phase: 05-cloud-run-deployment/05-04
    provides: Simplified schema (no users table, no FK constraints)
provides:
  - Running Cloud Run service at https://finance-tracker-rntookejza-uc.a.run.app
  - Docker image in GCR: gcr.io/wealth-tracker-1eb4d/finance-tracker:latest
  - Cloud SQL connection via Unix socket in production
  - Firebase credentials mounted from Secret Manager
affects: [production, deployment]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Build Docker images for linux/amd64 explicitly on Apple Silicon (arm64)"
    - "uv venv PATH: add /app/.venv/bin to PATH so venv binaries are discoverable"
    - "Cloud Run deploy with --add-cloudsql-instances for Unix socket attachment"
    - "Secret Manager file mount via --set-secrets=/path=secret-name:version"

key-files:
  created: []
  modified:
    - Dockerfile

key-decisions:
  - "Add ENV PATH=/app/.venv/bin:$PATH to Dockerfile so streamlit binary is found in uv venv"
  - "Must build with --platform linux/amd64 when developing on Apple Silicon Mac"
  - "Cloud Run service URL: https://finance-tracker-rntookejza-uc.a.run.app"
  - "DATABASE_URL uses IAM auth format: postgresql+psycopg2://SA_EMAIL:@/DB?host=/cloudsql/INSTANCE"

patterns-established:
  - "Platform: Always specify --platform linux/amd64 for Cloud Run builds on Apple Silicon"
  - "uv venv PATH: ENV PATH=/app/.venv/bin:$PATH required in Dockerfile when using uv sync"

requirements-completed: [DEPLOY-03, DEPLOY-04]

# Metrics
duration: 7min
completed: 2026-02-28
---

# Phase 5 Plan 03: Cloud Run Deployment Summary

**Streamlit app deployed to Cloud Run at https://finance-tracker-rntookejza-uc.a.run.app with Cloud SQL via Unix socket and Firebase credentials from Secret Manager**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-28T06:53:59Z
- **Completed:** 2026-02-28T07:00:36Z
- **Tasks:** 2 of 3 complete (Task 3 is human verification checkpoint)
- **Files modified:** 1 (Dockerfile)

## Accomplishments

- Docker image built for linux/amd64 and pushed to GCR (sha256:5185bce0...)
- Cloud Run service deployed successfully, serving 100% traffic on revision 00003-lkm
- Service returns HTTP 200, Streamlit listening on port 8080 (confirmed in logs)
- Cloud SQL attached via Unix socket: `wealth-tracker-1eb4d:us-central1:finance-tracker-db`
- Firebase credentials mounted from Secret Manager at `/secrets/firebase.json`
- Max instances set to 1 for free tier compliance

## Task Commits

Each task was committed atomically:

1. **Task 1: Build and push Docker image to GCR** - `8f397ba` (chore)
2. **Task 2: Deploy to Cloud Run with configuration** - `c5c7990` (feat)
3. **Task 3: Verify Cloud Run deployment** - Awaiting human verification checkpoint

## Files Created/Modified

- `/Users/kristiakarakatsani/Repos/finance-tracker/Dockerfile` - Added `ENV PATH="/app/.venv/bin:$PATH"` to make uv virtualenv binaries discoverable

## Decisions Made

- Build with `--platform linux/amd64` on Apple Silicon: Cloud Run requires amd64, arm64 images cause "exec format error"
- Add `ENV PATH="/app/.venv/bin:$PATH"` in Dockerfile: uv installs into `.venv` directory, not system PATH

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed arm64 image architecture for Cloud Run (amd64 required)**
- **Found during:** Task 2 (Deploy to Cloud Run)
- **Issue:** Initial docker build on Apple Silicon produced arm64 image. Cloud Run runs on amd64. Container failed with "failed to load /bin/sh: exec format error"
- **Fix:** Rebuilt image with `docker build --platform linux/amd64`
- **Files modified:** None (build flag change only)
- **Verification:** Deployment succeeded, container started, Streamlit logs confirmed on port 8080
- **Committed in:** c5c7990

**2. [Rule 1 - Bug] Fixed streamlit not found in PATH when using uv venv**
- **Found during:** Task 2 (Deploy to Cloud Run) - second deploy attempt
- **Issue:** uv installs packages to `.venv/bin/` which is not in PATH. Cloud Run logs showed "/bin/sh: 1: streamlit: not found"
- **Fix:** Added `ENV PATH="/app/.venv/bin:$PATH"` to Dockerfile
- **Files modified:** Dockerfile
- **Verification:** Third deployment (revision 00003-lkm) started successfully. Logs show "You can now view your Streamlit app in your browser."
- **Committed in:** c5c7990

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes were essential for Cloud Run compatibility. No scope creep.

## Issues Encountered

- arm64 vs amd64 architecture mismatch (Apple Silicon Mac building for Cloud Run) - auto-fixed
- uv venv not in PATH in Docker container - auto-fixed with one-line Dockerfile change

## Cloud Run Deployment Details

| Parameter | Value |
|-----------|-------|
| Service URL | https://finance-tracker-rntookejza-uc.a.run.app |
| Image | gcr.io/wealth-tracker-1eb4d/finance-tracker:latest |
| Region | us-central1 |
| Revision | finance-tracker-00003-lkm |
| Max Instances | 1 (free tier) |
| Memory | 512Mi |
| CPU | 1 |
| Timeout | 300s |
| Cloud SQL | wealth-tracker-1eb4d:us-central1:finance-tracker-db |
| Firebase Secret | finance-tracker-firebase-creds:latest |

## Next Phase Readiness

- Task 3 (human verification) required before plan is fully complete
- User must visit https://finance-tracker-rntookejza-uc.a.run.app and verify:
  - Login screen displays
  - Google Sign-In works
  - Dashboard loads after authentication
  - Database CRUD operations succeed
  - Session persists across navigation
  - Logout flow works

---
*Phase: 05-cloud-run-deployment*
*Completed: 2026-02-28*
