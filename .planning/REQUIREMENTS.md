# Requirements: Finance Tracker

**Defined:** 2026-02-17
**Core Value:** Seeing your net worth trend over time at a glance, without the overhead of transaction tracking.

## v1.0 Requirements (Complete)

### Authentication

- [x] **AUTH-01**: User can sign in with Google Sign-In via Firebase OAuth popup
- [x] **AUTH-02**: App verifies Firebase ID token server-side before granting access to any page
- [x] **AUTH-03**: User session persists across page reruns (survives Streamlit navigation, lost on browser close or container cold start)
- [x] **AUTH-04**: App shows login screen with no page content if user is not authenticated
- [x] **AUTH-05**: User can log out, clearing session state and returning to the login screen
- [x] **AUTH-06**: User account is auto-created on first successful login (satisfies FK constraint on accounts, liabilities, snapshots)

### Deployment

- [x] **DEPLOY-01**: Firebase service account credentials are stored in GCP Secret Manager (not in Docker image, not in repository, not in .env)
- [x] **DEPLOY-02**: `.dockerignore` excludes `.env`, credential JSON files, and `.git` from Docker image
- [x] **DEPLOY-03**: App connects to Cloud SQL via Unix socket when running on Cloud Run (DATABASE_URL format change only — no code changes to `app/database.py`)
- [x] **DEPLOY-04**: App is deployed to Cloud Run, accessible via HTTPS URL, with working Google Sign-In authentication
- [x] **DEPLOY-05**: Data migration script updates all `user_id = 'test-user'` rows to the real Firebase UID before production traffic reaches the app

## v1.1 Requirements (Partially Complete)

### Dashboard

- [x] **DASH-01**: Metric cards display as styled rounded boxes with soft colored backgrounds (Net Worth=blue, Assets=green, Liabilities=red)
- [x] **DASH-02**: Net Worth delta is shown in red when negative (not green)
- [x] **DASH-03**: Line chart y-axis displays values with thousands comma separator
- [x] **DASH-04**: Pension bar chart has drop shadows for visual depth

### Balance Entry

> Superseded by RDAT-01–07 (React versions). Not built in Streamlit.

- ~~**ENTRY-01**~~: Superseded by RDAT-02
- ~~**ENTRY-02**~~: Superseded by RDAT-03
- ~~**ENTRY-03**~~: Superseded by RDAT-04
- ~~**ENTRY-04**~~: Superseded by RDAT-05
- ~~**ENTRY-05**~~: Superseded by RDAT-06
- ~~**ENTRY-06**~~: Superseded by RDAT-07

### History

> Superseded by RHIST-01–04 (React versions). Not built in Streamlit.

- ~~**HIST-01**~~: Superseded by RHIST-01
- ~~**HIST-02**~~: Superseded by RHIST-01
- ~~**HIST-03**~~: Superseded by RHIST-02

### Configure

> Superseded by RCONF-01 (React version). Not built in Streamlit.

- ~~**CONF-01**~~: Superseded by RCONF-01

### Navigation

- [x] **NAV-01**: Sidebar active page indicator uses a color other than orange

## v2.0 Requirements

**Architecture constraint:** All business logic, data aggregation, chart data shaping, and calculations live in the FastAPI backend. The React frontend is purely presentational — it renders what the API returns, with no data processing in the client.

### API Layer

- [ ] **API-01**: FastAPI app initialises Firebase Admin SDK via `lifespan` context manager and sets `pool_pre_ping=True` on the database engine
- [ ] **API-02**: FastAPI configures CORS with explicit Firebase Hosting origins (`https://PROJECT.web.app`, `https://PROJECT.firebaseapp.com`, `http://localhost:5173`) and `allow_credentials=True` (no wildcard)
- [ ] **API-03**: FastAPI auth dependency verifies Firebase ID token from `Authorization: Bearer` header; returns HTTP 401 if missing or invalid
- [ ] **API-04**: All response schemas use `float` (not `Decimal`) for monetary values; chart data is returned in Recharts format (one object per date with all series as keys) — all data shaping and aggregation happens in the API
- [ ] **API-05**: API exposes endpoints for account CRUD, date-aware balance entry, and entry history (daily totals + per-account breakdown computed server-side)
- [ ] **API-06**: API exposes endpoints for liability CRUD, date-aware balance entry, and entry history (daily totals + per-liability breakdown computed server-side)
- [ ] **API-07**: API exposes endpoints for pension CRUD, date-aware balance entry, and entry history (daily totals + per-provider breakdown computed server-side)
- [ ] **API-08**: API exposes endpoints for snapshot history list, CSV export (server-generated file via `GET /snapshots/export.csv`), CSV import (multipart upload), and account/liability type CRUD with safe delete

### React Scaffold

- [ ] **REACT-01**: React + TypeScript project built with Vite, Tailwind v3, shadcn/ui initialised with Midnight dark theme
- [ ] **REACT-02**: User can sign in with Google Sign-In; app gates all pages behind `onAuthStateChanged` with no financial data visible before login
- [ ] **REACT-03**: Axios client calls `getIdToken()` before every request (never caches the raw token string) and redirects to login on HTTP 401
- [ ] **REACT-04**: Sidebar navigation shows all page links with active page highlight using Midnight-consistent colour

### Dashboard

