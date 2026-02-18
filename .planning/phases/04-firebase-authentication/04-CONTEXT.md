# Phase 4: Firebase Authentication - Context

**Gathered:** 2026-02-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the hardcoded `TEST_USER_ID = "test-user"` in `frontend/main.py` with real Firebase Authentication using Google Sign-In. This phase ends when: (1) an unauthenticated user sees a branded login screen, (2) Google Sign-In works via the Firebase JS SDK component, (3) the auth gate blocks all page content until authenticated, (4) session persists during Streamlit page navigation, (5) transparent re-auth on page reload works via Firebase localStorage, (6) logout clears session, (7) user record is auto-created on first login. Validated locally in docker-compose only — no cloud deployment in this phase.

</domain>

<decisions>
## Implementation Decisions

### Login screen design
- Branded login page: app name + short description ("your net worth tracker") + "Sign in with Google" button
- Full page takeover when unauthenticated — sidebar collapses or is hidden entirely, nothing from the app is visible
- No financial data preview or teasers behind the login card — clean login only

### Session & cold start behavior
- Transparent re-auth on page load: Firebase JS SDK uses `onAuthStateChanged` + localStorage to silently restore the session. User goes straight to the app if previously signed in.
- During the brief auth-check moment: show a blank screen or minimal spinner. Do NOT flash the login screen before resolving.
- Token truly expired or no localStorage entry → show login screen normally

### Post-login flow
- After Google Sign-In succeeds: always redirect to Dashboard (no "restore previous destination" logic)
- First login (user record doesn't exist yet): auto-create user silently, land on Dashboard with no welcome message or onboarding
- Logout button: bottom of sidebar, below page navigation links

### Claude's Discretion
- Exact spinner/loading UI during auth check (text, icon, position)
- Error handling for Google popup blocked or login failure — show a simple error message and re-present the login button
- Exact wording of the branded login screen description text
- Firebase JS SDK version to pin (verify latest 11.x from gstatic.com at implementation time)
- Whether to include user display name or email anywhere in the sidebar post-login (Claude can decide if it adds value)

</decisions>

<specifics>
## Specific Ideas

- The `st.components.v1.html()` postMessage token bridge is the key technical risk flagged in research. If it silently returns `None` in Streamlit 1.53.1, use the fallback approach: call Firebase REST API (`identitytoolkit.googleapis.com`) from Python — but note this doesn't support Google Sign-In (OAuth popup must run in browser). Google Sign-In requires the JS component approach. If the component bridge fails, we either fix it or switch to email/password via REST API. Document the decision before implementing.
- Research also flagged: guard Firebase Admin SDK initialization with `if not firebase_admin._apps` to prevent `ValueError` on Streamlit hot-reload.
- Data migration: write a script to `UPDATE accounts/liabilities/snapshots SET user_id = '<real_uid>' WHERE user_id = 'test-user'` — needed before Phase 5 deployment. Can be written in Phase 4 but executed in Phase 5.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-firebase-authentication*
*Context gathered: 2026-02-18*
