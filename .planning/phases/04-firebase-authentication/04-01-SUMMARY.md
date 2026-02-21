---
phase: 04-firebase-authentication
plan: 01
subsystem: authentication
tags: [firebase, auth, streamlit-component, backend-service]

dependency_graph:
  requires: [app/models.py, app/config.py]
  provides: [auth_service.py, auth_component/index.html]
  affects: []

tech_stack:
  added: [firebase-admin, firebase-js-sdk-12.9.0]
  patterns: [custom-streamlit-component, zero-build-component, postMessage-protocol]

key_files:
  created:
    - app/services/auth_service.py
    - frontend/auth_component/index.html
  modified:
    - app/config.py
    - .env.example

decisions:
  - "Use raw postMessage instead of Streamlit JS helper for zero-build component"
  - "Firebase Admin SDK hot-reload protection with if not firebase_admin._apps guard"
  - "Browser local persistence for transparent re-auth on page reload"
  - "Three-state protocol: initializing, authenticated (with token), unauthenticated"

metrics:
  duration_seconds: 118
  tasks_completed: 2
  files_created: 2
  files_modified: 2
  commits: 2
  completed_date: 2026-02-21
---

# Phase 04 Plan 01: Firebase Auth Foundation Summary

**One-liner:** Firebase Admin SDK integration with custom zero-build Streamlit component for Google Sign-In

## What Was Built

Created the foundational auth layer with two independent components:

1. **Backend auth service** (`app/services/auth_service.py`):
   - Firebase Admin SDK initialization with hot-reload protection
   - Token verification returning decoded claims (uid, email, name)
   - Get-or-create user pattern for auto-provisioning

2. **Frontend auth component** (`frontend/auth_component/index.html`):
   - Zero-build custom Streamlit component using Firebase JS SDK 12.9.0 from CDN
   - Raw postMessage protocol implementation (no build tooling needed)
   - Three-state protocol with token passing
   - Branded login UI with Google Sign-In
   - Browser local persistence for seamless re-auth

These components are ready for integration in Plan 02.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Auth service and config | 3f82e56 | app/services/auth_service.py, app/config.py, .env.example |
| 2 | Firebase auth custom Streamlit component | 877a53a | frontend/auth_component/index.html |

## Deviations from Plan

None - plan executed exactly as written.

## Technical Decisions

**1. Zero-build component approach**
- Used ES module imports from Firebase CDN (v12.9.0)
- Implemented raw `window.parent.postMessage` instead of Streamlit JS helper
- Single HTML file, no npm/webpack/build step
- **Rationale:** Simpler development and deployment; no build tooling complexity

**2. Hot-reload protection pattern**
- Guard Firebase Admin init with `if not firebase_admin._apps:`
- Prevents ValueError on Streamlit's hot-reload during development
- **Rationale:** Critical for dev experience; Streamlit hot-reloads on every file change

**3. Three-state protocol**
- `initializing`: Sent before auth state determined
- `authenticated`: Includes fresh ID token from `user.getIdToken()`
- `unauthenticated`: User signed out or no session
- **Rationale:** Parent component needs to distinguish "loading" from "logged out"

**4. Browser local persistence**
- `setPersistence(auth, browserLocalPersistence)` before listener setup
- Token survives page refreshes and browser restarts
- **Rationale:** Reduces auth friction; users stay logged in

## Implementation Notes

**Auth service:**
- Returns `None` on token verification failure (logged with loguru)
- Skips Firebase Admin init if `firebase_credentials_path` is empty (allows dev without creds)
- Auto-creates User row on first login (get-or-create pattern)

**Auth component:**
- `componentReady` message sent before any render
- UI auto-hides (height 0) when authenticated
- Error handling for popup blocked, cancelled, or auth failure
- Supports `action: "logout"` from parent to trigger sign-out

## Verification Results

All verification passed:
- ✓ auth_service imports work
- ✓ config.py has Firebase web config fields
- ✓ auth_component/index.html exists with all required code
- ✓ ruff check passes
- ✓ .env.example documents all Firebase env vars

## Next Steps

Plan 02 will wire these components into `main.py`:
- Call `init_firebase_admin()` on app startup
- Render auth component in main layout
- Use token from component to verify and get/create user
- Store user in session state
- Implement login/logout flow

## Self-Check: PASSED

Verifying all claimed artifacts exist:

```bash
# Files created
FOUND: app/services/auth_service.py
FOUND: frontend/auth_component/index.html

# Commits exist
FOUND: 3f82e56
FOUND: 877a53a
```

All artifacts verified successfully.