- [ ] **RDASH-01**: Dashboard shows Net Worth / Assets / Liabilities metric cards as styled rounded boxes (blue/green/red); negative delta shown in red — values and delta computed by API
- [ ] **RDASH-02**: Dashboard shows net worth trend line chart with y-axis values formatted with thousands comma separators — data served in Recharts format by API
- [ ] **RDASH-03**: Dashboard shows asset allocation pie/donut chart using Recharts — data served by API
- [ ] **RDASH-04**: Dashboard shows pension balance bar chart using Recharts — data served by API

### Data Pages

- [ ] **RDAT-01**: Accounts page shows account list with CRUD actions (add/edit/delete)
- [ ] **RDAT-02**: Accounts page allows date-aware balance entry (date picker defaults to today) that saves a snapshot for that date
- [ ] **RDAT-03**: Accounts page shows entry history with daily totals and collapsible per-account breakdown — totals computed by API
- [ ] **RDAT-04**: Liabilities page shows liability list with CRUD actions and date-aware balance entry matching Accounts pattern
- [ ] **RDAT-05**: Liabilities page shows entry history with daily totals and collapsible per-liability breakdown — totals computed by API
- [ ] **RDAT-06**: Pension page shows provider list with CRUD actions and date-aware balance entry matching Accounts pattern
- [ ] **RDAT-07**: Pension page shows entry history with daily totals and collapsible per-provider breakdown — totals computed by API

### History

- [ ] **RHIST-01**: History page shows snapshot table with dates formatted as "Jan 2025" — formatting applied by API in response
- [ ] **RHIST-02**: Each snapshot row is expandable to show per-asset and per-liability item names and values — breakdown provided by API
- [ ] **RHIST-03**: User can download snapshot history as CSV via a server-generated file (`GET /snapshots/export.csv`) — no client-side data processing
- [ ] **RHIST-04**: User can import historical snapshots via CSV file upload to the API

### Configure

- [ ] **RCONF-01**: Configure page shows account type and liability type tables with inline delete button per row; button disabled (not absent) when type is in use — "in use" check performed by API

### Deployment

- [ ] **RDEP-01**: React SPA deployed to Firebase Hosting with catch-all SPA rewrite rule; direct URL navigation works for all routes
- [ ] **RDEP-02**: FastAPI replaces Streamlit in the Cloud Run container; Dockerfile updated, Cloud SQL Unix socket and Secret Manager wiring unchanged

## Future Requirements (v3+)

### Authentication

- **AUTH-F01**: Email/password login — Google Sign-In covers single-user access; add only if Google Sign-In proves inconvenient
- **AUTH-F02**: Token refresh / `onAuthStateChanged` re-auth handling — address if Cloud Run cold starts cause authentication loss in practice

## Out of Scope

| Feature | Reason |
|---------|--------|
| Transaction tracking | Not the product's purpose |
| Multi-user support | App is personal, single-user by design |
| Multi-currency conversion | Currency field exists; conversion adds API complexity |
| Mobile app | Web-first |
| Real-time data sync | Manual balance updates; no need for webhooks |
| Client-side data processing in React | All logic in FastAPI — React is purely presentational |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 4 | Complete |
| AUTH-02 | Phase 4 | Complete |
| AUTH-03 | Phase 4 | Complete |
| AUTH-04 | Phase 4 | Complete |
| AUTH-05 | Phase 4 | Complete |
| AUTH-06 | Phase 4 | Complete |
| DEPLOY-01 | Phase 5 | Complete |
| DEPLOY-02 | Phase 5 | Complete |
| DEPLOY-03 | Phase 5 | Complete |
| DEPLOY-04 | Phase 5 | Complete |
| DEPLOY-05 | Phase 5 | Complete |
| DASH-01 | Phase 6 | Complete |
| DASH-02 | Phase 6 | Complete |
| DASH-03 | Phase 6 | Complete |
| DASH-04 | Phase 6 | Complete |
| NAV-01 | Phase 6 | Complete |
| API-01 | Phase 9 | Pending |
| API-02 | Phase 9 | Pending |
| API-03 | Phase 9 | Pending |
| API-04 | Phase 9 | Pending |
| API-05 | Phase 10 | Pending |
| API-06 | Phase 10 | Pending |
| API-07 | Phase 10 | Pending |
| API-08 | Phase 10 | Pending |
| REACT-01 | Phase 11 | Pending |
| REACT-02 | Phase 11 | Pending |
| REACT-03 | Phase 11 | Pending |
| REACT-04 | Phase 11 | Pending |
| RDASH-01 | Phase 13 | Pending |
| RDASH-02 | Phase 13 | Pending |
| RDASH-03 | Phase 13 | Pending |
| RDASH-04 | Phase 13 | Pending |
| RDAT-01 | Phase 12 | Pending |
| RDAT-02 | Phase 12 | Pending |
| RDAT-03 | Phase 12 | Pending |
| RDAT-04 | Phase 12 | Pending |
| RDAT-05 | Phase 12 | Pending |
| RDAT-06 | Phase 12 | Pending |
| RDAT-07 | Phase 12 | Pending |
| RHIST-01 | Phase 14 | Pending |
| RHIST-02 | Phase 14 | Pending |
| RHIST-03 | Phase 14 | Pending |
| RHIST-04 | Phase 14 | Pending |
| RCONF-01 | Phase 14 | Pending |
| RDEP-01 | Phase 15 | Pending |
| RDEP-02 | Phase 15 | Pending |

**Coverage:**
- v1.0 requirements: 11 total, 11 mapped ✓
- v1.1 requirements: 5 complete, 10 superseded by v2.0 ✓
- v2.0 requirements: 28 total, 28 mapped ✓
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-17*
*Last updated: 2026-04-05 after v2.0 roadmap created (Phases 9-15)*
