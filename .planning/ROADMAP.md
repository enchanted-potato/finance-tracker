# Roadmap: Finance Tracker

## Overview

Phases 1-3 are pre-GSD foundation (complete): database models, service layer, and Streamlit UI — all working locally behind a hardcoded test user. This milestone (v1.0 — Ship) adds the two remaining capabilities to make the app production-ready: Firebase Authentication (Phase 4) and Cloud Run deployment (Phase 5). Auth must be complete and validated locally before deployment begins; you cannot safely expose financial data on a public URL without the auth gate in place.

## Milestones

- [x] **Phases 1-3: Foundation** — Pre-GSD (complete). Models, services, UI working locally.
- [ ] **v1.0 — Ship (Phases 4-5)** — Firebase Auth + Cloud Run deployment.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1-3: Foundation** - Pre-GSD complete (models, services, Streamlit UI)
- [ ] **Phase 4: Firebase Authentication** - Replace TEST_USER_ID with real Firebase auth, validated locally
- [ ] **Phase 5: Cloud Run Deployment** - Deploy app to Cloud Run + Cloud SQL, credentials via Secret Manager

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
- [ ] 05-01-PLAN.md — Prepare Docker configuration (.dockerignore, PORT-aware Dockerfile)
- [ ] 05-02-PLAN.md — Set up GCP infrastructure (Cloud SQL, Secret Manager, IAM)
- [~] 05-03-PLAN.md — Deploy to Cloud Run with Cloud SQL and Secret Manager integration (checkpoint: awaiting human verification)
- [ ] 05-04-PLAN.md — Migrate test-user data to production Firebase UID

---

## Progress

**Execution Order:**
Phases execute in numeric order: 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1-3. Foundation (pre-GSD) | — | Complete | Pre-2026-02-17 |
| 4. Firebase Authentication | 2/2 | Complete | 2026-02-21 |
| 5. Cloud Run Deployment | 3/4 | In Progress|  |
