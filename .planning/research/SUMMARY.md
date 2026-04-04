# Project Research Summary

**Project:** Finance Tracker — Net Worth Tracker (v2.0 React Migration)
**Domain:** Streamlit to React + TypeScript SPA with FastAPI REST layer
**Researched:** 2026-04-04
**Confidence:** HIGH (architecture and pitfalls verified against official docs and codebase; MEDIUM for specific npm package versions)

## Executive Summary

This project is a page-for-page rebuild of an existing working Streamlit personal net worth tracker into a React + TypeScript SPA backed by a new FastAPI REST layer. The core business logic (SQLModel services, PostgreSQL schema, Firebase Auth) is unchanged — the migration adds a thin FastAPI translation layer on top of existing services and replaces the Streamlit frontend with a React SPA deployed on Firebase Hosting. The critical insight from research is that the existing service layer is already designed for this: every service function takes `session` and `user_id` as keyword-only arguments, making FastAPI route handlers straightforward wrappers with zero logic duplication.

The recommended approach is sequential with a clear dependency chain: set up FastAPI infrastructure first (CORS, auth, database pool), define the API contract (JSON shapes for all endpoints, especially chart data), then build backend routes and React frontend in parallel, and deploy together at the end. The API contract step is blocking for parallel work but is low-cost to define upfront. Recharts requires a fundamentally different data shape than Plotly (one object per date vs. separate series arrays) — this must be settled at the API design stage, not retrofitted from React.

The key risks are operational rather than architectural. Five pitfalls can silently break a deployed app while working fine locally: CORS wildcard credentials (`allow_origins=["*"]` with `allow_credentials=True`), Firebase SPA routing (missing catch-all rewrite in `firebase.json`), Firebase ID token caching in React state (tokens expire after 1 hour), Decimal-to-string JSON serialization (breaks React arithmetic and Recharts charts), and stale database pool connections after the nightly Cloud SQL scheduled stop. All five have simple, known fixes that must be applied in the first two phases before any feature work.

## Key Findings

### Recommended Stack

