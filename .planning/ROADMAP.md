# Roadmap: Finance Tracker

## Overview

Phases 1-3 are pre-GSD foundation (complete): database models, service layer, and Streamlit UI — all working locally behind a hardcoded test user. v1.0 (Phases 4-5) added Firebase Authentication and Cloud Run deployment, making the app production-ready. v1.1 (Phases 6-8) polishes and extends the UI: dashboard cosmetics, date-aware balance entry with backfilling across all three data types, and history/configure page improvements.

## Milestones

- [x] **Phases 1-3: Foundation** — Pre-GSD (complete). Models, services, UI working locally.
- [x] **v1.0 — Ship (Phases 4-5)** — Firebase Auth + Cloud Run deployment.
- [ ] **v1.1 — UI Overhaul (Phases 6-8)** — Dashboard polish, date-aware entry, history and configure improvements.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1-3: Foundation** - Pre-GSD complete (models, services, Streamlit UI)
- [x] **Phase 4: Firebase Authentication** - Replace TEST_USER_ID with real Firebase auth, validated locally
- [x] **Phase 5: Cloud Run Deployment** - Deploy app to Cloud Run + Cloud SQL, credentials via Secret Manager
- [x] **Phase 6: Dashboard and Navigation Polish** - Metric card styling, chart improvements, sidebar active color (completed 2026-03-07)
- [ ] **Phase 7: Date-Aware Balance Entry** - Date picker + history view on Accounts, Liabilities, and Pension pages
- [ ] **Phase 8: History and Configure Improvements** - Styled history table, date formatting, expanded row actions, inline delete

## Phase Details

### Phase 4: Firebase Authentication
**Goal**: The app enforces authentication — only the owner can view their financial data
**Depends on**: Phases 1-3 (complete)
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06
**Success Criteria** (what must be TRUE):
  1. An unauthenticated browser request to any page shows the login screen with no financial data visible
  2. User can sign in with Google Sign-In and the full dashboard loads with their data
  3. Authenticated session survives Streamlit page navigation — switching between pages does not prompt re-login
  4. User can log out and is returned to the login screen with all financial data cleared from view
  5. First successful login auto-creates the user row so existing accounts, liabilities, and snapshots FK constraints are satisfied

**Research flag:** RESOLVED — `st.components.v1.html()` returns None; must use `declare_component()` with path to directory containing index.html.

**Plans:** 2 plans

Plans:
- [x] 04-01-PLAN.md — Auth service layer + Firebase custom Streamlit component
- [x] 04-02-PLAN.md — Auth gate integration into main.py + data migration script

---

### Phase 5: Cloud Run Deployment
**Goal**: The app is live at a public HTTPS URL, connected to managed Cloud SQL, with Firebase credentials never baked into the image
**Depends on**: Phase 4 (auth gate must exist before public exposure)
**Requirements**: DEPLOY-01, DEPLOY-02, DEPLOY-03, DEPLOY-04, DEPLOY-05
**Success Criteria** (what must be TRUE):
  1. Firebase service account credentials are stored in Secret Manager and injected at runtime — absent from the Docker image and repository
  2. The Docker image build excludes `.env`, credential JSON files, and `.git`
  3. The app connects to Cloud SQL via Unix socket on Cloud Run with no changes to `app/database.py` — only `DATABASE_URL` format changes
  4. The app is accessible via HTTPS Cloud Run URL with working Google Sign-In end-to-end
  5. All rows with `user_id = 'test-user'` are migrated to the real Firebase UID before production traffic reaches the app

**Research flag:** RESOLVED — Verified Cloud SQL Unix socket `DATABASE_URL` format (`postgresql+psycopg2://USER:PASS@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE`) and exact `gcloud run deploy` flag names (`--set-secrets`, `--add-cloudsql-instances`) via official GCP docs.

**Plans**: 4 plans

