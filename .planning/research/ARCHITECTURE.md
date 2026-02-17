# Architecture Research

**Domain:** Firebase Auth + Cloud Run deployment integration with existing Streamlit net worth tracker
**Researched:** 2026-02-17
**Confidence:** MEDIUM — Web tools unavailable; analysis based on training knowledge (Jan 2025) + direct codebase inspection. Flag all Cloud Run socket specifics for verification before implementation.

---

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER'S BROWSER                              │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Streamlit page (HTML/JS rendered by Streamlit server)   │   │
│  │                                                          │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │  st.components.v1.html() — firebase_auth.html   │    │   │
│  │  │  Firebase JS SDK (loaded from CDN)              │    │   │
│  │  │  Renders: login form (email/password + Google)  │    │   │
│  │  │  On success: postMessage(idToken) to parent     │    │   │
│  │  └─────────────────┬───────────────────────────────┘    │   │
│  └────────────────────┼────────────────────────────────────┘   │
└───────────────────────┼─────────────────────────────────────────┘
                        │ idToken (JWT string) via Streamlit
                        │ component return value
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CLOUD RUN CONTAINER (Streamlit server)          │
│                                                                 │
│  frontend/main.py                                               │
│  ├── auth_component.py                                          │
│  │   └── st.components.v1.html() → returns idToken             │
│  │       firebase_admin.auth.verify_id_token(idToken)          │
│  │       → decoded_token with uid, email, name                 │
│  │       get_or_create_user(uid, email, name) [app/auth.py]    │
│  │       st.session_state["user_id"] = uid                     │
│  │                                                              │
│  ├── pages/dashboard.py  ─┐                                     │
│  ├── pages/accounts.py   ─┤─ read st.session_state["user_id"] │
│  ├── pages/liabilities.py─┤   pass to service functions        │
│  ├── pages/history.py    ─┤                                     │
│  └── pages/configure.py  ─┘                                     │
│                                                                 │
│  app/services/                                                  │
│  ├── account_service.py   ─┐                                    │
│  ├── liability_service.py ─┤─ no change (already user_id param)│
│  ├── snapshot_service.py  ─┘                                    │
│  └── type_service.py                                            │
│                                                                 │
│  app/auth.py                                                    │
│  ├── verify_token(id_token: str) → dict                        │
│  └── get_or_create_user(uid, email, display_name) → User       │
│                                                                 │
│  app/database.py                                                │
│  └── create_engine(DATABASE_URL)  ← Unix socket on Cloud Run   │
│                                      TCP on local docker        │
└───────────────────────┬─────────────────────────────────────────┘
                        │ Unix socket (Cloud Run)
                        │ /cloudsql/PROJECT:REGION:INSTANCE
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│               CLOUD SQL (PostgreSQL 15)                         │
│               Managed Cloud SQL Auth Proxy (built into CR)      │
└─────────────────────────────────────────────────────────────────┘

External:
┌──────────────────────────────────┐
│  Firebase Authentication (GCP)   │
│  UID issuance, token signing     │
│  Accessed by: browser JS SDK     │
│  Accessed by: server admin SDK   │
│  (for verify_id_token)           │
└──────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Status |
|-----------|----------------|--------|
| `frontend/main.py` | App entry point; auth gate (show login or app); replace TEST_USER_ID | MODIFY |
| `frontend/auth_component.py` | Render Firebase JS login widget via st.components; capture token | NEW |
| `frontend/firebase_auth.html` | Firebase JS SDK HTML; postMessage idToken to Streamlit | NEW |
| `app/auth.py` | `verify_token()` + `get_or_create_user()` using firebase-admin | NEW |
| `app/config.py` | Add `firebase_project_id`, `cloud_sql_connection_name` settings | MODIFY |
| `app/database.py` | Engine creation unchanged; DATABASE_URL format changes per env | UNCHANGED (code) |
| `app/models.py` | Already correct — User.id is Firebase UID VARCHAR | UNCHANGED |
| `app/services/*` | Already receive user_id param — no change needed | UNCHANGED |
| `Dockerfile` | Already correct structure; may need `--server.enableCORS=false` flag | MINOR MODIFY |

---

## Firebase Auth Integration: How Token Flows from Browser to Python

