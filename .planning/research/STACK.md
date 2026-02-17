# Stack Research

**Domain:** Firebase Auth + Cloud Run/Cloud SQL deployment for existing Streamlit app
**Researched:** 2026-02-17
**Confidence:** HIGH (versions sourced from resolved uv.lock; integration patterns from official architecture)

## Existing Stack (Already Validated — Do Not Re-Research)

| Technology | Version (locked) | Purpose |
|------------|-----------------|---------|
| Python | 3.12 | Runtime |
| Streamlit | 1.53.1 | Frontend |
| SQLModel | (see uv.lock) | ORM |
| psycopg2-binary | (see uv.lock) | PostgreSQL driver |
| firebase-admin | 7.1.0 | Server-side Firebase SDK |
| pydantic-settings | (see uv.lock) | Config from env vars |
| loguru | (see uv.lock) | Logging |
| uv | latest | Package management |

## New Capabilities: Firebase Auth Integration

### Core Technologies (New)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Firebase JS SDK | 11.x (CDN) | Client-side auth (email/password + Google sign-in) | Only way to do client-side Firebase auth in a Streamlit custom HTML component; no server-side equivalent |
| firebase-admin (Python) | 7.1.0 (already locked) | Server-side ID token verification | Already in pyproject.toml; verifies tokens the JS SDK issues; no version change needed |
| `st.components.v1.html()` | Streamlit built-in | Render Firebase login HTML widget | Streamlit's mechanism for embedding arbitrary HTML/JS — no extra package |

**Firebase JS SDK CDN URL (use module syntax, not compat):**
```html
<script type="module">
  import { initializeApp } from 'https://www.gstatic.com/firebasejs/11.3.1/firebase-app.js';
  import { getAuth, signInWithEmailAndPassword, signInWithPopup, GoogleAuthProvider } from 'https://www.gstatic.com/firebasejs/11.3.1/firebase-auth.js';
</script>
```

