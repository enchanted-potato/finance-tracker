# Finance Tracker (Net Worth Tracker)

## What This Is

Personal net worth tracker for a single user. Track asset accounts and liabilities over time with graphs. No transaction tracking — just point-in-time balance snapshots and trends. Live on Google Cloud Run with Firebase Google Sign-In.

## Core Value

Seeing your net worth trend over time at a glance, without the overhead of transaction tracking.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ User can create and manage asset accounts (CRUD, balance updates) — v1.0 (Phases 1-3)
- ✓ User can create and manage liabilities (CRUD, balance updates) — v1.0 (Phases 1-3)
- ✓ App captures daily net worth snapshots when balances change — v1.0 (Phases 1-3)
- ✓ User can view net worth trend chart on dashboard — v1.0 (Phases 1-3)
- ✓ User can view asset allocation and liability breakdown charts — v1.0 (Phases 1-3)
- ✓ User can view snapshot history table with per-account breakdown — v1.0 (Phases 1-3)
- ✓ User can export snapshot history as CSV — v1.0 (Phases 1-3)
- ✓ User can import historical snapshots via CSV — v1.0 (Phases 1-3)
- ✓ User can configure custom account/liability types — v1.0 (Phases 1-3)
- ✓ User can sign in with Google Sign-In via Firebase OAuth popup — v1.0 (Phase 4)
- ✓ All pages protected by server-side Firebase token verification — v1.0 (Phase 4)
- ✓ Session persists across page navigation, lost only on browser close or cold start — v1.0 (Phase 4)
- ✓ App shows login screen with no page content if unauthenticated — v1.0 (Phase 4/6)
- ✓ User can log out, clearing session and returning to login screen — v1.0 (Phase 4)
- ✓ App deployed on Cloud Run with Firebase credentials in Secret Manager — v1.0 (Phase 5)
- ✓ Cloud SQL connected via Unix socket; only DATABASE_URL format changed — v1.0 (Phase 5)
- ✓ Docker image excludes credentials, .env, .git — v1.0 (Phase 5)

### Active

<!-- Next milestone scope. -->

- [ ] DEPLOY-04 human verified: Cloud Run URL added to Firebase Authorized Domains (confirmed working)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Transaction tracking — scope creep, not the product's purpose
- Multi-user support — single-user app by design (deployed privately)
- Mobile app — web-first
- Multi-currency conversion — currency field exists but conversion adds API complexity
- Real-time sync / webhooks — unnecessary for manual balance tracking
- Email/password login — Google Sign-In covers single-user access
- Token refresh / onAuthStateChanged — address only if cold starts cause auth loss in practice

## Context

**Current state (v1.0 shipped 2026-03-05):**
- App is live at `https://finance-tracker-rntookejza-uc.a.run.app`
- Firebase Google Sign-In enforced on all pages
- Cloud Run + Cloud SQL (PostgreSQL 15, db-f1-micro free tier) + Secret Manager
- `users` table removed — Firebase UID stored directly in accounts/liabilities/snapshots (no FK constraints)
- GCP infrastructure managed via Terraform (`terraform/`)
- Stack: Python 3.12, Streamlit, SQLModel, PostgreSQL, Plotly, Firebase Auth, uv
- ~3,663 Python LOC

## Constraints

- **Platform:** Google Cloud Run + Cloud SQL (free-tier) — keep resource usage minimal
- **Auth provider:** Firebase (already in dependencies) — Google Sign-In only
- **Stack:** No changes to Python/Streamlit/SQLModel — already built and working
- **Users:** Single user — no multi-tenancy needed

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| No REST API | Streamlit server-side Python can call services directly | ✓ Good |
| Firebase UID as PK (no users table) | Removed users table post-deploy — no FK constraints needed for single user | ✓ Good |
| Daily snapshots with JSONB detail | Captures full breakdown at each point without reconstructing history | ✓ Good |
| SQLModel.metadata.create_all() for schema | Simple; no migration tool overhead | ✓ Good (v1) |
| Hardcoded test user for Phases 1-3 | Unblock UI development without auth complexity | ✓ Good |
| Raw postMessage for Firebase component | Zero-build Streamlit custom component | ✓ Good |
| Terraform for GCP infra | Reproducible, version-controlled infrastructure | ✓ Good |
| Postgres superuser for schema init | IAM auth requires Cloud SQL Proxy setup; simpler for one-time init | ✓ Good |
| No user data migration | Cloud SQL was empty on first deploy; test-user data local only | ✓ Good |
| get_or_create_user as validation-only | Users table removed; function now validates UID and blocks test-user | ✓ Good |

---
*Last updated: 2026-03-05 after v1.0 milestone*
