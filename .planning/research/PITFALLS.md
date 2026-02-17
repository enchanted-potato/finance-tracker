# Pitfalls Research

**Domain:** Firebase Auth + Cloud Run/Cloud SQL deployment for Streamlit app
**Researched:** 2026-02-17
**Confidence:** MEDIUM-HIGH (based on well-established patterns; WebSearch/WebFetch unavailable for verification)

---

## Critical Pitfalls

### Pitfall 1: `st.session_state["user_id"]` Unconditionally Overwritten on Every Rerun

**What goes wrong:**
The current `main()` runs `st.session_state["user_id"] = TEST_USER_ID` on every Streamlit rerun. When replacing this with Firebase auth, if the assignment remains unconditional (even just the structure of "set if not in session"), the token verification runs on every rerun, not once. The opposite failure — placing the auth check inside an `if "user_id" not in st.session_state` guard — means the token is only verified once and never re-checked, so a revoked Firebase token stays valid in the session until the server restarts.

**Why it happens:**
Developers copy the pattern from the TEST_USER_ID line. The fix looks obvious ("just guard with `if not in session_state`"), but this skips token re-verification on every rerun. Streamlit reruns the entire script on every widget interaction; auth state must be stored, not re-fetched, but must also be invalidatable.

**How to avoid:**
Store the raw Firebase ID token in `st.session_state["firebase_token"]` and the resolved `user_id` in `st.session_state["user_id"]`. On each rerun, check if `"firebase_token"` is present and not expired (check `exp` claim, which is a Unix timestamp). Re-verify with Firebase Admin SDK only when the token is near expiry (Firebase ID tokens expire in 1 hour) or missing. Never re-verify on every single rerun (expensive network call).

**Warning signs:**
- Auth works on first login, then randomly fails after interactions
- "Logged out" after clicking any widget
- Token verification appearing in Streamlit profiler on every rerun

**Phase to address:** Phase 4 (Firebase Authentication)

---

### Pitfall 2: Firebase JS SDK Token Not Reliably Passed to Python

**What goes wrong:**
The plan uses `frontend/firebase_auth.html` (an HTML/JS component via `st.components.v1.html`) for the Firebase JS SDK login widget. The JS SDK signs in the user and gets an ID token, but passing it to Python session state is non-trivial. `st.components.v1.html` renders in an iframe; data returned from the component requires `st.components.v1.declare_component` with bidirectional communication, not `st.components.v1.html`. Using `html()` means the token never reaches Python — the component is one-way.

**Why it happens:**
`st.components.v1.html` is used for embedding static HTML. Developers assume JavaScript running inside it can write to `st.session_state` directly — it cannot. Only declared components with a return value can pass data back to Python.

**How to avoid:**
Use `st.components.v1.declare_component` with a proper React/JS component, OR use a simpler pattern: render a Firebase login button in the iframe, have it call `window.parent.postMessage({token: idToken}, "*")` after sign-in, then capture it with `st.components.v1.html` + a parent-frame listener. The most reliable approach for Streamlit is to use `streamlit-javascript` library (if available) or declare a proper component with `_component_func` that returns the token as its value.

Alternative approach: skip the Firebase JS SDK entirely for the UI flow. Use Firebase REST API (`identitytoolkit.googleapis.com`) called from a Streamlit form (Python `requests`), verify server-side, never touch JS components.

**Warning signs:**
- Login button works visually but `st.session_state` never receives the token
- `st.components.v1.html` component return value is always `None`
- No `st.rerun()` triggering after login

**Phase to address:** Phase 4 (Firebase Authentication)

---

### Pitfall 3: Cloud SQL Unix Socket Connection String Format

**What goes wrong:**
Cloud Run connects to Cloud SQL via Unix sockets, not TCP. The socket path format for psycopg2 is `postgresql://USER:PASS@/DB?host=/cloudsql/PROJECT:REGION:INSTANCE`. The `host` parameter goes in the query string, not the netloc. Using TCP format (`postgresql://USER:PASS@PRIVATE_IP:5432/DB`) fails because the Cloud SQL instance is not directly reachable via IP without VPC configuration. Using the wrong socket path (`/cloudsql/INSTANCE_CONNECTION_NAME` vs `postgresql+pg8000://...`) produces cryptic errors.

