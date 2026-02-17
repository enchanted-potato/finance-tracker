# Finance Tracker (Net Worth Tracker)

## What This Is

Personal net worth tracker for a single user. Track asset accounts and liabilities over time with graphs. No transaction tracking — just point-in-time balance snapshots and trends. Deployed on Google Cloud Run.

## Core Value

Seeing your net worth trend over time at a glance, without the overhead of transaction tracking.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ User can create and manage asset accounts (CRUD, balance updates) — Phase 1-3
- ✓ User can create and manage liabilities (CRUD, balance updates) — Phase 1-3
- ✓ App captures daily net worth snapshots when balances change — Phase 1-3
- ✓ User can view net worth trend chart on dashboard — Phase 1-3
- ✓ User can view asset allocation and liability breakdown charts — Phase 1-3
- ✓ User can view snapshot history table with per-account breakdown — Phase 1-3
- ✓ User can export snapshot history as CSV — Phase 1-3
- ✓ User can import historical snapshots via CSV — Phase 1-3
- ✓ User can configure custom account/liability types — Phase 1-3

### Active

<!-- Current scope. Building toward these. -->

- [ ] User can log in with Firebase Authentication (email/password)
- [ ] App is deployed and accessible on Cloud Run with Cloud SQL

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Transaction tracking — scope creep, not the product's purpose
- Multi-user support — single-user app by design (deployed privately)
- Mobile app — web-first
- Multi-currency conversion — currency field exists but conversion adds API complexity
- Real-time sync / webhooks — unnecessary for manual balance tracking

## Context

- Phases 1-3 complete: foundation, services, UI all working locally with a hardcoded test user (`TEST_USER_ID = "test-user"`)
- Firebase Admin SDK is declared as a dependency but not integrated
- App runs locally via `docker-compose up`; no production deployment yet
- Stack: Python 3.12, Streamlit, SQLModel, PostgreSQL, Plotly, Firebase Auth, uv
- Target: Google Cloud Run + Cloud SQL (free tier `db-f1-micro`)
- Codebase analysis in `.planning/codebase/`

## Constraints

- **Platform:** Google Cloud Run + Cloud SQL (free-tier) — keep resource usage minimal
- **Auth provider:** Firebase (already in dependencies, not negotiable) — email/password + Google sign-in
- **Stack:** No changes to Python/Streamlit/SQLModel — already built and working
- **Users:** Single user — no multi-tenancy needed

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| No REST API | Streamlit server-side Python can call services directly | ✓ Good |
| Firebase UID as users PK | Avoids mapping table, direct FK from all tables | ✓ Good |
| Daily snapshots with JSONB detail | Captures full breakdown at each point without reconstructing history | ✓ Good |
| SQLModel.metadata.create_all() for schema | Simple; no migration tool overhead for v1 | — Pending |
| Hardcoded test user for Phases 1-3 | Unblock UI development without auth complexity | ✓ Good |

---
*Last updated: 2026-02-17 after milestone v1.0 started*
