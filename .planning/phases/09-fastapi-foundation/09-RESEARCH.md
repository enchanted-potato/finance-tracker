# Phase 9: FastAPI Foundation - Research

**Researched:** 2026-04-27
**Domain:** FastAPI, Firebase Admin SDK, SQLAlchemy connection pooling, CORS, Pydantic v2 serialisation
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Top-level `api/` directory (not nested under `app/`)
- Layout: `api/main.py`, `api/dependencies.py`, `api/routers/`, `api/schemas/`
- `api/schemas/` is flat — one file per domain: `health.py` now, `accounts.py`, `liabilities.py`, `snapshots.py` in Phase 10
- API tests go in the existing `tests/` directory alongside service tests (`tests/test_api_health.py`, `tests/test_api_auth.py`)
- Add an `api` service to `docker-compose.yml` on port 8000; Streamlit service is unchanged
- Both services share the same build context; both run with `docker-compose up`
- Dockerfile is NOT touched in Phase 9 — deferred to Phase 15
- Add `pool_pre_ping=True` to the existing `create_engine()` call in `app/database.py` (shared change)
- FastAPI route handlers use `Depends(get_session)` from `app/database.py` directly — no wrapper in `api/dependencies.py`
- `GET /api/health` is public — no auth required
- Auth dependency (`get_current_user`) verifies the Firebase ID token from `Authorization: Bearer` header
- After token verification, UID is checked against `settings.allowed_firebase_uid` — returns HTTP 403 if a different Firebase account presents a valid token
- Dev bypass: if `settings.dev_user_id` is set (non-empty), the dependency returns it immediately without calling Firebase
- Returns HTTP 401 if token is missing or invalid; HTTP 403 if UID doesn't match

### Claude's Discretion

- Firebase Admin SDK initialisation details within the lifespan context manager
- Exact CORS middleware configuration (allowed headers, methods)
- Health response schema shape (beyond returning HTTP 200)
- Test fixtures for API tests (how to mock Firebase in tests)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| API-01 | FastAPI app initialises Firebase Admin SDK via `lifespan` context manager and sets `pool_pre_ping=True` on the database engine | Lifespan pattern verified from official FastAPI docs; Firebase Admin init from official Google docs; pool_pre_ping from SQLAlchemy 2.0 docs |
| API-02 | FastAPI configures CORS with explicit Firebase Hosting origins and `allow_credentials=True` (no wildcard) | CORSMiddleware documentation verified; wildcard-with-credentials constraint confirmed |
| API-03 | FastAPI auth dependency verifies Firebase ID token from `Authorization: Bearer` header; returns HTTP 401 if missing or invalid | HTTPBearer + verify_id_token pattern verified; dependency override for tests confirmed |
| API-04 | All response schemas use `float` (not `Decimal`) for monetary values | Pydantic v2 `field_serializer` pattern verified for Decimal → float conversion |
</phase_requirements>

---

## Summary

Phase 9 stands up the FastAPI server infrastructure before any feature routes exist. The four requirements map cleanly onto four distinct implementation areas: lifespan-managed Firebase Admin SDK initialisation (API-01), explicit CORS configuration for the React dev origin (API-02), a Firebase-backed Bearer-token auth dependency with dev bypass (API-03), and Pydantic response schemas that serialise `Decimal` as `float` rather than string (API-04).

All research findings are HIGH confidence, sourced from official FastAPI documentation, official Firebase documentation, and official SQLAlchemy documentation. The existing codebase already has `settings.dev_user_id`, `settings.allowed_firebase_uid`, and `settings.firebase_credentials_path` in `app/config.py`, and `get_session()` in `app/database.py` — both are used directly with no changes required beyond the `pool_pre_ping` addition.

The only cross-cutting concern is that `fastapi[standard]` must be added to `pyproject.toml` via `uv add "fastapi[standard]"`. This installs FastAPI, `uvicorn`, and `httpx` (needed for `TestClient`) in one step.

