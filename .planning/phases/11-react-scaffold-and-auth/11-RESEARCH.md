# Phase 11: React Scaffold and Auth - Research

**Researched:** 2026-05-08
**Domain:** Vite + React + TypeScript + Tailwind v3 + shadcn/ui + Firebase Auth + Axios
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** The Vite project lives at `client/` (root of repo). Mirrors the existing `api/` and `app/` directory naming. All future phases reference `client/src/` for React code.
- **D-02:** Use shadcn/ui's built-in dark preset as the baseline. Override only two CSS custom properties:
  - `--background`: `#161b22` (app background)
  - `--primary`: `#58a6ff` (accent / active sidebar highlight)
  - All other surfaces (text, muted, border, card) use shadcn/ui dark defaults.
- **D-03:** Poppins applied globally via Google Fonts. `@import` in `client/src/index.css`; `fontFamily.sans` in `tailwind.config` set to `['Poppins', 'sans-serif']`.
- **D-04:** All 6 page stubs created in Phase 11 so sidebar links resolve during Phases 12–14 development.
- **D-05:** Sidebar page order: Dashboard → Accounts → Liabilities → Pension → History → Configure.
- **D-06:** React dev server runs standalone: `cd client && npm run dev` (port 5173). No docker-compose changes in Phase 11.

### Claude's Discretion
- Internal file layout within `client/src/` (pages/, components/, lib/, hooks/)
- shadcn/ui init flags (style variant, baseColor)
- React Router v6 setup and route definitions
- Firebase SDK initialization location within the React app
- Auth state management approach (React Context is standard for this)
- Sidebar component choice (shadcn/ui Sheet vs a custom aside)
- Whether to add a loading spinner while `onAuthStateChanged` resolves

### Deferred Ideas (OUT OF SCOPE)
- docker-compose integration for the React dev server — deferred to Phase 15
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REACT-01 | React + TypeScript project built with Vite, Tailwind v3, shadcn/ui initialised with Midnight dark theme | Scaffold sequence documented; Tailwind v3 + shadcn@2.3.0 pinned |
| REACT-02 | User can sign in with Google Sign-In; app gates all pages behind `onAuthStateChanged` with no financial data visible before login | Firebase JS SDK v9+ modular API documented; AuthContext + PrivateRoute pattern documented |
| REACT-03 | Axios client calls `getIdToken()` before every request (never caches the raw token string) and redirects to login on HTTP 401 | Axios request interceptor pattern documented; 401 response interceptor pattern documented |
| REACT-04 | Sidebar navigation shows all page links with active page highlight using Midnight-consistent colour | shadcn/ui Sidebar component primitives documented; NavLink active class pattern documented |
</phase_requirements>

---

## Summary

Phase 11 creates the React SPA foundation: a Vite + TypeScript project with Tailwind v3, shadcn/ui dark theme, Firebase Google Sign-In auth gate, an Axios client that calls `getIdToken()` on every request, and a sidebar shell with 6 stub pages.

The critical scaffolding constraint is that **the current shadcn/ui CLI (v4.7.0) defaults to Tailwind v4**. Since REACT-01 locks Tailwind v3, the init sequence must use `npx shadcn@2.3.0 init` rather than `npx shadcn@latest init`. Tailwind v3 uses PostCSS + `tailwind.config.js` (not the `@tailwindcss/vite` plugin approach used in v4). The two approaches are incompatible and cannot be mixed.

The toast research flag from STATE.md is resolved: the old shadcn/ui `useToast` / `toast` component is officially deprecated as of early 2025. The CLI itself emits "The toast component is deprecated. Use the sonner component instead." Do not install the old toast component; install `sonner` when toast infrastructure is needed in later phases.

The auth pattern is standard React Context + `onAuthStateChanged` subscription. The Axios interceptor calls `getIdToken()` (no `forceRefresh: true`) in a request interceptor, attaching the result as `Authorization: Bearer <token>`. Firebase's SDK internally refreshes tokens that are within 5 minutes of expiry — no raw token string ever needs to be stored in React state.

