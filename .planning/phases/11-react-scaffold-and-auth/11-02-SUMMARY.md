---
phase: 11-react-scaffold-and-auth
plan: 02
subsystem: client/auth
tags: [firebase, auth, react-router, vitest]
key-files:
  - client/src/lib/firebase.ts
  - client/src/contexts/AuthContext.tsx
  - client/src/components/PrivateRoute.tsx
  - client/src/pages/LoginPage.tsx
  - client/src/App.tsx
  - client/src/__tests__/PrivateRoute.test.tsx
metrics:
  tests: "3 passed"
  build: "✓ 0 errors"
---

## Summary

Implemented the Firebase auth gate for the React frontend. All deliverables from the plan are complete.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | f20f6c5 | firebase.ts, AuthContext, PrivateRoute, unit tests |
| Task 2 | bbfcb91 | LoginPage and App.tsx route wiring |

## Deviations

**React 19 + MemoryRouter OOM in vitest worker**: React Router v6 `MemoryRouter` triggers an infinite microtask loop via `useSyncExternalStore` + React 19 concurrent mode inside vitest worker threads, exhausting heap (~4GB). Resolution: mocked `react-router-dom` in `PrivateRoute.test.tsx` (Navigate + useLocation) instead of wrapping in MemoryRouter. This tests the same contract (null on loading, redirect on no-user, render children on auth) without the Router context overhead. Also switched vitest config to `happy-dom` + `pool: vmThreads` + `teardownTimeout: 5000`.

**`verbatimModuleSyntax` TS6133**: `User` type from `firebase/auth` must be imported with `import type`. Fixed in `AuthContext.tsx`.

## Self-Check: PASSED

- `npx vitest run` exits 0 — all 3 PrivateRoute tests pass (507ms)
- `npm run build` exits 0 — 41 modules, no TypeScript errors
- PrivateRoute checks `if (loading) return null` before `if (!user)` — no-flash guarantee preserved
- firebase.ts exports `auth` and `googleProvider`, `initializeApp` called once
- LoginPage renders: "Finance Tracker", "Your net worth at a glance.", "Sign in with Google", "Sign-in failed. Please try again."
- App.tsx wraps all routes except `/login` with `PrivateRoute`
