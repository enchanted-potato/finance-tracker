# Architecture Research

**Domain:** FastAPI REST layer + React SPA migration on top of existing Python/SQLModel service layer
**Researched:** 2026-04-04
**Confidence:** HIGH — based on direct codebase inspection + FastAPI official docs. Firebase token flow confirmed against existing `auth_service.py`.

---

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FIREBASE HOSTING                             │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  React SPA (Vite build output, static files)                  │  │
│  │                                                               │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐ │  │
│  │  │  Firebase   │  │   React      │  │  API Client Layer     │ │  │
│  │  │  JS SDK     │  │   Router     │  │  (fetch + auth token  │ │  │
│  │  │  (Auth)     │  │  (pages)     │  │   injection)          │ │  │
│  │  └──────┬──────┘  └──────────────┘  └──────────┬───────────┘ │  │
│  └─────────┼──────────────────────────────────────┼─────────────┘  │
└────────────┼──────────────────────────────────────┼────────────────┘
             │ Google Sign-In / token refresh        │ Authorization: Bearer <id_token>
             ▼                                       ▼
┌───────────────────────┐         ┌─────────────────────────────────────────┐
│  Firebase Auth (GCP)  │         │      CLOUD RUN CONTAINER (FastAPI)      │
│  Token signing,       │         │                                         │
│  UID issuance         │◄────────│  api/main.py                            │
└───────────────────────┘  verify │  ├── CORSMiddleware (Firebase Hosting)  │
                           token  │  ├── routers/                           │
                                  │  │   ├── accounts.py  ─┐               │
                                  │  │   ├── liabilities.py─┤ call service  │
                                  │  │   ├── pension.py    ─┤ functions     │
                                  │  │   ├── snapshots.py  ─┤ directly      │
                                  │  │   ├── history.py    ─┘               │
                                  │  │   └── configure.py                  │
                                  │  ├── deps.py                           │
                                  │  │   ├── get_session() → SessionDep    │
                                  │  │   └── get_current_user() → str(uid) │
                                  │  │       (verifies Firebase ID token)  │
                                  │  └── app/services/ (UNCHANGED)         │
                                  │      ├── account_service.py            │
                                  │      ├── liability_service.py          │
                                  │      ├── snapshot_service.py           │
                                  │      └── type_service.py               │
                                  └──────────────┬──────────────────────────┘
                                                 │ Unix socket
                                                 ▼
                                  ┌─────────────────────────────────────────┐
                                  │  CLOUD SQL (PostgreSQL 15) — UNCHANGED  │
                                  └─────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Status |
|-----------|----------------|--------|
| `api/main.py` | FastAPI app entry point, CORS middleware, router inclusion | NEW |
| `api/deps.py` | Shared FastAPI dependencies: `get_session()`, `get_current_user()` | NEW |
| `api/routers/accounts.py` | `/api/accounts` endpoints — wraps `account_service` functions | NEW |
| `api/routers/liabilities.py` | `/api/liabilities` endpoints — wraps `liability_service` functions | NEW |
| `api/routers/pension.py` | `/api/pension` endpoints — wraps pension functions from account_service | NEW |
| `api/routers/snapshots.py` | `/api/snapshots` endpoints — wraps `snapshot_service` functions | NEW |
| `api/routers/history.py` | `/api/history` endpoints — CSV export/import, history table data | NEW |
| `api/routers/configure.py` | `/api/configure` endpoints — account/liability type CRUD | NEW |
| `app/services/*` | All existing business logic — zero changes | UNCHANGED |
| `app/models.py` | SQLModel models — zero changes | UNCHANGED |
| `app/database.py` | Engine + `get_session()` generator — zero changes | UNCHANGED |
| `app/services/auth_service.py` | `verify_firebase_token()` — already exists, used by FastAPI dep | UNCHANGED |
| `frontend/` (Streamlit) | Existing Streamlit app — runs in parallel during migration | UNCHANGED |
| `react-frontend/` | React + TypeScript SPA (Vite project) | NEW |

---

## FastAPI ↔ SQLModel Services Integration

### The Key Insight: Services Already Work

The existing service functions in `app/services/` already follow the correct pattern for FastAPI reuse:

