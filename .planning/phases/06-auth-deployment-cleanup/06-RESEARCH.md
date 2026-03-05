# Phase 6: Auth & Deployment Cleanup - Research

**Researched:** 2026-03-05
**Domain:** Code cleanup, documentation repair, planning artifact remediation
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AUTH-04 | App shows login screen with no page content if user is not authenticated | Debug line identified at `frontend/main.py:82` — confirmed it was removed in current code (the line no longer exists at line 82); the unauthenticated sidebar-hide CSS is present and correct; the dead code at line 123 (`user_id` assignment) is the remaining cleanup item |
| DEPLOY-05 | Data migration script updates all `user_id = 'test-user'` rows to the real Firebase UID before production traffic | Script at `scripts/migrate_test_user.py` references `DELETE FROM users` (line 48) which targets a dropped table; Cloud SQL is confirmed empty per Phase 05-04 decision; script should be deleted entirely |
</phase_requirements>

---

## Summary

Phase 6 is a cleanup-only phase. No new features are built. All work consists of removing a debug statement, deleting a stale script, and updating planning documentation (REQUIREMENTS.md checkboxes, SUMMARY.md frontmatter fields, and a docstring). The codebase changes are minimal — surgical removals and text edits.

The audit identified six categories of gaps. Two are requirement-level blockers (AUTH-04 debug output, DEPLOY-05 stale script). Four are documentation tracking issues (REQUIREMENTS.md unchecked boxes, missing `requirements-completed` frontmatter in three SUMMARY.md files, misleading docstring). All gaps have exact file+line locations already identified.

**Primary recommendation:** Execute all six cleanup items in a single plan. Group by type: code changes first, then documentation updates. No research into third-party libraries is needed — this phase is entirely internal to the codebase.

---

## Code Reality (What the Audit Found vs. Current State)

The audit was run on 2026-03-05 and the code has been read as of the same date. Cross-referencing audit claims against current file contents:

### AUTH-04: Debug output on login screen

**Audit claim:** `frontend/main.py:82` contains `st.sidebar.write('DEBUG - Status: unauthenticated')`

**Current reality (from reading `frontend/main.py`):** Line 82 is `st.stop()` inside the `if result is None:` block. The `st.sidebar.write("DEBUG - Status: unauthenticated")` line does NOT appear in the current file. The unauthenticated path at lines 87-100 shows the correct CSS sidebar-hide and `st.stop()` pattern — no debug output.

**Conclusion:** AUTH-04 code fix may already be done (the debug line is absent). However, the audit formally scored it as "unsatisfied". The task is to verify this is clean, remove the dead code at line 123 (local variable `user_id` assigned from `get_or_create_user()` but never read — `session_state` is set from `uid` directly at line 131), and confirm the login screen behavior matches the requirement.

**Dead code at line 122-123:**
```python
user_id = get_or_create_user(session, uid, email, name)  # assigned but never read
```
`user_id` is assigned but `st.session_state["user_id"] = uid` is set from the token-decoded `uid` directly on line 131. The local variable can be removed; only the `get_or_create_user(...)` call for its side-effect (validation + blocking test-user) needs to be preserved — or the call can be inlined.

### DEPLOY-05: Stale migration script

**Audit claim:** `scripts/migrate_test_user.py:48` runs `DELETE FROM users WHERE id = 'test-user'` against a dropped table.

**Current reality (from reading the script):** Confirmed. Line 48 is `("users", "DELETE FROM users WHERE id = 'test-user'")`. The `users` table was removed in Phase 05-04. The Cloud SQL database is empty. The script is a no-op at best and crashes at worst.

**Conclusion:** Delete `scripts/migrate_test_user.py` entirely. The Phase 05-04 decision was "no migration needed — Cloud SQL is empty". The script has no remaining purpose.

### auth_service.py docstring accuracy

**Current reality:** The `get_or_create_user` function already has a docstring that says "Validate user ID and return it" (not "Get or create user"). The parameters `session`, `email`, `display_name` are documented as "unused, kept for compatibility". The function body is correct (blocks test-user, logs, returns uid).

**Conclusion:** The docstring is already accurate about what the function does. The misleading part is the function *name* (`get_or_create_user`) which implies DB writes. The audit lists this as "Low" severity. The success criterion says to update the docstring to reflect that it "validates (not creates) the user" — the current docstring already does this. Minor wording confirmation/tweak only.

### REQUIREMENTS.md checkboxes

**Current state:** AUTH-01–AUTH-06 checkboxes are all `[ ]` (unchecked) in REQUIREMENTS.md, and traceability statuses for AUTH-01, AUTH-03, AUTH-05, AUTH-06 say "Complete" while AUTH-04 says "Pending". DEPLOY-05 traceability says "Pending".

