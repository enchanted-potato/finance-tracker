# Feature Research

**Domain:** Firebase Auth + Cloud Run Deployment for Single-User Streamlit App
**Researched:** 2026-02-17
**Confidence:** MEDIUM — WebSearch and WebFetch unavailable; findings derived from existing codebase evidence, plan.md, and training knowledge. All claims flagged with confidence level.

---

## Context

This is a **subsequent milestone** layered on top of a fully working Streamlit net worth tracker. The existing app has all business features built (dashboard, accounts, liabilities, history, configure pages, all services, tests). This research covers only what's needed to add auth and deploy.

The app is **single-user, personal use**. That constraint drives every decision: what's table stakes is what makes the app usable in production, not what multi-user SaaS products need.

---

## Feature Landscape

### Table Stakes (Must Work for Production)

Features required for the app to be usable when deployed. Missing any of these = the app is broken for its single purpose.

| Feature | Why Required | Complexity | Notes |
|---------|--------------|------------|-------|
| Email/password login | User must authenticate to reach the app | MEDIUM | Firebase JS SDK `signInWithEmailAndPassword`. ID token returned to Streamlit via `st.components.v1.html` + query param or JS→Python bridge |
| ID token verification (server-side) | Streamlit runs Python server-side; the token from the browser must be verified before trusting any user_id | LOW | `firebase-admin` SDK already in dependencies. `auth.verify_id_token(token)` returns decoded token with `uid`, `email`. One function in `app/auth.py` |
| Session persistence across page reruns | Streamlit reruns the entire script on every interaction; user must not be logged out on each rerun | LOW | Store verified `user_id` and `id_token` in `st.session_state`. Already established pattern in the codebase (`st.session_state["user_id"]`) |
| Logout button | User must be able to end their session | LOW | Clear `st.session_state` keys; call Firebase JS `signOut()` via component |
| Auto-create user record on first login | `users` table needs a row with the Firebase UID before any account/liability can be saved (FK constraint) | LOW | `get_or_create_user()` in `app/auth.py` using the token's `uid`, `email`, `display_name`. Already planned in plan.md |
| Cloud Run environment variables | `DATABASE_URL` and Firebase credentials must reach the container at runtime | LOW | `--set-env-vars` flag on `gcloud run deploy`, or Secret Manager mount. DATABASE_URL uses Unix socket format for Cloud SQL |
| Cloud SQL connection via Unix socket | Cloud Run connects to Cloud SQL via `/cloudsql/INSTANCE_CONNECTION_NAME` socket (not TCP). Requires Cloud SQL proxy sidecar or built-in connector | MEDIUM | DATABASE_URL format: `postgresql+psycopg2://user:password@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE`. The Cloud Run service account needs `Cloud SQL Client` IAM role |
| Firebase service account credentials in Cloud Run | `firebase-admin` needs credentials to verify tokens. `FIREBASE_CREDENTIALS_PATH` points to a JSON file — in Cloud Run this becomes a Secret Manager secret mounted as a file | MEDIUM | Alternative: set `GOOGLE_APPLICATION_CREDENTIALS` env var if running on GCP with Workload Identity; or mount secret as file. Secret Manager is the correct approach for Cloud Run |
| Health check compatibility | Cloud Run sends health checks to determine if container is ready. Streamlit's `/_stcore/health` endpoint responds to these | LOW | No code change needed — Streamlit exposes `/_stcore/health` by default. Cloud Run default HTTP health check on `/` also works since Streamlit returns 200 |
| Startup DB init on cold start | Cloud Run starts from zero; `SQLModel.metadata.create_all(engine)` and seed must run on each container start | LOW | Already handled in `_init_db()` in `frontend/main.py` — it runs once per Streamlit session via `st.session_state["db_initialized"]`. Cloud Run cold start triggers this naturally on first request |

### Differentiators (Valuable for Single-User Personal App)

