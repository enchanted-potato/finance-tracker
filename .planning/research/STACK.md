# Stack Research

**Domain:** React + TypeScript frontend with FastAPI REST layer (v2.0 migration)
**Researched:** 2026-04-04
**Confidence:** MEDIUM — Core library versions from training knowledge (cutoff August 2025); Firebase JS SDK version from prior Phase 4 research (2026-02-18, HIGH confidence); FastAPI installation pattern confirmed via official docs fetch. Verify specific npm package versions with `npm info <pkg> version` before pinning.

---

## Existing Stack (Already Validated — Do Not Re-Research)

| Technology | Version (locked) | Purpose |
|------------|-----------------|---------|
| Python | 3.12 | Runtime |
| SQLModel | (see uv.lock) | ORM |
| psycopg2-binary | (see uv.lock) | PostgreSQL driver |
| firebase-admin | 7.1.0 | Server-side Firebase ID token verification |
| pydantic-settings | (see uv.lock) | Config from env vars |
| loguru | (see uv.lock) | Logging |
| uv | latest | Package management |
| Cloud SQL (PostgreSQL 15) | db-f1-micro | Managed database |
| Cloud Run | N/A | Container hosting |

---

## New Capabilities: React Frontend

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| React | 18.x | UI framework | Stable LTS release; shadcn/ui and Recharts both require React 18 |
| TypeScript | 5.x | Type safety | Industry standard for React projects; catches API contract errors at compile time |
| Vite | 5.x | Build tool + dev server | Fastest dev server for React; native ES modules, HMR; Firebase Hosting serves the static build output |
| Tailwind CSS | 3.x | Utility-first CSS | shadcn/ui is built on Tailwind; dark mode via `dark:` variants fits the midnight colour scheme |
| shadcn/ui | latest CLI | Component library | Not a package — CLI copies components into your repo. Built on Radix UI primitives + Tailwind. Zero runtime overhead, fully customizable. Correct choice for a bespoke dark UI. |
| Recharts | 2.x | Chart library | React-native charting (not a wrapper). Replaces Plotly. Composable API matches how the dashboard already separates chart types. Works without a build-time plugin. |
| Firebase JS SDK | 12.9.0 | Client-side auth | Already validated in Phase 4 research (2026-02-18). Google Sign-In popup + `onAuthStateChanged` persistence. Install via npm for TypeScript types. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `react-router-dom` | 6.x | Client-side routing | One route per page (Dashboard, Accounts, Liabilities, Pension, History, Configure). Use `createBrowserRouter`. |
| `axios` | 1.x | HTTP client | Cleaner interceptor support than `fetch` — needed to attach Firebase ID token to every request via a request interceptor. Alternative: use `fetch` with a wrapper. |
| `date-fns` | 3.x | Date formatting | Format snapshot dates as "Jan 2025". Lightweight; no Moment.js. |
| `react-hook-form` | 7.x | Form state management | Balance entry forms, account CRUD forms. Reduces re-renders vs controlled inputs. |
| `zod` | 3.x | Runtime schema validation | Validate API response shapes client-side; pair with `react-hook-form` resolver for form validation. |
| `lucide-react` | latest | Icon set | shadcn/ui uses lucide-react by default; consistent with its component examples. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `@vitejs/plugin-react` | Vite plugin for React JSX transform | Required in `vite.config.ts`; use `@vitejs/plugin-react` (SWC-based is faster: `@vitejs/plugin-react-swc`) |
| `@types/react` / `@types/react-dom` | TypeScript declarations for React | Dev dep; must match React 18 |
| `eslint` + `eslint-plugin-react-hooks` | Lint rules for hooks | Catches stale closure bugs before runtime |
| `prettier` | Code formatting | Consistent with Ruff on Python side |
| Firebase CLI (`firebase-tools`) | Deploy to Firebase Hosting | `npm install -g firebase-tools`; run `firebase deploy --only hosting` |

---

## New Capabilities: FastAPI Backend

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| FastAPI | 0.115.x | REST API framework | Python-native, async, automatic OpenAPI docs. Wraps existing SQLModel services directly — no architectural change, services stay unchanged. |
| Uvicorn | 0.30.x | ASGI server | FastAPI's standard production server; replaces Streamlit's server. Use `uvicorn[standard]` for production (includes `httptools` + `uvloop`). |
| `python-multipart` | 0.0.9+ | Form data + file uploads | Required by FastAPI for CSV file upload endpoint (History page import). Install separately — not included by default. |

