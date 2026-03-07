---
phase: 6
slug: dashboard-and-navigation-polish
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-07
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 6-xx-01 | 01 | 0 | DASH-02 | unit | `pytest tests/test_dashboard_helpers.py::test_net_worth_delta_negative -x` | ❌ W0 | ⬜ pending |
| 6-xx-02 | 01 | 0 | DASH-03 | unit | `pytest tests/test_dashboard_helpers.py::test_line_chart_tick_format -x` | ❌ W0 | ⬜ pending |
| 6-xx-03 | 01 | 1 | DASH-01 | manual | n/a — visual inspection of rendered card layout | n/a | ⬜ pending |
| 6-xx-04 | 01 | 1 | DASH-02 | unit | `pytest tests/test_dashboard_helpers.py::test_net_worth_delta_negative -x` | ❌ W0 | ⬜ pending |
| 6-xx-05 | 01 | 1 | DASH-03 | unit | `pytest tests/test_dashboard_helpers.py::test_line_chart_tick_format -x` | ❌ W0 | ⬜ pending |
| 6-xx-06 | 01 | 1 | DASH-04 | manual | n/a — visual inspection of chart drop shadow | n/a | ⬜ pending |
| 6-xx-07 | 01 | 1 | NAV-01 | manual | n/a — visual inspection of sidebar active indicator | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_dashboard_helpers.py` — stubs for DASH-02 (delta sign) and DASH-03 (tick format)
  - DASH-02: verify negative delta renders HTML with `color: red`
  - DASH-03: verify `_render_line_chart` Plotly figure has `tickprefix="£"` and `tickformat=",.0f"`

*Existing infrastructure (pytest + conftest.py) covers all other setup needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Metric cards render as rounded boxes with soft colored backgrounds | DASH-01 | Pure visual/CSS — Streamlit rendering has no testable Python logic | Open app, verify Net Worth=blue, Assets=green, Liabilities=red cards with rounded corners |
| Pension bar chart has drop shadows | DASH-04 | CSS injection on container div — no Python logic to unit test | Open app, verify `.stPlotlyChart` containers have visible drop shadow |
| Sidebar active page indicator is not orange | NAV-01 | Streamlit widget type attribute — no testable logic | Navigate between pages, verify active page shows left border accent (not orange background) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