The existing Python stack (SQLModel, PostgreSQL, firebase-admin, uv) is unchanged and locked. The new additions are: FastAPI 0.115.x + Uvicorn as the ASGI server (replaces Streamlit's server on Cloud Run), and a Vite 5 + React 18 + TypeScript 5 SPA (deployed to Firebase Hosting, replacing the Streamlit frontend). shadcn/ui provides the component library (CLI-based, Tailwind 3 + Radix UI primitives), Recharts 2.x replaces Plotly for charts, and Firebase JS SDK 12.9.0 handles client-side auth.

**Core technologies:**
- **FastAPI 0.115.x**: REST API framework — wraps existing SQLModel services with zero service-layer changes; async support and automatic OpenAPI docs
- **Uvicorn 0.30.x**: ASGI server replacing Streamlit on Cloud Run; use `uvicorn[standard]` for production
- **React 18 + TypeScript 5**: SPA framework — stable LTS, required by shadcn/ui and Recharts
- **Vite 5**: Build tool — fastest dev server, native ES modules, outputs static files for Firebase Hosting
- **Tailwind CSS 3.x**: Utility-first CSS — use v3 not v4; shadcn/ui targets v3 and v4 support is not yet confirmed
- **shadcn/ui (latest CLI)**: Component library — copies components into repo, full control over midnight dark theme, built on Radix UI for accessibility
- **Recharts 2.x**: Chart library — React-native SVG charts, replaces Plotly; ~10x smaller bundle than react-plotly.js
- **Firebase JS SDK 12.9.0**: Client-side auth — Google Sign-In popup, `onAuthStateChanged` persistence (version confirmed from prior research, HIGH confidence)
- **react-hook-form 7.x + Zod 3.x**: Form state and validation — fewer re-renders than controlled inputs, type-safe validation
- **python-multipart**: Required FastAPI dep for CSV file upload endpoints — not included by default, must be installed explicitly

**What not to add:** Redux/Zustand (overkill for single-user), TanStack Query (useful later but useState+useEffect is sufficient for v2.0 launch), separate auth backend (Firebase handles it), react-plotly.js (3MB bundle vs Recharts 200KB).

### Expected Features

The v2.0 milestone is a strict 1:1 rebuild — all existing Streamlit pages in React, no feature expansion. All six pages (Dashboard, Accounts, Liabilities, Pension, History, Configure) plus a new Auth/Login page that did not exist in Streamlit.

**Must have (v2.0 launch):**
- Firebase Google Sign-In with persistent auth state — never flash unauthenticated state on reload
- Dashboard: 4 metric cards, time-range toggle (6M/1Y/All), line chart, 2 donut charts, pension bar chart
- Accounts/Liabilities/Pension pages: balance history table + add/edit/delete via dialog (replaces `st.data_editor`), date picker, type select
- History page: monthly snapshot table with year dividers, expandable detail rows, edit/delete, CSV export (client-side) and import (server endpoint)
- Configure page: account/liability type CRUD with pension flag toggle and inline delete
- Midnight dark colour scheme, sidebar navigation, loading skeletons, toast feedback for all mutations

**Should have (competitive — adds value over Streamlit baseline):**
- Optimistic UI on balance saves (Accounts/Liabilities/Pension) — instant feedback vs. waiting for API round-trip
- Expandable row detail in History using Collapsible — no full-page re-render on toggle, unlike Streamlit
- Inline delete with AlertDialog confirmation — no page reload
- Toast feedback for mutations — replaces Streamlit's blocking `st.success()` banner

**Defer to v2.1+:**
- URL-persisted time range filter (bookmarkable views)
- Keyboard shortcut to open "Add entry" dialog
- Chart data labels on hover (minor Recharts enhancement)

**Explicitly out of scope:** Transaction tracking, multi-currency conversion, real-time WebSocket sync, dark mode toggle (hard-code dark), drag-and-drop CSV upload, pagination on History table (max ~48 rows).

### Architecture Approach

The architecture is a three-layer stack with a clean separation: React SPA on Firebase Hosting communicates via HTTPS REST to a FastAPI app on Cloud Run, which calls existing SQLModel service functions directly (no inter-service HTTP), which query Cloud SQL via Unix socket. The FastAPI layer is purely a translation layer — route handlers contain zero business logic, all logic stays in `app/services/`. The existing `app/services/`, `app/models.py`, `app/database.py`, and `app/services/auth_service.py` are unchanged.

**Major components:**
1. **`react-frontend/`** — Vite project; pages mirror Streamlit pages; all HTTP calls go through `src/api/client.ts` which calls `user.getIdToken()` before every request
2. **`api/`** — new FastAPI package; `main.py` (CORS, lifespan), `deps.py` (SessionDep, CurrentUser), `routers/` (one file per domain mirroring `app/services/`), `schemas/` (separate from SQLModel models — required to prevent Decimal serialization issues and `user_id` leakage)
3. **`app/services/`** — unchanged; called directly by FastAPI routers with `session=session, user_id=uid` keyword args
4. **Firebase Auth** — Firebase JS SDK (React) + `firebase_admin.auth.verify_id_token()` (FastAPI dep); token is never stored in React state, always fetched fresh per-request via `user.getIdToken()`

Build order: API contract definition (blocking) then FastAPI infrastructure + React scaffold (parallel) then backend routes + frontend pages (parallel) then integration testing then deployment.

### Critical Pitfalls

1. **CORS wildcard with credentials silently breaks all authenticated production requests** — never use `allow_origins=["*"]` with `allow_credentials=True`; list explicit Firebase Hosting origins from day one. This is the single most dangerous misconfiguration because it works locally and fails silently in production.

2. **Decimal fields serialize as strings in FastAPI JSON responses** — `balance: "10753.42"` instead of `balance: 10753.42`; define separate Pydantic response schemas with `float` for all monetary fields; verify with `curl` before building any React arithmetic or Recharts data binding.

3. **Recharts data format is the inverse of Plotly** — Recharts requires one object per X-axis point with all series as keys; Plotly uses separate arrays per series. Shape all time-series API responses in Recharts format at the API design stage. Retrofitting this is medium-cost.

4. **Firebase ID token not refreshed — silent 401s after 1 hour** — always call `user.getIdToken()` in the API client before each request (SDK returns cached token if valid, refreshes if near expiry); never store raw token string in React state.

5. **Firebase Hosting SPA returns 404 on direct URL navigation and page refresh** — add `{"source": "**", "destination": "/index.html"}` as the last rewrite rule in `firebase.json` before first deploy; also required for OAuth redirect flows.

6. **Stale database pool connections after nightly Cloud SQL scheduled stop (11pm)** — add `pool_pre_ping=True` and `pool_recycle=1800` to the SQLAlchemy engine in `app/database.py`; failure mode is 500 errors every morning at 8am when Cloud SQL restarts.

7. **Firebase Admin SDK not initialized before first request on Cloud Run** — use FastAPI `lifespan` context manager to call `init_firebase_admin()` at startup; do not call it inside the auth dependency (overhead on every request) or rely on module-level execution (not guaranteed in Cloud Run).

## Implications for Roadmap

Based on research, the suggested phase structure prioritizes infrastructure correctness before feature work. The pitfalls research is unusually clear about which failures are hard to retrofit vs. easy to fix later, which drives the ordering.

### Phase 1: FastAPI Foundation
**Rationale:** All subsequent phases depend on a working, correctly configured FastAPI server. CORS, auth dependency, database session, Firebase Admin lifespan, and `pool_pre_ping` must be in place before any routes are written. Getting these wrong causes silent failures that only appear in production (CORS) or at specific times (pool pre-ping). Zero features are visible at the end of this phase, but the platform is correct.
**Delivers:** `api/main.py` (CORS configured with explicit origins), `api/deps.py` (SessionDep, CurrentUser), FastAPI lifespan with `init_firebase_admin()`, `pool_pre_ping=True` on engine, one smoke-test endpoint (`GET /api/health`), Uvicorn running locally
**Avoids:** CORS wildcard pitfall, Firebase Admin init pitfall, stale pool pitfall

### Phase 2: API Contract and Schema Design
**Rationale:** Recharts data shape requirements mean the API contract must be decided before routes are implemented — otherwise Plotly-shaped responses get baked into the backend and require a medium-cost retrofit. This is a design/specification phase, not implementation. It defines JSON shapes for all endpoints, confirms all monetary fields serialize as `float`, and specifies Recharts-compatible formats for time-series and allocation endpoints. Unblocks parallel FastAPI and React development in all subsequent phases.
**Delivers:** Documented endpoint list (paths, methods, request bodies, response shapes); validated Decimal-to-float serialization approach via Pydantic response schemas; Recharts-compatible JSON shapes specified for all chart endpoints; TypeScript types in `react-frontend/src/types/`
**Avoids:** Decimal-as-string pitfall, Recharts data shape mismatch pitfall

### Phase 3: React Scaffold and Auth
**Rationale:** Auth gate must work before any page can render. This phase sets up the Vite project, Firebase JS SDK initialization, the `api/client.ts` with `getIdToken()` per-request pattern, `AuthGuard` component, login page, and `onAuthStateChanged` observer. Establishes the correct token-handling pattern that all subsequent pages inherit.
**Delivers:** Vite + React + TypeScript + Tailwind + shadcn/ui scaffolded; Firebase JS SDK initialized; login page (Google Sign-In); `AuthGuard` redirecting unauthenticated users; `api/client.ts` with per-request token refresh; sidebar navigation shell; `firebase.json` catch-all rewrite configured
**Avoids:** Token caching in React state pitfall, Firebase Hosting SPA 404 pitfall (catch-all added here before first deploy)

### Phase 4: Core Data Pages (Accounts, Liabilities, Pension)
**Rationale:** These three pages share an identical structure (balance table + CRUD dialog + type select + date picker). Building them together avoids duplicating component discovery across separate phases. The FastAPI routes for these are the most representative of the service-wrapper pattern, making them the right place to establish and validate the keyword-arg calling convention for all subsequent routes.
**Delivers:** FastAPI routes for `/api/accounts`, `/api/liabilities`, `/api/pension` with correct Pydantic response schemas (float monetary fields); React pages with Table, Dialog, Form, DatePicker, AlertDialog; optimistic adds/edits/deletes; toast feedback
**Avoids:** Service keyword-only arg pitfall — enforce `session=session, user_id=uid` pattern in code review for these routes

### Phase 5: Dashboard
**Rationale:** Dashboard is read-only but depends on data from all three balance-entry pages being available and correctly shaped. Chart components (Recharts LineChart, PieChart, BarChart) should be built after the data shape contract is validated in Phase 2 and real data exists from Phase 4. Building earlier means validating against mock data then re-validating against real data.
**Delivers:** FastAPI routes for `/api/snapshots` (history, dashboard aggregates) in Recharts format; Dashboard page with 4 metric cards, time-range toggle, net worth trend line chart, asset/liability donut charts, pension bar chart
**Avoids:** Recharts data format pitfall — chart endpoints already specified in Phase 2 and verified here with real data

### Phase 6: History Page and Configure Page
**Rationale:** History page has the most custom rendering (year dividers, expandable rows, CSV export/import) but no new infrastructure dependencies. Configure page is the simplest page (CRUD, no charts). Grouping them clears all remaining pages before deployment while keeping related complexity in one phase.
**Delivers:** FastAPI routes for `/api/history` (list, edit, delete, CSV import); History page with Collapsible rows, year dividers, client-side CSV export, file upload; Configure page with Tabs, inline add forms, Checkbox pension toggle, AlertDialog delete; `python-multipart` installed for CSV upload endpoint

### Phase 7: Deployment
**Rationale:** Deployment is its own phase because Firebase Hosting setup (SPA rewrites, `firebase.json` configuration) and Cloud Run deployment have specific sequencing requirements and pitfalls that only manifest post-deploy (SPA 404 on direct navigation, Firebase Hosting rewrite region mismatch). Running through the "Looks Done But Isn't" checklist from PITFALLS.md systematically verifies all production pitfalls.
**Delivers:** Firebase Hosting deployed with `firebase.json` catch-all rewrite; Cloud Run running FastAPI (Streamlit can remain in parallel initially); CORS pointing at Firebase Hosting production domain; end-to-end smoke test checklist verified (CORS preflight, 65-minute token test, Decimal serialization, SPA routing, Recharts data, Firebase Admin startup, pool pre-ping, ALLOWED_FIREBASE_UID guard)
**Avoids:** Firebase Hosting rewrite region mismatch, SPA routing 404 on production

### Phase Ordering Rationale

- **Infrastructure before features:** CORS, auth, and pool configuration failures are silent in local development and catastrophic in production. Fixing them retroactively after routes exist requires touching every route. Phase 1 eliminates this entire class of problem before any feature work begins.
- **Contract before code:** The Recharts data shape requirement means that if FastAPI routes return Plotly-shaped data (matching existing service output), every chart endpoint needs to be rewritten after React dev discovers the mismatch. Defining the contract in Phase 2 costs one meeting but saves a medium-cost retrofit across multiple files.
- **Parallel tracks unblocked after Phase 2:** FastAPI routes and React pages can be built in parallel from Phase 3 onward once the JSON contract is agreed. The architecture research explicitly documents this parallelism.
- **Dashboard after data pages:** Dashboard aggregates data from all balance-entry tables. Building it before the data tables exist means working with mock data and then re-validating. Building after Phase 4 means building against real data from the start.
- **Deploy last:** Firebase Hosting rewrites and Cloud Run deployment have their own failure modes that only appear post-deploy. Doing this as a dedicated phase with an explicit verification checklist (from PITFALLS.md) ensures all production pitfalls are systematically verified.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (API Contract):** Recharts `PieChart` donut configuration (innerRadius prop) and `dataKey` binding specifics — MEDIUM confidence; verify against Recharts docs at implementation time. shadcn/ui `Sidebar` component API — added later than other components; verify CLI output before building navigation shell.
- **Phase 7 (Deployment):** Firebase Hosting `run` rewrite `region` field must exactly match `gcloud run services describe` output — MEDIUM confidence (training knowledge); verify `firebase.json` rewrite syntax against Firebase Hosting docs before deploying. Also confirm whether `CORSMiddleware` must be disabled if Firebase Hosting rewrites are used (double-header conflict risk).

Phases with well-documented standard patterns (skip research-phase):
- **Phase 1 (FastAPI Foundation):** CORS middleware, lifespan context manager, HTTPBearer, SessionDep — all verified against official FastAPI docs (HIGH confidence). Pattern is exact and directly usable.
- **Phase 3 (React Auth):** Firebase JS SDK `onAuthStateChanged` + `getIdToken()` per-request — established, well-documented. React Hook Form + Zod integration is extremely stable (unchanged API).
- **Phase 4 (Core Data Pages):** shadcn/ui Dialog + Form + Table pattern is standard; service-wrapper FastAPI router pattern is fully specified in ARCHITECTURE.md with code examples.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Existing Python stack HIGH (locked in uv.lock); React/npm versions MEDIUM — verify with `npm info <pkg> version` before pinning; Firebase JS SDK 12.9.0 HIGH (confirmed 2026-02-18) |
| Features | HIGH | Derived from direct codebase analysis of all six Streamlit pages; shadcn/ui Sidebar component API specifically MEDIUM |
| Architecture | HIGH | FastAPI patterns verified against official docs (fetched 2026-04-04); existing service layer inspected directly; token flow confirmed against `auth_service.py` |
| Pitfalls | HIGH/MEDIUM | FastAPI/CORS pitfalls HIGH (verified against official docs); Firebase Hosting rewrites and Recharts format MEDIUM (training knowledge — manual verification recommended during implementation) |

**Overall confidence:** HIGH — the architecture is grounded in direct codebase inspection and official documentation. The main uncertainty is specific npm/shadcn package versions and Firebase Hosting config syntax, both of which have clear verification paths at implementation time.

### Gaps to Address

- **npm package versions:** STACK.md lists major versions (React 18.x, Vite 5.x, etc.) but specific patch versions should be verified with `npm info <pkg> version` before committing to `package.json`. No blocking risk — semver ranges handle this in practice.
- **shadcn/ui Sidebar component API:** Added later than other components; the CLI may generate a different file structure than expected. Verify `npx shadcn@latest add sidebar` output before building the navigation shell in Phase 3.
- **Recharts PieChart donut configuration:** The exact props for rendering a donut (hole in centre) should be verified against Recharts docs — `innerRadius` prop on `<Pie>` — before building Dashboard charts in Phase 5.
- **Firebase Hosting `run` rewrite region field:** Must exactly match the Cloud Run service region. Confirm region from `gcloud run services describe` before writing `firebase.json` in Phase 7.
- **Sonner vs. `useToast` for toasts:** FEATURES.md flags that shadcn/ui may have changed its recommended toast solution from `useToast` to `sonner` — verify which is current in the shadcn/ui CLI before adding toast infrastructure in Phase 3.
- **Tailwind v3 pin:** shadcn/ui targets Tailwind v3; if Tailwind v4 is installed, shadcn/ui components may not render correctly. Pin to `tailwindcss@3` explicitly in `package.json` until shadcn/ui publishes confirmed v4 support.

## Sources

### Primary (HIGH confidence)
- FastAPI official docs (fetched 2026-04-04): CORS middleware, dependency injection, SQLModel session pattern, Bearer token security, lifespan events — `https://fastapi.tiangolo.com/`
- Direct codebase inspection (2026-04-04): `app/services/account_service.py`, `app/services/auth_service.py`, `app/database.py`, `app/models.py`, `frontend/pages/*.py` (all six pages), `terraform/main.tf`
- Phase 4 research (`.planning/phases/04-firebase-authentication/04-RESEARCH.md`, verified 2026-02-18): Firebase JS SDK 12.9.0, firebase-admin 7.1.0

### Secondary (MEDIUM confidence)
- Training knowledge (cutoff August 2025): React 18, Vite 5, Tailwind 3, Recharts 2.x, shadcn/ui CLI patterns, react-hook-form + Zod integration, Firebase Hosting SPA rewrite syntax, `getIdToken()` refresh behaviour
- Firebase Hosting pricing (training knowledge): Spark plan free tier limits — verify at `https://firebase.google.com/pricing` before launch

### Tertiary (verify at implementation)
- Recharts data format requirements — `https://recharts.org/en-US/api`
- Firebase Hosting `firebase.json` rewrite syntax — `https://firebase.google.com/docs/hosting/config`
- shadcn/ui Sidebar component API — `https://ui.shadcn.com/docs/components/sidebar`

---
*Research completed: 2026-04-04*
*Ready for roadmap: yes*
