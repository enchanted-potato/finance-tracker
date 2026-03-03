# State

## Current Position

Phase: 5 of 5 (Cloud Run Deployment) — in progress
Plan: 03 of 04 — CHECKPOINT (awaiting human verification)
Status: Executing Phase 5 plans
Last activity: 2026-02-28 — Completed 05-03 Tasks 1+2; awaiting checkpoint verification at Task 3

Progress: [████████░░] ~85%  (phases 4-5; phases 1-3 pre-GSD complete)

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-17)

**Core value:** Seeing your net worth trend over time at a glance, without the overhead of transaction tracking.
**Current focus:** Phase 5 — Cloud Run Deployment

## Performance Metrics

**Velocity:**
- Total plans completed: 5
- Average duration: 1630 seconds (~27 minutes)
- Total execution time: 8151 seconds

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 04 | 2 | 575s | 288s |
| 05 | 3 | 7576s | 2525s |

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
- [Phase 05]: Remove users table entirely — single-user app, use Firebase UID directly in accounts/liabilities/snapshots
- [Phase 05]: No migration needed — database is empty, fresh start on Cloud SQL
- [Phase 05]: Block 'test-user' as valid user_id in app validation
- [Phase 05]: Store Firebase UID directly as string in user_id fields with no FK constraints
- [Phase 05-03]: Build Docker images with --platform linux/amd64 on Apple Silicon — Cloud Run requires amd64
- [Phase 05-03]: Add ENV PATH="/app/.venv/bin:$PATH" to Dockerfile — uv venv not in PATH by default
- [Phase 05-03]: Cloud Run service URL: https://finance-tracker-rntookejza-uc.a.run.app

### Pending Todos

None yet.

### Blockers/Concerns

- ~~Phase 4: `st.components.v1.html()` postMessage return value mechanism needs verification~~ — RESOLVED: postMessage protocol works correctly, auth flow verified end-to-end
- ~~Phase 5: Cloud SQL Unix socket URL format and `gcloud run deploy` flag syntax need verification against current GCP docs before executing deploy commands~~ — RESOLVED: Deploy succeeded with documented flags
- ~~Phase 5: Must execute migration script with real Firebase UID after first production login~~ — RESOLVED: No data exists, no migration needed

## Quick Tasks Completed

| # | Task | Commits | Date |
|---|------|---------|------|
| 1 | Add pension as separate category with dedicated page and dashboard chart | 4194ef8, 7ed7004 | 2026-03-01 |
| 2 | Add liabilities CSV upload to history page | 449efe2, 5106830 | 2026-03-02 |
| 3 | Fix NULL values for missing history data (nullable snapshot fields, gap charts, dash display) | 6c98f39, 96b9a07, 096b69b | 2026-03-03 |

## Session Continuity

Last session: 2026-03-03
Stopped at: Completed quick-3 (fix null values for missing history data)
Resume file: .planning/phases/05-cloud-run-deployment/05-CONTEXT.md
