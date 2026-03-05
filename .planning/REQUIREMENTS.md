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

## v1.1 Requirements

### Dashboard

- [ ] **DASH-01**: Metric cards display as styled rounded boxes with soft colored backgrounds (Net Worth=blue, Assets=green, Liabilities=red)
- [ ] **DASH-02**: Net Worth delta is shown in red when negative (not green)
- [ ] **DASH-03**: Line chart y-axis displays values with thousands comma separator
- [ ] **DASH-04**: Pension bar chart has drop shadows for visual depth

### Balance Entry

- [ ] **ENTRY-01**: User can select a date when entering asset account balances (default = today)
- [ ] **ENTRY-02**: User can view asset entry history with daily totals and expandable per-account breakdown on the Accounts page
- [ ] **ENTRY-03**: User can select a date when entering liability balances (default = today)
- [ ] **ENTRY-04**: User can view liability entry history with daily totals and expandable per-liability breakdown on the Liabilities page
- [ ] **ENTRY-05**: User can select a date when entering pension balances (default = today)
- [ ] **ENTRY-06**: User can view pension entry history with daily totals and expandable per-provider breakdown on the Pension page

### History

- [ ] **HIST-01**: Snapshot table uses a properly styled table component (not manual column layout)
- [ ] **HIST-02**: Dates in the history table are formatted as "Jan 2025" (month + year)
- [ ] **HIST-03**: Expanded history row shows asset and liability item breakdown with edit and delete actions

### Configure

- [ ] **CONF-01**: Account type and liability type delete action is inline per row (disabled if type is in use)

### Navigation

- [ ] **NAV-01**: Sidebar active page indicator uses a color other than orange

## Future Requirements (v2+)

### Authentication

- **AUTH-F01**: Email/password login — Google Sign-In covers single-user access; add only if Google Sign-In proves inconvenient
- **AUTH-F02**: Token refresh / `onAuthStateChanged` re-auth handling — address if Cloud Run cold starts cause authentication loss in practice

## Out of Scope

| Feature | Reason |
|---------|--------|
| Transaction tracking | Not the product's purpose |
| Multi-user support | App is personal, single-user by design |
| Multi-currency conversion | Currency field exists; conversion adds API complexity |
| Mobile app | Web-first; Streamlit doesn't support native mobile |
| Real-time data sync | Manual balance updates; no need for webhooks |

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
| DASH-01 | Phase 6 | Pending |
| DASH-02 | Phase 6 | Pending |
| DASH-03 | Phase 6 | Pending |
| DASH-04 | Phase 6 | Pending |
| NAV-01 | Phase 6 | Pending |
| ENTRY-01 | Phase 7 | Pending |
| ENTRY-02 | Phase 7 | Pending |
| ENTRY-03 | Phase 7 | Pending |
| ENTRY-04 | Phase 7 | Pending |
| ENTRY-05 | Phase 7 | Pending |
| ENTRY-06 | Phase 7 | Pending |
| HIST-01 | Phase 8 | Pending |
| HIST-02 | Phase 8 | Pending |
| HIST-03 | Phase 8 | Pending |
| CONF-01 | Phase 8 | Pending |

**Coverage:**
- v1.1 requirements: 15 total
- Mapped to phases: 15
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-17*
*Last updated: 2026-03-05 after v1.1 milestone definition*