- Every function takes `session: Session` as an explicit keyword argument
- Every function takes `user_id: str` as an explicit keyword argument
- Functions raise `ValueError` for domain errors — map to HTTP 400/404 in routers
- Functions return SQLModel model instances directly (Pydantic-serializable)

The FastAPI router layer is a thin translation layer: receive HTTP request, inject dependencies, call service, return result.

### Pattern: Dependency Injection for Session + User

`api/deps.py` provides two shared dependencies for all protected routes:

```python
# api/deps.py
from typing import Annotated, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session

from app.database import engine
from app.services.auth_service import verify_firebase_token, init_firebase_admin

# Initialize Firebase Admin once at startup (idempotent guard already in auth_service.py)
init_firebase_admin()

bearer_scheme = HTTPBearer()

def get_session() -> Generator[Session, None, None]:
    """Yield one Session per request. Reuses existing database.py engine."""
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> str:
    """Verify Firebase ID token. Return UID or raise 401."""
    token = credentials.credentials
    decoded = verify_firebase_token(token)  # existing auth_service function
    if decoded is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decoded["uid"]

CurrentUser = Annotated[str, Depends(get_current_user)]
```

The `get_session()` in `deps.py` wraps the existing `engine` from `database.py` — it does the same thing as the existing `get_session()` generator. FastAPI's `Depends()` ensures one session per HTTP request, with automatic cleanup via the context manager.

### Pattern: Router Wrapping a Service

```python
# api/routers/accounts.py
from fastapi import APIRouter, HTTPException
from app.services import account_service
from api.deps import SessionDep, CurrentUser

router = APIRouter(prefix="/api/accounts", tags=["accounts"])

@router.get("/")
def list_account_types(session: SessionDep, user_id: CurrentUser):
    return account_service.list_account_types(session=session, user_id=user_id)

@router.get("/entries")
def list_account_entries(session: SessionDep, user_id: CurrentUser):
    return account_service.list_account_entries(session=session, user_id=user_id)

@router.put("/entries")
def upsert_account_entry(body: AccountEntryIn, session: SessionDep, user_id: CurrentUser):
    try:
        return account_service.upsert_account_entry(
            session=session,
            user_id=user_id,
            account_type_id=body.account_type_id,
            entry_date=body.entry_date,
            balance=body.balance,
            currency=body.currency,
            exchange_rate=body.exchange_rate,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/entries/{entry_id}")
def delete_account_entry(entry_id: int, session: SessionDep, user_id: CurrentUser):
    try:
        account_service.delete_account_entry(
            session=session, entry_id=entry_id, user_id=user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### ValueError → HTTP Exception Mapping

All service functions raise `ValueError` on domain errors. The router catches these and maps them to appropriate HTTP status codes:

| Service exception | HTTP status | Condition |
|-------------------|-------------|-----------|
| `ValueError("...not found...")` | 404 | Entity not found for user |
| `ValueError("...")` (other) | 400 | Bad input / domain constraint violation |
| No exception | 200/201 | Success |

---

## Firebase Token Flow: React → FastAPI

### Token Acquisition in React

```
1. User opens React app on Firebase Hosting
2. Firebase JS SDK (modular) is initialized with project config
3. User clicks "Sign in with Google"
4. Firebase JS SDK handles OAuth popup → Firebase Auth issues ID token (JWT, 1hr expiry)
5. JS SDK stores token internally and auto-refreshes before expiry
6. React app calls user.getIdToken() to get current valid token
7. Token is attached to all API requests: Authorization: Bearer <token>
```

The Firebase JS SDK refreshes tokens automatically. The React API client must call `getIdToken()` (not cache the raw token string) on every request to get a non-expired token.

### Token Verification in FastAPI

```
1. FastAPI receives: Authorization: Bearer <firebase-id-token>
2. HTTPBearer security scheme extracts the token string
3. get_current_user() dependency calls verify_firebase_token(token)
4. verify_firebase_token() calls firebase_admin.auth.verify_id_token(token)
   → verifies signature against Firebase's public keys (cached by Admin SDK)
   → verifies expiry, audience (project ID), issuer
   → checks UID against ALLOWED_FIREBASE_UID if set (single-user guard)
