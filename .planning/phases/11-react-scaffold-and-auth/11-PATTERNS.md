# Phase 11: React Scaffold and Auth - Pattern Map

**Mapped:** 2026-05-09
**Files analyzed:** 15 (new client/ files)
**Analogs found:** 8 / 15 (7 net-new with no codebase analog — use RESEARCH.md patterns)

---

## File Classification

| New File | Role | Data Flow | Closest Analog | Match Quality |
|----------|------|-----------|----------------|---------------|
| `client/package.json` | config | — | `pyproject.toml` (root) | structure-ref |
| `client/vite.config.ts` | config | — | none | no-analog |
| `client/tailwind.config.js` | config | — | none | no-analog |
| `client/postcss.config.js` | config | — | none | no-analog |
| `client/components.json` | config | — | none | no-analog |
| `client/.env` | config | — | `.env` (root) | exact |
| `client/src/index.css` | config | — | `frontend/main.py` (CSS block) | style-ref |
| `client/src/main.tsx` | config | — | none | no-analog |
| `client/src/App.tsx` | provider | request-response | `api/main.py` | role-match |
| `client/src/lib/firebase.ts` | utility | — | `app/config.py` | config-mirror |
| `client/src/lib/apiClient.ts` | utility | request-response | `api/dependencies.py` | contract-mirror |
| `client/src/contexts/AuthContext.tsx` | provider | event-driven | `api/dependencies.py` | contract-mirror |
| `client/src/components/PrivateRoute.tsx` | middleware | request-response | `api/dependencies.py` | contract-mirror |
| `client/src/components/AppSidebar.tsx` | component | — | `frontend/main.py` (sidebar block) | style-ref |
| `client/src/pages/*.tsx` (×6 stubs) | component | — | `frontend/pages/` modules | structure-ref |

---

## Pattern Assignments

### `client/.env` (config)

**Analog:** `.env` (root — same Firebase project, same field names)

**Mirror from `app/config.py` lines 8–10** — the three Firebase fields that the Python backend reads must match the three `VITE_`-prefixed equivalents in the React env file:

```python
# app/config.py — source field names
firebase_web_api_key: str = ""
firebase_auth_domain: str = ""
firebase_project_id: str = ""
```

**React `.env` must mirror those exact values under these keys:**
```
VITE_FIREBASE_API_KEY=<same value as firebase_web_api_key>
VITE_FIREBASE_AUTH_DOMAIN=<same value as firebase_auth_domain>
VITE_FIREBASE_PROJECT_ID=<same value as firebase_project_id>
VITE_API_BASE_URL=http://localhost:8000
```

**Constraint:** This file is gitignored. It is never committed. The `.env` in the repo root is also gitignored — follow the same convention.

---

### `client/src/lib/firebase.ts` (utility — Firebase init singleton)

**Analog:** `app/config.py` (field-name mirror) and `api/main.py` lines 37–47 (single-init pattern)

**Config field mapping** (`app/config.py` lines 8–10 → `firebase.ts`):

```typescript
// client/src/lib/firebase.ts
// Field names mirror app/config.py: firebase_web_api_key → apiKey, etc.
import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';

const firebaseConfig = {
  apiKey:     import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId:  import.meta.env.VITE_FIREBASE_PROJECT_ID,
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
```

**Single-init constraint from `api/main.py` lines 37–47:** The Python backend calls `firebase_admin.initialize_app()` exactly once in the lifespan context. Apply the same discipline in React: `initializeApp` is called once in this module; all other files import `auth` from here — never call `initializeApp` again.

---

### `client/src/lib/apiClient.ts` (utility — Axios HTTP client)

**Analog:** `api/dependencies.py` (auth contract that this client must satisfy)

**Auth contract from `api/dependencies.py` lines 13–53:**

```python
# The FastAPI dependency that the React Axios client must satisfy
bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    token: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    # Expects: Authorization: Bearer <firebase-id-token>
    # Returns: uid string on success
    # Raises: HTTP 401 if token is missing or fails firebase_admin.auth.verify_id_token()
    # Raises: HTTP 403 if uid != settings.allowed_firebase_uid
```

**Dev bypass to be aware of** (`api/dependencies.py` lines 27–28): When `settings.dev_user_id` is set, the backend skips Firebase verification entirely. The React Axios client does not need to change for this — it still sends a token (or no token if `auth.currentUser` is null). The interceptor simply won't attach a header if there is no logged-in user.

**React client pattern:**