Features that aren't strictly required but meaningfully improve the experience for someone running this for themselves.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Google Sign-In (OAuth) | Eliminates password management entirely for a personal tool — just click "Sign in with Google" | MEDIUM | Firebase JS SDK `signInWithPopup(new GoogleAuthProvider())`. Requires enabling Google provider in Firebase console. The Python server-side is identical — same token verification. Main complexity is the HTML/JS component |
| "Remember me" / persistent token across browser sessions | Don't have to log in every time the browser is opened | LOW | Firebase JS SDK defaults to `browserLocalStorage` persistence — tokens survive browser restarts automatically. No extra code needed once login works |
| Display user email/name in sidebar | Confirms who is logged in — reassuring for a personal tool | LOW | Token's `email` and `display_name` fields are already stored in `users` table and `st.session_state`. Sidebar already shows a logged-in name (currently hardcoded `TEST_USER_NAME`) |
| Token refresh handling | Firebase ID tokens expire after 1 hour. Long browser sessions need auto-refresh | MEDIUM | Firebase JS SDK handles refresh automatically client-side. The Streamlit component re-fetches a fresh `getIdToken(true)` before sending. Needs careful implementation to avoid re-triggering login on every rerun |
| Graceful auth error messages | Clear errors for wrong password vs account not found vs network failure | LOW | Firebase error codes (`auth/wrong-password`, `auth/user-not-found`) map to human messages in the JS component |

### Anti-Features (Skip These Entirely)