5. Returns decoded["uid"] — the Firebase UID string
6. UID is passed as user_id to all service function calls
7. All service queries filter by user_id — data isolation guaranteed
```

The existing `verify_firebase_token()` in `app/services/auth_service.py` already does all of this. The FastAPI dependency layer wraps it and converts `None` return to a 401 HTTP exception.

### Token Refresh Strategy in React

```typescript
// api/client.ts — centralized API client
import { getAuth } from "firebase/auth";

async function apiFetch(path: string, options?: RequestInit): Promise<Response> {
  const auth = getAuth();
  const user = auth.currentUser;
  if (!user) throw new Error("Not authenticated");

  // Always call getIdToken() — SDK returns cached token if not expired,
  // fetches new one if within 5 min of expiry
  const token = await user.getIdToken();

  return fetch(`${import.meta.env.VITE_API_URL}${path}`, {
    ...options,
    headers: {
      ...options?.headers,
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });
}
```

This pattern means the React app never stores a raw token string — it always requests the current valid token from the Firebase JS SDK before each API call.

---

## CORS Configuration

Firebase Hosting serves the React SPA from `https://PROJECT.web.app` and `https://PROJECT.firebaseapp.com`. The FastAPI server on Cloud Run is at a different origin.

```python
# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://PROJECT_ID.web.app",
        "https://PROJECT_ID.firebaseapp.com",
        "http://localhost:5173",  # Vite dev server default
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
```

Note: When `allow_credentials=True`, `allow_origins` cannot be `["*"]` — must list explicit origins. This is a CORS spec requirement enforced by browsers.

---

## Recommended Project Structure

### Python Side (FastAPI layer — new)

```
api/                           # New FastAPI application package
├── __init__.py
├── main.py                    # FastAPI app, middleware, router inclusion
├── deps.py                    # Shared dependencies: SessionDep, CurrentUser
├── schemas/                   # Request/response Pydantic models (separate from DB models)
│   ├── __init__.py
│   ├── accounts.py            # AccountEntryIn, AccountEntryOut, AccountTypeIn
│   ├── liabilities.py         # LiabilityEntryIn, LiabilityEntryOut
│   ├── pension.py             # PensionEntryIn (reuses AccountEntry shape)
│   ├── snapshots.py           # SnapshotOut, SnapshotHistoryOut
│   └── configure.py           # AccountTypeIn, LiabilityTypeIn
└── routers/                   # One file per domain, mirrors service layer
    ├── __init__.py
    ├── accounts.py            # /api/accounts — wraps account_service
    ├── liabilities.py         # /api/liabilities — wraps liability_service
    ├── pension.py             # /api/pension — wraps pension functions
    ├── snapshots.py           # /api/snapshots — wraps snapshot_service
    ├── history.py             # /api/history — snapshot history + CSV
    └── configure.py           # /api/configure — type CRUD (wraps type_service)

app/                           # UNCHANGED — existing service layer
├── models.py
├── database.py
├── config.py
├── seed.py
└── services/
    ├── account_service.py
    ├── liability_service.py
    ├── snapshot_service.py
    ├── type_service.py
    └── auth_service.py        # verify_firebase_token() already here
```

### React Side (new)

```
react-frontend/                # Vite project root
├── index.html                 # Vite entry point (references /src/main.tsx)
├── vite.config.ts             # VITE_API_URL proxy for local dev
├── tsconfig.json
├── package.json
├── .env.local                 # VITE_API_URL=http://localhost:8000 (local)
├── .env.production            # VITE_API_URL=https://finance-tracker-xxxx.run.app
├── public/
│   └── favicon.ico
└── src/
    ├── main.tsx               # React DOM render, Firebase init, router setup
    ├── firebase.ts            # Firebase app initialization (config from env vars)
    ├── api/
    │   ├── client.ts          # Base fetch wrapper with token injection
    │   ├── accounts.ts        # API calls for accounts + pension
    │   ├── liabilities.ts     # API calls for liabilities
    │   ├── snapshots.ts       # API calls for snapshots + history
    │   └── configure.ts       # API calls for type management
    ├── components/            # Reusable UI components (shadcn/ui wrappers)
    │   ├── ui/                # shadcn/ui generated components live here
    │   ├── NetWorthCard.tsx
    │   ├── AccountTable.tsx
    │   ├── NetWorthChart.tsx  # Recharts wrapper
    │   └── AuthGuard.tsx      # Route-level auth check
    ├── pages/                 # One file per app page (mirrors Streamlit pages)
    │   ├── Dashboard.tsx
    │   ├── Accounts.tsx
    │   ├── Liabilities.tsx
    │   ├── Pension.tsx
    │   ├── History.tsx
    │   └── Configure.tsx
    ├── hooks/                 # Custom React hooks
    │   ├── useCurrentUser.ts  # Firebase auth state observer
    │   ├── useAccounts.ts     # Data fetching hooks per domain
    │   └── useSnapshots.ts
    └── types/                 # TypeScript types mirroring API schemas
        ├── accounts.ts
        ├── liabilities.ts
        └── snapshots.ts
```

### Structure Rationale

- **`api/` vs `app/`:** The existing `app/` package stays completely unchanged. The new `api/` package adds FastAPI on top without touching services. Clear boundary.
- **`api/schemas/`:** Separate from SQLModel models in `app/models.py`. DB models have server-only fields (e.g., `user_id` on every record — never sent to client); schemas expose only what the API surface needs.
- **`api/routers/`:** One file per domain mirrors the existing service file structure. `accounts.py` wraps `account_service.py`, `liabilities.py` wraps `liability_service.py`, etc. Direct correspondence makes navigation obvious.
- **`react-frontend/src/api/`:** All HTTP calls centralized here. Pages and hooks never call `fetch()` directly. Swap implementation without touching components.
- **`react-frontend/src/pages/`:** One-to-one with existing Streamlit pages. Same mental model for the migration.
- **`react-frontend/src/types/`:** TypeScript types generated from or manually mirroring the API response schemas. Keeps type safety across the boundary.

---

## API Route Organization: Mirror the Service Layer

| Existing Service Function | FastAPI Endpoint | Method |
|---------------------------|------------------|--------|
| `account_service.list_account_types()` | `GET /api/accounts/types` | GET |
| `account_service.list_account_entries()` | `GET /api/accounts/entries` | GET |
| `account_service.list_non_pension_entries()` | `GET /api/accounts/entries?exclude_pension=true` | GET |
| `account_service.upsert_account_entry()` | `PUT /api/accounts/entries` | PUT |
| `account_service.delete_account_entry()` | `DELETE /api/accounts/entries/{id}` | DELETE |
| `account_service.list_pension_types()` | `GET /api/pension/types` | GET |
| `account_service.list_pension_entries()` | `GET /api/pension/entries` | GET |
| `liability_service.*` | `GET|PUT|DELETE /api/liabilities/*` | varies |
| `type_service.create_account_type()` | `POST /api/configure/account-types` | POST |
| `type_service.delete_account_type()` | `DELETE /api/configure/account-types/{id}` | DELETE |
| `type_service.create_liability_type()` | `POST /api/configure/liability-types` | POST |
| `type_service.delete_liability_type()` | `DELETE /api/configure/liability-types/{id}` | DELETE |
| `snapshot_service.capture_snapshot()` | `POST /api/snapshots/capture` | POST |
| `snapshot_service.get_snapshot_history()` | `GET /api/history` | GET |
| `snapshot_service.export_csv()` | `GET /api/history/export.csv` | GET |
| `snapshot_service.import_csv()` | `POST /api/history/import` | POST |

All routes under `/api/` are protected by the `CurrentUser` dependency (Firebase token verification).

---

## Data Flow

### Authenticated API Request Flow

```
React page (e.g., Accounts.tsx)
    ↓ calls useAccounts() hook
hooks/useAccounts.ts → api/accounts.ts → api/client.ts
    ↓ user.getIdToken() → Firebase JS SDK (returns valid/refreshed token)
HTTP GET /api/accounts/entries
Authorization: Bearer <firebase-id-token>
    ↓ CORS preflight handled by CORSMiddleware (FastAPI)
api/routers/accounts.py → list_account_entries()
    ↓ Depends(get_current_user) → verify_firebase_token() → uid
    ↓ Depends(get_session) → Session(engine)
app/services/account_service.list_account_entries(session=session, user_id=uid)
    ↓ SQLModel query filtered by user_id
Cloud SQL (Unix socket)
    ↓ List[AccountEntry] SQLModel instances
JSON serialization (FastAPI auto-serializes SQLModel/Pydantic models)
    ↓
React: JSON array of account entries → renders table
```

### Balance Update + Snapshot Flow

```
React Accounts page: user submits balance form
    ↓
api/accounts.ts → PUT /api/accounts/entries (body: {account_type_id, entry_date, balance})
    ↓ FastAPI router
account_service.upsert_account_entry(session, user_id, ...)
    ↓ success
POST /api/snapshots/capture (called immediately after from React, or by server)
snapshot_service.capture_snapshot(session, user_id, snapshot_date)
    ↓ upserts snapshot (one per user per day — UniqueConstraint)
204 No Content / Snapshot object
    ↓
React invalidates query cache → refetches account entries + dashboard
```

Two design options for snapshot capture after balance update:

**Option A (recommended):** React makes two sequential calls — PUT balance, then POST snapshot. Keeps server endpoints single-responsibility. React can handle the cascade.

**Option B:** PUT balance endpoint triggers snapshot capture server-side in the same transaction. Reduces round trips but couples concerns.

Option A is recommended: easier to test, aligns with existing service layer separation (balance update and snapshot are separate service calls today).

### Firebase Auth State Flow in React

```
App mounts → firebase.ts initializes Firebase app
    ↓
main.tsx: onAuthStateChanged(auth, user => { ... })
    ↓ no user
AuthGuard redirects to /login
    ↓ user clicks "Sign in with Google"
Firebase JS SDK → Google OAuth popup → Firebase Auth token issued
    ↓ onAuthStateChanged fires with user object
AuthGuard renders children (app routes)
    ↓ every API call
user.getIdToken() → returns cached token (refreshes automatically if near expiry)
```

---

## Architectural Patterns

### Pattern 1: Thin Router, Fat Service

**What:** FastAPI routers contain zero business logic. They receive HTTP input, call one service function, handle exceptions, return results. All logic stays in `app/services/`.

**When to use:** Always. The service layer was already designed to be UI-agnostic. FastAPI routers are a third caller (after Streamlit pages and pytest tests).

**Trade-offs:** Routers are trivially thin. Some duplication in error handling boilerplate. Worth it — services remain independently testable without HTTP context.

### Pattern 2: HTTPBearer + Dependency for Auth

**What:** Use FastAPI's `HTTPBearer` security scheme to extract the `Authorization: Bearer` token. Wrap it in a `get_current_user()` dependency that returns the verified UID. Inject `CurrentUser` into any protected route.

**When to use:** Every non-public endpoint. Apply at router level via `dependencies=[Depends(get_current_user)]` if all routes in a router are protected.

**Trade-offs:** Every request hits Firebase's token verification. The Firebase Admin SDK caches Firebase's public keys locally (refreshes every hour), so most verifications are local crypto operations — fast. No database lookup needed for auth.

```python
# Apply auth to entire router at inclusion time in main.py:
app.include_router(
    accounts_router,
    dependencies=[Depends(get_current_user)],  # all routes in router are protected
)
# Or declare per-route as shown in router examples above.
```

### Pattern 3: Shared `SessionDep` Type Alias

**What:** Define `SessionDep = Annotated[Session, Depends(get_session)]` once in `deps.py`. Use it as a type annotation in every route handler. FastAPI resolves the dependency automatically.

**When to use:** Always — this is the official FastAPI + SQLModel pattern. Avoids repeating `Annotated[Session, Depends(get_session)]` in every route signature.

**Trade-offs:** One session per HTTP request, created and destroyed per request. Correct for a REST API (unlike Streamlit, which held sessions open across reruns).

### Pattern 4: Schema Separation (DB models vs API schemas)

**What:** `app/models.py` defines SQLModel table models. `api/schemas/` defines separate Pydantic models for request bodies and response shapes. Route functions receive schema objects as input and may return either schema or model objects.

**When to use:** For any field that differs between DB and API: `user_id` should never appear in response bodies (inferred from auth token); `created_at`/`updated_at` may be excluded from create request bodies.

**Trade-offs:** Some duplication between `models.py` and `schemas/`. Acceptable — the SQLModel dual-inheritance makes models serve as response schemas directly in many cases. Only create explicit schemas where the shape truly differs.

---

## Build Order: Parallel Development After API Contract

The API contract (route paths + request/response shapes) can be agreed first, then FastAPI and React developed in parallel.

**Step 1 (blocking): Define API contract**
- List all endpoints, methods, request bodies, response shapes
- Agree on JSON field names (snake_case to match Python, or camelCase for JS — pick one, configure FastAPI serialization alias if needed)
- This unblocks parallel work

**Step 2 (parallel):**

| FastAPI track | React track |
|---------------|-------------|
| `api/main.py` + `api/deps.py` setup | Vite project scaffold + Firebase JS SDK init |
| `api/routers/accounts.py` + `api/schemas/accounts.py` | `src/api/accounts.ts` + `src/types/accounts.ts` |
| `api/routers/liabilities.py` | `src/api/liabilities.ts` |
| `api/routers/configure.py` | Configure page |
| `api/routers/snapshots.py` + `api/routers/history.py` | Dashboard + History pages |

**Step 3 (integration):** Connect React to live FastAPI. Fix any contract mismatches. End-to-end auth flow testing.

**Step 4 (deployment):** Firebase Hosting deploy for React (`firebase deploy --only hosting`). FastAPI on Cloud Run replaces Streamlit (or runs as separate service initially).

**Dependency constraints:**
- `api/deps.py` must exist before any router (imports it)
- Firebase project web config must be known before React `firebase.ts` can be written (API key, project ID, app ID)
- FastAPI CORS must list the Firebase Hosting origin before React can call the API in production
- Streamlit can continue running on Cloud Run during migration — React + FastAPI can be a separate Cloud Run service initially

---

## Integration Points

### External Services

| Service | Integration Pattern | Confidence | Notes |
|---------|---------------------|------------|-------|
| Firebase Auth (React) | Firebase JS SDK modular API — `signInWithPopup`, `onAuthStateChanged`, `getIdToken` | HIGH | Use modular (v9+) SDK, not compat layer |
| Firebase Auth (FastAPI) | `firebase_admin.auth.verify_id_token()` — already in `auth_service.py` | HIGH | No changes needed; wrap in FastAPI dep |
| Firebase Hosting | `firebase deploy --only hosting` from `react-frontend/dist/` | HIGH | Static host; needs `firebase.json` rewrite rules for SPA routing |
| Cloud SQL | Unchanged — Unix socket via Cloud Run Auth Proxy | HIGH | FastAPI uses same engine as Streamlit |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `api/routers/` → `app/services/` | Direct Python function calls | The entire point — no HTTP between them |
| `api/deps.py` → `app/database.py` | Reuses `engine` object directly | Don't create a second engine; import the existing one |
| `api/deps.py` → `app/services/auth_service.py` | Calls `verify_firebase_token()` | Already production-hardened; no rewrite needed |
| React `src/api/` → FastAPI | HTTPS REST with `Authorization: Bearer` | All calls go through `api/client.ts` |
| React `src/pages/` → `src/api/` | Custom hooks that call api functions | Pages never call fetch directly |

---

## Anti-Patterns

### Anti-Pattern 1: Business Logic in Routers

**What people do:** Put filtering, computation, or validation logic directly in FastAPI route handler functions.

**Why it's wrong:** The services are already tested and correct. Duplicating logic in routers creates divergence. The services can't be tested independently anymore.

**Do this instead:** Routers call one service function. Period. If the service doesn't exist for a use case, add it to the service file — not the router.

### Anti-Pattern 2: Creating a New SQLAlchemy Engine in FastAPI

**What people do:** Create a second `create_engine()` call in `api/deps.py` or `api/main.py` with a new URL.

**Why it's wrong:** Two engines = two connection pools = doubled Cloud SQL connections. On the free tier `db-f1-micro` this causes exhaustion. Also, session lifecycle between engines is undefined.

**Do this instead:** Import `engine` from `app/database.py` in `api/deps.py`. One engine, one pool.

### Anti-Pattern 3: Caching the Firebase ID Token String in React State

**What people do:** Store `idToken` as a `useState` variable, attach it to all requests from that state.

**Why it's wrong:** Firebase ID tokens expire after 1 hour. The cached string becomes invalid. API calls start returning 401 silently.

**Do this instead:** Call `user.getIdToken()` in the API client layer before every request. The Firebase JS SDK returns a cached valid token or automatically fetches a refreshed one — this call is fast when the token is still valid.

### Anti-Pattern 4: Exposing `user_id` in API Request Bodies

**What people do:** Include `user_id` as a field in POST/PUT request body schemas, letting the client tell the server who they are.

**Why it's wrong:** Client-provided user identity is trivially forgeable. Any client can claim any `user_id`.

**Do this instead:** `user_id` is always extracted from the verified Firebase token via `CurrentUser` dependency. It never appears in request body schemas. The router passes `user_id=user_id` (from the dep) to service functions.

### Anti-Pattern 5: Using `allow_origins=["*"]` with `allow_credentials=True`

**What people do:** Set both `allow_origins=["*"]` and `allow_credentials=True` in CORSMiddleware.

**Why it's wrong:** Browsers reject this combination per CORS spec — credentialed requests require explicit origin lists. This causes silent CORS failures in production that work fine in development (where `localhost` might be explicitly listed).

**Do this instead:** List explicit origins: Firebase Hosting domain(s) + `http://localhost:5173` for dev.

---

## Scaling Considerations

This is a single-user app. The architecture is intentionally simple.

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1 user (current target) | Current plan is correct. No changes needed. |
| 1-10 users | Add basic rate limiting (FastAPI middleware). Connection pool stays small (`pool_size=2`). |
| 10+ users | Multi-user is explicitly out of scope. Would require removing single-user UID guard and adding proper multi-tenancy — significant change. |

The Cloud Run + Cloud SQL free tier (`db-f1-micro`) is the binding constraint. Keep `pool_size=2` in the engine. FastAPI's async I/O is not needed here — synchronous service functions and sync route handlers work correctly with thread pool.

---

## Sources

**HIGH confidence (direct codebase inspection):**
- `/Users/kristiakarakatsani/Repos/finance-tracker/app/services/account_service.py` — service function signatures (session, user_id as kwargs)
- `/Users/kristiakarakatsani/Repos/finance-tracker/app/services/auth_service.py` — `verify_firebase_token()` already exists and production-hardened
- `/Users/kristiakarakatsani/Repos/finance-tracker/app/database.py` — `get_session()` generator and engine pattern
- `/Users/kristiakarakatsani/Repos/finance-tracker/app/models.py` — SQLModel model shapes (AccountEntry, LiabilityEntry, Snapshot, etc.)
- `/Users/kristiakarakatsani/Repos/finance-tracker/.planning/codebase/ARCHITECTURE.md` — existing layer analysis

**HIGH confidence (official documentation, fetched 2026-04-04):**
- FastAPI dependency injection: https://fastapi.tiangolo.com/tutorial/dependencies/
- FastAPI bigger applications (APIRouter): https://fastapi.tiangolo.com/tutorial/bigger-applications/
- FastAPI SQL databases with SQLModel: https://fastapi.tiangolo.com/tutorial/sql-databases/
- FastAPI CORS middleware: https://fastapi.tiangolo.com/tutorial/cors/
- FastAPI OAuth2 / Bearer token pattern: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/

**MEDIUM confidence (training knowledge, August 2025 cutoff — verify at implementation):**
- Firebase JS SDK modular API `getIdToken()` auto-refresh behavior
- `firebase deploy --only hosting` and `firebase.json` SPA rewrite rules
- Vite project structure conventions (`src/`, `public/`, `index.html` at root)

---

*Architecture research for: FastAPI REST layer + React SPA migration on existing Python/SQLModel net worth tracker*
*Researched: 2026-04-04*