**Primary recommendation:** Scaffold with `npm create vite@latest client -- --template react-ts`, then install Tailwind v3 via PostCSS, then `npx shadcn@2.3.0 init` — in that exact order. Pin React 18 and @types/react@18 to stay on the v3-compatible stack.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Google Sign-In popup | Browser / Client | — | `signInWithPopup` is a client-side Firebase SDK call; no server involvement for the popup itself |
| Auth state (user object) | Browser / Client | — | `onAuthStateChanged` maintains a local observer; kept in React Context |
| Token attachment | Browser / Client | — | Axios request interceptor runs in browser before each HTTP call |
| Token verification | API / Backend | — | FastAPI `get_current_user` dependency; React never validates tokens |
| Route gating | Browser / Client | — | PrivateRoute component reads auth context and redirects — no server round-trip |
| Sidebar navigation | Browser / Client | — | Pure React component; no API calls |
| Page stubs | Browser / Client | — | Minimal components; no data fetching in Phase 11 |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| vite | 8.0.11 | Build tool / dev server | Industry standard for React SPAs; sub-second HMR |
| react | 18.3.1 | UI framework | Pinned to 18 for shadcn@2.x / Tailwind v3 compatibility |
| react-dom | 18.3.1 | DOM renderer | Matches react version |
| typescript | (vite template) | Type safety | Required by project REACT-01 |
| tailwindcss | 3.4.19 | Utility CSS | REACT-01 locks v3; latest v3 patch |
| postcss | 8.5.14 | CSS processor | Required by Tailwind v3 (v3 uses PostCSS, not Vite plugin) |
| autoprefixer | 10.5.0 | Vendor prefix | Required peer for Tailwind v3 PostCSS pipeline |
| shadcn (CLI) | 2.3.0 | Component scaffolding | Pin to 2.x — v3+ CLI scaffolds Tailwind v4 by default |
| firebase | 12.13.0 | Auth SDK (JS) | Latest — matches existing Firebase Admin SDK project |
| react-router-dom | 6.30.3 | Client routing | v6 is stable, well-documented; v7 requires data-API rewrites |
| axios | 1.16.0 | HTTP client | REACT-03 specifies interceptor pattern; axios has clean interceptor API |
| @types/react | 18.3.28 | React types | Pin to 18.x — v19 types not compatible with React 18 |
| @types/react-dom | 18.3.7 | DOM types | Matches @types/react version |