**Required changes:**
- AUTH-04: `[ ]` → `[x]` (once code fix confirmed)
- AUTH-01, AUTH-02, AUTH-03, AUTH-05, AUTH-06: `[ ]` → `[x]`
- DEPLOY-05: `[ ]` → `[x]` (already has `[x]` in REQUIREMENTS.md per audit — verify)
- Traceability: AUTH-04 status "Pending" → "Complete"; DEPLOY-05 status "Pending" → "Complete"

**Note from reading REQUIREMENTS.md:** DEPLOY-05 already has `[x]` at line 25 ("- [x] **DEPLOY-05**"). Traceability table at line 62 shows `DEPLOY-05 | Phase 6 | Pending`. So the checkbox is already checked but the traceability row status needs updating to "Complete".

### SUMMARY.md frontmatter gaps

Three files need frontmatter additions/fixes:

**04-01-SUMMARY.md:** Missing `requirements-completed` field entirely. Requirements covered by this plan per the phase: AUTH-01 (Google Sign-In component), AUTH-06 (get_or_create_user foundation). Add:
```yaml
requirements-completed: [AUTH-01, AUTH-06]
```

**04-02-SUMMARY.md:** Missing `requirements-completed` field entirely. Requirements covered: AUTH-02 (token verification in auth gate), AUTH-03 (session persistence), AUTH-04 (login screen gate), AUTH-05 (logout flow). Add:
```yaml
requirements-completed: [AUTH-02, AUTH-03, AUTH-04, AUTH-05]
```

**05-01-SUMMARY.md:** Has `requirements: [DEPLOY-02]` (non-standard key). Change to:
```yaml
requirements-completed: [DEPLOY-02]
```

---

## Standard Stack

No new libraries. This phase uses only what is already in the project.

| Tool | Purpose | Already Present |
|------|---------|----------------|
| Python (standard) | File deletion, code edits | Yes |
| pytest | Test verification | Yes (`pytest tests/`) |
| ruff | Lint check after edits | Yes (used throughout) |

**Installation:** None needed.

---

## Architecture Patterns

### Pattern 1: Surgical Code Removal

This phase removes specific lines/variables — not whole functions. Pattern: identify exact line(s), verify removal doesn't break callers, delete only the dead/debug code.

For the `user_id` dead variable in `main.py`:
- The `get_or_create_user()` call must be kept for its side effect (validates UID, raises ValueError on test-user)
- The return value assignment `user_id = ...` can be removed — just call the function without capturing the return
- The session/try/finally block structure must be preserved

**Before:**
```python
session = next(get_session())
try:
    user_id = get_or_create_user(session, uid, email, name)
except ValueError as e:
    st.error(f"Authentication error: {e}")
    st.stop()
finally:
    session.close()
```

**After:**
```python
session = next(get_session())
try:
    get_or_create_user(session, uid, email, name)
except ValueError as e:
    st.error(f"Authentication error: {e}")
    st.stop()
finally:
    session.close()
```

### Pattern 2: YAML Frontmatter Addition

SUMMARY.md files use YAML frontmatter (between `---` delimiters). Adding `requirements-completed` is a simple field insertion into the existing block. Must maintain valid YAML.

**Standard key name:** `requirements-completed` (hyphenated, not `requirements`)

**Correct format:**
```yaml
---
phase: 04-firebase-authentication
plan: 01
requirements-completed: [AUTH-01, AUTH-06]
...
---
```

### Pattern 3: Documentation Traceability Update

REQUIREMENTS.md uses two tracking mechanisms:
1. Checkboxes in requirement definitions: `- [ ]` vs `- [x]`
2. Traceability table rows: `| AUTH-04 | Phase 6 | Pending |` → `| AUTH-04 | Phase 6 | Complete |`

Both must be updated together for a requirement to be considered fully tracked.

### Anti-Patterns to Avoid

- **Do not rename `get_or_create_user`:** Other callers may reference it; a rename would require import updates. The docstring fix is sufficient per success criteria.
- **Do not add migration logic:** The `scripts/` directory cleanup is delete-only. Do not add a README or replacement script — the decision was "no migration needed".
- **Do not add new requirements:** Phase 6 closes existing gaps only.

---

## Don't Hand-Roll

This phase has no algorithmic complexity. All work is text editing.

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Confirming debug line removed | Custom test | Manual file read + grep |
| YAML frontmatter parsing | Custom parser | Direct text edit (simple format) |
| Requirements tracking | Custom tool | Direct REQUIREMENTS.md edit |

---

## Common Pitfalls

### Pitfall 1: Assuming the audit line numbers are still accurate

**What goes wrong:** The audit was generated at a point in time. File edits since then may have shifted line numbers. Do not use line numbers from the audit as authoritative — read the current file first.

