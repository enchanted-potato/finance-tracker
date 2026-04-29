# Finance Tracker (Net Worth Tracker)

## What This Is

Personal net worth tracker for a single user. Track asset accounts and liabilities over time with graphs. No transaction tracking — just point-in-time balance snapshots and trends. Deployed on Google Cloud Run.

## Core Value

Seeing your net worth trend over time at a glance, without the overhead of transaction tracking.

## Current Milestone: v2.0 React Migration

**Goal:** Replace Streamlit with a React + TypeScript frontend backed by a FastAPI REST API, hosted on Firebase Hosting with zero new GCP charges.

**Target features:**
- FastAPI REST API wrapping all existing SQLModel services
- React + TypeScript frontend with Tailwind CSS + shadcn/ui
- Recharts replacing Plotly for all charts
- Midnight dark colour scheme carried over
- Firebase Auth integrated via Firebase JS SDK (replacing Streamlit Firebase component)
- All existing pages rebuilt: Dashboard, Accounts, Liabilities, Pension, History, Configure
- Date-aware balance entry and history views (previously planned for v1.1 Phases 7-8)
- Firebase Hosting deployment for React; FastAPI stays on Cloud Run

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
- ✓ User can log in with Firebase Authentication — Phase 4
- ✓ App is deployed and accessible on Cloud Run with Cloud SQL — Phase 5

### Active

<!-- Current scope. Building toward these. -->

- [ ] FastAPI REST API exposes endpoints for all existing functionality (accounts, liabilities, pension, snapshots, configure)
- [ ] React frontend authenticates via Firebase JS SDK (Google Sign-In)
- [ ] Dashboard page shows net worth metric cards and charts (trend, allocation, pension)
- [ ] Accounts page supports CRUD, date-aware balance entry, and per-day history view
- [ ] Liabilities page supports CRUD, date-aware balance entry, and per-day history view
- [ ] Pension page supports CRUD, date-aware balance entry, and per-day history view
- [ ] History page shows styled snapshot table with "Jan 2025" date format and expandable rows with edit/delete
- [ ] Configure page manages account/liability types with inline delete per row
- [ ] CSV export and import available in History page
- [ ] React app deployed to Firebase Hosting; FastAPI deployed to Cloud Run

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Transaction tracking — scope creep, not the product's purpose
- Multi-user support — single-user app by design (deployed privately)
- Mobile app — web-first
- Multi-currency conversion — currency field exists but conversion adds API complexity
- Real-time sync / webhooks — unnecessary for manual balance tracking

## Context

- App is live: https://finance-tracker-rntookejza-uc.a.run.app (Cloud Run + Cloud SQL)
- Firebase Auth integrated (Google Sign-In); single user
- Phases 1-5 complete; quick tasks added post-v1.0: pension tracking, liabilities CSV upload, null value fixes
- Stack: Python 3.12, Streamlit, SQLModel, PostgreSQL, Plotly, Firebase Auth, uv
- Deployed on Google Cloud Run + Cloud SQL (free tier `db-f1-micro`)
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
*Last updated: 2026-04-29 after Phase 9 (FastAPI Foundation) complete — api/ package scaffolded, CORS/auth/lifespan/pool_pre_ping all verified*