### Supporting (installed by shadcn init)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| clsx | 2.1.1 | Conditional classnames | Used by all shadcn components |
| tailwind-merge | 3.5.0 | Merge Tailwind classes | Prevents class conflicts in shadcn utilities |
| class-variance-authority | 0.7.1 | Variant-based styling | Used by shadcn Button, Badge, etc. |
| lucide-react | 1.14.0 | Icon library | shadcn default icon set |
| @radix-ui/* | (various) | Accessible primitives | Underlying primitives for all shadcn components |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| react-router-dom v6 | v7 | v7 integrates data loading but is a larger API surface; v6 is simpler for a pure SPA with no SSR |
| axios | fetch | Axios interceptor API is cleaner for the per-request token pattern; fetch requires manual wrapper |
| shadcn/ui Sidebar | custom aside | shadcn Sidebar has responsive/collapsible built in at zero extra cost; custom aside is fine but more work |
| sonner | old shadcn toast | Old toast component officially deprecated by shadcn; sonner is the current recommendation |

### Installation

```bash
# Step 1 — scaffold Vite project
npm create vite@latest client -- --template react-ts
cd client
npm install

# Step 2 — pin React 18 types (vite template may pull React 19 types)
npm install --save-dev @types/react@18 @types/react-dom@18

# Step 3 — Tailwind v3 via PostCSS (NOT the @tailwindcss/vite plugin — that is v4 only)
npm install -D tailwindcss@3.4.19 postcss autoprefixer
npx tailwindcss init -p

# Step 4 — shadcn/ui (pinned to v2 for Tailwind v3 compatibility)
npx shadcn@2.3.0 init

# Step 5 — routing + auth + HTTP
npm install react-router-dom@6.30.3 firebase axios

# Step 6 — shadcn Sidebar (added via CLI, not manual)
npx shadcn@2.3.0 add sidebar
```

**Version verification:** All versions above confirmed against npm registry on 2026-05-08.

---

## Architecture Patterns

### System Architecture Diagram

```
Browser
  │
  ├─► LoginPage
  │     └─ signInWithPopup(auth, GoogleAuthProvider)
  │           └─► Firebase Auth servers (OAuth popup)
  │                 └─ onAuthStateChanged fires → AuthContext.user set
  │
  ├─► AuthContext (React Context)
  │     ├─ user: User | null
  │     ├─ loading: boolean  (true until onAuthStateChanged fires once)
  │     └─ signOut()
  │
  ├─► PrivateRoute
  │     ├─ loading=true → spinner (or null)
  │     ├─ user=null  → <Navigate to="/login" replace />
  │     └─ user≠null → render children
  │
  ├─► AppLayout (sidebar + <Outlet>)
  │     ├─ shadcn Sidebar
  │     │   └─ NavLink × 6 pages (active class via isActive)
  │     └─ <Outlet> → page stubs
  │
  └─► axios instance (apiClient)
        ├─ request interceptor:
        │     const token = await getIdToken(auth.currentUser)
        │     config.headers.Authorization = `Bearer ${token}`
        │     return config
        └─ response interceptor:
              error.response.status === 401 → navigate('/login')
```

### Recommended Project Structure

```
client/
├── src/
│   ├── lib/
│   │   ├── firebase.ts        # initializeApp, getAuth, GoogleAuthProvider export
│   │   └── apiClient.ts       # axios instance with request + 401 interceptors
│   ├── contexts/
│   │   └── AuthContext.tsx    # onAuthStateChanged observer, user + loading state
│   ├── components/
│   │   ├── PrivateRoute.tsx   # auth gate component
│   │   └── AppSidebar.tsx     # shadcn Sidebar with NavLink items
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── AccountsPage.tsx
│   │   ├── LiabilitiesPage.tsx
│   │   ├── PensionPage.tsx
│   │   ├── HistoryPage.tsx
│   │   └── ConfigurePage.tsx
│   ├── App.tsx                # BrowserRouter + route definitions
│   ├── main.tsx               # ReactDOM.createRoot entry point
│   └── index.css              # Tailwind directives + Google Fonts import + CSS vars override
├── tailwind.config.js         # Tailwind v3 config with Poppins fontFamily
├── postcss.config.js          # Tailwind + autoprefixer plugins
├── components.json            # shadcn config (generated by shadcn init)
├── tsconfig.json              # baseUrl + paths for @/* alias
├── tsconfig.app.json          # same paths config
├── vite.config.ts             # @/* alias resolve
├── .env                       # VITE_FIREBASE_* vars (gitignored)
└── package.json
```

### Pattern 1: Firebase Initialization (lib/firebase.ts)

**What:** Single module that initializes Firebase and exports `auth` singleton.
**When to use:** Import `auth` from here in AuthContext and apiClient — never call `initializeApp` twice.

```typescript
// Source: https://github.com/firebase/firebase-js-sdk/blob/main/docs-devsite/app.md
// Source: api/dependencies.py — field names match: firebase_web_api_key, firebase_auth_domain, firebase_project_id
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

**VITE_ env file** (`client/.env`, gitignored — same values as `app/config.py` fields):
```
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
```

### Pattern 2: AuthContext with loading state (contexts/AuthContext.tsx)

**What:** React Context that wraps `onAuthStateChanged`. Exposes `user`, `loading`, and `signOut`.
**When to use:** Wrap `<App>` or the root router in `<AuthProvider>`. Read via `useAuth()` hook.

```typescript
// Source: https://github.com/firebase/firebase-js-sdk/blob/main/docs-devsite/auth.md (onAuthStateChanged)
import { createContext, useContext, useEffect, useState } from 'react';
import { onAuthStateChanged, signOut as firebaseSignOut, User } from 'firebase/auth';
import { auth } from '@/lib/firebase';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true); // true until first callback fires

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser);
      setLoading(false);
    });
    return unsubscribe; // cleanup on unmount
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

### Pattern 3: PrivateRoute (components/PrivateRoute.tsx)

**What:** Component that blocks rendering until `onAuthStateChanged` has fired and redirects to `/login` if no user.
**When to use:** Wrap all protected route elements.

```typescript
// Source: https://github.com/remix-run/react-router/blob/main/examples/auth/src/App.tsx (RequireAuth pattern)
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

export function PrivateRoute({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return null; // or a spinner — decisions say it is Claude's discretion
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  return children;
}
```

### Pattern 4: Axios apiClient with per-request token (lib/apiClient.ts)

**What:** Axios instance with a request interceptor that calls `getIdToken()` before every request. A response interceptor handles 401 by redirecting to login.
**When to use:** All API calls in Phases 12–14 use this instance, never raw `fetch`.

```typescript
// Source: https://github.com/firebase/firebase-js-sdk/blob/main/docs-devsite/auth.md (getIdToken)
import axios from 'axios';
import { getIdToken } from 'firebase/auth';
import { auth } from '@/lib/firebase';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
});

// Request interceptor — never store the token string in state
apiClient.interceptors.request.use(async (config) => {
  const user = auth.currentUser;
  if (user) {
    const token = await getIdToken(user); // Firebase refreshes if < 5 min from expiry
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — 401 means expired/revoked token → force re-login
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = '/login'; // hard redirect clears React state cleanly
    }
    return Promise.reject(error);
  }
);
```

**Why `getIdToken(user)` without `forceRefresh: true`:** Firebase's SDK returns the cached token if it is valid for more than 5 minutes; it silently refreshes otherwise. Passing `forceRefresh: true` on every request would hammer Firebase's token endpoint unnecessarily. The `window.location.href` redirect on 401 is appropriate here because a 401 in production means the token is no longer accepted server-side — that requires a fresh login, not just a retry.

### Pattern 5: Tailwind v3 configuration with Poppins and dark CSS vars (tailwind.config.js + index.css)

**What:** Tailwind v3 config with Poppins font family and `darkMode: 'class'`. CSS file overrides two CSS variables for the Midnight palette.
**When to use:** Set up in Wave 0 scaffolding tasks.

```javascript
// tailwind.config.js — Tailwind v3 format (tailwind.config.js, not tailwind.config.ts for shadcn@2.3.0 compat)
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Poppins', 'sans-serif'],  // D-03
      },
    },
  },
  plugins: [],
};
```

```css
/* src/index.css — D-03 Google Fonts + D-02 Midnight overrides */
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* shadcn/ui dark preset variables set by shadcn init */
  }
  .dark {
    --background: 216 18% 11%;   /* #161b22 in HSL */
    --primary:    212 100% 68%;  /* #58a6ff in HSL */
  }
}
```

**Note on CSS variable format:** shadcn/ui v2.x defines CSS variables as raw HSL channel values (e.g., `216 18% 11%`), not full `hsl(...)` calls. Override in the same format.

### Pattern 6: shadcn/ui Sidebar for navigation

**What:** shadcn Sidebar component with `SidebarProvider`, `Sidebar`, `SidebarContent`, `SidebarMenu`, `SidebarMenuItem`, `SidebarMenuButton`. Use `NavLink` from react-router-dom inside `SidebarMenuButton` to get `isActive`.

```typescript
// Source: https://ui.shadcn.com/docs/components/sidebar
import { NavLink } from 'react-router-dom';
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent,
  SidebarMenu, SidebarMenuItem, SidebarMenuButton, SidebarProvider,
} from '@/components/ui/sidebar';

