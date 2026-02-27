# State

## Current Position

Phase: 5 of 5 (Cloud Run Deployment) — in progress
Plan: 02 of 04
Status: Executing Phase 5 plans
Last activity: 2026-02-27 — Completed 05-02-PLAN.md (GCP Infrastructure Setup)

Progress: [████████░░] ~85%  (phases 4-5; phases 1-3 pre-GSD complete)

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-17)

**Core value:** Seeing your net worth trend over time at a glance, without the overhead of transaction tracking.
**Current focus:** Phase 5 — Cloud Run Deployment

## Performance Metrics

**Velocity:**
- Total plans completed: 4
- Average duration: 733 seconds (~12 minutes)
- Total execution time: 2932 seconds

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 04 | 2 | 575s | 288s |
| 05 | 2 | 2357s | 1179s |

*Updated after each plan completion*

## Accumulated Context

### Decisions

- Phases 1-3: No REST API — Streamlit calls service functions directly (confirmed good)
- Phases 1-3: Firebase UID as users PK — avoids mapping table, direct FK from all tables
- Phases 1-3: Hardcoded TEST_USER_ID to unblock UI development — must be replaced in Phase 4
- Phase 4-01: Use raw postMessage instead of Streamlit JS helper for zero-build component
- Phase 4-01: Firebase Admin SDK hot-reload protection with if not firebase_admin._apps guard
- Phase 4-01: Browser local persistence for transparent re-auth on page reload
- Phase 4-01: Three-state protocol: initializing, authenticated (with token), unauthenticated
- Phase 4-02: Remove TEST_USER_ID completely — auth_service.get_or_create_user handles user provisioning
- Phase 4-02: Auth gate pattern: check session_state first, then widget, then verify token
- Phase 4-02: Session persistence via st.session_state.user_id across Streamlit reruns
- Phase 4-02: Logout flow uses session_state flag + st.rerun to trigger component signOut
- Phase 4-02: Migration script written now for Phase 5 execution
- [Phase 05]: Use shell parameter expansion ${PORT:-8501} for Cloud Run PORT compatibility
- [Phase 05]: Remove 'uv run' wrapper from CMD (dependencies installed via uv sync in image)
- [Phase 05]: Exclude *.json except pyproject.json to catch Firebase credentials
- [Phase 05]: Use Terraform for GCP infrastructure provisioning instead of manual Console (reproducible, version-controlled)
- [Phase 05]: Comment out IAM database user resource - automatic creation on first connection with cloudsql.client role
- [Phase 05]: Use postgres superuser with password for initial schema creation instead of IAM auth

### Pending Todos

None yet.

### Blockers/Concerns

- ~~Phase 4: `st.components.v1.html()` postMessage return value mechanism needs verification~~ — RESOLVED: postMessage protocol works correctly, auth flow verified end-to-end
- Phase 5: Cloud SQL Unix socket URL format and `gcloud run deploy` flag syntax need verification against current GCP docs before executing deploy commands
- Phase 5: Must execute migration script with real Firebase UID after first production login

## Session Continuity

Last session: 2026-02-27
Stopped at: Completed 05-02-PLAN.md (GCP Infrastructure Setup) — Cloud SQL with schema initialized, ready for data migration
Resume file: None