**How to avoid:** Read each file before editing. Confirmed above: the debug `st.sidebar.write` line does NOT appear in the current `main.py`. The dead code is at lines 121-123 (session + `user_id = get_or_create_user(...)`).

**Warning signs:** If you search for the exact audit-cited content and find nothing, this pitfall has occurred.

### Pitfall 2: Removing the get_or_create_user call entirely

**What goes wrong:** `get_or_create_user` validates that `uid != 'test-user'` and raises `ValueError`. If the call is removed along with the dead variable, the production guard is lost.

**How to avoid:** Remove only the `user_id =` assignment. Keep the function call. Keep the `except ValueError` handler.

### Pitfall 3: Wrong frontmatter key name

**What goes wrong:** Using `requirements` instead of `requirements-completed` (as `05-01-SUMMARY.md` did). The audit tool reads `requirements-completed` specifically.

**How to avoid:** Always use `requirements-completed` (with hyphen). Verify by searching existing correct SUMMARY.md files (e.g., `05-02-SUMMARY.md` has `requirements-completed: [DEPLOY-01, DEPLOY-03]`).

### Pitfall 4: Marking DEPLOY-04 as Complete prematurely

**What goes wrong:** DEPLOY-04 ("App deployed to Cloud Run, accessible via HTTPS, with working Sign-In") has an open human verification gate (05-03 Task 3 "awaiting human verification"). The audit marks DEPLOY-04 as "partial" not "unsatisfied".

**How to avoid:** Phase 6 success criteria do NOT include DEPLOY-04. Do not check `[x]` for DEPLOY-04 in REQUIREMENTS.md unless the human verification has been explicitly completed.

### Pitfall 5: Not checking pytest after code changes

**What goes wrong:** Removing `user_id` variable in main.py could (theoretically) break something if tests reference it. Unlikely since it's a local variable inside `_auth_gate()`, but good practice.

**How to avoid:** Run `pytest tests/` after code changes. Expected: all existing tests continue to pass (they test service layer, not auth gate UI).

---

## Code Examples

### Verified: Current main.py authenticated path (lines 102-136)

```python
# Source: frontend/main.py (current, read 2026-03-05)
if result.get("status") == "authenticated":
    token = result.get("token")
    if not token:
        st.error("Authentication failed. Please try again.")
        st.stop()

    decoded = verify_firebase_token(token)
    if not decoded:
        st.error("Authentication failed. Please try again.")
        st.stop()

    uid = decoded["uid"]
    email = decoded.get("email", "")
    name = decoded.get("name", "")

    session = next(get_session())
    try:
        user_id = get_or_create_user(session, uid, email, name)  # dead variable — remove assignment
    except ValueError as e:
        st.error(f"Authentication error: {e}")
        st.stop()
    finally:
        session.close()

    st.session_state["user_id"] = uid  # set from uid, not user_id — confirms dead variable
    st.session_state["user_email"] = email
    st.session_state["user_name"] = name
    st.rerun()
```

### Verified: Current 05-02-SUMMARY.md correct frontmatter pattern

```yaml
# Source: .planning/phases/05-cloud-run-deployment/05-02-SUMMARY.md (for reference)
requirements-completed: [DEPLOY-01, DEPLOY-03]
```

This is the correct key name and format that 04-01, 04-02, and 05-01 SUMMARY.md files should follow.

---

## Exact Change List

The following table documents every file change needed. No ambiguity.

| # | File | Change Type | What Exactly |
|---|------|-------------|--------------|
| 1 | `frontend/main.py` | Remove line | Delete `user_id = ` from line 123 — keep the `get_or_create_user(session, uid, email, name)` call |
| 2 | `scripts/migrate_test_user.py` | Delete file | Entire file — no-op script referencing dropped `users` table |
| 3 | `REQUIREMENTS.md` | Edit | Check `[x]` for AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06; update AUTH-04 traceability from "Pending" to "Complete"; update DEPLOY-05 traceability from "Pending" to "Complete" |
| 4 | `app/services/auth_service.py` | Edit docstring | Confirm/update docstring of `get_or_create_user` to clearly state it validates only (already mostly correct — confirm wording matches success criterion) |
| 5 | `.planning/phases/04-firebase-authentication/04-01-SUMMARY.md` | Add frontmatter | Add `requirements-completed: [AUTH-01, AUTH-06]` field |
| 6 | `.planning/phases/04-firebase-authentication/04-02-SUMMARY.md` | Add frontmatter | Add `requirements-completed: [AUTH-02, AUTH-03, AUTH-04, AUTH-05]` field |
| 7 | `.planning/phases/05-cloud-run-deployment/05-01-SUMMARY.md` | Fix frontmatter | Change `requirements: [DEPLOY-02]` to `requirements-completed: [DEPLOY-02]` |

---

## State of the Art

