# Pitfalls Research

**Domain:** Streamlit → React + FastAPI migration (Firebase Auth, Cloud Run, Firebase Hosting, Recharts)
**Researched:** 2026-04-04
**Confidence:** HIGH for FastAPI/CORS patterns (verified against official FastAPI docs); MEDIUM for Firebase Hosting rewrites and Recharts data format (training knowledge, not verified against live docs due to tool restrictions — flag for manual verification)

---

## Critical Pitfalls

### Pitfall 1: `allow_credentials=True` Combined With `allow_origins=["*"]` Breaks All Authenticated Requests

**What goes wrong:**
The CORS spec forbids `allow_credentials=True` with a wildcard origin. If FastAPI's `CORSMiddleware` is configured with `allow_origins=["*"]` and `allow_credentials=True`, browsers silently reject every preflight response. The React app sends `Authorization: Bearer <token>` (a credential header), the browser fires an `OPTIONS` preflight, receives a wildcard `Access-Control-Allow-Origin`, and blocks the request. Every API call returns a CORS error in the browser console. The FastAPI server processes the request and returns 200 — the error only appears in the browser, making it look like a frontend bug.

**Why it happens:**
During local development, developers add `allow_origins=["*"]` to stop CORS errors fast. It works because local dev often uses the same origin. When deployed, the React app is on `https://PROJECT.web.app` and FastAPI is on `https://finance-tracker-XYZ.run.app` — different origins, credentials required. Developers copy the `allow_origins=["*"]` from local config into production without adjusting it.

