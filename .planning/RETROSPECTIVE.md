# Retrospective: Finance Tracker

---

## Milestone: v1.0 — Ship

**Shipped:** 2026-03-05
**Phases:** 3 GSD phases (4, 5, 6) + 3 pre-GSD phases (1-3)
**Plans:** 7 | **Timeline:** 34 days

### What Was Built

- Firebase auth service layer (Admin SDK, token verification, hot-reload protection)
- Google Sign-In custom Streamlit component via raw postMessage (zero-build)
- Full auth gate in `main.py` — all pages protected, session persists across navigation
- Docker image with `.dockerignore`, Cloud Run `PORT`-aware `CMD`
- GCP infrastructure via Terraform — Cloud SQL PostgreSQL 15, Secret Manager, IAM roles
- Cloud Run deployment; app live at `https://finance-tracker-rntookejza-uc.a.run.app`
- Removed `users` table after deploy; Firebase UID stored directly in accounts/liabilities/snapshots
- Audit gap closure — dead variable removed, stale migration script deleted, requirements tracking cleaned up

### What Worked

- **Research-first planning:** The `06-RESEARCH.md` approach caught the exact auth pattern needed before the plan was written, resulting in a zero-deviation Phase 6 execution.
- **Audit-driven gap closure:** Running `/gsd:audit-milestone` before completing produced a concrete action list (Phase 6). The gap-closure phase was tiny and fast because the audit was specific.
- **Terraform for infra:** Choosing Terraform over manual Console clicks paid off — infrastructure was reproducible and the IAM/Secret Manager wiring was clear in code.
- **Removing the users table:** The decision to drop the users table post-deploy and use Firebase UID directly simplified the data model significantly with no migration cost (DB was empty).

### What Was Inefficient

- **Phase 5 never got a VERIFICATION.md:** The phase was deployed and tested manually but the formal verify-phase step was skipped. The audit caught this, but it added a cleanup phase that could have been avoided.
- **SUMMARY.md frontmatter inconsistency:** Phases 04-01 and 04-02 were missing `requirements-completed` fields, and 05-01 used the wrong key (`requirements` vs `requirements-completed`). Small issues but required a dedicated cleanup plan.
- **Debug output left in production code:** The `st.sidebar.write("DEBUG - Status: unauthenticated")` in `main.py` was a blocker that required a full gap-closure phase. Should be caught during plan verification or a pre-commit check.

### Patterns Established

- Custom Streamlit components via `declare_component()` with a directory containing `index.html` — `st.components.v1.html()` does not support return values.
- Firebase Admin SDK initialization with `if not firebase_admin._apps` guard for Streamlit hot-reload safety.
- Three-state auth protocol: `initializing` → `authenticated` → `unauthenticated`.
- Build Docker images with `--platform linux/amd64` on Apple Silicon — Cloud Run requires amd64.
- Add `ENV PATH="/app/.venv/bin:$PATH"` to Dockerfile — uv venv not in PATH by default.
- Cloud SQL Unix socket `DATABASE_URL`: `postgresql+psycopg2://USER:PASS@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE`

### Key Lessons

- Run verify-phase before considering a phase done, even for infra phases. A missing VERIFICATION.md creates audit debt.
- Strip all debug output before committing to main — use grep in CI or pre-commit hook.
- The milestone audit (`/gsd:audit-milestone`) is worth running even when you think everything is done. It found 6 real gaps worth fixing.

### Cost Observations

- Phase 5 (infra + deploy) took 2525s avg per plan — the longest, as expected for GCP provisioning and Docker builds.
- Phase 4 (auth) averaged 288s per plan — fast, well-researched.
- Phase 6 (cleanup) took 133s — the audit made it extremely focused.

---

## Cross-Milestone Trends

| Milestone | Phases | Plans | Avg Plan Duration | Key Pattern |
|-----------|--------|-------|-------------------|-------------|
| v1.0 Ship | 3 GSD | 7 | ~825s | Research-first prevents deviation |

---

*Created: 2026-03-05*
