---
phase: 04-firebase-authentication
verified: 2026-02-21T12:00:00Z
status: gaps_found
score: 5/6 truths verified
re_verification: false
gaps:
  - truth: "Unauthenticated browser shows login screen with no financial data visible"
    status: partial
    reason: "Debug output visible in sidebar on login screen"
    artifacts:
      - path: "frontend/main.py"
        issue: "Line 82 has debug statement visible to unauthenticated users"
    missing:
      - "Remove debug statement: st.sidebar.write('DEBUG - Status: unauthenticated')"
---

# Phase 04: Firebase Authentication Verification Report

**Phase Goal:** The app enforces authentication — only the owner can view their financial data  
**Verified:** 2026-02-21T12:00:00Z  
**Status:** gaps_found  
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

Based on ROADMAP.md success criteria and Plan 02 must_haves:

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Unauthenticated browser shows login screen with no financial data visible | ⚠️ PARTIAL | Login screen implemented with sidebar hiding, but debug output leaks to sidebar (line 82) |
| 2 | Google Sign-In authenticates and loads dashboard with user data | ✓ VERIFIED | Component implements signInWithPopup, main.py verifies token and sets session_state |
| 3 | Session survives Streamlit page navigation without re-login | ✓ VERIFIED | st.session_state.user_id checked in _auth_gate() before rendering component |
| 4 | Logout clears session and returns to login screen | ✓ VERIFIED | Logout button sets flag, calls widget with action="logout", clears session state |
| 5 | First login auto-creates user row satisfying FK constraints | ✓ VERIFIED | get_or_create_user() called in auth gate with uid, email, display_name |
| 6 | Page reload with valid localStorage session goes straight to app (no login flash) | ✓ VERIFIED | Component uses browserLocalPersistence, onAuthStateChanged fires on reload |

**Score:** 5/6 truths verified (1 partial due to debug output)

### Required Artifacts

#### Plan 01 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `app/services/auth_service.py` | Firebase Admin init, token verification, user auto-creation | ✓ VERIFIED | 89 lines, exports init_firebase_admin, verify_firebase_token, get_or_create_user; hot-reload guard present |
| `app/config.py` | Firebase web config settings | ✓ VERIFIED | Contains firebase_web_api_key, firebase_auth_domain, firebase_project_id |
| `frontend/auth_component/index.html` | Custom Streamlit component with Firebase JS SDK | ✓ VERIFIED | 285 lines (exceeds 50 min), implements postMessage protocol, three-state handling |
| `.env.example` | Firebase env var placeholders | ✓ VERIFIED | Contains FIREBASE_WEB_API_KEY, FIREBASE_AUTH_DOMAIN, FIREBASE_PROJECT_ID, FIREBASE_CREDENTIALS_PATH |

#### Plan 02 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/main.py` | Auth gate, component integration, sidebar logout | ⚠️ PARTIAL | Contains declare_component, auth_gate, logout button; but has debug output at line 82 |
| `scripts/migrate_test_user.py` | Data migration script for test-user to real UID | ✓ VERIFIED | Contains UPDATE statements for 4 tables, DELETE for test-user, --dry-run support |

### Key Link Verification

#### Plan 01 Key Links

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `frontend/auth_component/index.html` | Streamlit component protocol | window.parent.postMessage with isStreamlitMessage | ✓ WIRED | Found 3 instances of "isStreamlitMessage: true" at lines 136, 146, 279 |
| `app/services/auth_service.py` | app/models.py User | SQLModel session to create user | ✓ WIRED | Line 82: User(id=uid, email=email, display_name=display_name) |

#### Plan 02 Key Links

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `frontend/main.py` | `frontend/auth_component/index.html` | declare_component with path | ✓ WIRED | Line 21: declare_component("firebase_auth", path=_AUTH_COMPONENT_DIR) |
| `frontend/main.py` | `app/services/auth_service.py` | verify_firebase_token + get_or_create_user | ✓ WIRED | Lines 13-15 import, lines 104, 117 call functions |
| `frontend/main.py` | st.session_state | user_id stored after verification | ✓ WIRED | Lines 57, 65, 122 interact with session_state.user_id |

