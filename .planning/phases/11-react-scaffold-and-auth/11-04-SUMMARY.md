---
phase: 11-react-scaffold-and-auth
plan: 04
subsystem: client/layout
tags: [sidebar, layout, pages, react-router, shadcn, vitest]
key-files:
  - client/src/components/AppSidebar.tsx
  - client/src/components/AppLayout.tsx
  - client/src/pages/DashboardPage.tsx
  - client/src/pages/AccountsPage.tsx
  - client/src/pages/LiabilitiesPage.tsx
  - client/src/pages/PensionPage.tsx
  - client/src/pages/HistoryPage.tsx
  - client/src/pages/ConfigurePage.tsx
  - client/src/App.tsx
  - client/src/__tests__/AppSidebar.test.tsx
metrics:
  tests: "14 passed (7 AppSidebar + 4 apiClient + 3 PrivateRoute)"
  build: "✓ 0 errors, 1837 modules"
---

## Summary

Implemented sidebar navigation shell, shared layout, and 6 page stubs. Phase 11 scope is now complete.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | 2651787 | AppSidebar + AppLayout + AppSidebar tests |
| Task 2 | 403b699 | 6 page stubs + App.tsx route wiring |

## Deviations

**AppSidebar.test.tsx mocks react-router-dom + shadcn sidebar**: Plan specified using MemoryRouter, but MemoryRouter causes React 19 microtask OOM in vitest workers (same issue found in Plan 02). Used the same fix as PrivateRoute: mock `react-router-dom` (NavLink → plain anchor) and mock all shadcn sidebar primitives as transparent wrappers. Tests verify label text presence, which covers the REACT-04 requirement that "all 6 nav links render".

## Self-Check: PASSED

- `npx vitest run` exits 0 — all 14 tests pass (7 AppSidebar + 4 apiClient + 3 PrivateRoute) in 549ms
- `npm run build` exits 0 — 1837 modules, no TypeScript errors
- AppSidebar.tsx contains `text-[#58a6ff]`, `border-l-2 border-[#58a6ff]`, and `isActive` callback
- navItems array has exactly 6 routes in D-05 order: /, /accounts, /liabilities, /pension, /history, /configure
- AppLayout.tsx renders `<Outlet />` for nested routes
- App.tsx uses AppLayout as layout shell, no inline placeholder divs
