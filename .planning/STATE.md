---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: verifying
stopped_at: Phase 9 context gathered
last_updated: "2026-05-08T16:44:06.698Z"
last_activity: 2026-04-29 — Phase 9 complete
progress:
  total_phases: 12
  completed_phases: 5
  total_plans: 17
  completed_plans: 17
  percent: 100
---

# State

## Current Position

Phase: Phase 9 complete — Phase 10 next
Plan: —
Status: Phase 9 FastAPI Foundation complete (2/2 plans, 12/12 verification passed)
Last activity: 2026-04-29 — Phase 9 complete

Progress: [█░░░░░░░░░] ~14% (1/7 v2.0 phases complete)

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-04)

**Core value:** Seeing your net worth trend over time at a glance, without the overhead of transaction tracking.
**Current focus:** v2.0 — React Migration (Phases 9-15)

## Milestone Scope

| Phase | Goal | Requirements |
|-------|------|--------------|
| 9. FastAPI Foundation | Correctly configured FastAPI server before any feature routes | API-01, API-02, API-03, API-04 |
| 10. Core Data API Routes | All feature endpoints live with float schemas and Recharts-shaped responses | API-05, API-06, API-07, API-08 |
| 11. React Scaffold and Auth | Vite SPA with Firebase auth gate and per-request token refresh | REACT-01, REACT-02, REACT-03, REACT-04 |
| 12. Data Pages | Accounts, Liabilities, Pension — CRUD, date-aware entry, collapsible history | RDAT-01, RDAT-02, RDAT-03, RDAT-04, RDAT-05, RDAT-06, RDAT-07 |
| 13. Dashboard | Metric cards and four Recharts charts from real API data | RDASH-01, RDASH-02, RDASH-03, RDASH-04 |
| 14. History and Configure | Snapshot table with CSV I/O; type management with inline delete | RHIST-01, RHIST-02, RHIST-03, RHIST-04, RCONF-01 |
| 15. Deployment | React on Firebase Hosting; FastAPI on Cloud Run; production smoke test | RDEP-01, RDEP-02 |

## Performance Metrics

**Velocity (carried over from v1.x):**

- Total plans completed: 6
- Average duration: 1359 seconds (~23 minutes)
- Total execution time: 8151 seconds

**By Phase (v1.x history):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 04 | 2 | 575s | 288s |
| 05 | 4 | 7576s | 1894s |

*Updated after each plan completion*
| Phase 06 P03 | 81 | 2 tasks | 1 files |
| Phase 06 P01 | 84 | 1 tasks | 1 files |
| Phase 06 P02 | 480 | 2 tasks | 1 files |
| Phase 06 P04 | 900 | 2 tasks | 2 files |

## Accumulated Context

### Decisions

- [Phase 05-03]: Build Docker images with --platform linux/amd64 on Apple Silicon — Cloud Run requires amd64
- [Phase 05-03]: Add ENV PATH="/app/.venv/bin:$PATH" to Dockerfile — uv venv not in PATH by default
- [Phase 05-03]: Cloud Run service URL: https://finance-tracker-rntookejza-uc.a.run.app
- [Phase 05]: Remove users table entirely — single-user app, use Firebase UID directly in accounts/liabilities/snapshots
- [Phase 05]: Store Firebase UID directly as string in user_id fields with no FK constraints
- [Phase 06-01]: Deferred imports inside test bodies (not module-level) to allow pytest collection even before _build_net_worth_card_html exists
- [Phase 06-03]: Keep type='primary' for active sidebar buttons and restyle CSS rule (transparent + border-left) rather than switching to secondary — preserves existing CSS hook
- [Phase 06-02]: yaxis=dict(tickprefix, tickformat) is the correct Plotly API — combined yaxis_tickformat="£,.0f" is a bug (prefix+format can't be combined this way)
- [Phase 06-02]: HTML metric cards use st.markdown(f-string, unsafe_allow_html=True) with inline styles
- [Phase 06-04]: Equal card height via hidden placeholder div (visibility:hidden) rather than fixed px height
- [Phase 06-04]: Dual CSS selector (.stPlotlyChart + data-testid) for Plotly shadow — handles Streamlit version differences
- [Quick-4]: LiabilityEntry uses UniqueConstraint(user_id, entry_date, liability_type_id) enabling upsert semantics
- [Quick-4]: capture_snapshot filters LiabilityEntry by entry_date == snapshot_date (not is_active flag)
- [Quick-4]: Deletion in st.data_editor detected by diffing original _id set vs edited _id set (hidden column pattern)

### Architecture Decisions for v2.0

- FastAPI layer is a pure translation layer — zero business logic in route handlers; all logic stays in app/services/
- Pydantic response schemas are separate from SQLModel models — required to avoid Decimal serialisation and user_id leakage
- React API client calls user.getIdToken() before every request — raw token string never stored in React state
- All data shaping for Recharts (one object per date, all series as keys) happens in FastAPI routes, not in React
- All monetary values serialised as float (not Decimal) via explicit Pydantic response schemas

### Pending Todos

None.

### Blockers/Concerns

- Research flags for Phase 10/13: Recharts PieChart donut innerRadius prop — verify against Recharts docs at planning time
- Research flags for Phase 15: Firebase Hosting `run` rewrite `region` field must match `gcloud run services describe` output — verify before writing firebase.json
- Research flag for Phase 11: Confirm whether shadcn/ui now recommends sonner over useToast for toasts — verify with CLI before adding toast infrastructure

## Quick Tasks Completed

| # | Task | Commits | Date |
|---|------|---------|------|
| 1 | Add pension as separate category with dedicated page and dashboard chart | 4194ef8, 7ed7004 | 2026-03-01 |
| 2 | Add liabilities CSV upload to history page | 449efe2, 5106830 | 2026-03-02 |
| 3 | Fix NULL values for missing history data (nullable snapshot fields, gap charts, dash display) | 6c98f39, 96b9a07, 096b69b | 2026-03-03 |
| 4 | Refactor liabilities to date-keyed LiabilityEntry model with st.data_editor UI | 38db8ee, 675ea64 | 2026-03-09 |
| 5 | Refactor accounts to type-keyed AccountEntry model matching liabilities pattern | 1905305, 9f75a20, 79acd4b, b4d5e4e, ab1d06e | 2026-03-12 |
| 6 | Apply Midnight colour scheme to entire Streamlit app | 52b57a9, 07bc3e0, 3ea417a | 2026-03-13 |

## Session Continuity

Last session: 2026-04-27T20:03:22.666Z
Stopped at: Phase 9 context gathered
Resume file: .planning/phases/09-fastapi-foundation/09-CONTEXT.md