### Requirements Coverage

From REQUIREMENTS.md, Phase 4 has 6 requirements:

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| AUTH-01: User can sign in with Google Sign-In via Firebase OAuth popup | ✓ SATISFIED | Component implements signInWithPopup with GoogleAuthProvider |
| AUTH-02: App verifies Firebase ID token server-side before granting access | ✓ SATISFIED | Line 104 calls verify_firebase_token() before allowing access |
| AUTH-03: User session persists across page reruns | ✓ SATISFIED | st.session_state.user_id checked at line 65, survives reruns |
| AUTH-04: App shows login screen with no page content if user is not authenticated | ⚠️ PARTIAL | Login screen implemented but debug output visible (line 82) |
| AUTH-05: User can log out, clearing session state | ✓ SATISFIED | Lines 259-261 implement logout button, lines 53-62 handle logout flow |
| AUTH-06: User account is auto-created on first successful login | ✓ SATISFIED | Line 117 calls get_or_create_user(session, uid, email, name) |

**Coverage:** 5/6 requirements fully satisfied, 1 partial

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| frontend/main.py | 82 | Debug output in production code | ⚠️ Warning | Leaks implementation detail to unauthenticated users via sidebar |

**Details:**
- Line 82: `st.sidebar.write("DEBUG - Status: unauthenticated")` — This writes to the sidebar on the login screen, violating the goal that "no financial data visible" should extend to no implementation details visible.
- The sidebar is hidden via CSS (lines 84-94), but the write() call happens before the CSS injection, potentially causing a brief flash or accessibility leak.

### Human Verification Required

The following items were verified by the user in Plan 02, Task 3 (checkpoint):

#### 1. Login Screen Appearance

**Test:** Open app at localhost:8501 when unauthenticated  
**Expected:** Branded login card with "Net Worth Tracker" title, Google Sign-In button, no sidebar, no financial data  
**Status:** User verified as passed in 04-02-SUMMARY.md  
**Why human:** Visual appearance, branding quality, UX polish

#### 2. Google Sign-In Flow

**Test:** Click "Sign in with Google", complete OAuth flow in popup  
**Expected:** Popup appears, user authenticates, dashboard loads with user name/email in sidebar  
**Status:** User verified as passed in 04-02-SUMMARY.md  
**Why human:** Requires real Firebase project, browser popup interaction, OAuth flow

#### 3. Navigation Persistence

**Test:** After login, click through Dashboard → Accounts → Liabilities → History → Configure  
**Expected:** Each page loads without re-login prompt  
**Status:** User verified as passed in 04-02-SUMMARY.md  
**Why human:** Multi-step navigation flow, session state behavior across reruns

#### 4. Page Reload Persistence

**Test:** Refresh browser (F5) while logged in  
**Expected:** App loads directly to last viewed page, no login screen flash  
**Status:** User verified as passed in 04-02-SUMMARY.md  
**Why human:** Browser localStorage behavior, timing of auth state detection

#### 5. Logout Flow

**Test:** Click "Log out" button at bottom of sidebar  
**Expected:** Return to login screen, all session data cleared, no financial data visible  
**Status:** User verified as passed in 04-02-SUMMARY.md  
**Why human:** End-to-end logout flow, state cleanup verification

#### 6. User Auto-Creation

**Test:** Check database users table after first login  
**Expected:** User row exists with Firebase UID, email, display_name  
**Status:** User verified as passed in 04-02-SUMMARY.md  
**Why human:** Requires database inspection, real auth flow

### Gaps Summary

**1 minor gap found:**

The auth gate is fully functional but has a debug output statement that violates the principle of "no data visible" on the login screen. The statement `st.sidebar.write("DEBUG - Status: unauthenticated")` at line 82 of `frontend/main.py` should be removed before declaring Phase 4 complete.

**Impact:** Low severity — the sidebar is hidden via CSS immediately after this write, so it's unlikely to be visible in practice. However, it's technically present in the DOM and represents incomplete cleanup.

**Fix:** Delete line 82 in `frontend/main.py`.

---

_Verified: 2026-02-21T12:00:00Z_  
_Verifier: Claude (gsd-verifier)_