```typescript
// client/src/lib/apiClient.ts
import axios from 'axios';
import { getIdToken } from 'firebase/auth';
import { auth } from '@/lib/firebase';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
});

// Request interceptor — call getIdToken() at request time, never store the token string
apiClient.interceptors.request.use(async (config) => {
  const user = auth.currentUser;   // read at call time, not at setup time (avoids stale closure)
  if (user) {
    const token = await getIdToken(user); // Firebase refreshes if < 5 min from expiry
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — 401 from get_current_user → force re-login
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = '/login'; // hard redirect clears React state
    }
    return Promise.reject(error);
  }
);
```

**CORS allow-list from `api/main.py` lines 21–25:** `http://localhost:5173` is already in `ALLOWED_ORIGINS`. The Axios client's `baseURL` of `http://localhost:8000` is correct — no proxy needed in Phase 11.

---

### `client/src/contexts/AuthContext.tsx` (provider — auth state)

**Analog:** `api/dependencies.py` (Python auth gate) and `frontend/main.py` lines 40–141 (`_auth_gate` function)

**Python auth gate pattern to replicate in React** (`frontend/main.py` lines 40–103, condensed):

```python
# frontend/main.py — _auth_gate() structure that AuthContext mirrors
# 1. Build firebase_config from settings (already done in firebase.ts)
# 2. If dev_user_id is set, bypass (apiClient interceptor handles this for React)
# 3. Block all rendering until auth state is known (loading=True in React)
# 4. If unauthenticated: hide sidebar, stop rendering (PrivateRoute redirects)
# 5. If authenticated: verify token, store user, allow rendering
```

**React AuthContext pattern:**

```typescript
// client/src/contexts/AuthContext.tsx
import { createContext, useContext, useEffect, useState } from 'react';
import { onAuthStateChanged, signOut as firebaseSignOut, User } from 'firebase/auth';
import { auth } from '@/lib/firebase';

interface AuthContextValue {
  user: User | null;
  loading: boolean;          // true until onAuthStateChanged fires once
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser);
      setLoading(false);      // clears the "initializing" block
    });
    return unsubscribe;       // cleanup mirrors _auth_gate component unmount
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, signOut: () => firebaseSignOut(auth) }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
```

---

### `client/src/components/PrivateRoute.tsx` (middleware — route guard)

**Analog:** `api/dependencies.py` lines 13–53 (FastAPI auth gate) mirrored in `frontend/main.py` lines 73–103 (Streamlit auth check)

**Gate logic from `frontend/main.py` lines 73–103:**

```python
# frontend/main.py — gate pattern PrivateRoute must replicate
if st.session_state.get("user_id"):   # user known → pass through
    return
# else: render login UI, st.stop() — maps to <Navigate to="/login" replace />
```

```typescript
// client/src/components/PrivateRoute.tsx
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

export function PrivateRoute({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return null;   // wait for onAuthStateChanged — never flash content
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  return children;
}
```

**Critical constraint:** Check `loading` before `user`. Firebase restores auth state asynchronously from IndexedDB — if only `user` is checked, every hard refresh redirects an authenticated user to `/login`. This mirrors the Streamlit `"initializing"` status check in `frontend/main.py` lines 83–86.

---

### `client/src/App.tsx` (provider — router and layout)

**Analog:** `api/main.py` (app factory pattern — registers all routes, applies middleware)

**Route registration pattern from `api/main.py` lines 65–72:**

```python
# api/main.py — all routers registered in one place
app.include_router(health.router)
app.include_router(accounts.router)
app.include_router(liabilities.router)
app.include_router(pension.router)
app.include_router(snapshots.router)
app.include_router(configure.router)
app.include_router(dashboard.router)
```

**React equivalent — all 6 routes registered in App.tsx, all wrapped in PrivateRoute:**

```typescript
// client/src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { PrivateRoute } from '@/components/PrivateRoute';
import { AppSidebar } from '@/components/AppSidebar';
import LoginPage from '@/pages/LoginPage';
import DashboardPage from '@/pages/DashboardPage';
// ... remaining 5 page imports

function AppLayout() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <main>
        <Outlet />
      </main>
    </SidebarProvider>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<PrivateRoute><AppLayout /></PrivateRoute>}>
            <Route path="/"             element={<DashboardPage />} />
            <Route path="/accounts"     element={<AccountsPage />} />
            <Route path="/liabilities"  element={<LiabilitiesPage />} />
            <Route path="/pension"      element={<PensionPage />} />
            <Route path="/history"      element={<HistoryPage />} />
            <Route path="/configure"    element={<ConfigurePage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
```

---

### `client/src/components/AppSidebar.tsx` (component — sidebar nav)

**Analog:** `frontend/main.py` lines 275–308 (sidebar navigation with Midnight active styles)

**Midnight active-item styling from `frontend/main.py` lines 286–303:**

