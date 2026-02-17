# Project Research Summary

**Project:** Finance Tracker — Firebase Auth + Cloud Run Deployment
**Domain:** Firebase Auth integration + GCP Cloud Run/Cloud SQL deployment for existing Streamlit net worth tracker
**Researched:** 2026-02-17
**Confidence:** MEDIUM (codebase analysis HIGH; deployment specifics MEDIUM — web verification unavailable)

## Executive Summary

This is a deployment and auth milestone layered on a fully working Streamlit net worth tracker. The app's business logic, models, and services are complete. The two remaining concerns are: (1) replacing the hardcoded `TEST_USER_ID` with real Firebase Authentication, and (2) deploying the app to Cloud Run with Cloud SQL as the managed database. Because the app is single-user and personal, the auth implementation is intentionally minimal — no registration UI, no password reset flow, no MFA. The goal is "only I can see my financial data," not SaaS-grade auth hardening.

The recommended approach follows established GCP patterns: Firebase JS SDK in a Streamlit HTML component handles client-side sign-in, the ID token is passed to Python via the component's return value, and `firebase-admin` verifies the token server-side before trusting the UID. Cloud Run connects to Cloud SQL via built-in Unix socket support — no additional connector library is needed, only a URL format change in `DATABASE_URL`. No new Python packages are required; `firebase-admin 7.1.0` is already locked in `uv.lock`.

The primary risk is the token handoff from the Firebase JS SDK to Streamlit Python: `st.components.v1.html()` does not return values by default — the token can silently stay `None` if the component communication is not implemented correctly. The secondary risk is the Cloud SQL Unix socket URL format, which is non-obvious and differs from the local TCP format in a way that produces cryptic container crash-on-startup errors. Both risks are well-understood and have clear mitigations. Overall the scope is tight: ~5 new/modified files for auth, and a deployment config + gcloud commands for Cloud Run.

## Key Findings

### Recommended Stack

No new Python packages are needed. `firebase-admin 7.1.0` is already a locked dependency. The Firebase JS SDK is loaded from the Google CDN at runtime inside the Streamlit HTML component — no npm build step required. The Cloud Run-to-Cloud SQL connection uses psycopg2's Unix socket support, which is built into the already-locked `psycopg2-binary` package.

**Core technologies:**

- Firebase JS SDK 11.x (CDN): Client-side sign-in widget — the only way to run Firebase auth in a Streamlit app; loaded from `gstatic.com` CDN in a `st.components.v1.html` iframe
- firebase-admin 7.1.0 (already locked): Server-side ID token verification — verifies the JWT signature against Firebase's public keys; do not use PyJWT directly
- `st.components.v1.html()`: Streamlit's iframe embed mechanism — the token handoff bridge from JS to Python via `postMessage` + component return value
- psycopg2-binary (already locked): PostgreSQL driver — handles Unix socket connections natively with `?host=/cloudsql/...` in the query string
- GCP Secret Manager: Firebase credentials storage — mounts the service account JSON as a file at Cloud Run deploy time; keeps credentials out of the Docker image

### Expected Features

**Must have (table stakes — v1 launch):**
- Email/password login via Firebase JS SDK HTML component — the auth entry point
- Server-side ID token verification with `firebase-admin` in `app/auth.py`
- Auto-create user record on first verified login (`get_or_create_user()`) — required by FK constraint
- Session persistence in `st.session_state` — survives page reruns, lost on browser close or cold start
- Auth gate in `frontend/main.py` — show login component if no valid session, route to pages otherwise
- Logout button — clears session state; calls Firebase JS `signOut()` via component
- Cloud SQL Unix socket connection — config-only change to `DATABASE_URL` format
- Firebase service account credentials in Cloud Run via Secret Manager
- Cloud Run deployment with correct env vars and `--add-cloudsql-instances` flag

**Should have (v1.x — after production validation):**
- Google Sign-In (OAuth popup) — eliminates password management entirely for a personal tool; same server-side path as email/password, lower risk to add second
- Token refresh handling — Firebase JS SDK's `onAuthStateChanged` re-passing token after cold start reconnects is the key behavior to nail
- Graceful auth error messages — map Firebase error codes to human-readable strings