**Why it happens:**
Local dev uses `postgresql://finance:finance@db:5432/finance_tracker` (TCP). Developers copy this and just change the host, rather than switching to the Unix socket format. The current `.env.example` only shows TCP format — no Unix socket example exists.

**How to avoid:**
Set `DATABASE_URL` in Cloud Run environment to: `postgresql+psycopg2://USER:PASS@/DBNAME?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME`. Enable Cloud SQL Admin API. Add the Cloud SQL instance to the Cloud Run service with `--add-cloudsql-instances PROJECT_ID:REGION:INSTANCE_NAME`. Use `--set-env-vars DATABASE_URL=...` or Secret Manager.

The `app/database.py` currently creates the engine at module import time from `settings.database_url`. The Unix socket path must be correct at startup — a wrong path causes an engine creation error that crashes the container before Streamlit even starts, making the Cloud Run health check fail with a misleading timeout error.

**Warning signs:**
- Cloud Run container exits with code 1 immediately after deploy
- `gcloud run services describe` shows health check failures
- Local `docker-compose up` works but Cloud Run does not

**Phase to address:** Phase 5 (Cloud Deployment)

---

### Pitfall 4: Firebase Admin SDK Initialized Multiple Times (Streamlit Rerun Issue)

**What goes wrong:**
Firebase Admin SDK raises `ValueError: The default Firebase app already exists` if `firebase_admin.initialize_app()` is called more than once without checking. In a Streamlit app, the module-level code in `app/auth.py` runs each time the module is imported — but Python caches module imports so it only runs once per process. However, during development with `runOnSave = true` (which this project has in `.streamlit/config.toml`), Streamlit restarts the Python process on file changes, which can trigger re-initialization. In production, multiple Cloud Run instances run as separate processes (safe), but hot-reloading scenarios fail.

**Why it happens:**
`firebase_admin.initialize_app()` is placed at module level without the standard guard: `if not firebase_admin._apps: firebase_admin.initialize_app(...)`. Developers write it as a simple call and it works until a file changes trigger a rerun mid-session.

**How to avoid:**
Always guard initialization: `if not firebase_admin._apps: firebase_admin.initialize_app(cred)`. Place the initialization in a function that is called lazily (or at `main()` startup in `frontend/main.py` inside the `if "db_initialized" not in st.session_state` block — but only for non-Streamlit code). Better: create an `app/auth.py` module-level singleton that initializes once using the guard pattern.

**Warning signs:**
- `ValueError: The default Firebase app already exists` in Streamlit logs
- Error occurs after saving a file while the app is running
- Works after full server restart, fails on hot reload

**Phase to address:** Phase 4 (Firebase Authentication)

---

### Pitfall 5: Firebase Service Account JSON in Container — Secret Leakage

**What goes wrong:**
The `app/config.py` reads `firebase_credentials_path: str` pointing to a JSON file. Copying the Firebase service account JSON into the Docker image (via `COPY credentials.json .`) bakes secrets into the container layer permanently. Even if the file is later deleted, it remains in the layer history. The current `Dockerfile` copies everything with `COPY . .` — if `firebase-credentials.json` is present in the project directory, it gets baked in.

**Why it happens:**
Easiest approach during development is to put the credentials file in the project directory and reference it by path. The `.gitignore` exists but may not cover all credential file names. `COPY . .` in the Dockerfile doesn't respect `.gitignore`.

**How to avoid:**
Use Secret Manager, not a file path. Store the Firebase credentials JSON as a Secret Manager secret. Mount it as a volume in Cloud Run (`--update-secrets=/secrets/firebase-credentials.json=FIREBASE_CREDENTIALS:latest`) or read the JSON content directly from an environment variable. Change `app/config.py` to support `FIREBASE_CREDENTIALS_JSON` (the JSON content as a string) as an alternative to `FIREBASE_CREDENTIALS_PATH`. Add `*.json` and `*credentials*` and `*service-account*` to `.dockerignore`.

