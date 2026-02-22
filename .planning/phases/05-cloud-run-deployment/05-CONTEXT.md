# Phase 5: Cloud Run Deployment - Context

**Gathered:** 2026-02-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Deploy the Streamlit app to Google Cloud Run with Cloud SQL database connection via Unix socket. Firebase service account credentials stored in Secret Manager and mounted at runtime. Migrate all test-user data to real Firebase UID before deployment. App accessible via public HTTPS URL with working authentication.

</domain>

<decisions>
## Implementation Decisions

### Free Tier Optimization
- Stay within GCP free tier limits — optimize for $0 cost
- Cloud Run: 1 instance maximum (strictest free tier compliance)
- Cloud SQL: db-f1-micro tier (smallest shared-core instance, 0.6GB RAM)
- No connection pooling — direct connection (simple, fine for single instance)

### Data Migration Timing
- Migrate test-user data **before first deploy** — run migration locally, then deploy clean
- SQL script execution via Cloud SQL proxy — direct UPDATE against Cloud SQL
- Automated verification: script counts rows before/after, verifies no test-user rows remain, fails on mismatch
- No backup mechanism needed — migration is one-time, verified, low risk

### Secret Organization
- Firebase service account: Store entire JSON file as single Secret Manager secret
- Secret name: `finance-tracker-firebase-creds` (app-prefixed for multi-app clarity)
- Cloud Run access: Mount secret as file at `/secrets/firebase.json` (not env var)
- Database password: Use Cloud SQL IAM authentication (passwordless, Cloud Run service account)

### Deployment Validation
- Direct deploy to production — single deployment, no staged rollout
- Manual testing: Full end-to-end flow (login, view dashboard, add/edit account, create snapshot, view graphs)
- Logging: Cloud Logging only (GCP default stdout/stderr) — no structured logging or alerts
- Rollback plan: Fix forward — deploy new revisions with fixes, no rollback to previous revisions

### Claude's Discretion
- Exact `gcloud run deploy` command flags and order
- `.dockerignore` patterns beyond `.env`, credential JSON, `.git`
- Health check configuration
- Error messages and user feedback during deployment failures

</decisions>

<specifics>
## Specific Ideas

- Cloud Run instance limit constraint is critical — must configure `--max-instances=1` to enforce free tier
- DATABASE_URL format must use Unix socket pattern: `postgresql+psycopg2://USER:PASS@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE`
- Migration verification should fail loudly if any `user_id = 'test-user'` rows remain after migration

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-cloud-run-deployment*
*Context gathered: 2026-02-22*
