# Phase 4: Firebase Authentication - Research

**Researched:** 2026-02-18
**Domain:** Firebase Authentication + Streamlit custom component bridge
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Login screen design**
- Branded login page: app name + short description ("your net worth tracker") + "Sign in with Google" button
- Full page takeover when unauthenticated — sidebar collapses or is hidden entirely, nothing from the app is visible
- No financial data preview or teasers behind the login card — clean login only

**Session & cold start behavior**
- Transparent re-auth on page load: Firebase JS SDK uses `onAuthStateChanged` + localStorage to silently restore the session. User goes straight to the app if previously signed in.
- During the brief auth-check moment: show a blank screen or minimal spinner. Do NOT flash the login screen before resolving.
- Token truly expired or no localStorage entry → show login screen normally

**Post-login flow**
- After Google Sign-In succeeds: always redirect to Dashboard (no "restore previous destination" logic)
- First login (user record doesn't exist yet): auto-create user silently, land on Dashboard with no welcome message or onboarding
- Logout button: bottom of sidebar, below page navigation links

### Claude's Discretion
- Exact spinner/loading UI during auth check (text, icon, position)
- Error handling for Google popup blocked or login failure — show a simple error message and re-present the login button
- Exact wording of the branded login screen description text
- Firebase JS SDK version to pin (verify latest 11.x from gstatic.com at implementation time)
- Whether to include user display name or email anywhere in the sidebar post-login (Claude can decide if it adds value)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

## Summary

Firebase Authentication with Google Sign-In in Streamlit requires a custom component bridge because `st.components.v1.html()` returns `None` — it is display-only and cannot pass values back to Python. The correct approach is `st.components.v1.declare_component()` with a `path` pointing to a directory containing `index.html`. The HTML component uses raw `window.parent.postMessage()` with the Streamlit internal protocol (`isStreamlitMessage: true`, `type: "streamlit:setComponentValue"`) to return the Firebase ID token to Python without any build step or npm dependency.

The Firebase JS SDK 12.9.0 is available from gstatic.com CDN via `<script type="module">` and ES module imports. `onAuthStateChanged` with `browserLocalPersistence` handles transparent re-auth on page reload — the callback fires with the user object if localStorage has a valid session, or `null` if not. The component sends the token only after `onAuthStateChanged` resolves, eliminating the login-screen flash.

On the Python side, `firebase-admin 7.1.0` (already installed) provides `auth.verify_id_token(id_token)` which returns a decoded dict with `uid`, `email`, `name`, and other JWT claims. The `firebase_admin._apps` guard prevents `ValueError: The default Firebase app already exists` on Streamlit hot-reload. User auto-creation uses the `uid` from the decoded token to INSERT a `User` row if it doesn't exist, satisfying the FK constraint.

**Primary recommendation:** Build a zero-build-step custom component (`frontend/auth_component/index.html`) declared via `declare_component` that runs the Firebase JS SDK in an iframe, handles `onAuthStateChanged`, calls `signInWithPopup` on button click, and posts the ID token back via `window.parent.postMessage`. Python verifies, stores `user_id` in `st.session_state`, and gates all page content with `st.stop()`.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| firebase-admin | 7.1.0 (installed) | Server-side ID token verification | Only official server-side Firebase SDK for Python |
| Firebase JS SDK | 12.9.0 (CDN) | Google Sign-In popup + localStorage persistence | Official Firebase client SDK; loaded from gstatic.com |
| streamlit | 1.53.1 (installed) | App framework + `declare_component` bridge | Already in use |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sqlmodel | (installed) | User record auto-creation in PostgreSQL | Already in use; `User` model already defined |
| pydantic-settings | (installed) | `FIREBASE_CREDENTIALS_PATH` config | Already in use via `app/config.py` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom component via `declare_component` | Streamlit native OIDC `st.login()` | `st.login()` available in Streamlit 1.42+ and would eliminate the component bridge entirely — but it uses Google OAuth directly, not Firebase Auth. Firebase UID would not be the identity, breaking the DB schema. Avoid unless the DB schema is changed. |
| Firebase JS SDK CDN | npm/bundled JS | CDN requires no build step; bundled requires webpack/vite. CDN is simpler for this use case. |
| `signInWithPopup` | `signInWithRedirect` | Redirect approach has CSRF issues in Streamlit iframe context. Use popup only. |
| File-path credentials | Dict credentials | Dict allows storing JSON in env variable (better for Docker/Cloud Run). Both work with `credentials.Certificate`. |

**Installation:** No new packages needed — `firebase-admin` is already in `pyproject.toml`. Firebase JS SDK loaded from CDN.

---

## Architecture Patterns

### Recommended File Structure
```
frontend/
├── auth_component/
│   └── index.html          # Single-file custom component (Firebase JS SDK + postMessage bridge)
├── pages/
│   └── ...                 # Existing pages unchanged
└── main.py                 # Auth gate added here; TEST_USER_ID removed

app/
├── services/
│   ├── auth_service.py     # NEW: Firebase Admin init + verify_id_token + user auto-create
│   └── ...                 # Existing services unchanged
└── config.py               # Add FIREBASE_API_KEY + credentials settings
```

### Pattern 1: Zero-Build-Step Custom Component (Token Bridge)

**What:** A plain HTML file served via `declare_component` that hosts the Firebase JS SDK, handles auth state, and posts the ID token back to Python.

**When to use:** Whenever you need to run JavaScript that returns a value to Streamlit Python without a React/npm build step.

**How `declare_component` works:**
1. Python calls `declare_component("firebase_auth", path="/abs/path/to/auth_component")` once at module level.
2. Streamlit serves `index.html` from that directory inside an iframe.
3. JavaScript calls `window.parent.postMessage({isStreamlitMessage: true, type: "streamlit:setComponentValue", ...}, "*")` to return a value.
4. The Python invocation of the component function returns that value on the next script rerun.

**index.html skeleton (verified pattern):**
```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
<script type="module">
  import { initializeApp } from 'https://www.gstatic.com/firebasejs/12.9.0/firebase-app.js';
  import {
    getAuth,
    GoogleAuthProvider,
    signInWithPopup,
    onAuthStateChanged,
    browserLocalPersistence,
    setPersistence,
  } from 'https://www.gstatic.com/firebasejs/12.9.0/firebase-auth.js';

  // Streamlit postMessage protocol (no npm required)
  function sendToStreamlit(value) {
    window.parent.postMessage({
      isStreamlitMessage: true,
      type: "streamlit:setComponentValue",
      value: value,
      dataType: "json",
    }, "*");
  }

  function sendReady() {
    window.parent.postMessage({
      isStreamlitMessage: true,
      type: "streamlit:componentReady",
      apiVersion: 1,
    }, "*");
  }

  // Receive firebaseConfig from Python via streamlit:render event
  window.addEventListener("message", async (event) => {
    if (!event.data.isStreamlitMessage) return;
    if (event.data.type !== "streamlit:render") return;

    const { firebase_config } = event.data.args;
    const app = initializeApp(firebase_config);
    const auth = getAuth(app);

    await setPersistence(auth, browserLocalPersistence);

    onAuthStateChanged(auth, async (user) => {
      if (user) {
        const idToken = await user.getIdToken();
        sendToStreamlit({ status: "authenticated", id_token: idToken });
      } else {
        // No active session — show login UI
        sendToStreamlit({ status: "unauthenticated" });
      }
    });

    // Sign-in button handler (rendered in this iframe)
    document.getElementById("sign-in-btn").onclick = async () => {
      try {
        const provider = new GoogleAuthProvider();
        const result = await signInWithPopup(auth, provider);
        const idToken = await result.user.getIdToken();
        sendToStreamlit({ status: "authenticated", id_token: idToken });
      } catch (err) {
        sendToStreamlit({ status: "error", message: err.message });
      }
    };
  });

  sendReady();
</script>
<!-- Login UI shown only when unauthenticated -->
<button id="sign-in-btn">Sign in with Google</button>
</body>
</html>
```

**Python side:**
```python
# Source: st.components.v1.declare_component docs + community pattern
import os
import streamlit.components.v1 as components

_AUTH_COMPONENT_DIR = os.path.join(os.path.dirname(__file__), "auth_component")
_auth_component = components.declare_component("firebase_auth", path=_AUTH_COMPONENT_DIR)

def firebase_auth_component(firebase_config: dict) -> dict | None:
    """Returns dict with status/id_token or None on first render."""
    return _auth_component(firebase_config=firebase_config, default=None)
```

### Pattern 2: Firebase Admin SDK Initialization Guard

**What:** Initialize Firebase Admin once, guard against hot-reload re-initialization.

**Why:** Streamlit re-runs the Python script on every interaction. `firebase_admin.initialize_app()` raises `ValueError: The default Firebase app already exists` if called twice.

```python
# Source: firebase-admin Python SDK + community pattern confirmed by pyproject inspection
import firebase_admin
from firebase_admin import auth, credentials

def initialize_firebase(credentials_path: str | None, credentials_dict: dict | None = None) -> None:
    """Initialize Firebase Admin SDK with guard against hot-reload."""
    if firebase_admin._apps:  # dict; empty dict is falsy
        return
    if credentials_dict:
        cred = credentials.Certificate(credentials_dict)
    elif credentials_path:
        cred = credentials.Certificate(credentials_path)
    else:
        raise ValueError("No Firebase credentials provided")
    firebase_admin.initialize_app(cred)
```

### Pattern 3: Token Verification + User Auto-Create

**What:** Verify Firebase ID token server-side, extract uid/email/name, create DB user if first login.

```python
# Source: firebase-admin Python SDK (verified via local inspection)
from firebase_admin import auth
from firebase_admin.auth import (
    ExpiredIdTokenError,
    InvalidIdTokenError,
    UserNotFoundError,
)
from sqlmodel import Session, select
from app.models import User

def verify_and_get_or_create_user(id_token: str, session: Session) -> User:
    """
    Verify Firebase ID token. Auto-create User row on first login.
    Returns the User record.
    Raises InvalidIdTokenError or ExpiredIdTokenError on bad token.
    """
    decoded = auth.verify_id_token(id_token)
    # decoded dict keys: "uid", "email", "name" (display name), "iat", "exp", etc.
    uid: str = decoded["uid"]
    email: str = decoded.get("email", "")
    display_name: str = decoded.get("name", "")

    user = session.exec(select(User).where(User.id == uid)).first()
    if user is None:
        user = User(id=uid, email=email, display_name=display_name)
        session.add(user)
        session.commit()
        session.refresh(user)
    return user
```

### Pattern 4: Auth Gate in main.py

**What:** Wrap all page rendering behind an auth check using `st.stop()`.

```python
# Pattern: check session_state, render auth component if not logged in, call st.stop()
def _auth_gate() -> None:
    """Block page render if not authenticated. Call before sidebar/page content."""
    if st.session_state.get("user_id"):
        return  # Already authenticated in this session

    # Hide sidebar while unauthenticated
    st.markdown(
        "<style>[data-testid='stSidebar'] { display: none !important; }</style>",
        unsafe_allow_html=True,
    )

    firebase_config = _get_firebase_config()
    result = firebase_auth_component(firebase_config=firebase_config)

    if result is None:
        # Component not yet rendered (first frame) — show spinner
        st.spinner("Loading...")
        st.stop()

    if result["status"] == "unauthenticated":
        _render_login_page()
        st.stop()

    if result["status"] == "error":
        st.error(f"Sign-in failed: {result['message']}")
        _render_login_page()
        st.stop()

    if result["status"] == "authenticated":
        id_token = result["id_token"]
        with next(get_session()) as session:
            user = verify_and_get_or_create_user(id_token, session)
        st.session_state["user_id"] = user.id
        st.session_state["user_name"] = user.display_name
        st.session_state["selected_page"] = "Dashboard"
        st.rerun()
```

### Anti-Patterns to Avoid

- **Using `st.components.v1.html()` for the token bridge:** Returns `None` always. Has no mechanism for sending values back to Python. Do not use it for auth.
- **Calling `firebase_admin.initialize_app()` without the `_apps` guard:** Causes `ValueError` on every hot-reload. Always guard with `if not firebase_admin._apps:`.
- **Storing the raw ID token in session_state long-term:** ID tokens expire in 1 hour. Store only `user_id` (uid) and `user_name` in session_state. Re-auth happens transparently via `onAuthStateChanged` + localStorage.
- **`signInWithRedirect` instead of `signInWithPopup`:** Redirect-based auth has CSRF issues when Streamlit and the auth iframe are on different origins.
- **Building a REST API layer:** Not needed. Auth service functions are called directly from main.py and pages, consistent with the no-REST-API architecture decision.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Google OAuth popup | Custom OAuth flow | Firebase JS SDK `signInWithPopup` + `GoogleAuthProvider` | OAuth PKCE, CSRF tokens, nonce handling — dozens of edge cases |
| JWT verification | Custom JWT decode + signature check | `firebase_admin.auth.verify_id_token()` | Certificate rotation, clock skew, revocation checks |
| localStorage session persistence | Manual cookie/storage code | Firebase JS SDK `browserLocalPersistence` + `onAuthStateChanged` | Token refresh, expiry, multi-tab coordination |
| Streamlit component messaging protocol | Custom postMessage format | The documented `isStreamlitMessage` + `streamlit:setComponentValue` format | Streamlit validates the message format; wrong format is silently ignored |

**Key insight:** Firebase handles the hardest parts — OAuth flow, token signing, refresh, and revocation. The only custom code needed is the thin bridge between the Firebase JS callback and Streamlit's session state.

---

## Common Pitfalls

### Pitfall 1: Firebase Admin Re-Initialization on Hot-Reload
**What goes wrong:** `ValueError: The default Firebase app already exists` crashes the app on every file save.
**Why it happens:** Streamlit hot-reload re-executes the module. `initialize_app()` is called again.
**How to avoid:** Guard with `if not firebase_admin._apps: firebase_admin.initialize_app(cred)`. `firebase_admin._apps` is a dict; empty means no apps initialized.
**Warning signs:** `ValueError` in terminal immediately after saving a Python file.

### Pitfall 2: Login Screen Flash Before onAuthStateChanged Resolves
**What goes wrong:** User sees the login screen for 200-500ms on page reload, even when they have a valid localStorage session.
**Why it happens:** The component renders, immediately sends `status: "unauthenticated"`, then `onAuthStateChanged` fires ~200ms later.
**How to avoid:** Add an `"initializing"` state. The component sends `status: "initializing"` on first load, then the real status after `onAuthStateChanged` fires. Python treats `"initializing"` as "show spinner, call `st.stop()`".
**Warning signs:** Users report being bounced to login and back to dashboard on every refresh.

### Pitfall 3: Component Returns None on First Render
**What goes wrong:** `firebase_auth_component()` returns `None` on the very first script run (before the frontend sends any message).
**Why it happens:** Streamlit's `declare_component` returns the `default` value until the frontend calls `setComponentValue`. This is expected behavior.
**How to avoid:** Always pass `default=None` and handle `None` as the "loading" state (show spinner, call `st.stop()`).
**Warning signs:** `TypeError: 'NoneType' object is not subscriptable` when accessing `result["status"]`.

### Pitfall 4: `signInWithPopup` Blocked by Browser
**What goes wrong:** The browser blocks the popup because it wasn't triggered by a direct user gesture.
**Why it happens:** Some browsers enforce that popups must be opened in response to a click event. If the popup is triggered programmatically (e.g., in `onAuthStateChanged`), it may be blocked.
**How to avoid:** Only call `signInWithPopup` in a click event handler, never automatically. Show the button and let the user click.
**Warning signs:** Browser console shows `auth/popup-blocked` error.

### Pitfall 5: Sidebar Visible Before Auth Check Completes
**What goes wrong:** The sidebar with navigation briefly appears for unauthenticated users.
**Why it happens:** Streamlit renders `st.set_page_config` and sidebar initialization before any Python logic runs. There is no way to prevent this 100%.
**How to avoid:** Use CSS `[data-testid="stSidebar"] { display: none !important; }` injected in `st.markdown()` before calling `st.stop()`. This hides it within ~1 frame. Accept the brief flash is not fully eliminable.
**Warning signs:** Navigation links visible for <100ms on unauthenticated load.

### Pitfall 6: Expired ID Token Not Refreshed
**What goes wrong:** `auth.verify_id_token()` raises `ExpiredIdTokenError` for a user who is still "logged in" in the browser.
**Why it happens:** Firebase ID tokens expire after 1 hour. If the component cached the token from 2 hours ago and the user navigates between pages, the old token is reused.
**How to avoid:** The component should call `user.getIdToken()` (without `forceRefresh`) on each `onAuthStateChanged` call or page render. Firebase JS SDK automatically refreshes tokens in the background. Calling `getIdToken()` returns a valid (possibly freshly refreshed) token. Do not cache the raw token string in `st.session_state`.
**Warning signs:** `ExpiredIdTokenError` in server logs when user has been in the app for >1 hour.

### Pitfall 7: Data Migration Needed for Existing Test Data
**What goes wrong:** After deploying Firebase auth, all existing accounts/liabilities/snapshots with `user_id = 'test-user'` are orphaned — the FK constraint is satisfied for the test user but not the real Firebase user.
**Why it happens:** Phase 3 used hardcoded `TEST_USER_ID = "test-user"`. The real Firebase UID will be different.
**How to avoid:** Write a migration script (required in Phase 5 before production deployment) that updates all rows: `UPDATE accounts SET user_id = '<real_uid>' WHERE user_id = 'test-user'` (also liabilities, snapshots, account_types, liability_types).
**Warning signs:** Dashboard shows empty data after first login even though data was entered during development.

---

## Code Examples

### Firebase Admin: verify_id_token return structure
```python
# Source: firebase-admin 7.1.0 local inspection + Firebase JWT spec
decoded = auth.verify_id_token(id_token)
# decoded is a dict with these relevant keys:
# {
#   "uid": "abc123",           # Firebase UID — use as users.id PK
#   "email": "user@ex.com",    # User's email
#   "name": "John Doe",        # Display name (from Google profile)
#   "picture": "https://...",  # Profile photo URL (optional)
#   "iat": 1700000000,         # Issued at (unix timestamp)
#   "exp": 1700003600,         # Expires at (1 hour after iat)
#   "firebase": {              # Firebase-specific claims
#     "identities": {...},
#     "sign_in_provider": "google.com"
#   }
# }
uid = decoded["uid"]  # Always present
email = decoded.get("email", "")  # Present for Google Sign-In
display_name = decoded.get("name", "")  # Present for Google Sign-In
```

### Firebase Admin: Initialize with guard
```python
# Source: firebase-admin docs + local module inspection confirming _apps is a dict
import firebase_admin
from firebase_admin import credentials

def initialize_firebase() -> None:
    if not firebase_admin._apps:  # empty dict = not initialized
        cred_path = settings.firebase_credentials_path
        if cred_path:
            cred = credentials.Certificate(cred_path)
        else:
            # Alternative: JSON stored in env var
            import json, os
            cred_dict = json.loads(os.environ["FIREBASE_CREDENTIALS_JSON"])
            cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
```

### Firebase Admin: Error handling
```python
# Source: firebase-admin 7.1.0 local inspection
from firebase_admin.auth import ExpiredIdTokenError, InvalidIdTokenError

try:
    decoded = auth.verify_id_token(id_token)
except ExpiredIdTokenError:
    # Token expired — clear session, show login
    st.session_state.clear()
    st.rerun()
except InvalidIdTokenError:
    # Bad token — clear session, show login
    st.session_state.clear()
    st.rerun()
```

### User Auto-Create Pattern
```python
# Source: SQLModel docs + firebase-admin local inspection
from sqlmodel import Session, select
from app.models import User

def get_or_create_user(session: Session, uid: str, email: str, display_name: str) -> User:
    user = session.exec(select(User).where(User.id == uid)).first()
    if user is None:
        user = User(id=uid, email=email, display_name=display_name)
        session.add(user)
        session.commit()
        session.refresh(user)
    return user
```

### Streamlit postMessage Protocol (no-build component)
```javascript
// Source: Streamlit community pattern confirmed working (discuss.streamlit.io/t/13064)
// Must be called after DOM is ready

function sendToStreamlit(value) {
  window.parent.postMessage({
    isStreamlitMessage: true,
    type: "streamlit:setComponentValue",
    value: value,
    dataType: "json",
  }, "*");
}

function signalReady() {
  window.parent.postMessage({
    isStreamlitMessage: true,
    type: "streamlit:componentReady",
    apiVersion: 1,
  }, "*");
}

// Receive config from Python
window.addEventListener("message", (event) => {
  if (event.data?.isStreamlitMessage && event.data?.type === "streamlit:render") {
    const args = event.data.args;  // args passed from Python invocation
    // e.g., args.firebase_config
  }
});
```

### Data Migration Script (write in Phase 4, execute in Phase 5)
```sql
-- Execute AFTER Firebase auth is deployed and you know your real UID
BEGIN;
UPDATE account_types SET user_id = '<YOUR_FIREBASE_UID>' WHERE user_id = 'test-user';
UPDATE accounts SET user_id = '<YOUR_FIREBASE_UID>' WHERE user_id = 'test-user';
UPDATE liabilities SET user_id = '<YOUR_FIREBASE_UID>' WHERE user_id = 'test-user';
UPDATE snapshots SET user_id = '<YOUR_FIREBASE_UID>' WHERE user_id = 'test-user';
DELETE FROM users WHERE id = 'test-user';
COMMIT;
```

### Sidebar Hide CSS (unauthenticated state)
```python
# Source: Streamlit community (CSS selector confirmed via browser devtools)
# Note: Brief flash is unavoidable — Streamlit renders sidebar before Python logic runs
st.markdown(
    "<style>[data-testid='stSidebar'] { display: none !important; }</style>",
    unsafe_allow_html=True,
)
st.set_page_config(initial_sidebar_state="collapsed")  # Set in page_config, not dynamically
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `st.components.v1.html()` for token bridge | `declare_component` with `path` | Always — `html()` never supported return values | Must use `declare_component` for any JS→Python data flow |
| Email/password Firebase auth via REST API | Google Sign-In via Firebase JS SDK | Google Sign-In requires browser JS | REST API does not support OAuth popup flows |
| Custom JWT verification | `firebase_admin.auth.verify_id_token()` | Firebase Admin SDK v1+ | Never build custom JWT verification |
| npm/webpack build for components | Zero-build `window.parent.postMessage` protocol | Community documented 2021 | Simple auth components need no build toolchain |

**Relevant to this project: Streamlit 1.42+ native OIDC `st.login()`**

Streamlit 1.53.1 (installed) includes `st.login()` / `st.user` / `st.logout()` — a native OIDC flow that works with Google directly. This would be much simpler than the custom component approach. However, it authenticates via Google OAuth directly, not via Firebase. The UID returned would be a Google OIDC `sub` claim, not a Firebase UID. Since the DB schema uses Firebase UID as the PK and the project has `firebase-admin` already installed, switching to native OIDC would require abandoning Firebase Admin SDK entirely and changing the users table. This is outside the locked decision scope but worth noting for future phases.

**Deprecated/outdated:**
- `signInWithRedirect`: Has CSRF issues in iframes; use `signInWithPopup` only
- `firebase/compat` CDN modules (e.g., `firebase-app-compat.js`): Legacy API; use modular SDK
- `st.components.v1.html()` return value: Never worked; community confirmed returns `None` always

---

## Open Questions

1. **Firebase config exposure in frontend**
   - What we know: The Firebase "web config" (API key, project ID, etc.) is safe to expose client-side — it identifies the project, not grants admin access. Firebase security rules protect data.
   - What's unclear: Whether the project already has a Firebase web app configured with the web config values (apiKey, authDomain, projectId, etc.)
   - Recommendation: Add `FIREBASE_WEB_API_KEY`, `FIREBASE_AUTH_DOMAIN`, `FIREBASE_PROJECT_ID` to `app/config.py` and `.env.example`. Pass them from Python to the component as `firebase_config` dict.

2. **Component iframe height for login page**
   - What we know: The auth component lives in an iframe. When unauthenticated, it needs to display the full-page login UI including the Google Sign-In button.
   - What's unclear: The exact approach to make the component appear full-screen. `declare_component` accepts `height` parameter in the Python invocation.
   - Recommendation: When unauthenticated, pass `height=600` and render the full login UI inside the component iframe. When authenticated (or initializing), use `height=0` to hide the component.

3. **onAuthStateChanged timing — initializing state handling**
   - What we know: `onAuthStateChanged` fires asynchronously after the component renders. The first render, the component should send `status: "initializing"` immediately and the real status ~100-500ms later.
   - What's unclear: Whether one additional Streamlit rerun cycle causes a visible flash in the specific Streamlit 1.53.1 rendering pipeline.
   - Recommendation: Use `status: "initializing"` with a spinner in Python; do not show login screen until `"unauthenticated"` is explicitly received.

---

## Sources

### Primary (HIGH confidence)
- Firebase JS SDK 12.9.0 CDN — verified file exists at `https://www.gstatic.com/firebasejs/12.9.0/firebase-app.js`
- firebase-admin 7.1.0 local inspection — `auth.verify_id_token` docstring, `_apps` dict guard, `credentials.Certificate` dict support, `auth.get_user`, `auth.create_user`
- `st.components.v1.declare_component` official docs — `path` parameter, return value semantics
- `st.components.v1.html` official docs — confirmed returns `None` (display-only)
- Streamlit community thread #13064 — zero-build `window.parent.postMessage` protocol with exact message format

### Secondary (MEDIUM confidence)
- Firebase JS SDK release notes (12.9.0 confirmed current as of 2026-02-18) — `browserLocalPersistence`, `onAuthStateChanged`, `signInWithPopup`
- firebase-admin Python release notes — v7.1.0 API stability, `clock_skew_seconds` parameter in `verify_id_token`
- `munaita-0/streamlit-firebase-auth` source — confirms `declare_component` + `path` pattern returns Firebase auth result dict to Python

### Tertiary (LOW confidence)
- Sidebar CSS hide approach — community reports brief flash is unavoidable; `display: none !important` reduces but doesn't eliminate it

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — firebase-admin installed, version confirmed; Firebase JS SDK CDN URL verified
- Token bridge architecture: HIGH — `declare_component` vs `html()` confirmed by official docs; postMessage format confirmed by community pattern
- Firebase Admin API: HIGH — verified locally via Python introspection
- Sidebar CSS hiding: LOW — community reports it's not fully reliable

**Research date:** 2026-02-18
**Valid until:** 2026-03-18 (Firebase JS SDK patch versions release frequently; verify latest before pinning)