**Defer (v2+ or skip entirely):**
- Password reset UI — use Firebase Console directly; zero practical benefit for a single developer
- Registration/sign-up flow — unnecessary; account created once in Firebase Console
- Multi-factor authentication — threat model doesn't justify complexity for a personal finance tracker

### Architecture Approach

The architecture is additive: 3 new files (`app/auth.py`, `frontend/auth_component.py`, `frontend/firebase_auth.html`) and modifications to 3 existing files (`frontend/main.py`, `app/config.py`, `Dockerfile`). All existing services, models, and pages are unchanged because they already accept `user_id` as a parameter. The auth gate in `main.py` replaces the `TEST_USER_ID = "test-user"` constant with a check on `st.session_state["user_id"]`; if missing, it renders the Firebase login component and calls `st.stop()` before any page renders.

**Major components:**

1. `frontend/firebase_auth.html` + `frontend/auth_component.py` — Renders Firebase JS SDK login widget in an iframe; on success, `postMessage`s the ID token to the Streamlit parent; Python receives it as the component return value
2. `app/auth.py` — `verify_token(id_token)` calls `firebase_admin.auth.verify_id_token()`; `get_or_create_user(uid, email, display_name, session)` upserts to the `users` table; Firebase Admin app initialized as a singleton with `if not firebase_admin._apps` guard
3. Cloud Run + Cloud SQL Auth Proxy — `--add-cloudsql-instances` flag injects the Unix socket; `DATABASE_URL` switches from TCP (`@db:5432/`) to socket (`@/finance_tracker?host=/cloudsql/...`); `app/database.py` code is unchanged

### Critical Pitfalls

1. **Token never reaches Python via `st.components.v1.html()`** — `html()` is one-way by default; token is silently `None` unless the component properly uses `postMessage` with Streamlit's component bridge. Verify the `html()` return value mechanism against current Streamlit docs; if unreliable, fall back to the Firebase REST API (`identitytoolkit.googleapis.com`) called from Python `requests` — avoids JS entirely.

2. **Cloud SQL Unix socket URL format wrong on Cloud Run** — Wrong format causes container crash before Streamlit starts, producing a misleading health-check timeout. Correct format: `postgresql+psycopg2://USER:PASS@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE`. Verify against `https://cloud.google.com/sql/docs/postgres/connect-run` before executing the deploy.

3. **Firebase Admin SDK initialized multiple times** — Streamlit hot-reload triggers `ValueError: The default Firebase app already exists`. Always guard with `if not firebase_admin._apps: firebase_admin.initialize_app(cred)`. Use the `_get_app()` singleton pattern in `app/auth.py`.

4. **Firebase credentials baked into Docker image** — `COPY . .` in the Dockerfile picks up any `*.json` credentials file present in the project directory. Add `.dockerignore` with `*.json`, `*credentials*`, `.env`, `.git`. Use Secret Manager for credentials in production.

5. **`test-user` data orphaned after auth migration** — Existing accounts/liabilities/snapshots have `user_id = 'test-user'`. The real Firebase UID is different. Write and execute a data migration script (`UPDATE accounts SET user_id='REAL_UID' WHERE user_id='test-user'`) before switching auth in production.

6. **Cold start wipes session state** — Cloud Run scales to zero with `--min-instances=0`; every cold start means users must re-authenticate. Mitigation: design the Firebase JS component so `onAuthStateChanged` re-sends the token from `localStorage` on every page load (Firebase JS SDK persists auth state in `localStorage` by default). This makes re-auth transparent. Alternatively, set `--min-instances=1` (minimal cost for single-user app).

## Implications for Roadmap

Research confirms the existing `plan.md` phase structure is sound. The recommendation is two phases: Firebase Auth (backend + frontend bridge), then Cloud Run deployment (infrastructure + config). The dependency chain is strict: auth backend must exist before the auth UI, and Cloud SQL must exist before Cloud Run deploy.

### Phase 4: Firebase Authentication

**Rationale:** Auth must be complete and tested locally before any deployment work begins. The token handoff mechanism (Pitfall 2) is the highest-risk item in the entire project — it should be isolated and validated in the local docker-compose environment where iteration is fast. All business features already work behind `TEST_USER_ID`; replacing that constant with real auth is the entire scope.

**Delivers:** Working login/logout in local docker-compose; `TEST_USER_ID` removed from `main.py`; `app/auth.py` with Firebase token verification; data migration script ready for Phase 5.