### The Core Problem

Streamlit is a Python server. Firebase authentication happens client-side in JavaScript. There is no built-in bridge. The solution is `st.components.v1.html()`, which embeds an iframe and allows bidirectional communication via the component's return value.

### Pattern: st.components.v1.html() as Auth Bridge

**Confidence: MEDIUM** — This is the established community pattern. The exact `postMessage` / return value mechanism has worked since Streamlit ~1.0 but verify the component return API against current Streamlit docs.

**How it works:**

1. `auth_component.py` calls `st.components.v1.html(html_string, height=400)` and captures the return value.
2. `firebase_auth.html` is loaded as the HTML string. It loads Firebase JS SDK from CDN, renders a login form.
3. On successful Firebase login, the JS calls `window.parent.postMessage({idToken: token}, "*")` — Streamlit's component bridge picks this up and surfaces it as the return value of `html()`.
4. Python receives the JWT string, calls `firebase_admin.auth.verify_id_token(id_token)`, gets `{uid, email, name, ...}`.
5. Python calls `get_or_create_user()` and stores `uid` in `st.session_state["user_id"]`.

**Alternative considered: URL query params** — less secure, token visible in browser history. Rejected.
**Alternative considered: st.experimental_user** — Streamlit's built-in auth; does not support Firebase. Rejected.

```python
# frontend/auth_component.py  (simplified)
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from app.auth import verify_token, get_or_create_user

_HTML = (Path(__file__).parent / "firebase_auth.html").read_text()

def render_login() -> str | None:
    """Render Firebase login widget and return Firebase UID if authenticated."""
    result = components.html(_HTML, height=500)
    if result and isinstance(result, dict) and "idToken" in result:
        decoded = verify_token(result["idToken"])
        user = get_or_create_user(
            uid=decoded["uid"],
            email=decoded.get("email", ""),
            display_name=decoded.get("name", ""),
        )
        return user.id
    return None
```

```javascript
// frontend/firebase_auth.html  (key JS section)
// After firebase.auth().signInWithEmailAndPassword(email, password)
firebase.auth().onAuthStateChanged(function(user) {
    if (user) {
        user.getIdToken().then(function(idToken) {
            // Send token to Streamlit Python layer
            window.parent.postMessage({idToken: idToken}, "*");
        });
    }
});
```

### Replacing the Hardcoded Test User in main.py

**Current state (`frontend/main.py`):**
```python
TEST_USER_ID = "test-user"
st.session_state["user_id"] = TEST_USER_ID  # line 118
```

**After auth integration:**
```python
# In main() — auth gate pattern
if "user_id" not in st.session_state:
    uid = auth_component.render_login()
    if uid:
        st.session_state["user_id"] = uid
        st.rerun()
    st.stop()  # Don't render the rest of the app
# else: user authenticated, fall through to normal app render
```

**`_ensure_test_user()` is deleted.** `get_or_create_user()` in `app/auth.py` replaces it with production logic.

**`_init_db()` is modified** — remove `_ensure_test_user(session)` call. Keep `SQLModel.metadata.create_all(engine)` and `seed_default_types()`.

---

## Cloud SQL Connection: Docker-Compose TCP vs Cloud Run Unix Socket

### Local (docker-compose) — TCP

```
DATABASE_URL=postgresql://finance:finance@db:5432/finance_tracker
```

`db` resolves to the docker-compose Postgres service via Docker networking. Standard TCP connection. This stays unchanged for local dev.

### Cloud Run — Unix Socket via Cloud SQL Auth Proxy

**Confidence: MEDIUM** — This is the canonical GCP pattern. Verify exact socket path format and `pg_bouncer` flag requirements against official docs before deploying.

Cloud Run has built-in Cloud SQL Auth Proxy support. When you add `--add-cloudsql-instances PROJECT:REGION:INSTANCE` to the Cloud Run deploy command, Cloud Run mounts a Unix socket at:

```
/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
```

The SQLAlchemy/psycopg2 connection string for Unix socket is:

```
postgresql+psycopg2://USER:PASSWORD@/DBNAME?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
```

Note the empty host (`@/`) and the `host=` query parameter pointing to the socket directory.

