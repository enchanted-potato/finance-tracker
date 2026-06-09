# Roadmap: Finance Tracker

## Overview

Phases 1-3 are pre-GSD foundation (complete): database models, service layer, and Streamlit UI — all working locally behind a hardcoded test user. v1.0 (Phases 4-5) added Firebase Authentication and Cloud Run deployment, making the app production-ready. v1.1 (Phases 6-8) polishes and extends the UI: dashboard cosmetics, date-aware balance entry with backfilling across all three data types, and history/configure page improvements. v2.0 (Phases 9-15) replaces Streamlit with a React + TypeScript SPA backed by a new FastAPI REST layer deployed on Firebase Hosting.

## Milestones

- [x] **Phases 1-3: Foundation** — Pre-GSD (complete). Models, services, UI working locally.
- [x] **v1.0 — Ship (Phases 4-5)** — Firebase Auth + Cloud Run deployment.
- [x] **v1.1 — UI Overhaul (Phases 6-8)** — Dashboard polish, date-aware entry, history and configure improvements.
- [ ] **v2.0 — React Migration (Phases 9-15)** — FastAPI REST layer + React + TypeScript SPA on Firebase Hosting.

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
- [x] **Phase 9: FastAPI Foundation** - CORS, auth dependency, Firebase Admin lifespan, pool_pre_ping — platform correct before any feature routes (completed 2026-04-29)
- [ ] **Phase 10: Core Data API Routes** - All feature endpoints (accounts, liabilities, pension, snapshots, configure) with float schemas and Recharts-shaped responses
- [ ] **Phase 11: React Scaffold and Auth** - Vite + Tailwind + shadcn/ui, Firebase Google Sign-In auth gate, Axios client with per-request token refresh, sidebar shell
- [x] **Phase 12: Data Pages** - Accounts, Liabilities, and Pension pages with CRUD dialogs, date-aware entry, and collapsible entry history (completed 2026-05-19)
- [ ] **Phase 13: Dashboard** - Metric cards and four Recharts charts (trend, allocation, pension) consuming real API data
- [ ] **Phase 14: History and Configure** - Snapshot history table with expandable rows and CSV export/import; Configure page with inline type management
- [ ] **Phase 15: Deployment** - React SPA on Firebase Hosting; FastAPI replaces Streamlit on Cloud Run; end-to-end production smoke test

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

### Phase 9: FastAPI Foundation
**Goal**: A correctly configured FastAPI server is running locally — CORS, auth, database session, and Firebase Admin initialisation are all in place before any feature route is written
**Depends on**: Phase 8 (v1.1 Streamlit app complete; v2.0 API layer starts here)
**Requirements**: API-01, API-02, API-03, API-04
**Success Criteria** (what must be TRUE):
  1. `GET /api/health` returns HTTP 200; the server starts without errors and Firebase Admin SDK is initialised via the lifespan context manager — not at module level
  2. `curl -H "Authorization: Bearer <valid-token>" /api/health` returns 200; the same request without a token returns HTTP 401
  3. A CORS preflight from `http://localhost:5173` succeeds (HTTP 200 with correct `Access-Control-Allow-Origin` header); a preflight from an unlisted origin is rejected
  4. A Pydantic response schema with a `Decimal` balance field serialises to `{"balance": 10753.42}` (float), not `{"balance": "10753.42"}` (string) — verified with `curl`
  5. `pool_pre_ping=True` is set on the database engine; the app reconnects cleanly after a simulated database connection drop
**Plans**: 2 plans

Plans:
- [x] 09-01-PLAN.md — FastAPI package scaffold, auth dependency, health endpoint, pool_pre_ping + full test suite (Wave 1)
- [x] 09-02-PLAN.md — Add api service to docker-compose.yml + Docker smoke test checkpoint (Wave 2)

---