**Primary recommendation:** Use `fastapi[standard]` package, `@asynccontextmanager` lifespan for Firebase Admin init, `CORSMiddleware` with explicit origins, `HTTPBearer(auto_error=False)` for token extraction, and Pydantic `@field_serializer` to convert `Decimal` to `float`.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi[standard] | latest (0.115.x) | Web framework + includes uvicorn + httpx | Official meta-package; installs uvicorn and httpx for TestClient in one step |
| uvicorn | (bundled) | ASGI server | Required to serve FastAPI; included in fastapi[standard] |
| firebase-admin | already installed | Firebase ID token verification | Already in pyproject.toml; `verify_id_token()` is the standard server-side check |
| sqlmodel / sqlalchemy | already installed | `pool_pre_ping=True` on engine | One-line change to existing `app/database.py` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | (bundled in fastapi[standard]) | TestClient for pytest | Required for `from fastapi.testclient import TestClient` |
| pytest-mock | already in dev deps | Mock Firebase calls in tests | Use `mocker.patch` to patch `firebase_admin.auth.verify_id_token` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `fastapi[standard]` | bare `fastapi` + separate `uvicorn` + `httpx` | More explicit but more lines in pyproject.toml; no real benefit here |
| sync `TestClient` | async `httpx.AsyncClient` + `anyio` | For sync endpoints (health, auth), sync `TestClient` is simpler and sufficient; no `pytest-asyncio` needed |
| `@field_serializer` | type alias `float` instead of `Decimal` | Using `float` in schema model fields directly avoids the serializer entirely; cleaner for new schemas |

**Installation:**
```bash
uv add "fastapi[standard]"
```

---

## Architecture Patterns

### Recommended Project Structure
```
api/
├── __init__.py
├── main.py          # FastAPI app instance, lifespan, middleware, router includes
├── dependencies.py  # get_current_user auth dependency
├── routers/
│   ├── __init__.py
│   └── health.py    # GET /api/health
└── schemas/
    ├── __init__.py
    └── health.py    # HealthResponse schema
```

### Pattern 1: Lifespan Context Manager
**What:** Async context manager passed to `FastAPI(lifespan=...)` runs startup code before `yield` and shutdown code after `yield`.
**When to use:** Any resource initialisation that must happen once at startup — Firebase Admin SDK, connection pools, ML models.
**Example:**
```python
# Source: https://fastapi.tiangolo.com/advanced/events/
from contextlib import asynccontextmanager
from fastapi import FastAPI
import firebase_admin
from firebase_admin import credentials
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialise Firebase Admin SDK
    if settings.firebase_credentials_path:
        cred = credentials.Certificate(settings.firebase_credentials_path)
        firebase_admin.initialize_app(cred)
    else:
        # On Cloud Run, uses Application Default Credentials automatically
        firebase_admin.initialize_app()
    yield
    # Shutdown: delete app to release resources
    firebase_admin.delete_app(firebase_admin.get_app())

app = FastAPI(lifespan=lifespan)
```

**Key detail:** Use `firebase_admin.get_app()` (not the global `_apps` private dict) to check or retrieve the default app after initialisation. On Cloud Run where `firebase_credentials_path` is empty, `initialize_app()` with no arguments uses Application Default Credentials — the same mechanism v1 Streamlit uses.

### Pattern 2: CORS Middleware
**What:** Starlette's `CORSMiddleware` added via `app.add_middleware()`.
**When to use:** Any browser-to-API cross-origin request — required because React dev server runs on port 5173 while API runs on port 8000.
**Example:**
```python
# Source: https://fastapi.tiangolo.com/tutorial/cors/
from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = [
    "http://localhost:5173",           # React dev server (Vite)
    "https://PROJECT.web.app",         # Firebase Hosting production
    "https://PROJECT.firebaseapp.com", # Firebase Hosting production (legacy domain)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)
```

**Critical constraint (verified):** When `allow_credentials=True`, you CANNOT use `["*"]` for `allow_origins`. The origins must be an explicit list. `allow_methods` and `allow_headers` can still use `["*"]` — but being explicit is safer and clearer for security review.

### Pattern 3: Firebase Auth Dependency
**What:** FastAPI `Depends()` dependency that extracts the Bearer token, verifies it with Firebase, checks UID against `settings.allowed_firebase_uid`, and supports a dev bypass.
**When to use:** All routes except `GET /api/health`.
**Example:**
```python
# Source: https://medium.com/@gabriel.cournelle/firebase-authentication-in-the-backend-with-fastapi-4ff3d5db55ca
# + project-specific decisions from CONTEXT.md
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin.auth
from app.config import settings

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    token: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    """Return Firebase UID for the authenticated user.

    :returns: The Firebase UID string.
    :raises HTTPException 401: If token is missing or invalid.
    :raises HTTPException 403: If UID does not match the allowed UID.
    """
    # Dev bypass: skip Firebase entirely
    if settings.dev_user_id:
        return settings.dev_user_id

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        decoded = firebase_admin.auth.verify_id_token(token.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    uid: str = decoded["uid"]
    if settings.allowed_firebase_uid and uid != settings.allowed_firebase_uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return uid
```

