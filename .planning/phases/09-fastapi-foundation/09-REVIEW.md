---
phase: "09"
status: clean
depth: standard
files_reviewed: 11
findings:
  critical: 0
  warning: 2
  info: 2
  total: 4
---

# Code Review — Phase 09: FastAPI Foundation

## Summary

11 files reviewed at standard depth. No critical issues. 2 warnings (non-blocking), 2 informational notes.

---

## Findings

### WR-01 — Test route mutation leaks between tests

**File:** `tests/test_api_auth.py`
**Severity:** warning

Each auth test adds a new route to the shared `app` instance via `@app.get("/api/test-protected")`. Because FastAPI's `app` is a module-level singleton, these routes accumulate across test runs. The fourth definition of `/api/test-protected` causes Starlette to silently shadow earlier ones. No test currently fails because the routes happen to use distinct handler names, but running tests in a different order could produce unexpected 422 errors.

**Fix:** Use `app.router.routes` cleanup or create a test-local `FastAPI()` app for auth tests, or use `APIRouter` and mount/unmount per test.

---

### WR-02 — `allow_headers` list excludes `Content-Language` and `Accept-Language`

**File:** `api/main.py`
**Severity:** warning

The CORS config specifies:
```python
allow_headers=["Authorization", "Content-Type", "Accept"],
```
The live server's `OPTIONS` response included `access-control-allow-headers: Accept, Accept-Language, Authorization, Content-Language, Content-Type` — that broader list comes from Starlette's defaults being merged in. This discrepancy means the Python config and the actual runtime behaviour differ. If CORSMiddleware behaviour changes across Starlette versions, `Accept-Language` / `Content-Language` may stop being allowed. Either align the `allow_headers` list with what's actually needed, or use `allow_headers=["*"]` for simplicity (safe since credentials are bearer tokens, not cookies).

---

### INFO-01 — `test_firebase_not_init_at_import` has ordering assumption

**File:** `tests/test_api_health.py`
**Severity:** info

The test asserts Firebase is not initialised *before* importing `api.main`, relying on the prior test (`test_health_returns_200`) having used `DEV_USER_ID` to suppress Firebase init. If test ordering changes (e.g., `pytest -k test_firebase_not_init_at_import` in isolation), the assertion may fail because a previous test session left Firebase initialised. Not currently a problem; flagged for awareness.

---

### INFO-02 — `lifespan` does not handle `initialize_app` idempotency on hot-reload

**File:** `api/main.py`
**Severity:** info

With `--reload` enabled in docker-compose, uvicorn restarts the process on file changes, which reinvokes the lifespan. The `firebase_admin.initialize_app()` call raises `ValueError: The default Firebase app already exists` if the previous process didn't shut down cleanly (rare but possible). The executor noted this was addressed with a `get_app()` try/except; confirm that guard covers the `initialize_app` call path, not just the check. Current code looks correct — this is a heads-up for the Cloud Run deployment phase.

---

## Verdict

**Clean** — no critical or blocking issues. WR-01 (test isolation) is the most actionable item if auth tests start behaving non-deterministically. WR-02 is a documentation alignment issue.