### Phase 10: Core Data API Routes
**Goal**: All feature endpoints are live and returning correctly shaped data — the API contract is the single source of truth for all business logic and data shaping
**Depends on**: Phase 9 (FastAPI foundation must be correct before any feature routes)
**Requirements**: API-05, API-06, API-07, API-08
**Success Criteria** (what must be TRUE):
  1. Account CRUD endpoints (`GET/POST /api/accounts`, `PUT/DELETE /api/accounts/{id}`) return correctly and the balance entry endpoint saves a dated snapshot — verified with `curl` using a valid Firebase token
  2. Liability CRUD and balance entry endpoints match the accounts pattern; daily totals and per-liability breakdown are computed server-side and returned in the response
  3. Pension CRUD and balance entry endpoints match the accounts pattern; daily totals and per-provider breakdown are computed server-side and returned in the response
  4. `GET /api/snapshots/export.csv` returns a downloadable CSV file; `POST /api/snapshots/import` accepts a multipart CSV upload and persists the imported snapshots
  5. Account type and liability type CRUD endpoints return whether each type is in use — the "in use" check is performed by the API, not the client
**Plans**: TBD

---

### Phase 11: React Scaffold and Auth
**Goal**: A React SPA exists with working Firebase Google Sign-In — all pages are gated behind authentication and the API client is wired to refresh tokens before every request
**Depends on**: Phase 9 (API auth endpoint must exist to test the React auth gate end-to-end; Phase 10 not required — scaffold uses the health endpoint)
**Requirements**: REACT-01, REACT-02, REACT-03, REACT-04
**Success Criteria** (what must be TRUE):
  1. The app loads at `http://localhost:5173` with the Midnight dark theme applied; navigating to any page URL without being authenticated redirects to the login screen with no financial data visible
  2. User can sign in with Google Sign-In; after login, the dashboard shell loads and the sidebar shows all page links with the active page highlighted
  3. Every API request made by the app includes a fresh Firebase ID token in the `Authorization` header — the raw token string is never stored in React component state
  4. Receiving HTTP 401 from the API redirects the user to the login screen
**Plans**: 4 plans

Plans:
- [x] 11-01-PLAN.md — Vite scaffold + Tailwind v3 + shadcn@2.3.0 init + Midnight theme + vitest config (Wave 1)
- [ ] 11-02-PLAN.md — Firebase init + AuthContext + PrivateRoute + LoginPage + App routes + unit tests (Wave 2)
- [ ] 11-03-PLAN.md — Axios apiClient with per-request getIdToken() + 401 redirect + unit tests (Wave 3)
- [ ] 11-04-PLAN.md — AppSidebar + AppLayout + 6 page stubs + App.tsx route wiring + unit tests (Wave 3)

---

### Phase 12: Data Pages
**Goal**: Users can manage accounts, liabilities, and pension providers — adding, editing, and deleting entries with date-aware balance capture and a collapsible entry history on each page
**Depends on**: Phase 10 (data API routes must exist), Phase 11 (React scaffold and auth gate must exist)
**Requirements**: RDAT-01, RDAT-02, RDAT-03, RDAT-04, RDAT-05, RDAT-06, RDAT-07
**Success Criteria** (what must be TRUE):
  1. The Accounts page shows the account list; user can add, edit, and delete accounts via a dialog — changes persist and are reflected immediately in the list
  2. The Accounts page date picker defaults to today; submitting a balance entry for a past date saves a snapshot for that date and the entry appears in the history table
  3. The Accounts page entry history shows daily totals (computed by API); expanding a row reveals per-account balances for that day
  4. The Liabilities and Pension pages replicate the Accounts page behaviour exactly — CRUD dialogs, date-aware entry, and collapsible history with server-computed totals all work on all three pages
**Plans**: 4 plans

Plans:
- [x] 12-01-PLAN.md — Install deps + shadcn components + QueryClientProvider + test scaffolding (Wave 0, blocking)
- [x] 12-02-PLAN.md — API modules + shared DataPage components + AccountsPage (Wave 1)
- [x] 12-03-PLAN.md — LiabilitiesPage thin wrapper (Wave 2, parallel with 12-04)
- [x] 12-04-PLAN.md — PensionPage thin wrapper (Wave 2, parallel with 12-03)

**Wave 1** *(blocked on Wave 0 completion)*
**Wave 2** *(blocked on Wave 1 completion — plans 12-03 and 12-04 parallel)*

Cross-cutting constraints:
- `form.reset()` in `useEffect([open, editItem?.id])` — prevents stale dialog values (all plans)
- `invalidateQueries` in `onSuccess` only — no optimistic updates (server computes history totals)
- `toast.success/error` from `sonner` — locked from Phase 11, all plans
- All monetary display: `Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' })`

---

