---
phase: 11-react-scaffold-and-auth
plan: 03
subsystem: client/api
tags: [axios, firebase, interceptor, vitest]
key-files:
  - client/src/lib/apiClient.ts
  - client/src/__tests__/apiClient.test.ts
metrics:
  tests: "7 passed (4 new apiClient + 3 PrivateRoute from plan 02)"
  build: "✓ 0 errors"
---

## Summary

Implemented the Axios apiClient with Firebase ID token interceptor and 401 redirect. All tests pass.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | a62c21a | apiClient with interceptors and unit tests |

## Deviations

None. Implemented exactly as specified in the plan.

## Self-Check: PASSED

- `npx vitest run` exits 0 — all 7 tests pass (4 apiClient + 3 PrivateRoute) in 560ms
- `npm run build` exits 0 — no TypeScript errors
- apiClient.ts reads `auth.currentUser` inside the interceptor body (not module scope)
- Token string exists only as local variable inside the interceptor function, never stored
- Response interceptor sets `window.location.href = '/login'` on 401
- No redirect on non-401 errors (500 tested explicitly)