Use the gstatic.com CDN (Google's own CDN for Firebase). Do NOT use jsDelivr or unpkg for Firebase — the gstatic CDN is the canonical source and is version-pinned.

### Supporting Libraries (New)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `streamlit.components.v1` | built-in | Embed HTML auth widget + receive token via `component_value` | Always — this is how the JS-to-Python token handoff works |
| PyJWT | 2.11.0 (already locked via firebase-admin) | JWT decoding internals | Already a transitive dep; never use directly — firebase-admin wraps it |

## New Capabilities: Cloud Run + Cloud SQL Deployment

### Core Technologies (New)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Cloud SQL (PostgreSQL 15) | db-f1-micro | Managed Postgres | Already in plan; free tier fits single-user app |
| Unix socket connection | N/A (psycopg2 built-in) | App-to-Cloud-SQL connection on Cloud Run | Cloud Run injects `/cloudsql/INSTANCE_CONNECTION_NAME` socket; psycopg2 connects natively without any connector library |
| Cloud Run service account | N/A (GCP IAM) | Grants Cloud SQL Client role to the Cloud Run service | Required for Cloud SQL proxy sidecar that Cloud Run manages automatically |
| Secret Manager | N/A (GCP service) | Store Firebase service account JSON | Avoids baking credentials into container image; mount as env var or file at runtime |

### What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `cloud-sql-python-connector` | Adds complexity; only needed when you can't use Unix sockets (e.g., from local machine hitting Cloud SQL directly). Cloud Run provides the socket automatically. | psycopg2 with `host=/cloudsql/PROJECT:REGION:INSTANCE` |
| `google-cloud-run` client library | Not needed to deploy or configure Cloud Run from within the app | `gcloud` CLI for deployment; no runtime library needed |
| Firebase REST API calls | More fragile than the Admin SDK; no token caching | firebase-admin SDK `auth.verify_id_token()` |
| Storing Firebase service account JSON in the Docker image | Security risk; credentials in image layers | GCP Secret Manager → mount as env var `GOOGLE_APPLICATION_CREDENTIALS` or Secret Manager volume |

### Development Tools (No Change)

| Tool | Purpose | Notes |
|------|---------|-------|
| Docker + docker-compose.yml | Local dev | Already working; no changes needed for auth milestone |
| `gcloud` CLI | Build/push image, create Cloud Run service, create Cloud SQL instance | Used at deployment time, not in app code |

## Installation

No new Python packages are required for this milestone.

```bash
# firebase-admin is already in pyproject.toml (pinned to 7.1.0 in uv.lock)
# All google-* transitive deps already resolved:
#   google-api-core 2.29.0
#   google-auth 2.48.0
#   google-cloud-firestore 2.23.0
#   google-cloud-storage 3.8.0
#   google-cloud-core 2.5.0

# Nothing to uv add — run sync to ensure lockfile is applied
uv sync --frozen
```

## Configuration Additions Required

These env vars need to be added to `app/config.py` (Settings class) and `.env.example`:

```python
# New fields for Settings(BaseSettings):
firebase_project_id: str           # e.g. "my-finance-tracker-12345"
firebase_web_api_key: str          # Firebase project web API key (for JS SDK config)

# Already exists — needs to be populated in production:
firebase_credentials_path: str = ""  # Path to service account JSON (or empty = use ADC)
```

**Cloud Run environment variables:**
```
DATABASE_URL=postgresql://finance:finance@/finance_tracker?host=/cloudsql/PROJECT:REGION:INSTANCE
FIREBASE_CREDENTIALS_PATH=/secrets/firebase-sa.json   # or use Workload Identity
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_WEB_API_KEY=AIza...
```

Note: The `DATABASE_URL` format for Unix socket with psycopg2 uses `host=` as a query parameter pointing to the socket directory — not a TCP host.

## Token Handoff Architecture (Critical Integration Point)

Streamlit has no WebSocket or bidirectional channel with embedded HTML components other than `component_value`. The auth flow is:

```
1. st.components.v1.html() renders firebase_auth.html in an iframe
2. User logs in via Firebase JS SDK (email/password or Google popup)
3. JS SDK calls getIdToken() to get a short-lived ID token (1hr)
4. iframe posts token to parent via Streamlit.setComponentValue(token)
5. Python receives token as return value of st.components.v1.html()
6. Python calls firebase_admin.auth.verify_id_token(token) → decoded claims
7. uid = decoded["uid"] stored in st.session_state["user_id"]
8. get_or_create_user(uid, email, display_name) upserts to users table
9. All subsequent service calls use st.session_state["user_id"]
```

**Session state keys to use:**
- `st.session_state["user_id"]` — Firebase UID (already used by pages in Phase 3)
- `st.session_state["id_token"]` — raw ID token (store for token refresh detection)
- `st.session_state["user_email"]` — display in sidebar

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Firebase JS SDK via st.components.v1.html() | streamlit-firebase (3rd party) | Never — unmaintained, outdated SDK version |
| psycopg2 Unix socket | cloud-sql-python-connector | When connecting from local machine to Cloud SQL for DB migrations during development |
| GCP Secret Manager for Firebase SA | FIREBASE_CREDENTIALS_PATH env var pointing to mounted file | Both work on Cloud Run; Secret Manager is cleaner but either is fine |
| Firebase Admin SDK verify_id_token() | Manual JWT decode with PyJWT | Never — Admin SDK handles key rotation, caching, audience validation automatically |

## Version Compatibility

| Package | Version | Compatible With | Notes |
|---------|---------|-----------------|-------|
| firebase-admin | 7.1.0 | Python 3.12, google-auth 2.48.0 | Confirmed by uv.lock resolution |
| Firebase JS SDK | 11.3.1 | All modern browsers | Use modular (tree-shakeable) API, not compat/v8 API |
| psycopg2-binary | (locked) | PostgreSQL 15 (Cloud SQL) | Unix socket path passed as `host=` parameter |

## Sources

- uv.lock at `/Users/kristiakarakatsani/Repos/finance-tracker/uv.lock` — firebase-admin 7.1.0 confirmed (resolved 2026-01-30 timestamp on PyJWT dep); google-* package versions confirmed — HIGH confidence
- Firebase JS SDK CDN: `https://www.gstatic.com/firebasejs/` — version 11.3.1 referenced in gstatic CDN (training knowledge, January 2025 cutoff) — MEDIUM confidence (pin to specific version at implementation time by checking gstatic)
- Cloud Run + Cloud SQL Unix socket pattern: standard GCP architecture; DATABASE_URL format for psycopg2 Unix socket is `postgresql://user:pass@/dbname?host=/cloudsql/CONN_NAME` — HIGH confidence (well-established pattern)
- `st.components.v1.html()` component value return: Streamlit built-in since v0.63; used for JS-to-Python data passing — HIGH confidence

---
*Stack research for: Firebase Auth + Cloud Run deployment on existing Streamlit net worth tracker*
*Researched: 2026-02-17*