### Supporting Libraries (Python)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pydantic` v2 | (transitive via FastAPI) | Request/response schema validation | Define Pydantic models for all API request bodies and response shapes. SQLModel models are NOT used directly as API schemas — define separate Pydantic response schemas. |
| `firebase-admin` | 7.1.0 (already installed) | Verify Firebase ID tokens in API middleware | `auth.verify_id_token(token)` in a FastAPI dependency. No version change. |
| `starlette` | (transitive via FastAPI) | CORS middleware | `CORSMiddleware` is from Starlette; FastAPI re-exports it. No separate install. |

### FastAPI Auth Dependency Pattern

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth

bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """Extract and verify Firebase ID token. Returns Firebase UID."""
    token = credentials.credentials
    try:
        decoded = auth.verify_id_token(token)
        return decoded["uid"]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
```

Inject as: `user_id: str = Depends(get_current_user)` on every route.

### CORS Configuration

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://<project-id>.web.app",          # Firebase Hosting production
        "https://<project-id>.firebaseapp.com",  # Firebase Hosting alternate
        "http://localhost:5173",                  # Vite dev server default port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)
```

Never use `allow_origins=["*"]` with `allow_credentials=True` — browsers reject this combination.

---

## New Capabilities: Firebase Hosting

### Tooling

| Tool | Version | Purpose | Why |
|------|---------|---------|-----|
| `firebase-tools` (CLI) | 13.x | Deploy React build to Firebase Hosting | Official CLI; `firebase deploy --only hosting` uploads `dist/` |

### Firebase Hosting Free Tier (Spark Plan) — Confirmed Limits

| Resource | Free Limit | Likely Usage |
|----------|------------|--------------|
| Storage | 10 GB | React build is ~1-5 MB — nowhere near limit |
| Data transfer (egress) | 360 MB/day | Single-user app: each page load ~200-500 KB — ~1000 loads/day before limit |
| Custom domains | 1 | Sufficient for single deployment |
| Hosting sites per project | 1 on Spark | Sufficient |

**Verdict:** Firebase Hosting Spark (free) is sufficient. A React app for a single user will not approach egress limits.

**MEDIUM confidence** — free tier limits from training knowledge; verify at https://firebase.google.com/pricing before launch.

### `firebase.json` Configuration

```json
{
  "hosting": {
    "public": "frontend/dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ]
  }
}
```

The `rewrites` rule is required for React Router's `createBrowserRouter` — all routes must serve `index.html`.

---

## Installation

### React Frontend

```bash
# Scaffold with Vite (run from project root or a new frontend/ subdirectory)
npm create vite@latest frontend -- --template react-ts
cd frontend

# Core runtime deps
npm install recharts react-router-dom axios date-fns react-hook-form zod lucide-react

# Firebase JS SDK (npm for TypeScript types — not CDN)
npm install firebase

# shadcn/ui (initialize after Tailwind is configured)
npx shadcn@latest init
# Then add components as needed:
npx shadcn@latest add button card dialog table input

# Tailwind CSS (Vite 5 + Tailwind 3)
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Dev deps
npm install -D @types/react @types/react-dom @vitejs/plugin-react-swc eslint prettier
```

### FastAPI Backend

```bash
# Add to existing pyproject.toml via uv
uv add fastapi uvicorn python-multipart

# Or with standard extras (includes uvloop, httptools for production performance)
uv add "fastapi[standard]" python-multipart
```

