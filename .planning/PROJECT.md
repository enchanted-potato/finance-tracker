# Finance Tracker (Net Worth Tracker)

## What This Is

Personal net worth tracker for a single user. Track asset accounts and liabilities over time with graphs. No transaction tracking — just point-in-time balance snapshots and trends. Deployed on Google Cloud Run.

## Core Value

Seeing your net worth trend over time at a glance, without the overhead of transaction tracking.

## Current Milestone: v1.1 UI Overhaul

**Goal:** Improve every page for both practicality and aesthetics — redesign balance entry to support date-based backfilling, add history views per data type, and polish dashboard and supporting pages.

**Target features:**
- Date-aware balance entry on Accounts, Liabilities, and Pension pages (backfilling support)
- Per-page history views with daily totals and expandable per-item breakdown
- Dashboard metric cards with colored styled boxes; fix negative delta color
- History page table styling and date formatting
- Configure page inline delete per row
- Sidebar active state color improvement

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

- [ ] User can enter account balances for any chosen date (backfilling)
- [ ] User can view asset entry history with daily totals and per-account breakdown
- [ ] User can enter liability balances for any chosen date (backfilling)
- [ ] User can view liability entry history with daily totals and per-liability breakdown
- [ ] User can enter pension balances for any chosen date (backfilling)
- [ ] User can view pension entry history with daily totals and per-provider breakdown
- [ ] Dashboard metric cards display with colored styled boxes; negative delta shown in red
- [ ] Line chart y-axis shows thousands comma separator
- [ ] Pension bar chart has visual depth (shadows)
- [ ] History page uses styled table with dates formatted as "Jan 2025"
- [ ] History expanded row shows asset and liability breakdown with edit and delete
- [ ] Configure page delete type action is inline per row
- [ ] Sidebar active page indicator uses improved color

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
*Last updated: 2026-03-05 after milestone v1.1 started*
