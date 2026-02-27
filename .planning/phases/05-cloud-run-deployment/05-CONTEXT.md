# Phase 5: Cloud Run Deployment - Context

**Gathered:** 2026-02-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Deploy the Streamlit app to Google Cloud Run with Cloud SQL database connection via Unix socket. Firebase service account credentials stored in Secret Manager and mounted at runtime. Remove users table and simplify schema to single-user architecture. App accessible via public HTTPS URL with working authentication.

</domain>

<decisions>
## Implementation Decisions

### Free Tier Optimization
- Stay within GCP free tier limits — optimize for $0 cost
- Cloud Run: 1 instance maximum (strictest free tier compliance)
- Cloud SQL: db-f1-micro tier (smallest shared-core instance, 0.6GB RAM)
- No connection pooling — direct connection (simple, fine for single instance)

### Schema Simplification
- Remove users table entirely — single-user app doesn't need it
- Remove foreign key constraints from accounts, liabilities, snapshots
- Use Firebase UID directly in user_id columns (no FK to users table)
- Prevent 'test-user' as a valid user_id (add validation to block hardcoded test ID)
- No migration needed — database is empty, fresh start on Cloud SQL

### Domain & SSL Setup
- Use Cloud Run auto-generated URL (*.run.app) — no custom domain
- Cloud Run provides automatic HTTPS — no custom SSL config needed
- Public URL with Firebase auth gate protecting all content

### Secret Organization
- Firebase service account: Store entire JSON file as single Secret Manager secret
- Secret name: `finance-tracker-firebase-creds` (app-prefixed for multi-app clarity)
- Cloud Run access: Mount secret as file at `/secrets/firebase.json` (not env var)
- Database password: Use Cloud SQL IAM authentication (passwordless, Cloud Run service account)

### Deployment Validation
- Direct deploy to production — single deployment, no staged rollout
- Manual testing: Full end-to-end flow (login, view dashboard, add/edit account, create snapshot, view graphs)
- First data created through UI after deployment — no seed scripts
- Logging: Cloud Logging only (GCP default stdout/stderr) — no structured logging or alerts
- Rollback plan: Fix forward — deploy new revisions with fixes, no rollback to previous revisions

### Claude's Discretion
- Exact `gcloud run deploy` command flags and order
- `.dockerignore` patterns beyond `.env`, credential JSON, `.git`
- Health check configuration
- HTTPS enforcement (redirect HTTP to HTTPS or allow both)
- Access control beyond Firebase auth (if any additional restrictions needed)
- Error messages and user feedback during deployment failures

</decisions>

<specifics>
## Specific Ideas

- Cloud Run instance limit constraint is critical — must configure `--max-instances=1` to enforce free tier
- DATABASE_URL format must use Unix socket pattern: `postgresql+psycopg2://USER:PASS@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE`
- Schema changes: Drop FK constraints on accounts.user_id, liabilities.user_id, snapshots.user_id before deployment
- Test user prevention: Block 'test-user' string from being used as user_id in app logic

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-cloud-run-deployment*
*Context gathered: 2026-02-27*