**Addresses:** Email/password login, server-side token verification, auto-create user, session persistence, auth gate, logout button.

**Avoids:** Token-not-reaching-Python pitfall (validate locally before deploy), Firebase Admin double-init pitfall, credentials-in-Docker pitfall (prepare `.dockerignore` and config structure now).

**Build order within phase:**
1. `app/auth.py` — singleton Firebase Admin + `verify_token` + `get_or_create_user`
2. `app/config.py` — add `firebase_project_id`, `firebase_web_api_key` settings
3. Firebase project setup locally (download service account JSON, set `FIREBASE_CREDENTIALS_PATH` in `.env`)
4. `frontend/firebase_auth.html` — standalone HTML/JS widget; test in browser directly first
5. `frontend/auth_component.py` — wraps HTML in `st.components.v1.html()`, calls `app/auth.py`
6. `frontend/main.py` — remove `TEST_USER_ID`, add auth gate pattern
7. Data migration script — `UPDATE` all tables from `test-user` to real Firebase UID

**Research flag:** NEEDS VERIFICATION — the `st.components.v1.html()` return value mechanism for passing the ID token from JS to Python must be verified against current Streamlit docs before committing to this pattern. If it does not work as expected, the fallback is the Firebase REST API called from Python (`requests.post` to `identitytoolkit.googleapis.com`), which avoids JS components entirely.

### Phase 5: Cloud Run Deployment

**Rationale:** Deployment is pure infrastructure configuration — no Python code changes to business logic. The only code changes are the Dockerfile `CMD` flags and the `DATABASE_URL` format in environment variables. All IAM, Secret Manager, and Cloud Run flags must be executed in dependency order; getting any step wrong produces errors that are hard to debug remotely.

**Delivers:** App running on Cloud Run, accessible via HTTPS, connected to Cloud SQL, Firebase auth working in production, all `test-user` data migrated to real Firebase UID.

**Addresses:** Cloud SQL Unix socket connection, Firebase credentials via Secret Manager, Cloud Run deployment config, health check path, cold start behavior.

**Avoids:** Wrong Unix socket URL format (Pitfall 3), credentials in Docker image (Pitfall 5), test-user data orphaned (Pitfall 7), over-privileged service account.

**Build order within phase:**
1. Cloud SQL instance creation + database + user
2. Cloud Run service account + minimal IAM roles (Cloud SQL Client, Secret Manager Secret Accessor)
3. Secret Manager secret for Firebase credentials JSON
4. Dockerfile modification (add `--server.enableCORS=false`, `--server.enableXsrfProtection=false` if needed)
5. `.dockerignore` — exclude `.env`, `*.json`, `.git`
6. `gcloud builds submit` + `gcloud run deploy` with `--add-cloudsql-instances`, `--set-secrets`, `--set-env-vars`
7. Execute data migration script against Cloud SQL
8. Smoke test: verify login, verify data visible, verify logout

**Research flag:** VERIFY BEFORE EXECUTING — Cloud SQL Unix socket URL format (`postgresql+psycopg2://` vs `postgresql://` dialect prefix) and the exact `gcloud run deploy` flag names for `--set-secrets` and `--add-cloudsql-instances` should be confirmed against official GCP docs before running deploy commands. A wrong URL format crashes the container with a misleading health-check error.

### Phase Ordering Rationale

- Auth must precede deployment: the auth gate in `main.py` must exist before the app is exposed on a public Cloud Run URL. Deploying without auth means anyone with the URL can view your financial data.
- Firebase Admin backend (`app/auth.py`) must precede the frontend bridge (`auth_component.py`): the component imports and calls `app/auth`.
- Data migration script must be written in Phase 4 and executed in Phase 5 before any traffic reaches the Firebase-auth-enabled app: the window between deploy and migration is a data-visibility gap.
- No Google Sign-In until email/password is confirmed working in production: same server-side path but adds JS complexity; validate the baseline first.

### Research Flags

Phases likely needing deeper verification during implementation:

- **Phase 4 — `st.components.v1.html()` return value:** The postMessage-to-Python bridge is the highest-uncertainty technical point in the project. Verify with a minimal proof-of-concept (HTML that sends a string to Python via the component) before building the full auth widget. If it fails, use the Firebase REST API fallback.
- **Phase 5 — Cloud SQL Unix socket + gcloud flags:** MEDIUM confidence from training knowledge. The URL format and exact `gcloud run deploy` flag syntax should be confirmed against `cloud.google.com/sql/docs/postgres/connect-run` and `cloud.google.com/run/docs/reference/rest` before the deploy command is constructed.
- **Phase 4 — Streamlit CORS/XSRF flags in Dockerfile:** LOW confidence that `--server.enableCORS=false --server.enableXsrfProtection=false` are required. Test the Cloud Run deployment without these flags first; add them only if the auth component's postMessage is blocked.

Phases with standard patterns (no additional research needed):

- **Phase 4 — Firebase Admin SDK singleton and `verify_id_token()`:** Well-established pattern; code in ARCHITECTURE.md is directly usable.
- **Phase 4 — `get_or_create_user()` and auth gate in `main.py`:** Standard Streamlit session state pattern; straightforward given the existing codebase structure.
- **Phase 5 — Secret Manager setup and IAM roles:** Standard GCP pattern; well-documented.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | firebase-admin 7.1.0 confirmed from uv.lock; no new packages needed; CDN URL from gstatic.com is stable |
| Features | HIGH | Derived from direct codebase inspection + plan.md (author intent); feature scope is small and well-defined |
| Architecture | MEDIUM | Codebase analysis is HIGH; `st.components.v1.html()` postMessage return value mechanism is MEDIUM — needs verification against current Streamlit docs |
| Pitfalls | MEDIUM | Patterns are well-established; specific Cloud Run socket path format and gcloud flag syntax need verification against current docs |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **`st.components.v1.html()` bidirectional communication:** Verify that the component's `postMessage` to `window.parent` is reliably captured as the Python return value in current Streamlit 1.53.1. If not, the fallback (Firebase REST API from Python) is the correct path — document the decision before implementing the HTML widget.
- **Cloud SQL Unix socket dialect prefix:** Confirm whether `postgresql://` or `postgresql+psycopg2://` is required for Unix socket connections in SQLAlchemy with psycopg2. The research suggests `postgresql+psycopg2://` is more explicit and reliable; verify before constructing the production `DATABASE_URL`.
- **Streamlit `/_stcore/health` endpoint:** Verify it exists in Streamlit 1.53.1 (introduced ~v1.12). Cloud Run's default health check on `/` also works; this is a low-risk gap.
- **`--server.enableCORS=false` requirement:** Test without this flag first. Only add it if the auth component fails in production — adding it prematurely masks potential issues.

## Sources

### Primary (HIGH confidence)

- `/Users/kristiakarakatsani/Repos/finance-tracker/uv.lock` — firebase-admin 7.1.0, all google-* transitive deps confirmed
- `/Users/kristiakarakatsani/Repos/finance-tracker/pyproject.toml` — dependency declarations
- `/Users/kristiakarakatsani/Repos/finance-tracker/frontend/main.py` — existing auth structure and TEST_USER_ID location
- `/Users/kristiakarakatsani/Repos/finance-tracker/app/models.py` — User.id is Firebase UID VARCHAR 128
- `/Users/kristiakarakatsani/Repos/finance-tracker/app/database.py` — engine creation pattern
- `/Users/kristiakarakatsani/Repos/finance-tracker/plan.md` — author's Phase 4/5 implementation intent

### Secondary (MEDIUM confidence)

- Firebase JS SDK CDN (gstatic.com) — Firebase 11.3.1 module imports; pin version at implementation time
- `st.components.v1.html()` postMessage pattern — community-established Streamlit auth pattern; verify against Streamlit 1.53.1 docs
- Cloud Run + Cloud SQL Unix socket pattern — canonical GCP architecture; verify URL format before deploy
- Firebase Admin SDK singleton initialization guard — official SDK design pattern

### Tertiary (LOW confidence — verify before use)

- `--server.enableCORS=false --server.enableXsrfProtection=false` Dockerfile flags — frequently cited in community but not officially documented as required for Cloud Run
- `gcloud run deploy` exact flag syntax for `--set-secrets` and `--add-cloudsql-instances` — verify against current gcloud CLI docs

---
*Research completed: 2026-02-17*
*Ready for roadmap: yes*