**In `app/config.py`**, no code changes are needed — the URL comes from the `DATABASE_URL` environment variable. Only the value changes per environment:

```bash
# Cloud Run environment variable (set via gcloud or Secret Manager)
DATABASE_URL=postgresql+psycopg2://finance:PASSWORD@/finance_tracker?host=/cloudsql/my-project:us-central1:finance-db
```

**Engine creation in `app/database.py` is code-unchanged.** The `create_engine(settings.database_url)` call works for both TCP and Unix socket — the difference is purely in the URL string.

### Connection Pool Consideration

Cloud Run scales to zero and has cold starts. Connection pooling settings matter:

```python
# app/database.py — add pool settings for Cloud Run
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=2,          # Cloud Run instances are single-user; keep small
    max_overflow=0,
    pool_pre_ping=True,   # Detect stale connections after scale-from-zero
)
```

**Confidence: MEDIUM** — pool_pre_ping is widely recommended for Cloud Run; verify pool_size/max_overflow tuning.

---

## Secrets Management on Cloud Run

**Confidence: MEDIUM** — This is standard GCP pattern. Verify IAM permissions required.

Firebase service account credentials and DB password must NOT be in the container image or environment variables in plain text. Use Google Secret Manager.

**Approach:**

1. Store Firebase credentials JSON as a Secret Manager secret.
2. Mount it as a volume in Cloud Run (not env var — it's a file, not a string).
3. `FIREBASE_CREDENTIALS_PATH` env var points to the mounted path.

```bash
# Deploy command pattern
gcloud run deploy finance-tracker \
  --image gcr.io/PROJECT_ID/finance-tracker \
  --add-cloudsql-instances PROJECT:REGION:INSTANCE \
  --set-env-vars DATABASE_URL=postgresql+psycopg2://...,FIREBASE_CREDENTIALS_PATH=/secrets/firebase \
  --set-secrets /secrets/firebase=firebase-credentials:latest \
  --set-secrets DATABASE_PASSWORD=db-password:latest \
  --service-account finance-tracker-sa@PROJECT.appspot.com
```

**Alternative for DB password:** embed in DATABASE_URL secret (store the whole URL as a secret, mount as env var from secret).

**`app/config.py` extension needed:**

```python
class Settings(BaseSettings):
    database_url: str
    firebase_credentials_path: str = ""
    firebase_project_id: str = ""   # NEW: for token verification
    debug: bool = False
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
```

`firebase_project_id` is needed by `verify_id_token()` to check the `aud` claim.

---

## app/auth.py: New File Structure

```python
# app/auth.py
import firebase_admin
from firebase_admin import auth, credentials
from sqlmodel import Session, select
from loguru import logger

from app.config import settings
from app.models import User

_app: firebase_admin.App | None = None

def _get_app() -> firebase_admin.App:
    """Initialize Firebase Admin app (singleton)."""
    global _app
    if _app is None:
        if settings.firebase_credentials_path:
            cred = credentials.Certificate(settings.firebase_credentials_path)
        else:
            cred = credentials.ApplicationDefault()  # GCP service account
        _app = firebase_admin.initialize_app(cred)
    return _app

def verify_token(*, id_token: str) -> dict:
    """Verify a Firebase ID token and return the decoded claims."""
    _get_app()
    return auth.verify_id_token(id_token)  # raises on invalid/expired

def get_or_create_user(*, uid: str, email: str, display_name: str, session: Session) -> User:
    """Return existing user or create a new one from Firebase claims."""
    user = session.exec(select(User).where(User.id == uid)).first()
    if user is None:
        logger.info(f"Creating new user: {uid}")
        user = User(id=uid, email=email, display_name=display_name)
        session.add(user)
        session.commit()
        session.refresh(user)
    return user
```

**Credential resolution strategy:**
- Local dev: `FIREBASE_CREDENTIALS_PATH` points to downloaded service account JSON.
- Cloud Run: `FIREBASE_CREDENTIALS_PATH` points to Secret Manager mounted file OR use `ApplicationDefault()` (Cloud Run SA with Firebase permissions).

---

## Dockerfile: Health Check for Cloud Run

Cloud Run requires the container to respond to HTTP requests. Streamlit does respond on port 8501, but adding `--server.enableCORS=false` and `--server.enableXsrfProtection=false` is often needed behind Cloud Run's proxy.

```dockerfile
# Current CMD — works but may need flags
CMD ["uv", "run", "streamlit", "run", "frontend/main.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
```

**Confidence: LOW** — The CORS/XSRF flags are frequently cited in community resources for Cloud Run deployments but not definitively documented as required. Test without first; add if auth token posting fails.

Cloud Run health check: Cloud Run uses HTTP GET `/healthz` or the root path by default. Streamlit responds on `/` so the default health check passes. No explicit health check endpoint needed.

---

## Recommended Project Structure Changes

```
finance-tracker/
├── app/
│   ├── auth.py                    # NEW — Firebase token verify + get_or_create_user
│   ├── config.py                  # MODIFY — add firebase_project_id
│   ├── database.py                # MODIFY — add pool_pre_ping, pool_size
│   ├── models.py                  # UNCHANGED
│   ├── seed.py                    # UNCHANGED
│   └── services/                  # UNCHANGED
├── frontend/
│   ├── auth_component.py          # NEW — st.components.v1.html() wrapper
│   ├── firebase_auth.html         # NEW — Firebase JS SDK login widget
│   ├── main.py                    # MODIFY — remove TEST_USER_ID, add auth gate
│   └── pages/                     # UNCHANGED
├── Dockerfile                     # MODIFY — add server flags
├── docker-compose.yml             # UNCHANGED (local still uses TCP)
└── .env.example                   # MODIFY — add FIREBASE_PROJECT_ID
```

---

## Data Flow

### Authentication Flow (new users / logged-out state)

```
Browser (unauthenticated)
    ↓
frontend/main.py: "user_id" not in st.session_state
    ↓
auth_component.render_login()
    ↓
st.components.v1.html(firebase_auth.html)
    ↓ user enters credentials
Firebase JS SDK → Firebase Auth API (GCP)
    ↓ success
JS: user.getIdToken() → JWT string
    ↓ postMessage
Streamlit component return value → Python
    ↓
app/auth.verify_token(id_token)
    ↓ firebase_admin SDK → Firebase public keys (cached)
decoded claims: {uid, email, name}
    ↓
app/auth.get_or_create_user(uid, email, name, session)
    ↓ upsert into users table (Cloud SQL)
User record
    ↓
st.session_state["user_id"] = uid
st.rerun()
    ↓
App renders normally (Dashboard, Accounts, etc.)
```

### Normal App Flow (authenticated, unchanged from Phase 3)

```
User action (e.g., update account balance)
    ↓
frontend/pages/accounts.py
    ↓ reads st.session_state["user_id"]
app/services/account_service.update_balance(user_id=uid, ...)
    ↓
Cloud SQL (Unix socket) via SQLModel Session
    ↓
snapshot_service.capture_snapshot(user_id=uid, session=session)
```

### Cloud Run Request Flow

```
HTTPS request → Cloud Run ingress
    ↓ TLS termination
Streamlit server (port 8501)
    ↓ WebSocket (Streamlit's normal mode)
Python session (st.session_state persisted per browser tab)
    ↓ Unix socket
Cloud SQL Auth Proxy (built into Cloud Run runtime)
    ↓ encrypted TCP
Cloud SQL PostgreSQL
```

---

## Architectural Patterns

### Pattern 1: st.session_state as Auth Context Carrier

**What:** Store Firebase UID in `st.session_state["user_id"]` after verification. Every page reads it from there.

**When to use:** Always — this is the only viable per-session state store in Streamlit.

**Trade-offs:** Session state is per-tab (browser tab), not per-user across tabs. Acceptable for single-user app. State is lost on server restart (user must re-auth). With Cloud Run, containers may be replaced — session state does not persist across container instances. This is a known Streamlit-on-Cloud-Run constraint.

**Implication:** Auth token re-verification happens on every new Streamlit session (new tab, server restart). The Firebase JS SDK handles token refresh transparently on the client; the Python side needs to be aware that tokens expire in 1 hour and re-verification is needed.

### Pattern 2: Firebase Admin SDK Singleton Initialization

**What:** Initialize `firebase_admin` app once at module level (or on first call) as a singleton. Re-initialization on every request throws an error.

**When to use:** Always — `firebase_admin.initialize_app()` is not idempotent.

**Trade-offs:** Global state, but Firebase Admin is designed for this. The `_get_app()` guard in `app/auth.py` handles this correctly.

### Pattern 3: DATABASE_URL Abstraction for Environment Parity

**What:** All database connection logic lives in `DATABASE_URL`. Local uses TCP format, Cloud Run uses Unix socket format. `app/database.py` code never changes between environments.

**When to use:** Always — 12-factor app principle. Avoids environment-specific code branches.

**Trade-offs:** The URL format difference (TCP vs Unix socket) is subtle. Unix socket format uses `?host=` query param which is non-obvious. Document this clearly in `.env.example`.

---

## Integration Points

### External Services

| Service | Integration Pattern | Confidence | Notes |
|---------|---------------------|------------|-------|
| Firebase Auth (client) | Firebase JS SDK via CDN in st.components iframe | MEDIUM | CDN load in iframe may have CSP issues on some hosting |
| Firebase Auth (server) | `firebase-admin` Python SDK — `verify_id_token()` | HIGH | Already in pyproject.toml dependencies |
| Cloud SQL | Unix socket via Cloud SQL Auth Proxy (built into Cloud Run) | MEDIUM | Proxy is automatic with `--add-cloudsql-instances` flag |
| Secret Manager | Volume mount for Firebase credentials JSON | MEDIUM | Alternative: Application Default Credentials via SA permissions |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `frontend/auth_component.py` → `app/auth.py` | Direct Python import call | Keep `app/auth.py` free of st.* calls |
| `frontend/main.py` → auth gate | `st.session_state["user_id"]` presence check | Gate must be first in `main()` before any page render |
| `app/auth.py` → `app/database.py` | Receives `Session` as parameter | `get_or_create_user` takes session arg; does not create its own |
| Pages → Services | `st.session_state["user_id"]` passed as `user_id` kwarg | Pattern already established in Phase 3 |

---

## Build Order (What Must Exist Before What)

**Phase 4A — Firebase backend infrastructure:**
1. `app/auth.py` — core token verification and user creation (no UI dependency)
2. `app/config.py` modification — add `firebase_project_id` setting
3. Local Firebase project setup + download credentials JSON + set `FIREBASE_CREDENTIALS_PATH` in `.env`

**Phase 4B — Frontend auth bridge:**
4. `frontend/firebase_auth.html` — standalone HTML/JS that can be tested in a browser directly
5. `frontend/auth_component.py` — wraps the HTML, calls `app/auth.py`
6. `frontend/main.py` modification — replace `TEST_USER_ID` with auth gate

**Phase 5A — Cloud Run deployment:**
7. Cloud SQL instance creation + database + user
8. Cloud Run service account creation + IAM permissions (Cloud SQL Client, Secret Manager Secret Accessor)
9. Secret Manager secrets: Firebase credentials, DB password
10. Dockerfile modification (server flags)
11. `gcloud builds submit` + `gcloud run deploy` with `--add-cloudsql-instances`

**Dependency constraints:**
- `app/auth.py` must exist before `auth_component.py` (imports it)
- Firebase project must exist before `firebase_auth.html` can reference the config (API key, project ID)
- Cloud SQL must exist before Cloud Run deploy (needs connection name)
- IAM permissions must be set before deploy (Cloud Run SA needs Cloud SQL Client role)

---

## Anti-Patterns

### Anti-Pattern 1: Trusting the Token Payload Without Verification

**What people do:** Decode the JWT client-side, send `uid` directly to the server, use it without verification.

**Why it's wrong:** JWT payload is not encrypted — anyone can craft a token with any `uid`. Firebase token verification (`verify_id_token`) checks the signature against Firebase's public keys.

**Do this instead:** Always call `firebase_admin.auth.verify_id_token(id_token)` server-side. Never trust client-sent `uid` values directly.

### Anti-Pattern 2: Re-initializing firebase_admin on Every Request

**What people do:** Call `firebase_admin.initialize_app()` at the top of a function that runs on every Streamlit rerun.

**Why it's wrong:** Streamlit reruns the entire script on every interaction. `initialize_app()` throws `ValueError: The default Firebase app already exists` on the second call.

**Do this instead:** Use a singleton guard (`if not firebase_admin._apps: firebase_admin.initialize_app(...)` or the `_get_app()` pattern shown above).

### Anti-Pattern 3: Hardcoding TCP URL for Cloud Run

**What people do:** Use `postgresql://user:pass@localhost:5432/db` in Cloud Run, then run the Cloud SQL proxy as a sidecar or separate service.

**Why it's wrong:** Cloud Run has native Cloud SQL Auth Proxy support via `--add-cloudsql-instances`. Running a separate proxy defeats this and adds complexity.

**Do this instead:** Use the Unix socket URL format `postgresql+psycopg2://user:pass@/db?host=/cloudsql/PROJECT:REGION:INSTANCE` and the native `--add-cloudsql-instances` flag.

### Anti-Pattern 4: Storing ID Token in st.session_state Long-Term

**What people do:** Store the raw Firebase ID token string in `st.session_state` and use it as the user identifier for all service calls.

**Why it's wrong:** Firebase ID tokens expire in 1 hour. If the user stays on the page, subsequent service calls would use an expired token as the user ID — this is fragile.

**Do this instead:** Verify the token once, extract the `uid`, store only the `uid` in `st.session_state`. The `uid` is permanent and does not expire. Re-verify from the JS side (Firebase JS SDK auto-refreshes; user must re-login if Streamlit session is new).

### Anti-Pattern 5: Putting Firebase Credentials in the Docker Image

**What people do:** `COPY firebase-credentials.json /app/` in the Dockerfile.

**Why it's wrong:** The image is pushed to a container registry. Credentials are baked in and visible to anyone with registry access.

**Do this instead:** Mount the credentials file via Secret Manager volume mount at Cloud Run deploy time.

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1 user (current target) | Current architecture is correct and sufficient |
| 1-10 users | Consider Streamlit session state persistence — users can't share server state; each user has their own session. Works fine. |
| 10+ users | Cloud Run scales horizontally; each instance has independent session state. Streamlit WebSocket sessions are sticky to an instance — Cloud Run handles this. DB connection pool per instance matters (`pool_size=2` recommended). |

Single-user is the stated target. The architecture is appropriate. No premature optimization needed.

---

## Sources

**Codebase analysis (HIGH confidence):**
- `/Users/kristiakarakatsani/Repos/finance-tracker/frontend/main.py` — existing auth structure
- `/Users/kristiakarakatsani/Repos/finance-tracker/app/config.py` — Settings shape
- `/Users/kristiakarakatsani/Repos/finance-tracker/app/database.py` — Engine creation pattern
- `/Users/kristiakarakatsani/Repos/finance-tracker/app/models.py` — User model (Firebase UID as PK)
- `/Users/kristiakarakatsani/Repos/finance-tracker/docker-compose.yml` — Local TCP connection
- `/Users/kristiakarakatsani/Repos/finance-tracker/Dockerfile` — Container entry point
- `/Users/kristiakarakatsani/Repos/finance-tracker/pyproject.toml` — firebase-admin already a dependency

**Training knowledge (MEDIUM confidence — Jan 2025 cutoff, web verification unavailable):**
- `st.components.v1.html()` postMessage pattern for Firebase-Streamlit bridge
- `firebase_admin.auth.verify_id_token()` API and singleton initialization pattern
- Cloud SQL Auth Proxy Unix socket path format and `--add-cloudsql-instances` Cloud Run flag
- SQLAlchemy Unix socket URL format with `?host=` query parameter
- Google Secret Manager volume mount approach for Cloud Run

**Flags requiring verification before implementation:**
- Exact Streamlit component return value mechanism for `postMessage` (verify against current Streamlit docs — component API has evolved)
- Streamlit `--server.enableCORS=false` requirement for Cloud Run (LOW confidence — community claim, not officially documented as mandatory)
- Unix socket URL dialect: confirm `postgresql+psycopg2://` vs `postgresql://` requirement with psycopg2 on Unix sockets
- Cloud Run IAM role required for Cloud SQL: verify `roles/cloudsql.client` is sufficient

---

*Architecture research for: Firebase Auth + Cloud Run integration with existing Streamlit net worth tracker*
*Researched: 2026-02-17*