const navItems = [
  { to: '/',            label: 'Dashboard' },
  { to: '/accounts',   label: 'Accounts' },
  { to: '/liabilities',label: 'Liabilities' },
  { to: '/pension',    label: 'Pension' },
  { to: '/history',    label: 'History' },
  { to: '/configure',  label: 'Configure' },
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
                        isActive ? 'text-[#58a6ff] font-semibold' : ''
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

### Anti-Patterns to Avoid

- **Storing the Firebase ID token in state or localStorage:** The token string expires hourly. Always call `getIdToken(user)` on demand — this is what REACT-03 requires and what the Axios interceptor pattern above does.
- **Using shadcn@latest init with Tailwind v3 requirement:** `shadcn@latest` (currently 4.7.0) scaffolds Tailwind v4 with `@tailwindcss/vite`. This is incompatible with the Tailwind v3 `tailwind.config.js` + PostCSS approach. Always use `shadcn@2.3.0` for this project.
- **Rendering protected page content during auth loading:** `onAuthStateChanged` fires asynchronously. If `loading=true` is not checked before rendering, financial data may briefly flash for unauthenticated states. Return `null` (or a spinner) while `loading=true`.
- **Installing the old shadcn toast component:** CLI will warn it is deprecated. Use `sonner` instead in all phases.
- **Calling `initializeApp` in multiple modules:** Import the `auth` singleton from `lib/firebase.ts` — do not call `initializeApp` in AuthContext or apiClient.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Accessible sidebar navigation | Custom `<aside>` + ARIA roles | shadcn/ui Sidebar | Keyboard nav, collapse, aria-current, responsive already built |
| CSS variable dark mode | Manual class toggling | shadcn/ui dark preset + `class` mode | shadcn handles all token definitions |
| Conditional classnames | String concatenation | `cn()` (clsx + tailwind-merge) | Avoids Tailwind class conflicts, installed by shadcn init |
| Protected routes | Manual `if (user)` in every page | `PrivateRoute` wrapper component | Single source of auth gate — consistent redirect + loading handling |
| Token refresh logic | setTimeout / manual refresh loop | Firebase `getIdToken()` SDK | SDK handles expiry, refresh, network retry internally |
| Toast notifications | Custom notification component | `sonner` (via shadcn) | Old shadcn toast deprecated; sonner is the current recommendation |

**Key insight:** The Firebase JS SDK's `getIdToken()` handles token refresh transparently. There is no need for a custom refresh loop, a background worker, or storing expiry timestamps.

---

## Common Pitfalls

### Pitfall 1: Tailwind v4 scaffold when v3 is required
**What goes wrong:** Running `npx shadcn@latest init` (v4.7.0+) produces a Tailwind v4 project using `@tailwindcss/vite` plugin and `@import "tailwindcss"` — no `tailwind.config.js`, no PostCSS. All subsequent Tailwind v3 utilities and `tailwind.config.js` references break.
**Why it happens:** shadcn's current CLI defaults to Tailwind v4 for new projects.
**How to avoid:** Always use `npx shadcn@2.3.0 init` when the project requires Tailwind v3.
**Warning signs:** No `tailwind.config.js` or `postcss.config.js` after init; `index.css` contains `@import "tailwindcss"` instead of `@tailwind base/components/utilities` directives.

### Pitfall 2: CSS variable format mismatch
**What goes wrong:** Overriding `--background: #161b22` (hex) instead of `--background: 216 18% 11%` (raw HSL channels). shadcn/ui components use CSS variables as HSL channels inside `hsl()`: `background-color: hsl(var(--background))`. A hex value will silently produce an invalid colour.
**Why it happens:** shadcn/ui v2.x uses raw HSL channel notation, not full CSS colour values.
**How to avoid:** Convert hex to HSL channels — `#161b22` = `216 18% 11%`, `#58a6ff` = `212 100% 68%`. Set `--background: 216 18% 11%` and `--primary: 212 100% 68%` in the `.dark` block.
**Warning signs:** Background renders as transparent or white despite CSS var being set.

### Pitfall 3: onAuthStateChanged not awaited before rendering
**What goes wrong:** On page load, `user` is `null` and `loading` is `true`. If PrivateRoute checks only `user`, it immediately redirects to `/login` on every hard refresh — even for authenticated users — because the `onAuthStateChanged` callback hasn't fired yet.
**Why it happens:** Firebase auth state is restored asynchronously from browser storage (IndexedDB).
**How to avoid:** Check `loading` first: `if (loading) return null`. Only check `user` after `loading=false`.
**Warning signs:** Authenticated user is always redirected to login on browser refresh.

### Pitfall 4: Axios interceptor accessing stale currentUser
**What goes wrong:** The response interceptor captures a reference to `auth.currentUser` at setup time (inside a closure). If the user object changes, the closure holds a stale reference.
**Why it happens:** Closures over mutable module-level variables.
**How to avoid:** Always read `auth.currentUser` inside the async interceptor body at call time — not in the module scope. The pattern in Code Examples reads `const user = auth.currentUser` at request time, which is correct.
**Warning signs:** Token refreshes silently failing; 401 errors on requests after token expiry.

### Pitfall 5: `react-router-dom` v7 API changes
**What goes wrong:** If `npm install react-router-dom` resolves to v7 (currently possible since latest is v7.x), the `<Routes>/<Route>` declarative API still works but v7 adds breaking changes to data routers and imports.
**Why it happens:** npm installs latest by default.
**How to avoid:** Pin: `npm install react-router-dom@6.30.3`. This is the latest stable v6 release.
**Warning signs:** TypeScript errors on `<Routes>` import; unexpected `createBrowserRouter` requirement.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| shadcn `useToast` hook + toast component | `sonner` library | Early 2025 | Must use sonner; CLI rejects old toast install |
| `shadcn-ui` npm package (old) | `shadcn` npm package | 2024 | The CLI is now `npx shadcn@2.3.0`, not `npx shadcn-ui@latest` |
| Tailwind v3 PostCSS pipeline | Tailwind v4 Vite plugin | Feb 2025 | New shadcn projects default to v4; v3 requires pinned CLI |
| `firebase/compat` namespace imports | Modular v9+ tree-shakeable imports | Firebase v9 (2021) | Import `getAuth`, `signInWithPopup` from `firebase/auth`; no `firebase.auth()` |
| React Router v5 `<Switch>` | React Router v6 `<Routes>` | 2021 | `<Switch>` removed; use `<Routes>` + `<Route element={...}>` |

**Deprecated/outdated:**
- `shadcn-ui` CLI package: replaced by `shadcn` — the command is now `npx shadcn@2.3.0`
- shadcn `toast` component with `useToast`: deprecated, replaced by `sonner`
- Firebase compat API (`import firebase from 'firebase/app'`): use modular imports only

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `#161b22` converts to HSL `216 18% 11%` and `#58a6ff` converts to HSL `212 100% 68%` | Code Examples / CSS Vars | Wrong HSL values = incorrect Midnight background or primary colour; easy to spot and fix |
| A2 | shadcn@2.3.0 with Tailwind v3 accepts `darkMode: ['class']` in tailwind.config.js | Standard Stack | If false, dark mode setup needs different config; verify by inspecting generated `components.json` after init |
| A3 | `window.location.href = '/login'` is acceptable for 401 redirect in the apiClient | Code Examples | If React Router context is needed (e.g., to preserve scroll), use `navigate` from a custom hook instead; for an auth-required app this is low risk |

---

## Open Questions

1. **tailwind.config.js vs tailwind.config.ts format for shadcn@2.3.0**
   - What we know: shadcn@2.3.0 generates a `tailwind.config.js` (JS, not TS) when run with default prompts on a Vite project
   - What's unclear: Whether passing `--ts` during init produces a `.ts` version and if that causes any issues
   - Recommendation: Use `.js` format as generated; no need to force TypeScript for the config file

2. **Exact `components.json` `style` value for shadcn@2.3.0**
   - What we know: shadcn v2.x prompts for `style: default | new-york`; CONTEXT.md doesn't lock a style
   - What's unclear: Which style produces a result closer to the Midnight design
   - Recommendation: Use `new-york` — it has slightly sharper radius defaults and better dark mode contrast. This is Claude's discretion per CONTEXT.md.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Vite dev server | Yes | v25.6.1 | — |
| npm | Package installation | Yes | 11.9.0 | — |
| npx | shadcn CLI | Yes | bundled with npm | — |
| git | Repo | Yes | (implied by repo) | — |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** None.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest (client-side); pytest (existing Python tests) |
| Config file | `client/vitest.config.ts` — does not exist yet (Wave 0 gap) |
| Quick run command | `cd client && npx vitest run --reporter=verbose` |
| Full suite command | `cd client && npx vitest run` |

**Note:** Phase 11 is a scaffolding phase — most verification is structural (files exist, app starts, login works) rather than unit-testable. The smoke test is `cd client && npm run dev` + manual browser check for login flow.

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REACT-01 | Vite dev server starts on port 5173 | smoke | `cd client && npm run build` (no errors) | No — Wave 0 |
| REACT-01 | tailwind.config.js exists with Poppins and darkMode:class | structural | `ls client/tailwind.config.js` | No — Wave 0 |
| REACT-02 | PrivateRoute redirects unauthenticated user to /login | unit | `npx vitest run` with mock auth context | No — Wave 0 |
| REACT-02 | PrivateRoute renders null while loading=true | unit | `npx vitest run` with loading mock | No — Wave 0 |
| REACT-03 | apiClient attaches Authorization header | unit | `npx vitest run` with mocked Firebase auth | No — Wave 0 |
| REACT-03 | apiClient redirects on 401 | unit | `npx vitest run` with mocked 401 response | No — Wave 0 |
| REACT-04 | Sidebar renders all 6 nav links | unit | `npx vitest run` with jsdom | No — Wave 0 |

### Sampling Rate
- **Per task commit:** `cd client && npm run build` (TypeScript compile check)
- **Per wave merge:** `cd client && npx vitest run`
- **Phase gate:** `npm run build` passes + manual browser smoke test of login flow

### Wave 0 Gaps
- [ ] `client/vitest.config.ts` — Vitest configuration (also requires `@testing-library/react`, `jsdom`)
- [ ] `client/src/__tests__/PrivateRoute.test.tsx` — covers REACT-02
- [ ] `client/src/__tests__/apiClient.test.ts` — covers REACT-03
- [ ] `client/src/__tests__/AppSidebar.test.tsx` — covers REACT-04

**Test dependencies to install:**
```bash
npm install -D vitest @vitest/coverage-v8 @testing-library/react @testing-library/user-event jsdom
```

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Firebase Google Sign-In popup; `onAuthStateChanged` gate |
| V3 Session Management | yes | Firebase manages session; no custom session storage |
| V4 Access Control | yes | PrivateRoute pattern; all routes gated |
| V5 Input Validation | no | Phase 11 has no forms (stubs only) |
| V6 Cryptography | no | Firebase handles token signing; React never touches raw keys |

### Known Threat Patterns for React + Firebase Auth + Axios

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Token stored in localStorage | Information Disclosure | Never store token — call `getIdToken()` per request via interceptor |
| CSRF via state mutation | Tampering | All state changes go through FastAPI with Bearer token; CORS allow-list in api/main.py already restricts origins |
| Popup blocked by browser | Denial of Service | `signInWithPopup` can fall back to `signInWithRedirect`; document in error handling |
| Stale auth state after token revocation | Elevation of Privilege | 401 response interceptor forces re-login immediately |
| XSS token extraction | Information Disclosure | Token never in DOM/localStorage; only in memory as transient interceptor variable |

---

## Sources

### Primary (HIGH confidence)
- `/firebase/firebase-js-sdk` (Context7) — `getIdToken`, `onAuthStateChanged`, `signInWithPopup`, `initializeApp`, `GoogleAuthProvider`
- `/remix-run/react-router` (Context7) — RequireAuth/PrivateRoute pattern, `Navigate`, `useLocation`
- `/llmstxt/ui_shadcn_llms_txt` (Context7) — Sidebar component hierarchy, Tailwind init for Vite, toast/sonner status
- `npm registry` — All package versions verified: firebase@12.13.0, vite@8.0.11, react@18.3.1, tailwindcss@3.4.19, react-router-dom@6.30.3, shadcn@2.3.0 (2026-05-08)
- `https://v3.tailwindcss.com/docs/guides/vite` — Tailwind v3 PostCSS install steps
- `https://ui.shadcn.com/docs/tailwind-v4` — Confirmed new projects default to Tailwind v4; v3 requires `shadcn@2.3.0`

### Secondary (MEDIUM confidence)
- `https://github.com/shadcn-ui/ui/discussions/6772` — Maintainer-confirmed: use `shadcn@2.3.0` for Tailwind v3
- `https://github.com/shadcn-ui/ui/issues/7120` — Toast deprecation: CLI emits "use sonner instead" on toast install
- `https://github.com/shadcn-ui/ui/pull/6982` — Deprecation callout added to toast docs
- `api/main.py` (codebase) — CORS allow-list confirmed; `http://localhost:5173` already in `ALLOWED_ORIGINS`
- `api/dependencies.py` (codebase) — Auth contract confirmed: `Authorization: Bearer <token>` → returns `uid` string
- `app/config.py` (codebase) — `firebase_web_api_key`, `firebase_auth_domain`, `firebase_project_id` field names confirmed

### Tertiary (LOW confidence — none used as primary claims)
- WebSearch results for Axios + Firebase interceptor patterns — supported by Context7 Firebase docs

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified against npm registry on 2026-05-08
- Architecture: HIGH — patterns from official React Router, Firebase, and shadcn/ui docs
- Pitfalls: HIGH — Tailwind v3/v4 conflict and CSS var format verified from official shadcn docs; others from codebase + docs

**Research date:** 2026-05-08
**Valid until:** 2026-06-08 (30 days — shadcn/ui and Firebase version landscape is evolving but stable at patch level)