**How to avoid:**
Set `allow_origins` to the explicit Firebase Hosting URL from day one. Never use `["*"]` with credentials. The CORSMiddleware must be:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",           # Vite dev server
        "https://PROJECT_ID.web.app",      # Firebase Hosting primary
        "https://PROJECT_ID.firebaseapp.com",  # Firebase Hosting alt
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
```
None of `allow_origins`, `allow_methods`, `allow_headers` can be `["*"]` when `allow_credentials=True`.

**Warning signs:**
- Browser console shows "CORS error" but Cloud Run logs show requests completing successfully with 200
- Error only appears after deploying (works on localhost)
- `Access-Control-Allow-Origin: *` in response headers when credentials are being sent

**Phase to address:** FastAPI setup phase (very first phase — set correct CORS before writing any routes)

---

### Pitfall 2: Firebase Hosting Rewrites and Direct Cloud Run CORS Headers Conflict

**What goes wrong:**
There are two deployment topologies for this migration. If Firebase Hosting rewrites proxy `/api/*` to Cloud Run, Firebase Hosting adds its own `Access-Control-Allow-Origin` header before returning the response to the browser. If FastAPI also adds the header via `CORSMiddleware`, the browser receives duplicate `Access-Control-Allow-Origin` headers and rejects the response. Alternatively, if the React app calls the Cloud Run URL directly (not via the Firebase Hosting rewrite), CORS must be configured in FastAPI because Firebase Hosting is not in the path — but if the Cloud Run URL changes, the hardcoded URL breaks.

There is also a second failure mode: the Firebase Hosting rewrite for Cloud Run uses a `run` key with `serviceId` and `region` fields. If the `region` field does not match the Cloud Run service's actual region, requests return 404 silently with no useful error message.

**Why it happens:**
Two competing architectures are often conflated: (a) React → Firebase Hosting rewrite → Cloud Run (CORS handled by Hosting, FastAPI CORS middleware not needed for browser requests) vs (b) React → Cloud Run directly (CORS required in FastAPI). Developers enable `CORSMiddleware` in FastAPI regardless, causing header duplication when option (a) is used.

**How to avoid:**
Pick one architecture and commit to it. For this project, the simplest approach is: React calls Cloud Run directly (no Firebase Hosting rewrites for the API). This avoids the header conflict, the rewrite config complexity, and the region matching problem. FastAPI handles all CORS via `CORSMiddleware`. The Cloud Run URL is stored as a `VITE_API_BASE_URL` environment variable in the React build, set to the Firebase Hosting custom domain or the Cloud Run URL.

If rewrites are used instead, disable `CORSMiddleware` in FastAPI (Firebase Hosting adds the CORS headers), and configure the `firebase.json` rewrite as:
```json
{
  "hosting": {
    "rewrites": [
      {
        "source": "/api/**",
        "run": {
          "serviceId": "finance-tracker",
          "region": "us-central1"
        }
      },
      { "source": "**", "destination": "/index.html" }
    ]
  }
}
```
The `region` must exactly match the Cloud Run service region shown in `gcloud run services describe`.

**Warning signs:**
- Browser receives response headers with two `Access-Control-Allow-Origin` values
- API calls return 404 when routed through Firebase Hosting but work when hitting Cloud Run URL directly
- CORS errors disappear on direct Cloud Run URL but appear on `*.web.app` domain

**Phase to address:** Deployment phase — decide the architecture (direct Cloud Run calls vs. Hosting rewrites) before building the React API client

---

### Pitfall 3: Firebase ID Token Expiry Not Handled in React — Silent 401s After 1 Hour

**What goes wrong:**
Firebase ID tokens expire after 1 hour. The Firebase JS SDK automatically refreshes the token in the background via `onAuthStateChanged`, but `getIdToken()` returns the cached (potentially expired) token unless called with `getIdToken(true)` (force refresh). If the React app stores the token in state once at login and reuses it for all API calls, requests start returning 401 after 60 minutes without any visible error. FastAPI returns 401 with `{"detail": "Token expired"}` but the React app has no global interceptor to handle this, so the UI just shows a generic error or hangs.

**Why it happens:**
Developers call `getIdToken()` once on login, store the token in React state or `localStorage`, and pass it as a header. Firebase re-signs the token silently but the stored reference is stale. The SDK does not push the new token to the app unless the app explicitly requests it or listens to `onIdTokenChanged`.

**How to avoid:**
Never store the raw token in React state. Always call `getIdToken()` (without force) immediately before each API request — the SDK returns a cached token if valid, or refreshes it if near expiry. For an axios-based API client:
```typescript
import { getAuth } from "firebase/auth";

const getToken = async (): Promise<string> => {
  const user = getAuth().currentUser;
  if (!user) throw new Error("Not authenticated");
  return user.getIdToken(); // SDK handles refresh automatically
};
```
Add a global response interceptor: if any API call returns 401, force-refresh with `getIdToken(true)` and retry once. If it still returns 401, redirect to login.

**Warning signs:**
- App works for the first hour, then API calls silently fail
- `401 Unauthorized` responses appear exactly 60 minutes after login
- Firebase console shows valid user session but API rejects token

**Phase to address:** React API client phase — build the token refresh pattern into the API client from the start, not retrofitted later

---

### Pitfall 4: FastAPI Returns `Decimal` Fields as Strings in JSON — React Gets Unexpected Types

**What goes wrong:**
Python's `Decimal` type is not JSON-serializable by default. SQLModel models use `Decimal` for all balance fields (`balance`, `amount`, `total_assets`, `net_worth`, etc.). FastAPI's default JSON encoder converts `Decimal` to a string (e.g., `"10753.42"`) rather than a number. React code that does arithmetic on these values — for example, subtracting liabilities from assets to display net worth — receives strings. JavaScript string arithmetic (`"50000" - "10000"`) works coincidentally for subtraction (implicit coercion), but `"50000" + "10000"` returns `"5000010000"`. Chart libraries like Recharts expect numbers in the data array; passing strings causes charts to render as flat lines or not render at all.

**Why it happens:**
FastAPI's `jsonable_encoder` calls `str()` on `Decimal` by default. The behaviour is not obvious from the Pydantic model definition — the field looks numeric but the serialized JSON is a string. This is only discovered when React does addition on the values.

**How to avoid:**
Define explicit Pydantic response schemas (separate from the SQLModel table models) where all monetary fields are typed as `float` rather than `Decimal`. Use `model_config = ConfigDict(json_encoders={Decimal: float})` in the response schema, or add a custom FastAPI serializer. Verify with `curl` that the API returns `"balance": 10753.42` (number) not `"balance": "10753.42"` (string) before building the frontend. For Recharts: all `dataKey` values must be numeric — validate this in the API response before wiring charts.

**Warning signs:**
- `typeof response.balance === "string"` in browser console
- Net worth addition returns a concatenated string instead of a sum
- Recharts chart renders as flat or empty when data is correct in the network tab

**Phase to address:** FastAPI route implementation phase — validate JSON serialization for every endpoint with `curl` or the FastAPI `/docs` UI before React touches the data

---

### Pitfall 5: Recharts Expects One Object Per X-Axis Point With All Series as Keys — Plotly Shape Is Different

**What goes wrong:**
Plotly charts use a separate data series per trace: `{x: [...dates], y: [...values], name: "Assets"}`. Multiple traces are separate objects in an array. Recharts requires the inverse: one object per X-axis point, with all series as keys on that object. For the net worth trend chart with assets, liabilities, and net worth lines:

```typescript
// Plotly shape (does NOT work in Recharts):
[
  { x: ["2025-01", "2025-02"], y: [50000, 52000], name: "Assets" },
  { x: ["2025-01", "2025-02"], y: [10000, 9500], name: "Liabilities" },
]

// Recharts shape (required):
[
  { date: "2025-01", assets: 50000, liabilities: 10000, netWorth: 40000 },
  { date: "2025-02", assets: 52000, liabilities: 9500, netWorth: 42500 },
]
```

If the API returns Plotly-shaped data (separate arrays per series), the frontend must pivot it before passing it to Recharts. If the pivot is skipped or wrong, charts render empty.

The pie/donut chart for asset allocation similarly expects `[{ name: "ISA", value: 25000 }, ...]` — the `name` and `value` keys are hardcoded in Recharts `<Pie>` unless overridden by `nameKey` and `dataKey` props.

**Why it happens:**
Developers shape the API response to match what the existing Plotly charts consume (Python dict with separate x/y arrays per series, matching the current Streamlit code in `frontend/pages/`). The React dev then uses the same API response directly with Recharts without realising the data pivot is required.

**How to avoid:**
Shape all API responses in Recharts format from the beginning. For time-series endpoints, return an array of objects with one entry per date, all series as keys:
```json
[
  { "date": "2025-01-01", "assets": 50000.0, "liabilities": 10000.0, "net_worth": 40000.0 },
  { "date": "2025-02-01", "assets": 52000.0, "liabilities": 9500.0, "net_worth": 42500.0 }
]
```
For allocation endpoints (pie charts), return `[{ "name": "ISA", "value": 25000.0 }]`.
Do not mirror the Plotly/Streamlit data shapes in the FastAPI responses — these are different consumers with different requirements.

**Warning signs:**
- Recharts chart renders with correct axes but no lines/bars
- `LineChart` `<Line dataKey="y" />` references a key that doesn't exist in the data object
- Pie chart shows correct legend but empty arcs

**Phase to address:** FastAPI route design phase — specify and test the exact JSON shape for every chart-related endpoint before building React components

---

### Pitfall 6: Firebase Hosting SPA Routing — All Non-Root Paths Return 404 Without Catch-All Rewrite

**What goes wrong:**
React Router uses client-side routing. When a user navigates directly to `https://PROJECT.web.app/accounts` or refreshes the page on any route other than `/`, Firebase Hosting returns a 404 because there is no `accounts.html` file in the hosting bucket. The React app never loads. This also breaks any bookmarked URL and OAuth redirect flows (Google Sign-In redirects back to the app at a specific path).

**Why it happens:**
Firebase Hosting serves static files from the deploy directory. Without a catch-all rewrite, unknown paths return 404. Developers test locally with Vite (`vite dev`) which handles SPA routing natively, so the issue only appears after deploying to Firebase Hosting.

**How to avoid:**
The `firebase.json` must include a catch-all rewrite to `index.html` as the last rewrite rule. This is distinct from any API rewrites:
```json
{
  "hosting": {
    "public": "dist",
    "rewrites": [
      { "source": "**", "destination": "/index.html" }
    ]
  }
}
```
If API rewrites are also configured, the catch-all must be last. Verify by deploying and navigating directly to a non-root path.

**Warning signs:**
- App works at `https://PROJECT.web.app` but 404 on `https://PROJECT.web.app/accounts`
- Page refresh on any route returns Firebase Hosting 404 error page
- Google Sign-In popup redirects back to 404

**Phase to address:** React deployment phase — add the catch-all rewrite before the first Firebase Hosting deploy

---

### Pitfall 7: FastAPI Wrapping Existing Services — Session Passed as Positional Arg Breaks Keyword-Only Convention

**What goes wrong:**
All existing service functions use keyword-only arguments: `upsert_account_entry(*, session=session, user_id=uid, ...)`. FastAPI route handlers receive a session via `Depends(get_session)` and must call service functions correctly. If a FastAPI route handler uses `session` as a positional argument or renames it, and calls the service function positionally, Python raises `TypeError: takes 0 positional arguments but 1 was given`. This is a subtle bug because the services work correctly in tests (which call them with explicit keyword args) but fail only when called from FastAPI route handlers.

**Why it happens:**
The `*` in the existing function signatures enforces keyword-only calling. FastAPI route handlers are new code written quickly, and developers call `account_service.upsert_account_entry(session, user_id, ...)` positionally without checking the service signature.

**How to avoid:**
Always call services with keyword arguments from FastAPI route handlers. Create a `SessionDep` type alias for injection:
```python
from typing import Annotated
from fastapi import Depends
from sqlmodel import Session
from app.database import get_session

SessionDep = Annotated[Session, Depends(get_session)]
```
Then in route handlers, always use `session=session` when calling existing services. Add a linting rule or comment to service files warning that all functions are keyword-only.

**Warning signs:**
- `TypeError: takes 0 positional arguments` in FastAPI route handler logs
- Service works in `pytest` but fails when called through a FastAPI endpoint
- Error only appears on specific routes, not all

**Phase to address:** FastAPI route implementation phase — enforce keyword argument calling in code review for every service call

---

### Pitfall 8: Firebase Admin SDK Not Initialized Before First Request on Cloud Run

**What goes wrong:**
The existing `auth_service.py` initializes Firebase Admin SDK via `init_firebase_admin()`. In Streamlit, this was called once at startup in `main()`. In FastAPI, there is no explicit startup hook called by default. If `init_firebase_admin()` is not placed in a FastAPI lifespan event, it may not be called before the first request arrives. The first request that tries to verify a token calls `auth.verify_id_token()` on an uninitialized app and raises `ValueError: The default Firebase app does not exist`.

**Why it happens:**
FastAPI has a `lifespan` context manager for startup/shutdown events (replacing the deprecated `@app.on_event("startup")`). Developers unfamiliar with FastAPI's lifecycle add initialization inside route handler functions or forget it entirely, assuming it runs at module import time. The `init_firebase_admin()` function has the correct guard (`if firebase_admin._apps`), but it must be called somewhere.

**How to avoid:**
Use FastAPI's `lifespan` context manager:
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.services.auth_service import init_firebase_admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_firebase_admin()
    yield

app = FastAPI(lifespan=lifespan)
```
Do not call `init_firebase_admin()` inside the auth dependency — it will be called on every request (harmless due to the guard, but adds unnecessary overhead and log noise).

**Warning signs:**
- `ValueError: The default Firebase app does not exist` on first request
- App works after the second request (if initialization is accidentally in the dependency and the guard kicks in)
- Error does not appear in local testing if module-level initialization happens to run

**Phase to address:** FastAPI setup phase — establish the lifespan pattern before writing any authenticated routes

---

### Pitfall 9: Cloud Run Scheduled Stop Causes Database Connection Errors During Active Sessions

**What goes wrong:**
The existing Terraform config stops the Cloud SQL instance at 11pm via Cloud Scheduler. The FastAPI app on Cloud Run holds a SQLAlchemy connection pool. When Cloud SQL stops abruptly, existing pool connections become stale. On the next request after Cloud SQL restarts (8am), SQLAlchemy attempts to use a stale connection and raises `OperationalError: server closed the connection unexpectedly`. This silent failure returns a 500 to the React app with no useful error message.

**Why it happens:**
SQLAlchemy's connection pool does not know that the backing database has been stopped. It assumes connections are reusable until the connection is actually used and fails. The `pool_pre_ping=True` option causes SQLAlchemy to issue a `SELECT 1` before using each connection, discarding stale connections automatically — but this option is not currently set in `app/database.py`.

**How to avoid:**
Add `pool_pre_ping=True` to the SQLAlchemy engine in `app/database.py`:
```python
engine = create_engine(settings.database_url, echo=settings.debug, pool_pre_ping=True)
```
Also set a short `pool_recycle` interval (e.g., 1800 seconds) to prevent connections from being held longer than the database scheduler window. This is more important for FastAPI than Streamlit because FastAPI keeps long-running server processes with persistent connection pools.

**Warning signs:**
- 500 errors on the first requests of the day (around 8am when Cloud SQL restarts)
- SQLAlchemy `OperationalError: server closed the connection unexpectedly` in Cloud Run logs
- App works normally after a few requests (as stale connections are replaced)

**Phase to address:** FastAPI setup phase — add `pool_pre_ping=True` when creating the FastAPI engine; can reuse the existing `app/database.py` engine if the same is imported

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| `allow_origins=["*"]` in CORS config | No CORS errors during development | All authenticated requests fail in production | Never — list specific origins from day one |
| Store Firebase token in React `useState` once at login | Simple auth state | Token expires after 1 hour, API calls return 401 silently | Never — always call `getIdToken()` per-request |
| Return SQLModel table models directly from FastAPI routes | No extra schema boilerplate | Decimal fields serialize as strings; internal fields (e.g., `user_id`) may leak | Never for Decimal fields — define response schemas |
| Skip `pool_pre_ping=True` on the engine | Slightly faster connection checkout | Stale connection errors after Cloud SQL scheduled stops | Only acceptable if Cloud SQL is always on (not the case here) |
| Mirror Plotly data shape in FastAPI responses | Reuse existing service output directly | Recharts requires pivot — data pivot either happens in every React component or requires API rework | Never — shape for Recharts at the API layer |
| No catch-all rewrite in `firebase.json` | Simpler config | Direct URL navigation and page refresh returns 404 | Never |
| Verify Firebase token inside FastAPI dependency on every call with `check_revoked=True` | Ensures revoked tokens are caught | `check_revoked=True` makes a network call to Firebase on every request — latency spike | Only for sensitive operations; for a single-user app, skip `check_revoked` |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| FastAPI CORSMiddleware | `allow_origins=["*"]` with `allow_credentials=True` | List explicit Firebase Hosting origins; none of origins/methods/headers can be `"*"` with credentials |
| Firebase Hosting rewrites | Missing `region` field in `run` rewrite block | Always specify `region` matching `gcloud run services describe` output |
| Firebase Hosting SPA | No catch-all rewrite | Add `{"source": "**", "destination": "/index.html"}` as last rewrite rule |
| Firebase JS SDK token | Call `getIdToken()` once at login, store in state | Call `getIdToken()` before each API request; SDK handles refresh internally |
| FastAPI + SQLModel Decimal | Return table models directly | Define separate response schemas with `float` for monetary fields, or configure `json_encoders` |
| Existing service functions | Call with positional args in route handlers | All existing services use `*` keyword-only — always call with `session=session, user_id=uid, ...` |
| FastAPI lifespan | Initialize Firebase Admin SDK in request handler | Use `lifespan` context manager for startup initialization |
| SQLAlchemy pool + Cloud SQL scheduler | Default pool with no ping | Add `pool_pre_ping=True` and `pool_recycle=1800` to engine creation |
| Recharts data format | Pass Plotly-shaped separate series arrays | Pivot to one-object-per-date format with all series as keys before passing to Recharts |
| React Router + Firebase Hosting | Refresh on non-root path returns 404 | Firebase Hosting catch-all rewrite to `index.html` is required |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| `getIdToken(true)` on every API call | 200-400ms added latency per request (forced token refresh roundtrip to Firebase) | Call `getIdToken()` without `true`; only force-refresh on 401 responses | Every request from day one |
| No `pool_pre_ping` with scheduled Cloud SQL stops | 500 errors on first requests after 8am restart | `pool_pre_ping=True` on engine | Every morning after Cloud SQL restarts |
| FastAPI `SessionDep` without yield — session never closed | Connection pool exhaustion on `db-f1-micro` (25 connection limit) | Always use `yield` in `get_session()`, never `return` | After ~10 concurrent requests on Cloud Run |
| Recharts re-renders entire chart on every data fetch | Chart flicker on polling or navigation | Memoize chart data with `useMemo`; stable object references for data prop | Immediately visible but not a crash — UX degradation |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| FastAPI returns `user_id` in API responses | Internal Firebase UID exposed to browser; useless for single-user app but bad habit | Exclude `user_id` from all response schemas — it is a server-side identity field |
| Hardcoded Cloud Run URL in React source code | URL is public in the built JS bundle — acceptable for a personal app, but the URL changes on redeploy | Use `VITE_API_BASE_URL` environment variable set at build time; document the URL is public |
| `allow_credentials=True` without HTTPS in production | Credentials sent over HTTP can be intercepted | Cloud Run and Firebase Hosting both terminate TLS — ensure React never hits the Cloud Run URL over HTTP |
| Firebase Admin SDK initialized with overly broad service account | Compromised service account has broad GCP access | Use the existing minimal IAM roles (`cloudsql.client`, `secretmanager.secretAccessor`) — do not grant Editor or Owner |
| No ALLOWED_FIREBASE_UID check in FastAPI token verification | If someone obtains the Cloud Run URL, any valid Firebase user could call the API | Preserve the existing `settings.allowed_firebase_uid` check in the FastAPI auth dependency — same guard as the current `auth_service.verify_firebase_token()` |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No loading state during API calls | UI appears frozen during fetch; no feedback | Use React Query or SWR with `isLoading` states; show skeleton loaders for chart areas |
| No error boundary around charts | One bad API response crashes the entire page | Wrap each chart section in an error boundary; show "No data" placeholder instead of crashing |
| Recharts `<Tooltip>` shows raw floats from API | `£40253.819999` instead of `£40,253.82` | Format all monetary values in the `formatter` prop of `<Tooltip>` and `<YAxis tickFormatter>` |
| Google Sign-In popup blocked by browser | No visible error; popup blocked silently | Trigger `signInWithPopup()` only in direct click handlers — never from `useEffect` or async calls not initiated by user interaction |
| React app shows blank screen after Firebase Hosting cold path | SPA not yet loaded when token refresh fires | Show a full-page loading spinner until `onAuthStateChanged` fires for the first time |

---

## "Looks Done But Isn't" Checklist

- [ ] **CORS:** Verify with `curl -H "Origin: https://PROJECT.web.app" -H "Authorization: Bearer TOKEN" -X OPTIONS https://CLOUDRUN_URL/api/accounts` returns `Access-Control-Allow-Origin: https://PROJECT.web.app` (not `*`)
- [ ] **Token Refresh:** Stay logged in for 65 minutes; confirm API calls still succeed (tests the `getIdToken()` per-request pattern)
- [ ] **Decimal serialization:** `curl https://CLOUDRUN_URL/api/accounts` — verify `balance` field is a JSON number (`10753.42`), not a string (`"10753.42"`)
- [ ] **SPA Routing:** Navigate directly to `https://PROJECT.web.app/accounts` in a new browser tab — must load the React app, not a 404
- [ ] **Recharts data:** Open browser devtools → Network tab → verify chart data endpoint returns one object per date with all series as numeric keys
- [ ] **Firebase Admin init:** Check Cloud Run startup logs — `Firebase Admin SDK initialized successfully` must appear before the first request is served
- [ ] **Pool pre-ping:** After the Cloud SQL scheduled stop at 11pm restarts at 8am, send a request — must succeed (not return 500)
- [ ] **Service keyword args:** `grep -r "account_service\.\|snapshot_service\." api/` — all calls must use `session=session, user_id=uid` keyword form
- [ ] **ALLOWED_FIREBASE_UID guard:** Attempt to call the API with a Firebase token from a different Firebase account — must return 403

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| CORS wildcard with credentials breaks production | LOW | Fix `allow_origins` list in FastAPI config, redeploy Cloud Run — no data changes needed |
| Firebase Hosting rewrite region mismatch causes 404 | LOW | Update `firebase.json` with correct region, run `firebase deploy --only hosting` |
| Decimal-as-string breaks React arithmetic | MEDIUM | Add response schemas with float fields or custom encoder; update all affected routes; verify frontend arithmetic |
| Token not refreshed — users get 401 after 1 hour | LOW | Add `getIdToken()` call to API client interceptor; no backend change needed |
| Missing catch-all rewrite — direct URL navigation fails | LOW | Add rewrite to `firebase.json`, redeploy hosting |
| Firebase Admin not initialized — first request crashes | LOW | Add `lifespan` startup handler, redeploy |
| Stale pool connections after Cloud SQL restart | LOW | Add `pool_pre_ping=True` to engine, redeploy |
| Recharts receives Plotly-shaped data — charts blank | MEDIUM | Rewrite API response shape for affected endpoints; update React components to use new keys |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| CORS wildcard with credentials | FastAPI setup (first phase) | `curl` preflight check returns specific origin, not `*` |
| Firebase Hosting rewrite region mismatch | Deployment phase | Direct URL navigation works after first `firebase deploy` |
| Firebase Hosting SPA 404 | Deployment phase | Refresh on `/accounts` loads React app |
| Token expiry not handled | React API client phase | 65-minute session test passes |
| Decimal serialization as string | FastAPI route implementation | `curl` response shows numeric balance fields |
| Recharts data format mismatch | FastAPI route design (before React) | Chart endpoints return one-object-per-date; charts render correctly |
| Service keyword-only arg convention | FastAPI route implementation | All service calls use keyword args; passes code review |
| Firebase Admin SDK not initialized | FastAPI setup | Startup logs show SDK init before first request |
| Stale pool after Cloud SQL restart | FastAPI setup | 8am post-restart request succeeds |
| ALLOWED_FIREBASE_UID not preserved | FastAPI auth dependency | Foreign Firebase token returns 403 |

---

## Sources

- FastAPI official docs — CORSMiddleware parameters: `https://fastapi.tiangolo.com/tutorial/cors/` — HIGH confidence (verified via WebFetch 2026-04-04)
- FastAPI official docs — SQLModel session pattern with Depends/yield: `https://fastapi.tiangolo.com/tutorial/sql-databases/` — HIGH confidence (verified via WebFetch 2026-04-04)
- FastAPI official docs — dependency injection: `https://fastapi.tiangolo.com/tutorial/dependencies/` — HIGH confidence (verified via WebFetch 2026-04-04)
- Codebase inspection — `app/services/auth_service.py`, `app/services/account_service.py`, `app/services/snapshot_service.py`, `app/database.py`, `app/models.py`, `app/config.py`, `terraform/main.tf` — HIGH confidence (direct inspection 2026-04-04)
- Firebase Hosting rewrites config and `run` key syntax — MEDIUM confidence (training knowledge; WebFetch blocked — verify against `https://firebase.google.com/docs/hosting/config` during deployment phase)
- Recharts data format requirements — MEDIUM confidence (training knowledge; WebFetch blocked — verify against `https://recharts.org/en-US/api` during React chart phase)
- Firebase JS SDK `getIdToken()` refresh behaviour — MEDIUM confidence (well-established pattern; verify against Firebase JS SDK docs during React auth phase)
- SQLAlchemy `pool_pre_ping` behaviour — HIGH confidence (SQLAlchemy core documentation pattern, widely established)

---
*Pitfalls research for: Streamlit → React + FastAPI migration (Firebase Auth, Cloud Run, Firebase Hosting, Recharts)*
*Researched: 2026-04-04*