Features that seem reasonable but are wrong for this project's constraints.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Password reset email flow | Standard auth feature — users expect it | This is a personal single-user app. The user is the developer. Password reset requires configuring Firebase's email delivery (custom SMTP or Firebase's own quota-limited delivery). That's infrastructure complexity for zero practical benefit — if you forget your password, reset it directly in the Firebase Console in 30 seconds | Skip. If needed, add a note in the app: "Reset password at console.firebase.google.com" |
| Sign-up / registration UI | Multi-user apps need this | Single user. The one account is created manually in the Firebase Console once. A registration form in the app adds code, tests, and a UI flow that will be used exactly zero times after setup | Create the Firebase account once in the Console. Remove `signUp` from the login component scope |
| Email verification enforcement | Security best practice for SaaS | Adds complexity (blocking UI if unverified, verification email delivery). For a personal app accessed only by you, email verification is security theater | Skip |
| Multi-factor authentication | Strong security feature | Firebase MFA requires phone number setup, TOTP, or other second factor. For a personal finance tracker on Cloud Run, the threat model doesn't justify the session management complexity | Skip for now. Can be enabled in Firebase Console if threat model changes |
| Session expiry / forced re-login timer | Security hardening | Firebase ID tokens expire in 1 hour, but the JS SDK silently refreshes them. Imposing an additional server-side expiry (e.g., 24h `st.session_state` timeout) creates annoying UX with no proportional security benefit for a single-user personal tool | Rely on Firebase's built-in token lifecycle |
| JWT stored in URL params long-term | Sometimes seen as a workaround for Streamlit component → Python communication | ID tokens in URLs appear in browser history, server logs, referrer headers. Security anti-pattern | Use `st.query_params` for the one-time token handoff only, then immediately clear it. Store the verified `user_id` (not the raw token) in `st.session_state` |

---

## Feature Dependencies

```
[Cloud SQL Unix socket connection]
    └──requires──> [Cloud SQL Client IAM role on Cloud Run service account]
    └──requires──> [DATABASE_URL with socket path, not TCP]

[firebase-admin token verification]
    └──requires──> [Firebase credentials in Cloud Run]
                       └──requires──> [Secret Manager secret created]
                       └──requires──> [Secret accessor IAM role on Cloud Run service account]

[auto-create user on first login]
    └──requires──> [firebase-admin token verification] (need uid, email from decoded token)
    └──requires──> [Cloud SQL connection working] (need DB to write to)

[Google Sign-In]
    └──requires──> [email/password login working first] (same token verification path, lower risk to add second)
    └──enhances──> [persistent session] (OAuth tokens refresh more reliably)

[token refresh handling]
    └──requires──> [email/password login working] (base auth flow must be solid first)

[logout button]
    └──requires──> [login working] (trivial dependency)
```

### Dependency Notes

- **Cloud SQL connection requires Unix socket path:** The DATABASE_URL format changes from `postgresql://user:pass@host:5432/db` (local TCP) to `postgresql+psycopg2://user:pass@/db?host=/cloudsql/PROJECT:REGION:INSTANCE` (Cloud Run socket). This is a config-only change but must happen before any Cloud Run deployment works.
- **Firebase credentials require Secret Manager:** Mounting a service account JSON file into Cloud Run is done via Secret Manager (not file copy in Dockerfile, which would leak credentials). The Cloud Run service account needs `Secret Manager Secret Accessor` role.
- **User auto-creation must precede any page render:** If `get_or_create_user()` fails (DB not connected, credentials wrong), every page will fail with FK violation. Validate this in the auth gate before routing to any page.

---

## MVP Definition

### Launch With (v1 — what makes the app work in production)

- [ ] Email/password login via Firebase JS SDK in Streamlit HTML component — the only way in
- [ ] Server-side ID token verification with `firebase-admin` (`app/auth.py`)
- [ ] Auto-create user record on first verified login (`get_or_create_user()`)
- [ ] Session persistence via `st.session_state` (survives page reruns, lost on browser close)
- [ ] Logout button clearing session state
- [ ] Auth gate in `frontend/main.py` — show login component if no valid session, else route to pages
- [ ] Cloud SQL connection via Unix socket with correct DATABASE_URL format
- [ ] Firebase service account credentials in Cloud Run via Secret Manager (mounted as file)
- [ ] Cloud Run deployment with `DATABASE_URL` and `FIREBASE_CREDENTIALS_PATH` env vars set
- [ ] Verify `/_stcore/health` is used as Cloud Run health check path (avoids slow startup false-positive kills)

### Add After Validation (v1.x — once the app is running in production)

- [ ] Google Sign-In — add `signInWithPopup` to the login component once email/password confirmed working. Same server-side path, lower risk to add second.
- [ ] Token refresh handling — implement `getIdToken(true)` force-refresh in the JS component to handle sessions that exceed 1 hour without page reload
- [ ] Graceful auth error messages — map Firebase error codes to human-readable strings in the login component

### Future Consideration (v2+ — not worth the effort for single-user personal tool)

- [ ] Password reset UI — use Firebase Console directly; not worth building
- [ ] Multi-factor authentication — revisit if threat model changes
- [ ] Sign-up/registration flow — unnecessary for single-user app

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Email/password login (Firebase JS component) | HIGH | MEDIUM | P1 |
| Server-side token verification | HIGH | LOW | P1 |
| Auto-create user on login | HIGH | LOW | P1 |
| Session persistence in st.session_state | HIGH | LOW | P1 |
| Logout button | HIGH | LOW | P1 |
| Auth gate in main.py routing | HIGH | LOW | P1 |
| Cloud SQL Unix socket connection | HIGH | MEDIUM | P1 |
| Firebase credentials via Secret Manager | HIGH | MEDIUM | P1 |
| Cloud Run deployment config | HIGH | LOW | P1 |
| Health check path configuration | MEDIUM | LOW | P1 |
| Google Sign-In | MEDIUM | MEDIUM | P2 |
| Token refresh (1-hour expiry handling) | MEDIUM | MEDIUM | P2 |
| Graceful error messages in login UI | LOW | LOW | P2 |
| Password reset UI | LOW | HIGH | P3 (skip) |
| Registration/sign-up UI | NONE | MEDIUM | P3 (skip) |

---

## Single-User Constraint Analysis

The single-user nature of this app directly simplifies auth requirements in ways that are easy to overlook:

**What simplifies:**
- No registration UI — account created once in Firebase Console
- No password reset UI — done in Firebase Console
- No email verification enforcement — you know who you are
- No multi-tenant data isolation logic — all data already keyed by `user_id`, but there's only ever one
- No rate limiting on login attempts — personal tool, not public-facing auth endpoint
- No admin panel — there's no one to administer

**What remains necessary:**
- Auth gate still required — Cloud Run endpoint is public by default. Without auth, anyone with the URL can see your financial data
- Token verification still required — even if you're the only user, the Firebase UID must be verified server-side (the client-side token is signed by Firebase's private key; without verification, a user could claim any UID)
- User record creation still required — FK constraint from accounts/liabilities to users table is non-negotiable

