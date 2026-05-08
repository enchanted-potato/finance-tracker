# Phase 11: React Scaffold and Auth - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning

<domain>
## Phase Boundary

A React + TypeScript SPA exists at `client/` with the Midnight dark theme applied, Firebase Google Sign-In gating all routes, and an Axios client that refreshes the ID token before every request. After login, a sidebar with 6 stub pages (Dashboard, Accounts, Liabilities, Pension, History, Configure) is navigable. No page content — that's Phases 12–14.

</domain>

<decisions>
## Implementation Decisions

### App directory
- **D-01:** The Vite project lives at `client/` (root of repo). Mirrors the existing `api/` and `app/` directory naming. All future phases reference `client/src/` for React code.

### Midnight theme
- **D-02:** Use shadcn/ui's built-in dark preset as the baseline. Override only two CSS custom properties to anchor the Midnight look:
  - `--background`: `#161b22` (app background)
  - `--primary`: `#58a6ff` (accent / active sidebar highlight)
  - All other surfaces (text, muted, border, card) use shadcn/ui dark defaults.
- **D-03:** Poppins applied globally via Google Fonts. `@import` in `client/src/index.css`; `fontFamily.sans` in `tailwind.config` set to `['Poppins', 'sans-serif']`.

### Page shells
- **D-04:** All 6 page stubs created in Phase 11 so sidebar links resolve during Phases 12–14 development. Each stub is a minimal component (heading only — no data fetching).
- **D-05:** Sidebar page order matches existing Streamlit app: Dashboard → Accounts → Liabilities → Pension → History → Configure.

### Dev setup
- **D-06:** React dev server runs standalone: `cd client && npm run dev` (port 5173). No docker-compose changes in Phase 11 — CORS is already configured for `localhost:5173` from Phase 9. docker-compose integration deferred to Phase 15.

### Claude's Discretion
- Internal file layout within `client/src/` (pages/, components/, lib/, hooks/)
- shadcn/ui init flags (style variant, baseColor)
- React Router v6 setup and route definitions
- Firebase SDK initialization location within the React app
- Auth state management approach (React Context is standard for this)
- Sidebar component choice (shadcn/ui Sheet vs a custom aside)
- Whether to add a loading spinner while `onAuthStateChanged` resolves

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase requirements
- `.planning/REQUIREMENTS.md` §REACT-01, REACT-02, REACT-03, REACT-04

### Existing API foundation (Phase 9 output — auth contract)
- `api/main.py` — CORS configured for `http://localhost:5173` (and Firebase Hosting origins); `allow_credentials=True`
- `api/dependencies.py` — `get_current_user` expects `Authorization: Bearer <token>`; returns HTTP 401 if missing/invalid

### Firebase config values (already in .env)
- `app/config.py` — `firebase_web_api_key`, `firebase_auth_domain`, `firebase_project_id` fields — same values feed the React Firebase JS SDK config

### Midnight palette (from existing Streamlit app — reference only, not consumed by agents)
- `frontend/main.py` — full CSS block with hex values; `frontend/pages/dashboard.py` — chart colours if needed in Phase 13

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `api/dependencies.py` — `get_current_user` is the auth contract; the React Axios client must send a token that satisfies this dependency
- `app/config.py` — Firebase project fields already defined; React `.env` file needs matching `VITE_` prefixed equivalents

### Established Patterns
- FastAPI and Streamlit coexist by running as separate processes; `client/` follows the same pattern — a standalone project, not nested inside an existing package
- All business logic stays in FastAPI — React components are purely presentational (architecture constraint from REQUIREMENTS.md)
- `api/` is the canonical model for a new top-level directory in this repo: its own `package.json` / `pyproject.toml`, not tangled with the Python app

### Integration Points
- React talks to FastAPI only via `http://localhost:8000` in dev; the CORS allow-list in `api/main.py` is already set
- `onAuthStateChanged` (Firebase JS SDK) is the auth gate — no financial data visible before the callback fires with a user
- Axios interceptor calls `getIdToken()` (never caches) and attaches the result as `Authorization: Bearer <token>`; a 401 response redirects to the login screen

</code_context>

<specifics>
## Specific Ideas

No specific references beyond the requirements — open to standard Vite + shadcn/ui + React Router patterns.

</specifics>

<deferred>
## Deferred Ideas

- docker-compose integration for the React dev server — deferred to Phase 15 (when Streamlit is replaced on Cloud Run and the full deployment picture is finalized)

</deferred>

---

*Phase: 11-react-scaffold-and-auth*
*Context gathered: 2026-05-08*