```python
# frontend/main.py — active item visual treatment (reference for React equivalent)
styles={
    "nav-link": {
        "color": "#e6edf3",        # text-foreground default
        "font-size": "16px",
        "font-weight": "400",
        "--hover-color": "rgba(255,255,255,0.05)",
    },
    "nav-link-selected": {
        "background-color": "rgba(88,166,255,0.1)",  # primary at 10% opacity
        "color": "#58a6ff",                           # --primary
        "font-weight": "600",
        "border-left": "3px solid #58a6ff",
    },
}
```

**Page order locked by D-05** (`frontend/main.py` line 276, cross-checked with CONTEXT.md D-05):
- Python app order: Dashboard → Accounts → Liabilities → Pension → Goals → Trends → Configure
- Phase 11 React order: Dashboard → Accounts → Liabilities → Pension → History → Configure
  (Goals and Trends are not in scope for Phase 11)

**React AppSidebar pattern:**

```typescript
// client/src/components/AppSidebar.tsx
import { NavLink } from 'react-router-dom';
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent,
  SidebarMenu, SidebarMenuItem, SidebarMenuButton,
} from '@/components/ui/sidebar';

const navItems = [
  { to: '/',             label: 'Dashboard' },
  { to: '/accounts',    label: 'Accounts' },
  { to: '/liabilities', label: 'Liabilities' },
  { to: '/pension',     label: 'Pension' },
  { to: '/history',     label: 'History' },
  { to: '/configure',   label: 'Configure' },
];

export function AppSidebar() {
  return (
    <Sidebar collapsible="none">
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map(({ to, label }) => (
                <SidebarMenuItem key={to}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to={to}
                      end={to === '/'}
                      className={({ isActive }) =>
                        isActive
                          ? 'text-[#58a6ff] font-semibold border-l-[3px] border-[#58a6ff] bg-[rgba(88,166,255,0.1)]'
                          : 'text-[#e6edf3]'
                      }
                    >
                      {label}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
```

---

### `client/src/index.css` (config — global styles and CSS vars)

**Analog:** `frontend/main.py` lines 164–226 (CSS block with Midnight palette and Poppins import)

**Poppins import from `frontend/main.py` line 169:**
```python
# frontend/main.py — exact Google Fonts URL for Poppins (same weights)
"@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');"
```

**Midnight background from `frontend/main.py` line 202:**
```python
# frontend/main.py — .stApp background
"background-color: #161b22 !important;"
```

**Accent colour from `frontend/main.py` line 213:**
```python
# frontend/main.py — active nav link and icon colour
"color: #58a6ff !important;"
```

**React CSS (shadcn/ui v2.x raw-HSL-channel format required):**
```css
/* client/src/index.css */
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  .dark {
    --background: 216 18% 11%;   /* #161b22 — Midnight app background */
    --primary:    212 100% 68%;  /* #58a6ff — accent / active sidebar */
  }
}
```

**Critical format note:** shadcn/ui v2.x reads CSS vars as raw HSL channels inside `hsl(var(--background))`. Setting `--background: #161b22` (hex) produces an invalid colour with no error. Use the channel values above.

---

### `client/src/pages/*.tsx` — 6 page stubs (component)

**Analog:** `frontend/pages/` modules (structural reference only — Python, not copyable)

**Pattern from `api/routers/accounts.py` line 22 (naming discipline):** Each router/page is a single focused module. The React page stubs follow the same one-file-per-domain convention.

**Stub template (identical for all 6 pages — minimal, no data fetching):**

```typescript
// client/src/pages/DashboardPage.tsx  (repeat for Accounts, Liabilities, Pension, History, Configure)
export default function DashboardPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
    </div>
  );
}
```

**Page-to-route mapping (D-05 order):**

| File | Route | Page heading |
|------|-------|--------------|
| `DashboardPage.tsx` | `/` | Dashboard |
| `AccountsPage.tsx` | `/accounts` | Accounts |
| `LiabilitiesPage.tsx` | `/liabilities` | Liabilities |
| `PensionPage.tsx` | `/pension` | Pension |
| `HistoryPage.tsx` | `/history` | History |
| `ConfigurePage.tsx` | `/configure` | Configure |

---

### `client/tailwind.config.js` (config)

**Analog:** none in codebase — use RESEARCH.md Pattern 5

**Key constraints:**
- Must be `.js`, not `.ts` (shadcn@2.3.0 generates `.js`; `.ts` may cause compatibility issues)
- `darkMode: ['class']` required (shadcn v2.x applies dark theme via `class` on `<html>`)
- Poppins as `fontFamily.sans` (D-03)

```javascript
// client/tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Poppins', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
```

---

### `client/vite.config.ts` (config)