**Warning signs:**
- Credentials file found in `docker history IMAGE_ID`
- `COPY . .` in Dockerfile without a `.dockerignore`
- `FIREBASE_CREDENTIALS_PATH` pointing to a relative path like `./credentials.json`

**Phase to address:** Phase 5 (Cloud Deployment) — but the config structure should be prepared in Phase 4

---

### Pitfall 6: Cloud Run Cold Starts Wipe `st.session_state` (Users Logged Out)

**What goes wrong:**
`st.session_state` is in-memory, process-local. When Cloud Run scales to zero and a new instance starts (cold start), all session state is gone. Users who were "logged in" are silently logged out. The Firebase ID token, stored in `st.session_state["firebase_token"]`, is lost. The user must log in again. Since Cloud Run free tier scales to zero after inactivity, this happens frequently for a personal app.

**Why it happens:**
Streamlit session state is browser-session-coupled to a specific server process via WebSocket. When the process dies (cold start), the WebSocket reconnects to a new process with empty state. The browser still has the Firebase token in localStorage (from the JS SDK), but Streamlit's Python side has no knowledge of it.

**How to avoid:**
Two mitigations:
1. Set Cloud Run `--min-instances=1` to prevent scale-to-zero (incurs cost but minimal for free tier).
2. Design the auth flow so the Firebase JS component always reads the token from localStorage on page load and re-sends it to Python, even on reconnect. Firebase JS SDK `onAuthStateChanged` callback should trigger on reconnect and re-pass the token.

This is the strongest argument for using the Firebase JS SDK approach (token is persisted in browser localStorage by the SDK) rather than REST API calls from Python.

**Warning signs:**
- User is logged out after 10+ minutes of inactivity
- Log shows new container instance starting
- "Please log in" shown after a successful previous session without explicit logout

**Phase to address:** Phase 4 (design) + Phase 5 (Cloud Run min-instances config)

---

### Pitfall 7: Migrating `test-user` Data — FK Constraint Failures

**What goes wrong:**
The existing database has accounts, liabilities, and snapshots with `user_id = "test-user"`. The `users` table has `User(id="test-user", ...)`. When Firebase auth is added, the real user gets a Firebase UID (e.g., `"abc123xyz"`). Running `get_or_create_user()` creates a new user row with the Firebase UID. The `test-user` data is now orphaned — it doesn't show up because pages query by `st.session_state["user_id"]` which is now the Firebase UID.

**Why it happens:**
The schema already supports the Firebase UID format (VARCHAR 128 PK), so no schema migration is needed. But the data migration (updating existing rows from `test-user` to the real Firebase UID) is easy to forget. It's not part of schema migration; it's a data migration that must be done manually or via a one-time script.

**How to avoid:**
Write a one-time migration script before switching auth: `UPDATE accounts SET user_id = 'REAL_UID' WHERE user_id = 'test-user'` (and same for liabilities, snapshots, account_types where user_id is not NULL). Run this script against the production Cloud SQL instance before deploying the Firebase-auth-enabled version. Test the script locally with a copy of production data.

**Warning signs:**
- After login with real Firebase account, "No accounts yet" even though accounts exist
- Database has rows but all have `user_id = 'test-user'`
- `select * from accounts where user_id = 'REAL_FIREBASE_UID'` returns empty