### Pattern 4: Pydantic Response Schemas with float (not Decimal)
**What:** Define API response schemas as plain `BaseModel` (not `SQLModel`) with `float` fields for monetary values. Do not reuse SQLModel table models as response schemas — they carry `Decimal` and expose `user_id`.
**When to use:** Every response schema that includes a balance or amount field.
**Example:**
```python
# Approach A: declare field as float directly (cleanest)
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    version: str

class BalanceResponse(BaseModel):
    balance: float   # Never Decimal — serialises to JSON number, not string
```

If you must accept `Decimal` from service layer output (e.g., reading from DB), convert explicitly:
```python
# Approach B: use field_serializer if Decimal enters the schema
from decimal import Decimal
from pydantic import BaseModel, field_serializer

class AccountBalanceResponse(BaseModel):
    balance: Decimal

    @field_serializer("balance")
    def serialize_balance(self, value: Decimal) -> float:
        return float(value)
```

**Recommendation:** Use Approach A (declare `balance: float`) in all new schemas for this phase. The service layer returns `Decimal` from SQLModel, so route handlers convert explicitly: `balance=float(entry.balance)` when constructing the response model.

### Pattern 5: pool_pre_ping
**What:** One-line change to `app/database.py` `create_engine()` call.
**When to use:** Any long-lived connection pool (Cloud SQL drops idle connections after ~10 minutes).
**Example:**
```python
# app/database.py — one-line change
engine = create_engine(settings.database_url, echo=settings.debug, pool_pre_ping=True)
```

SQLAlchemy issues `SELECT 1` before each checkout. If the connection is stale it is recycled automatically. No application code changes beyond this flag.

### Anti-Patterns to Avoid
- **Module-level Firebase init:** Do NOT call `firebase_admin.initialize_app()` at the top of `api/main.py`. This runs at import time, breaks tests, and causes double-init errors on hot reload. Always use `lifespan`.
- **Wildcard origins with credentials:** `allow_origins=["*"]` + `allow_credentials=True` is a CORSMiddleware error — it will either be silently ignored or raise. Always use an explicit origin list.
- **Returning SQLModel models as responses:** SQLModel table models contain `user_id` and `Decimal` fields. Return dedicated `BaseModel` response schemas only.
- **Caching the raw token string:** The React client calls `getIdToken()` before every request (Phase 11 concern, but the API must not cache tokens either — verify fresh on every request).
- **Using `firebase_admin._apps` private dict:** Fragile; changes without notice. Use `firebase_admin.get_app()` with a try/except `ValueError` instead.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Bearer token extraction | Custom `Authorization` header parsing | `HTTPBearer` from `fastapi.security` | Handles scheme validation, whitespace, missing headers correctly |
| CORS preflight handling | Manual `OPTIONS` handler | `CORSMiddleware` | Handles all preflight + simple request variants; tested against browsers |
| ASGI server | Custom socket server | `uvicorn` (bundled in fastapi[standard]) | Standards-compliant; handles HTTP/1.1, HTTP/2, WebSockets |
| Connection liveness | Manual reconnect logic | `pool_pre_ping=True` | SQLAlchemy handles stale connection detection and recycling transparently |

**Key insight:** FastAPI's `Depends()` system and middleware stack handle the cross-cutting concerns (auth, CORS, DB sessions) cleanly without custom middleware or route wrappers.

---

## Common Pitfalls

### Pitfall 1: Double Firebase Initialisation
**What goes wrong:** `firebase_admin.initialize_app()` raises `ValueError: The default Firebase app already exists` if called twice (e.g., on uvicorn `--reload` hot reload in Docker, or during test collection).
**Why it happens:** The Firebase Admin SDK keeps a global registry of app instances. The lifespan is called once per app instance but module-level code runs on every import.
**How to avoid:** Always initialise inside `lifespan()`. If you need guard logic: `try: firebase_admin.get_app() except ValueError: firebase_admin.initialize_app(...)`. Never initialise at module level.
**Warning signs:** `ValueError: The default Firebase app already exists` in startup logs.

### Pitfall 2: Decimal Serialises as String in Pydantic v2
**What goes wrong:** `{"balance": "10753.42"}` instead of `{"balance": 10753.42}` in JSON responses.
**Why it happens:** Pydantic v2 changed Decimal's JSON serialisation from float to string to preserve precision. FastAPI uses Pydantic v2 for response model serialisation.
**How to avoid:** Declare monetary fields as `float` in all response schemas, or use `@field_serializer` if receiving `Decimal` from service layer.
**Warning signs:** Response JSON contains quoted numbers; React `JSON.parse` produces strings instead of numbers.