**Analog:** none in codebase — use RESEARCH.md

**Required: `@/*` path alias** — all `client/src/` imports use `@/` prefix (shadcn components, contexts, lib, pages). Must be configured in both `vite.config.ts` and `tsconfig.app.json`:

```typescript
// client/vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
});
```

```json
// client/tsconfig.app.json — paths section (must match vite alias)
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": { "@/*": ["./src/*"] }
  }
}
```

---

## Shared Patterns

### Firebase Config Field Mapping
**Source:** `app/config.py` lines 8–10
**Apply to:** `client/.env`, `client/src/lib/firebase.ts`

The three Python settings fields map directly to React env vars:

| Python field (`app/config.py`) | React env var (`client/.env`) | Firebase JS SDK key |
|-------------------------------|-------------------------------|---------------------|
| `firebase_web_api_key` | `VITE_FIREBASE_API_KEY` | `apiKey` |
| `firebase_auth_domain` | `VITE_FIREBASE_AUTH_DOMAIN` | `authDomain` |
| `firebase_project_id` | `VITE_FIREBASE_PROJECT_ID` | `projectId` |

### CORS Contract
**Source:** `api/main.py` lines 21–25, 57–63
**Apply to:** `client/src/lib/apiClient.ts` (baseURL), `client/.env` (VITE_API_BASE_URL)

```python
# api/main.py — already allows React dev server
ALLOWED_ORIGINS = [
    "http://localhost:5173",           # React dev server (D-06)
    "https://finance-tracker-rntookejza.web.app",
    "https://finance-tracker-rntookejza.firebaseapp.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,           # required — Axios sends credentials
    allow_headers=["Authorization", "Content-Type", "Accept"],
)
```

No CORS changes needed in Phase 11. `VITE_API_BASE_URL=http://localhost:8000` in `client/.env`.

### Auth Bearer Contract
**Source:** `api/dependencies.py` lines 10–53
**Apply to:** `client/src/lib/apiClient.ts` (request interceptor header format)

The exact expected header:
```
Authorization: Bearer <firebase-id-token>
```

`HTTPBearer` on the FastAPI side strips the `Bearer ` prefix and passes only the raw token to `verify_id_token()`. The Axios interceptor must set `config.headers.Authorization = \`Bearer ${token}\`` — not just the raw token.

### Midnight Colour Tokens
**Source:** `frontend/main.py` lines 196–213
**Apply to:** `client/src/index.css` (CSS vars), `client/src/components/AppSidebar.tsx` (active classes)

| Use | Hex | Tailwind arbitrary / CSS var |
|-----|-----|------------------------------|
| App background | `#161b22` | `--background: 216 18% 11%` |
| Accent / active nav | `#58a6ff` | `--primary: 212 100% 68%` |
| Active bg tint | `rgba(88,166,255,0.1)` | `bg-[rgba(88,166,255,0.1)]` |
| Body text | `#e6edf3` | `text-[#e6edf3]` |
| Muted text | `#8b949e` | `text-[#8b949e]` |
| Active border | `#58a6ff` | `border-[#58a6ff]` |

### `cn()` Utility
**Source:** Installed by `npx shadcn@2.3.0 init` — `src/lib/utils.ts`
**Apply to:** All component files that compose conditional class names

```typescript
// Pattern set by shadcn init — use everywhere class names are conditional
import { cn } from '@/lib/utils';
// cn(clsx + tailwind-merge) — prevents Tailwind class conflicts
```

---

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `client/vite.config.ts` | config | — | No Vite/Node config files exist in this Python repo |
| `client/tailwind.config.js` | config | — | No CSS build tooling exists in this Python repo |
| `client/postcss.config.js` | config | — | No PostCSS config in this Python repo |
| `client/components.json` | config | — | shadcn-generated; no analog in Python toolchain |
| `client/src/main.tsx` | entry | — | No React entry point exists; generated by Vite template |
| `client/src/pages/LoginPage.tsx` | component | — | Streamlit auth is a custom web component, not React |

**For these files:** Use RESEARCH.md Patterns 1–6 directly. The Vite template (`npm create vite@latest client -- --template react-ts`) generates `main.tsx`, `vite.config.ts`, and `tsconfig*.json` automatically. `postcss.config.js` and `tailwind.config.js` are generated by `npx tailwindcss init -p`. `components.json` is generated by `npx shadcn@2.3.0 init`.

---

## Metadata

**Analog search scope:** `api/`, `app/`, `frontend/`
**Files scanned:** 8 (`api/main.py`, `api/dependencies.py`, `api/routers/accounts.py`, `app/config.py`, `frontend/main.py`, plus directory listings)
**Pattern extraction date:** 2026-05-09