Plans:
- [x] 05-01-PLAN.md — Prepare Docker configuration (.dockerignore, PORT-aware Dockerfile)
- [x] 05-02-PLAN.md — Set up GCP infrastructure (Cloud SQL, Secret Manager, IAM)
- [x] 05-03-PLAN.md — Deploy to Cloud Run with Cloud SQL and Secret Manager integration
- [x] 05-04-PLAN.md — Migrate test-user data to production Firebase UID

---

### Phase 6: Dashboard and Navigation Polish
**Goal**: The dashboard communicates financial position clearly with visual hierarchy; the sidebar reliably shows which page is active
**Depends on**: Phase 5 (app is live; this is pure frontend — no backend changes)
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04, NAV-01
**Success Criteria** (what must be TRUE):
  1. Net Worth, Assets, and Liabilities metric cards render as rounded boxes with distinct soft-colored backgrounds (blue, green, red) — not plain text
  2. A negative Net Worth delta is shown in red, not green
  3. The line chart y-axis labels include thousands comma separators (e.g., "1,250" not "1250")
  4. The pension bar chart displays with drop shadows that give visual depth
  5. The sidebar highlights the active page with a color clearly distinct from orange
**Plans**: 4 plans

Plans:
- [ ] 06-01-PLAN.md — Test scaffold for delta sign logic and chart axis format (Wave 1)
- [ ] 06-02-PLAN.md — Dashboard metric cards + chart fixes in dashboard.py (Wave 2)
- [ ] 06-03-PLAN.md — CSS injection + sidebar active border in main.py (Wave 1)
- [ ] 06-04-PLAN.md — Visual verification checkpoint (Wave 3)

---

### Phase 7: Date-Aware Balance Entry
**Goal**: Users can enter balances for any past date on the Accounts, Liabilities, and Pension pages, and can see the entry history per page
**Depends on**: Phase 6 (polish first; Phase 7 adds backend changes)
**Requirements**: ENTRY-01, ENTRY-02, ENTRY-03, ENTRY-04, ENTRY-05, ENTRY-06
**Success Criteria** (what must be TRUE):
  1. The Accounts page balance entry form has a date picker that defaults to today; submitting with a past date saves a backfilled snapshot for that date
  2. The Accounts page shows an entry history table with daily totals and expandable rows revealing per-account balances for that day
  3. The Liabilities page balance entry form has a date picker that defaults to today; submitting with a past date saves a backfilled snapshot for that date
  4. The Liabilities page shows an entry history table with daily totals and expandable rows revealing per-liability balances for that day
  5. The Pension page balance entry form has a date picker that defaults to today; submitting with a past date saves a backfilled snapshot for that date
  6. The Pension page shows an entry history table with daily totals and expandable rows revealing per-provider balances for that day
**Plans**: TBD

---

### Phase 8: History and Configure Improvements
**Goal**: The History page uses a properly styled table with readable date formatting and full per-item breakdown; the Configure page allows inline deletion of unused types
**Depends on**: Phase 7 (history improvements build on the snapshot data that backfilling enables)
**Requirements**: HIST-01, HIST-02, HIST-03, CONF-01
**Success Criteria** (what must be TRUE):
  1. The History page snapshot table renders using a styled table component — not a manual column layout
  2. Dates in the history table are displayed as "Jan 2025" format (month + abbreviated year)
  3. Expanding a history row shows asset and liability item names with their values, plus edit and delete action buttons per item
  4. The Configure page account type and liability type rows each have an inline delete button; the button is disabled (not absent) when the type is in use
**Plans**: TBD

---

## Progress

**Execution Order:**
Phases execute in numeric order: 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1-3. Foundation (pre-GSD) | — | Complete | Pre-2026-02-17 |
| 4. Firebase Authentication | 2/2 | Complete | 2026-02-21 |
| 5. Cloud Run Deployment | 4/4 | Complete | 2026-03-01 |
| 6. Dashboard and Navigation Polish | 4/4 | Complete   | 2026-03-07 |
| 7. Date-Aware Balance Entry | 0/TBD | Not started | - |
| 8. History and Configure Improvements | 0/TBD | Not started | - |