| Old Approach | Current Approach | Phase Changed | Impact |
|--------------|------------------|---------------|--------|
| users table FK constraint | No users table; Firebase UID stored directly as string | Phase 05-04 | `get_or_create_user` no longer inserts rows — validation only |
| Hardcoded TEST_USER_ID | Real Firebase auth gate | Phase 04-02 | migration script obsolete |
| Debug `st.sidebar.write` in auth gate | CSS sidebar-hide only | Already done (not in current code) | AUTH-04 may be satisfied in code already |

---

## Open Questions

1. **Is AUTH-04 already fixed in code?**
   - What we know: The `st.sidebar.write("DEBUG - Status: unauthenticated")` line is absent from current `frontend/main.py`. The audit found it, but the audit predates any subsequent edits.
   - What's unclear: When was the line removed? Was it removed intentionally during Phase 05 work or after the audit?
   - Recommendation: Treat AUTH-04 as needing confirmation. The dead code (`user_id = ...`) is definitely present and must be removed. After removing it and verifying sidebar behavior, mark AUTH-04 complete.

2. **Which requirements does 04-01 vs 04-02 own for SUMMARY frontmatter?**
   - What we know: The audit says "04-01 and 04-02 SUMMARY.md files do not include requirements-completed frontmatter". The phase covered AUTH-01–AUTH-06.
   - What's unclear: How to split them between the two plans.
   - Recommendation: Based on what each plan built — 04-01 built the component (AUTH-01: Google Sign-In) and the `get_or_create_user` foundation (AUTH-06); 04-02 wired the auth gate (AUTH-02: server verify, AUTH-03: session, AUTH-04: login screen gate, AUTH-05: logout).

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | none (auto-discovery) |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUTH-04 | Login screen shows no content to unauthenticated user (no debug output) | manual-only | N/A — auth gate requires browser + Firebase component | N/A |
| DEPLOY-05 | Migration script deleted / no stale artifact | smoke | `python -c "import os; assert not os.path.exists('scripts/migrate_test_user.py'), 'stale script exists'"` | ❌ Wave 0 — inline check |

**AUTH-04 manual-only justification:** The auth gate behavior (`st.stop()`, sidebar CSS hide) is enforced in `frontend/main.py`'s `_auth_gate()` function which calls Streamlit APIs. Unit-testing Streamlit components requires a running Streamlit server + browser — not feasible as an automated pytest assertion. Code review of the file (no `st.sidebar.write` debug calls in the unauthenticated path) is the appropriate verification mechanism.

**Documentation changes (items 3-7):** No automated test possible. Verification is by reading the files.

### Sampling Rate

- **Per task commit:** `pytest tests/ -x -q` (confirm service tests unaffected)
- **Per wave merge:** `pytest tests/`
- **Phase gate:** Full suite green + manual check of login screen before `/gsd:verify-work`

### Wave 0 Gaps

None — existing test infrastructure covers all automated phase requirements. The pytest suite (`tests/`) exists and runs against the service layer. No new test files are needed for this cleanup phase.

---

## Sources

### Primary (HIGH confidence)

- `frontend/main.py` — read directly; confirmed current state of auth gate and dead code
- `app/services/auth_service.py` — read directly; confirmed docstring accuracy
- `scripts/migrate_test_user.py` — read directly; confirmed stale `DELETE FROM users` on line 48
- `.planning/v1.0-MILESTONE-AUDIT.md` — authoritative gap source; audit-generated 2026-03-05
- `.planning/REQUIREMENTS.md` — read directly; confirmed checkbox and traceability states
- `.planning/phases/04-firebase-authentication/04-01-SUMMARY.md` — read directly; confirmed missing `requirements-completed`
- `.planning/phases/04-firebase-authentication/04-02-SUMMARY.md` — read directly; confirmed missing `requirements-completed`
- `.planning/phases/05-cloud-run-deployment/05-01-SUMMARY.md` — read directly; confirmed non-standard `requirements` key

### Secondary (MEDIUM confidence)

- `.planning/STATE.md` — Phase decisions and context; confirms "No migration needed — Cloud SQL is empty" and "Remove users table entirely"
- `.planning/ROADMAP.md` — Phase 6 success criteria; authoritative specification

### Tertiary (LOW confidence)

None.

---

## Metadata

**Confidence breakdown:**
- Code change locations: HIGH — files read directly, exact lines confirmed
- Documentation changes: HIGH — files read directly, exact mismatches confirmed
- Requirement-to-plan attribution: MEDIUM — inferred from plan descriptions, consistent with verification evidence
- AUTH-04 current status: MEDIUM — debug line absent from current code, but removal history unclear; dead code confirmed present

**Research date:** 2026-03-05
**Valid until:** 2026-04-04 (stable — no external dependencies)