### Phase 13: Dashboard
**Goal**: The dashboard gives an at-a-glance view of net worth position — metric cards, trend chart, allocation charts, and pension chart all render with real data from the API
**Depends on**: Phase 12 (real account, liability, and pension data must exist to validate chart rendering and metric card values)
**Requirements**: RDASH-01, RDASH-02, RDASH-03, RDASH-04
**Success Criteria** (what must be TRUE):
  1. Net Worth, Assets, and Liabilities metric cards display as styled rounded boxes (blue, green, red); a negative net worth delta is shown in red — values and delta are returned by the API, not computed in React
  2. The net worth trend line chart renders with y-axis values formatted with thousands comma separators; chart data is in Recharts format (one object per date with all series as keys) as returned by the API
  3. The asset allocation donut chart renders using Recharts — data is returned by the API with one slice per asset type
  4. The pension balance bar chart renders using Recharts with one bar per provider — data is returned by the API
**Plans**: 2 plans

Plans:
- [ ] 13-01-PLAN.md — Install recharts + dashboard API module + full DashboardPage implementation (Wave 1)
- [ ] 13-02-PLAN.md — DashboardPage unit tests covering all 4 RDASH requirements (Wave 2)

**Wave 2** *(blocked on Wave 1 completion)*

---

### Phase 14: History and Configure
**Goal**: Users can review their full snapshot history with expandable detail rows and CSV import/export; account and liability types can be managed with inline deletion
**Depends on**: Phase 12 (snapshot data from data pages must exist), Phase 11 (React scaffold)
**Requirements**: RHIST-01, RHIST-02, RHIST-03, RHIST-04, RCONF-01
**Success Criteria** (what must be TRUE):
  1. The History page snapshot table displays dates in "Jan 2025" format — the date is formatted by the API in the response, not by React
  2. Expanding a snapshot row reveals per-asset and per-liability item names and values — the breakdown is provided by the API
  3. User can click a download button and receive a CSV file of all snapshots — the file is generated server-side via `GET /snapshots/export.csv` with no client-side data processing
  4. User can upload a CSV file on the History page and the imported snapshots appear in the table after upload
  5. The Configure page shows account type and liability type tables; each row has an inline delete button that is disabled (not absent) when the type is in use — the "in use" state is returned by the API
**Plans**: TBD

---

### Phase 15: Deployment
**Goal**: The React SPA is live on Firebase Hosting and FastAPI is running on Cloud Run — the full stack is accessible end-to-end in production with all production pitfalls verified
**Depends on**: Phase 14 (all pages complete), Phase 13 (dashboard complete)
**Requirements**: RDEP-01, RDEP-02
**Success Criteria** (what must be TRUE):
  1. The React SPA is deployed to Firebase Hosting; navigating directly to any page URL (e.g. `/history`) returns the app, not a 404 — the catch-all SPA rewrite rule in `firebase.json` is in place
  2. FastAPI is running on Cloud Run replacing Streamlit; the Cloud SQL Unix socket and Secret Manager wiring are unchanged from the v1.0 deployment
  3. A CORS preflight from the Firebase Hosting production domain succeeds — the `ALLOWED_ORIGINS` list in the deployed FastAPI app includes the production Firebase Hosting URL
  4. Signing in on the production URL, making a balance entry, and reloading the page shows the entry persisted — full end-to-end smoke test passes
**Plans**: TBD

---

## Progress

**Execution Order:**
Phases execute in numeric order: 9 → 10 → 11 → 12 → 13 → 14 → 15

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1-3. Foundation (pre-GSD) | — | Complete | Pre-2026-02-17 |
| 4. Firebase Authentication | 2/2 | Complete | 2026-02-21 |
| 5. Cloud Run Deployment | 4/4 | Complete | 2026-03-01 |
| 6. Dashboard and Navigation Polish | 4/4 | Complete | 2026-03-07 |
| 7. Date-Aware Balance Entry | 0/TBD | Not started | - |
| 8. History and Configure Improvements | 0/TBD | Not started | - |
| 9. FastAPI Foundation | 2/2 | Complete | 2026-04-29 |
| 10. Core Data API Routes | 0/TBD | Not started | - |
| 11. React Scaffold and Auth | 1/4 | In Progress|  |
| 12. Data Pages | 4/4 | Complete   | 2026-05-19 |
| 13. Dashboard | 0/2 | Ready to execute | - |
| 14. History and Configure | 0/TBD | Not started | - |
| 15. Deployment | 0/TBD | Not started | - |