### Pitfall 3: CORS Allow Credentials with Wildcard
**What goes wrong:** Browser rejects the CORS response even though the server appears to allow it.
**Why it happens:** `allow_credentials=True` + `allow_origins=["*"]` is invalid per the CORS spec. `CORSMiddleware` will not set `Access-Control-Allow-Credentials: true` when origin is `*`.
**How to avoid:** Always provide an explicit list in `allow_origins` when `allow_credentials=True`.
**Warning signs:** Browser DevTools shows `Access-Control-Allow-Origin` is `*` but `Access-Control-Allow-Credentials` is absent.

### Pitfall 4: Auth Dependency Returns Wrong Type on Dev Bypass
**What goes wrong:** Route handler receives `str` in production but `None` or unexpected type from dev bypass — type checker errors, or runtime failures.
**Why it happens:** Inconsistent return type between bypass and real paths.
**How to avoid:** Both paths of `get_current_user` must return `str` (the UID). Dev bypass returns `settings.dev_user_id` which is already `str`.

### Pitfall 5: docker-compose `api` service missing `--host 0.0.0.0`
**What goes wrong:** Uvicorn listens on `127.0.0.1` inside the container — port 8000 is mapped but unreachable from the host.
**Why it happens:** Uvicorn defaults to `127.0.0.1`; inside Docker this is container-local only.
**How to avoid:** Command must be `uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload`.
**Warning signs:** `curl http://localhost:8000/api/health` hangs or returns connection refused.

---

## Code Examples

Verified patterns from official sources:

### Health Router
```python
# api/routers/health.py
from fastapi import APIRouter
from api.schemas.health import HealthResponse

router = APIRouter(prefix="/api")

@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Public health endpoint — no auth required."""
    return HealthResponse(status="ok")
```

### Health Schema
```python
# api/schemas/health.py
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
```

### Main App Assembly
```python
# api/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials
from app.config import settings
from api.routers import health

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "https://PROJECT.web.app",
    "https://PROJECT.firebaseapp.com",
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Firebase Admin SDK init — not at module level
    if settings.firebase_credentials_path:
        cred = credentials.Certificate(settings.firebase_credentials_path)
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app()  # ADC on Cloud Run
    yield
    firebase_admin.delete_app(firebase_admin.get_app())

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(health.router)
```

### Test: Auth Dependency Override
```python
# Source: https://fastapi.tiangolo.com/advanced/testing-dependencies/
# tests/test_api_auth.py
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_current_user

client = TestClient(app)

@pytest.fixture(autouse=False)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: "test-user"
    yield
    app.dependency_overrides.clear()

def test_health_no_auth_required():
    response = client.get("/api/health")
    assert response.status_code == 200

def test_protected_route_without_token():
    # No override — dependency runs normally but dev_user_id is empty in test env
    response = client.get("/api/some-protected-route")
    assert response.status_code == 401
```

### docker-compose api service
```yaml
# Addition to docker-compose.yml
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - /app/.venv
    environment:
      DATABASE_URL: postgresql://finance:finance@db:5432/finance_tracker
      FIREBASE_CREDENTIALS_PATH: ""
      DEBUG: "true"
      DEV_USER_ID: "local-dev-user"
      ALLOWED_FIREBASE_UID: ""
    depends_on:
      - db
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@app.on_event("startup")` decorator | `lifespan` async context manager | FastAPI 0.93 (Feb 2023) | Startup/shutdown events are deprecated; lifespan is the official pattern |
| `json_encoders` in `model_config` | `@field_serializer` per field | Pydantic v2 (2023) | `json_encoders` is deprecated in Pydantic v2; use `@field_serializer` |
| `Decimal` fields in response schemas | `float` fields or `@field_serializer` | Pydantic v2 | Pydantic v2 serialises Decimal as string by default — breaking change from v1 |

**Deprecated/outdated:**
- `@app.on_event("startup")` / `@app.on_event("shutdown")`: deprecated since FastAPI 0.93. Do not use.
- Pydantic v1 `Config` class with `json_encoders = {Decimal: float}`: not valid in Pydantic v2. Use `@field_serializer`.

---

## Open Questions

1. **Firebase Hosting project ID for CORS origins**
   - What we know: Origins must include `https://PROJECT.web.app` and `https://PROJECT.firebaseapp.com`
   - What's unclear: The actual Firebase project ID is not stored in research (it's in the Cloud Run URL: `finance-tracker-rntookejza-uc.a.run.app`, but Firebase project ID may differ)
   - Recommendation: Hard-code the origins as constants in `api/main.py`. The planner should add a task to verify the Firebase project ID and update the constants before Phase 11 testing.

