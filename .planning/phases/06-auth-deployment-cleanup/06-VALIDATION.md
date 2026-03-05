---
phase: 6
slug: auth-deployment-cleanup
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-05
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none (auto-discovery) |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 6-01-01 | 01 | 1 | AUTH-04 | manual | N/A — auth gate requires browser + Firebase | N/A | ⬜ pending |
| 6-01-02 | 01 | 1 | DEPLOY-05 | smoke | `python -c "import os; assert not os.path.exists('scripts/migrate_test_user.py')"` | ❌ W0 inline | ⬜ pending |
| 6-01-03 | 01 | 1 | AUTH-04 | manual | code review — no debug writes in unauthenticated path | N/A | ⬜ pending |
| 6-01-04 | 01 | 1 | AUTH-04 | manual | read REQUIREMENTS.md checkboxes | N/A | ⬜ pending |
| 6-01-05 | 01 | 1 | AUTH-04 | manual | read auth_service.py docstring | N/A | ⬜ pending |
| 6-01-06 | 01 | 1 | AUTH-04 | manual | read SUMMARY.md frontmatter fields | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No new test files are needed for this cleanup phase.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Login screen shows no debug output to unauthenticated users | AUTH-04 | Streamlit auth gate requires running server + browser | Review `frontend/main.py` — no `st.sidebar.write` debug calls in unauthenticated path; optionally load login screen in browser |
| REQUIREMENTS.md checkboxes all checked | AUTH-04 | Documentation verification | Open file, confirm AUTH-01 through AUTH-06 are `[x]` and traceability is "Complete" |
| auth_service.py docstring accurate | AUTH-04 | Code review | Read `app/services/auth_service.py` — docstring reflects validation, not creation |
| SUMMARY.md frontmatter fields correct | DEPLOY-05 | Documentation verification | Read 04-01, 04-02, 05-01 SUMMARY.md files — check `requirements-completed` key present |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