**Phase to address:** Phase 4 (prepare migration script) + Phase 5 (execute before deploy)

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip token expiry check in session state | Simpler auth code | Users stay "logged in" with expired tokens; Firebase Admin SDK returns error on verification | Never — add expiry check |
| Copy Firebase JSON into Docker image | Easy local→prod parity | Credentials in image layers, security risk | Never |
| No `.dockerignore` | Simpler setup | Credentials, `.env`, `.git` all in image | Never |
| `--min-instances=0` (default scale-to-zero) | Free tier cost savings | Frequent cold starts logging users out | Acceptable if JS SDK re-passes token on reconnect |
| Verify Firebase token on every Streamlit rerun | Simple logic | Latency per rerun; Firebase Admin SDK network calls on every widget interaction | Never — verify once, cache with expiry |
| Use `st.components.v1.html` for token passing | Quick to implement | Token never reaches Python; silent failure | Never — use declared component or REST API |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Cloud SQL via psycopg2 on Cloud Run | TCP connection string (`host=IP:5432`) | Unix socket: `?host=/cloudsql/PROJECT:REGION:INSTANCE` in query string |
| Firebase Admin SDK | `firebase_admin.initialize_app()` without guard | `if not firebase_admin._apps: initialize_app(cred)` |
| Firebase Admin SDK | Reading credentials from file path in container | Mount via Secret Manager or use `Certificate` from JSON string in env var |
| Cloud Run secrets | Setting `DATABASE_URL` as plain env var in console | Use Secret Manager + `--update-secrets` for credentials; `DATABASE_URL` with socket path as env var is OK |
| Cloud Run + Cloud SQL | Forgetting `--add-cloudsql-instances` flag | Include `--add-cloudsql-instances PROJECT:REGION:INSTANCE` in `gcloud run deploy` |
| Streamlit + Firebase JS SDK | Using `st.components.v1.html` expecting return value | Use `st.components.v1.declare_component` for bidirectional data flow |
| Streamlit server-level XSRF | Default XSRF protection blocks custom component posts | Set `server.enableXsrfProtection = false` in config.toml only if custom components need it (evaluate risk for single-user app) |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Firebase token verification on every rerun | 200-500ms latency per widget interaction | Cache verified token in session state with expiry | Immediately on first interaction |
| Engine creation per request (if moved inside request) | New connection pool on every page load | Keep `engine` module-level singleton (already correct in `database.py`) | Immediately — pool exhaustion |
| `next(get_session())` without context manager | Session leak if exception before `session.close()` | Use `with Session(engine) as session:` pattern consistently | Under error conditions |
| Cloud SQL connection pool exhaustion | `OperationalError: connection pool exhausted` | `db-f1-micro` max 25 connections; set `pool_size=2, max_overflow=3` on engine | With multiple Cloud Run instances |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Trusting `user_id` from `st.session_state` without verifying it came from token verification | Any user who can modify session state (impossible normally, but indicates code smell) | Always derive `user_id` from verified Firebase token, not from session state that was set by non-auth code |
| Not validating Firebase ID token `aud` claim | Tokens from different Firebase projects accepted | Firebase Admin SDK `verify_id_token()` checks `aud` automatically — but only if initialized with the correct project credentials |
| Service account with Owner/Editor role | Credential theft gives full GCP access | Use minimal IAM roles: Cloud SQL Client + Secret Manager Secret Accessor only |
| Streamlit app accessible without auth (no auth gate) | Data exposed if auth check is bypassed | Auth gate must be in `main()` before any page render, not inside individual pages |
| Firebase credentials path logged | Credential location exposed in logs | Don't log `settings.firebase_credentials_path`; loguru may log all settings if `__repr__` is called |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No loading state during Firebase token verification | Blank page flash on every rerun while token is verified | Show `st.spinner("Verifying session...")` during verification |
| Login page re-renders the full Streamlit app on each rerun | Firebase login form flickers on every rerun | Keep login page minimal — no widgets that trigger reruns until token is acquired |
| No feedback on token expiry | User interacts with app, gets cryptic error when token expires | Catch `firebase_admin.auth.ExpiredIdTokenError`, clear session state, redirect to login with message |
| `st.rerun()` after login causes double page load | Slight jank at login | Expected and acceptable; unavoidable in Streamlit auth flow |

---

## "Looks Done But Isn't" Checklist