2. **Test isolation for Firebase lifespan**
   - What we know: `TestClient` runs the lifespan by default, which calls `firebase_admin.initialize_app()`
   - What's unclear: In CI or test environments without Firebase credentials, the lifespan will fail if `firebase_credentials_path` is empty and ADC is not available
   - Recommendation: In `lifespan`, guard the Firebase init with `if not settings.dev_user_id:` — when dev bypass is active (tests set `DEV_USER_ID`), skip Firebase init entirely. This keeps tests fast and avoids credential requirements in CI.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.x (already installed) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_api_health.py tests/test_api_auth.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | `GET /api/health` returns 200 with Firebase Admin initialised via lifespan | smoke | `pytest tests/test_api_health.py::test_health_returns_200 -x` | Wave 0 |
| API-01 | Firebase Admin init does NOT happen at module level (verifiable by checking `firebase_admin._apps` is empty before app import) | unit | `pytest tests/test_api_health.py::test_firebase_not_init_at_import -x` | Wave 0 |
| API-02 | CORS preflight from `http://localhost:5173` returns 200 with correct header | integration | `pytest tests/test_api_health.py::test_cors_preflight_allowed_origin -x` | Wave 0 |
| API-02 | CORS preflight from unlisted origin is rejected (no `Access-Control-Allow-Origin` header) | integration | `pytest tests/test_api_health.py::test_cors_preflight_rejected_origin -x` | Wave 0 |
| API-03 | Request without `Authorization` header returns HTTP 401 | unit | `pytest tests/test_api_auth.py::test_missing_token_returns_401 -x` | Wave 0 |
| API-03 | Request with invalid token returns HTTP 401 | unit | `pytest tests/test_api_auth.py::test_invalid_token_returns_401 -x` | Wave 0 |
| API-03 | Request with valid token but wrong UID returns HTTP 403 | unit | `pytest tests/test_api_auth.py::test_wrong_uid_returns_403 -x` | Wave 0 |
| API-04 | `HealthResponse` serialises to `{"status": "ok"}` (string, not Decimal concern here); a `BalanceResponse` with `Decimal("10753.42")` serialises to `{"balance": 10753.42}` (float) | unit | `pytest tests/test_api_health.py::test_decimal_serialises_as_float -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_api_health.py tests/test_api_auth.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_api_health.py` — covers API-01 (health endpoint, lifespan, CORS) and API-04 (float serialisation)
- [ ] `tests/test_api_auth.py` — covers API-03 (401/403 scenarios, dev bypass)
- [ ] Framework install: `uv add "fastapi[standard]"` — fastapi, uvicorn, httpx not yet in pyproject.toml

---

## Sources

### Primary (HIGH confidence)
- [FastAPI official docs — Lifespan Events](https://fastapi.tiangolo.com/advanced/events/) - lifespan context manager pattern verified
- [FastAPI official docs — CORS](https://fastapi.tiangolo.com/tutorial/cors/) - CORSMiddleware parameters and wildcard-with-credentials constraint verified
- [FastAPI official docs — Testing Dependencies](https://fastapi.tiangolo.com/advanced/testing-dependencies/) - `app.dependency_overrides` pattern verified
- [Firebase official docs — Admin SDK Setup](https://firebase.google.com/docs/admin/setup) - `initialize_app()` with `credentials.Certificate()` verified
- [SQLAlchemy 2.0 docs — Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html) - `pool_pre_ping=True` behaviour verified

### Secondary (MEDIUM confidence)
- [Gabriel Cournelle — Firebase Authentication with FastAPI](https://medium.com/@gabriel.cournelle/firebase-authentication-in-the-backend-with-fastapi-4ff3d5db55ca) - `HTTPBearer(auto_error=False)` + `verify_id_token` pattern; cross-checked with FastAPI security docs
- [Pydantic v2 serialization docs](https://docs.pydantic.dev/latest/concepts/serialization/) - `@field_serializer` for Decimal → float; cross-checked with pydantic/pydantic GitHub issues #7120 and #7457

### Tertiary (LOW confidence)
- None — all critical claims verified against official sources.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages are existing project dependencies + fastapi[standard] from official PyPI
- Architecture: HIGH — patterns sourced from official FastAPI and Firebase docs
- Pitfalls: HIGH — Decimal-as-string and double-init are documented in official GitHub issues; CORS wildcard constraint is in official docs
- Test patterns: HIGH — `dependency_overrides` pattern from official FastAPI testing docs

**Research date:** 2026-04-27
**Valid until:** 2026-07-27 (FastAPI 0.11x is stable; Pydantic v2 behaviour is stable; Firebase Admin SDK is stable)