No other Python packages needed — `firebase-admin`, `sqlmodel`, `pydantic-settings` are already installed.

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| Vite | Create React App | CRA is deprecated since 2023; no active maintenance |
| Vite | Next.js | SSR adds complexity; this is a pure SPA behind Firebase Auth — no SEO, no SSR needed |
| shadcn/ui | MUI / Chakra UI | Both impose their design system on top of Tailwind; shadcn/ui copies code into the repo allowing full control of the midnight dark theme |
| Recharts | Plotly (React) | `react-plotly.js` is a heavy wrapper around Plotly.js; Recharts is React-native and ~10x smaller bundle size |
| Recharts | Chart.js | Chart.js is canvas-based; Recharts is SVG-based and integrates naturally with React's declarative rendering |
| `axios` | native `fetch` | Both work; axios request interceptors are cleaner for attaching the Firebase token header to every request |
| `react-hook-form` | Formik | react-hook-form has fewer re-renders and simpler API with Zod integration |
| FastAPI | Flask | FastAPI has async support, automatic OpenAPI docs, and native Pydantic integration — all needed here |
| FastAPI | Django REST Framework | DRF is heavier; FastAPI wraps the existing services with minimal boilerplate |
| `uvicorn[standard]` | gunicorn + uvicorn workers | Cloud Run runs one container instance per request; single uvicorn process is appropriate |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Redux / Zustand | Overkill for a single-user app with simple page-level data. React's `useState` + `useEffect` + context is enough. | React built-in state + context for auth |
| `react-query` / TanStack Query | Useful for caching, but adds complexity that isn't warranted until there's evidence of performance issues | Simple `useEffect` + `useState` fetching with axios |
| Separate auth backend | Firebase handles auth — adding a custom auth server duplicates work and creates a second point of failure | Firebase Auth + firebase-admin `verify_id_token` |
| `cloud-sql-python-connector` | Cloud Run already provides the Unix socket; this library adds complexity with no benefit here | psycopg2 Unix socket (unchanged from existing setup) |
| Plotly.js / react-plotly.js | Large bundle (~3MB); Recharts produces equivalent charts at ~200KB | Recharts |
| Firebase CDN for JS SDK (new development) | CDN was correct for the Streamlit component (no build step); now that there's a Vite build, use npm for TypeScript types and tree-shaking | `npm install firebase` |
| `express` / Node.js backend | Python services are already written; duplicating them in Node adds maintenance burden | FastAPI wrapping existing Python services |

---

## Version Compatibility

| Package | Version | Compatible With | Notes |
|---------|---------|-----------------|-------|
| React | 18.x | TypeScript 5.x, Vite 5.x, Recharts 2.x | React 19 released 2024 but shadcn/ui adoption not universal yet; 18.x is safe default |
| shadcn/ui | CLI (latest) | React 18, Tailwind 3, Radix UI | shadcn/ui is not versioned — CLI generates from templates. Run `npx shadcn@latest` |
| Recharts | 2.x | React 18 | Recharts 3 is in development as of Aug 2025; 2.x is the stable release |
| Firebase JS SDK | 12.9.0 | React 18, TypeScript 5 | Confirmed current as of 2026-02-18 (Phase 4 research) |
| FastAPI | 0.115.x | Python 3.12, Pydantic v2 | FastAPI 0.100+ uses Pydantic v2 natively |
| Uvicorn | 0.30.x | FastAPI 0.115.x, Python 3.12 | `uvicorn[standard]` for production extras |
| Tailwind CSS | 3.x | Vite 5, shadcn/ui | Tailwind v4 released 2025 but shadcn/ui still targets v3; use v3 until shadcn/ui officially supports v4 |

---

## Integration Points

### Firebase Auth Flow (React SPA → FastAPI → SQLModel)

```
1. React mounts → firebase.auth().onAuthStateChanged() fires
2. User present → getIdToken() → store token in memory (React context)
3. axios interceptor attaches: Authorization: Bearer <id_token>
4. FastAPI receives request → HTTPBearer extracts token
5. firebase_admin.auth.verify_id_token(token) → decoded["uid"]
6. uid passed to existing SQLModel service functions (unchanged)
7. Services query PostgreSQL as before
```

This flow replaces the Streamlit component bridge entirely. The services themselves do not change.

### CSV Export/Import (multipart upload)

FastAPI requires `python-multipart` for `UploadFile` in route handlers. Without it, FastAPI raises a runtime error when a file upload endpoint is hit. Install explicitly — it is not a FastAPI default.

---

## Sources

- Phase 4 Research (`.planning/phases/04-firebase-authentication/04-RESEARCH.md`) — Firebase JS SDK 12.9.0, firebase-admin 7.1.0 — HIGH confidence (verified 2026-02-18)
- FastAPI official docs (https://fastapi.tiangolo.com/) — CORS middleware via Starlette, `fastapi[standard]` installation — HIGH confidence (fetched 2026-04-04)
- Training knowledge (cutoff August 2025) — React 18, Vite 5, Tailwind 3, Recharts 2.x, shadcn/ui CLI, react-router-dom 6, axios 1.x, FastAPI 0.115.x, uvicorn 0.30.x — MEDIUM confidence (verify npm versions before pinning)
- Firebase Hosting pricing page (https://firebase.google.com/pricing) — free tier limits — MEDIUM confidence (from training; verify before launch)
- shadcn/ui docs (https://ui.shadcn.com/docs/installation/vite) — Vite installation pattern — MEDIUM confidence (training knowledge)

---

*Stack research for: React + FastAPI + Firebase Hosting migration (v2.0)*
*Researched: 2026-04-04*