- [ ] **Firebase Auth Gate:** Auth check is in `main()` before page routing — verify it cannot be bypassed by navigating directly to a page function
- [ ] **Token Expiry:** Session state includes token expiry time and is re-verified before each session block — verify with a 1-hour-old token
- [ ] **Cloud SQL Connection:** Unix socket path is correct format — verify `SELECT 1` works in production after deploy, not just in local docker-compose
- [ ] **Data Migration:** All existing `test-user` rows updated to real Firebase UID — verify with `SELECT COUNT(*) FROM accounts WHERE user_id = 'test-user'` returns 0 after migration
- [ ] **Firebase Admin SDK Guard:** `if not firebase_admin._apps` guard in place — verify by triggering a file-save hot reload during development
- [ ] **Secret Management:** No credentials in Docker image — verify with `docker history IMAGE` showing no credential files
- [ ] **Dockerignore:** `.dockerignore` excludes `.env`, `*.json` credential files, `.git` — verify image size and contents
- [ ] **Account Types Seed Data:** `seed_default_types()` correctly handles NULL `user_id` rows (global defaults) — verify real user sees them after migration (they should, since `user_id IS NULL`)

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Test-user data orphaned after auth migration | LOW | Run UPDATE script: `UPDATE accounts SET user_id='REAL_UID' WHERE user_id='test-user'`; repeat for all tables |
| Firebase credentials baked into image | MEDIUM | Rotate service account key in GCP Console, redeploy with secret-managed credentials, invalidate old key |
| Wrong Cloud SQL connection string on Cloud Run | LOW | Update Cloud Run env var, redeploy; no data loss |
| Firebase Admin SDK double-init error | LOW | Add `if not firebase_admin._apps` guard, redeploy |
| Users logged out on cold start | LOW | Configure `--min-instances=1` on Cloud Run service |
| Token passed from JS never reaches Python | MEDIUM | Rewrite auth component using `declare_component` or switch to REST API approach; requires Phase 4 rework |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| session_state["user_id"] overwritten unconditionally | Phase 4 (Firebase Auth) | Auth state survives page navigation without re-login |
| Firebase JS token not passed to Python | Phase 4 (Firebase Auth) | Login sets session_state["firebase_token"] with non-None value |
| Firebase Admin SDK double-init | Phase 4 (Firebase Auth) | Save a file while logged in — no `ValueError` in logs |
| Cloud SQL Unix socket connection string | Phase 5 (Cloud Deployment) | `SELECT 1` succeeds against Cloud SQL from Cloud Run |
| Firebase credentials in Docker image | Phase 4 (config) + Phase 5 (deploy) | `docker history` shows no credential files |
| Cold start session loss | Phase 5 (Cloud Deployment) | Idle 15 min, reconnect, verify token re-passed by JS SDK |
| test-user data migration | Phase 4 (write script) + Phase 5 (execute) | Zero rows with `user_id = 'test-user'` in production after deploy |
| Service account over-privileged | Phase 5 (Cloud Deployment) | IAM policy shows only `cloudsql.client` + `secretmanager.secretAccessor` |

---

## Sources

- Codebase analysis: `/Users/kristiakarakatsani/Repos/finance-tracker/` (HIGH confidence — direct inspection)
- Firebase Admin Python SDK behavior: training data + official SDK design (MEDIUM confidence — well-established patterns)
- Cloud SQL + Cloud Run Unix socket connection: training data on Cloud SQL Python connector + psycopg2 integration (MEDIUM confidence — verify against official `connect-run` docs during Phase 5)
- Streamlit session state + component architecture: training data + Streamlit docs design (MEDIUM confidence — verify `declare_component` bidirectional flow pattern)
- WebSearch/WebFetch unavailable during research session — flag Cloud Run socket path format for manual verification against `https://cloud.google.com/sql/docs/postgres/connect-run` before Phase 5

---
*Pitfalls research for: Firebase Auth + Cloud Run/Cloud SQL deployment on existing Streamlit app*
*Researched: 2026-02-17*
