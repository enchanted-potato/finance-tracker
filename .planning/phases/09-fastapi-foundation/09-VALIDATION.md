---
phase: 9
slug: fastapi-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-27
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x (already installed) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/test_api_health.py tests/test_api_auth.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_api_health.py tests/test_api_auth.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 9-01-01 | 01 | 0 | API-01 | smoke | `pytest tests/test_api_health.py::test_health_returns_200 -x` | ❌ W0 | ⬜ pending |
| 9-01-02 | 01 | 0 | API-01 | unit | `pytest tests/test_api_health.py::test_firebase_not_init_at_import -x` | ❌ W0 | ⬜ pending |
| 9-01-03 | 01 | 0 | API-02 | integration | `pytest tests/test_api_health.py::test_cors_preflight_allowed_origin -x` | ❌ W0 | ⬜ pending |
| 9-01-04 | 01 | 0 | API-02 | integration | `pytest tests/test_api_health.py::test_cors_preflight_rejected_origin -x` | ❌ W0 | ⬜ pending |
| 9-02-01 | 02 | 0 | API-03 | unit | `pytest tests/test_api_auth.py::test_missing_token_returns_401 -x` | ❌ W0 | ⬜ pending |
| 9-02-02 | 02 | 0 | API-03 | unit | `pytest tests/test_api_auth.py::test_invalid_token_returns_401 -x` | ❌ W0 | ⬜ pending |
| 9-02-03 | 02 | 0 | API-03 | unit | `pytest tests/test_api_auth.py::test_wrong_uid_returns_403 -x` | ❌ W0 | ⬜ pending |
| 9-02-04 | 02 | 0 | API-04 | unit | `pytest tests/test_api_health.py::test_decimal_serialises_as_float -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_api_health.py` — stubs for API-01 (health + lifespan), API-02 (CORS), API-04 (float serialisation)
- [ ] `tests/test_api_auth.py` — stubs for API-03 (401/403 scenarios, dev bypass)
- [ ] `uv add "fastapi[standard]"` — installs fastapi, uvicorn, httpx (TestClient) in one step

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| App reconnects after DB connection drop | API-01 | Requires simulating a live connection drop | `docker-compose up`, disconnect DB container briefly (`docker stop <db>`), reconnect, verify next request succeeds |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