**The right threat model:** This is a personal finance app with real data. The auth goal is "only I can see it," not "withstand adversarial attack." Email/password + session state achieves this cleanly.

---

## Cloud Run Deployment Checklist

These are the discrete capabilities the deployment phase must implement, ordered by dependency:

1. **Secret Manager secret for Firebase credentials JSON**
   - `gcloud secrets create firebase-credentials --data-file=path/to/service-account.json`
   - Grant Cloud Run service account `roles/secretmanager.secretAccessor`
   - Mount as file in Cloud Run via `--set-secrets=/secrets/firebase.json=firebase-credentials:latest`
   - Set `FIREBASE_CREDENTIALS_PATH=/secrets/firebase.json` env var

2. **Cloud SQL connection string**
   - Change DATABASE_URL from TCP to socket: `postgresql+psycopg2://USER:PASS@/DB_NAME?host=/cloudsql/PROJECT:REGION:INSTANCE`
   - Add `--add-cloudsql-instances=PROJECT:REGION:INSTANCE` to Cloud Run deploy command
   - Grant Cloud Run service account `roles/cloudsql.client`

3. **Cloud Run deployment command (all flags together)**
   ```
   gcloud run deploy finance-tracker \
     --image gcr.io/PROJECT_ID/finance-tracker \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars DATABASE_URL=...,FIREBASE_CREDENTIALS_PATH=/secrets/firebase.json \
     --set-secrets /secrets/firebase.json=firebase-credentials:latest \
     --add-cloudsql-instances PROJECT:REGION:INSTANCE \
     --min-instances 0 \
     --max-instances 1 \
     --memory 512Mi \
     --port 8501
   ```
   Confidence: MEDIUM — flag names verified against known gcloud CLI patterns; exact syntax should be verified against current gcloud run deploy docs before executing.

4. **Health check path**
   - Streamlit exposes `/_stcore/health` returning HTTP 200 when ready
   - Cloud Run's default liveness check (GET `/`) also works since Streamlit serves 200 on root
   - No config change required unless you want to be explicit: `--set-startup-cpu-boost` helps with Streamlit's slow startup on free tier

5. **Cold start behavior**
   - `--min-instances=0` (free tier) means cold starts on first daily request
   - Streamlit cold start on `python:3.12-slim` with uv: ~10-15 seconds (MEDIUM confidence, based on typical Python container startup)
   - `_init_db()` runs on first Streamlit session — safe because `create_all` is idempotent and seed uses `INSERT OR IGNORE`-equivalent
   - Cloud Run default request timeout is 300 seconds — well above cold start time

---

## Sources

- Existing codebase: `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `app/config.py`, `app/models.py`, `frontend/main.py` (HIGH confidence — direct evidence)
- `plan.md` in repo root — detailed Phase 4 and Phase 5 implementation plan (HIGH confidence — project author's intent)
- Firebase Auth JS SDK flow (email/password, Google, ID token, session persistence): training knowledge (MEDIUM confidence — well-established pattern as of Jan 2025; verify current Firebase JS SDK v9+ modular API syntax)
- Cloud Run Unix socket for Cloud SQL: training knowledge (MEDIUM confidence — verify exact `?host=` parameter syntax against current Cloud SQL connector docs)
- Secret Manager file mount in Cloud Run via `--set-secrets`: training knowledge (MEDIUM confidence — verify flag syntax against current gcloud CLI docs)
- Cloud Run health checks and Streamlit `/_stcore/health`: training knowledge (MEDIUM confidence — Streamlit has exposed this endpoint since v1.12; verify it's still present in current Streamlit version)

---

*Feature research for: Firebase Auth + Cloud Run deployment, single-user Streamlit net worth tracker*
*Researched: 2026-02-17*
