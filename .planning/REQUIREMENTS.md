# Requirements: Finance Tracker

**Defined:** 2026-02-17
**Core Value:** Seeing your net worth trend over time at a glance, without the overhead of transaction tracking.

## v1.0 Requirements

Requirements for initial live release (auth + deployment). Phases 1-3 (foundation, services, UI) are pre-GSD foundation — validated and complete.

### Authentication

- [ ] **AUTH-01**: User can sign in with Google Sign-In via Firebase OAuth popup
- [ ] **AUTH-02**: App verifies Firebase ID token server-side before granting access to any page
- [ ] **AUTH-03**: User session persists across page reruns (survives Streamlit navigation, lost on browser close or container cold start)
- [ ] **AUTH-04**: App shows login screen with no page content if user is not authenticated
- [ ] **AUTH-05**: User can log out, clearing session state and returning to the login screen
- [ ] **AUTH-06**: User account is auto-created on first successful login (satisfies FK constraint on accounts, liabilities, snapshots)

### Deployment

- [ ] **DEPLOY-01**: Firebase service account credentials are stored in GCP Secret Manager (not in Docker image, not in repository, not in .env)
- [x] **DEPLOY-02**: `.dockerignore` excludes `.env`, credential JSON files, and `.git` from Docker image
- [ ] **DEPLOY-03**: App connects to Cloud SQL via Unix socket when running on Cloud Run (DATABASE_URL format change only — no code changes to `app/database.py`)
- [ ] **DEPLOY-04**: App is deployed to Cloud Run, accessible via HTTPS URL, with working Google Sign-In authentication
- [ ] **DEPLOY-05**: Data migration script updates all `user_id = 'test-user'` rows to the real Firebase UID before production traffic reaches the app

## Future Requirements (v1.1+)

### Authentication

- **AUTH-F01**: Email/password login — Google Sign-In covers single-user access; add only if Google Sign-In proves inconvenient
- **AUTH-F02**: Token refresh / `onAuthStateChanged` re-auth handling — address if Cloud Run cold starts cause authentication loss in practice
- **AUTH-F03**: Password reset UI — Firebase Console provides this directly; no in-app UI needed for single user

## Out of Scope

| Feature | Reason |
|---------|--------|
| Registration/sign-up flow | Single user; account created once in Firebase Console |
| Multi-user support | App is personal, single-user by design |
| Transaction tracking | Not the product's purpose — net worth only |
| Multi-currency conversion | Currency field exists; conversion adds API complexity |
| Mobile app | Web-first; Streamlit doesn't support native mobile |
| Real-time data sync | Manual balance updates; no need for webhooks |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 4 | Pending |
| AUTH-02 | Phase 4 | Pending |
| AUTH-03 | Phase 4 | Pending |
| AUTH-04 | Phase 4 | Pending |
| AUTH-05 | Phase 4 | Pending |
| AUTH-06 | Phase 4 | Pending |
| DEPLOY-01 | Phase 5 | Pending |
| DEPLOY-02 | Phase 5 | Complete |
| DEPLOY-03 | Phase 5 | Pending |
| DEPLOY-04 | Phase 5 | Pending |
| DEPLOY-05 | Phase 5 | Pending |

**Coverage:**
- v1.0 requirements: 11 total
- Mapped to phases: 11 (Phase 4: 6, Phase 5: 5)
- Unmapped: 0

---
*Requirements defined: 2026-02-17*
*Last updated: 2026-02-17 after roadmap creation*
