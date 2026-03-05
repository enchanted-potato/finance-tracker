# Milestones

## Completed

### v1.0 — Ship (Shipped: 2026-03-05)

**Goal:** Make the app production-ready — add Firebase Authentication and deploy to Cloud Run + Cloud SQL.

**Phases:** 4–6 (+ Phases 1-3 pre-GSD foundation)
**Plans:** 7 | **Timeline:** 2026-01-30 → 2026-03-05 (34 days)
**Requirements:** 11/11 complete

**Key accomplishments:**
1. Firebase auth service layer with Admin SDK, token verification, and hot-reload protection
2. Full auth gate in `main.py` — Google Sign-In popup, session persistence across navigation, logout flow
3. Docker image with `.dockerignore`, Cloud Run `PORT`-aware `CMD`, clean credential exclusion
4. GCP infrastructure via Terraform — Cloud SQL (PostgreSQL 15, db-f1-micro), Secret Manager, IAM roles
5. Cloud Run deployment with Firebase credentials injected from Secret Manager at runtime; app live at `https://finance-tracker-rntookejza-uc.a.run.app`
6. Removed `users` table — single-user app stores Firebase UID directly in accounts/liabilities/snapshots; `get_or_create_user` refactored to validation-only
7. Audit gap closure — dead `user_id` variable removed, stale migration script deleted, REQUIREMENTS.md tracking completed

**Archive:** `.planning/milestones/v1.0-ROADMAP.md`, `.planning/milestones/v1.0-REQUIREMENTS.md`

---

*Last updated: 2026-03-05*
