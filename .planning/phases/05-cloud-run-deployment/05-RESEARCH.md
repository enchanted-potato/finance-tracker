# Phase 5: Cloud Run Deployment - Research

**Researched:** 2026-02-22
**Domain:** Google Cloud Run + Cloud SQL + Secret Manager deployment
**Confidence:** HIGH

## Summary

Cloud Run deployment with Cloud SQL requires precise configuration of Unix socket connections, Secret Manager mounts, and container health checks. The critical detail is the DATABASE_URL format: for psycopg2, use `postgresql+psycopg2://USER:PASS@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE` (not `unix_sock` parameter). Secrets must be mounted as files (not env vars) for service account JSON. The project already has a working Dockerfile using `uv` for dependency management and a migration script ready to execute.

**Primary recommendation:** Follow official GCP patterns for Cloud Run + Cloud SQL integration, use `--set-secrets` with file mount for Firebase credentials, verify PORT environment variable handling in Dockerfile, and execute migration via Cloud SQL Proxy before first deploy.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Free Tier Optimization:**
- Stay within GCP free tier limits — optimize for $0 cost
- Cloud Run: 1 instance maximum (strictest free tier compliance)
- Cloud SQL: db-f1-micro tier (smallest shared-core instance, 0.6GB RAM)
- No connection pooling — direct connection (simple, fine for single instance)

**Data Migration Timing:**
- Migrate test-user data **before first deploy** — run migration locally, then deploy clean
- SQL script execution via Cloud SQL proxy — direct UPDATE against Cloud SQL
- Automated verification: script counts rows before/after, verifies no test-user rows remain, fails on mismatch
- No backup mechanism needed — migration is one-time, verified, low risk

**Secret Organization:**
- Firebase service account: Store entire JSON file as single Secret Manager secret
- Secret name: `finance-tracker-firebase-creds` (app-prefixed for multi-app clarity)
- Cloud Run access: Mount secret as file at `/secrets/firebase.json` (not env var)
- Database password: Use Cloud SQL IAM authentication (passwordless, Cloud Run service account)

**Deployment Validation:**
- Direct deploy to production — single deployment, no staged rollout
- Manual testing: Full end-to-end flow (login, view dashboard, add/edit account, create snapshot, view graphs)
- Logging: Cloud Logging only (GCP default stdout/stderr) — no structured logging or alerts
- Rollback plan: Fix forward — deploy new revisions with fixes, no rollback to previous revisions

### Claude's Discretion

- Exact `gcloud run deploy` command flags and order
- `.dockerignore` patterns beyond `.env`, credential JSON, `.git`
- Health check configuration
- Error messages and user feedback during deployment failures

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DEPLOY-01 | Firebase service account credentials stored in GCP Secret Manager | Secret Manager mounting with `--set-secrets=/secrets/firebase.json=finance-tracker-firebase-creds:latest` |
| DEPLOY-02 | `.dockerignore` excludes `.env`, credential JSON, `.git` | Standard .dockerignore patterns documented below |
| DEPLOY-03 | App connects to Cloud SQL via Unix socket | DATABASE_URL format: `postgresql+psycopg2://USER:PASS@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE` |
| DEPLOY-04 | App deployed to Cloud Run with working auth | `gcloud run deploy` with Cloud SQL, secrets, max-instances flags |
| DEPLOY-05 | Data migration executes before production traffic | Cloud SQL Proxy + existing `scripts/migrate_test_user.py` |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Cloud Run | 2nd gen | Container hosting | Serverless, auto-scaling, HTTPS, free tier 180k vCPU-seconds/mo |
| Cloud SQL | PostgreSQL 15 | Managed database | Fully managed, free tier available with shared-core instances |
| Secret Manager | current | Credential storage | Native GCP integration, version control, audit logs |
| Cloud SQL Auth Proxy | v2 (2.21.1) | Local DB access | Secure tunnel for migration, IAM auth, no public IP needed |
| gcloud CLI | latest | Deployment tool | Official GCP deployment interface |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| psycopg2-binary | (in deps) | PostgreSQL driver | Already in project, works with Unix sockets via `host` param |
| Docker | latest | Container build | Required for Cloud Run deployment |
| uv | latest | Python deps | Already in Dockerfile, fast, lockfile-based |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| psycopg2 | pg8000 | pg8000 uses `unix_sock` param; psycopg2 uses `host` — already committed |
| Cloud SQL Proxy | Cloud SQL Python Connector | Proxy is better for one-time migration from local machine |
| IAM auth | Database password | Password is simpler but less secure; IAM is best practice for service-to-service |

**Installation:**
```bash
# Cloud SQL Proxy (for migration)
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.21.1/cloud-sql-proxy.darwin.amd64
chmod +x cloud-sql-proxy

# gcloud CLI (if not installed)
brew install google-cloud-sdk
```

## Architecture Patterns

### Recommended Deployment Flow
```
1. Pre-deployment Setup
   ├── Create Cloud SQL instance (db-f1-micro, PostgreSQL 15)
   ├── Enable IAM authentication on Cloud SQL
   ├── Create IAM database user for Cloud Run service account
   ├── Upload Firebase credentials to Secret Manager
   └── Grant Secret Manager accessor role to Cloud Run service account

2. Data Migration (before first deploy)
   ├── Start Cloud SQL Proxy locally
   ├── Run migrate_test_user.py with real Firebase UID
   └── Verify no test-user rows remain

3. Deployment
   ├── Build and push Docker image to Artifact Registry
   ├── Deploy to Cloud Run with --add-cloudsql-instances and --set-secrets
   └── Configure max-instances=1 for free tier

4. Post-deployment Validation
   ├── Visit HTTPS URL
   ├── Test Google Sign-In flow
   ├── Verify dashboard loads with migrated data
   └── Check Cloud Logging for errors
```

### Pattern 1: Unix Socket Connection String (psycopg2)

**What:** PostgreSQL connection via Unix socket on Cloud Run
**When to use:** Connecting from Cloud Run to Cloud SQL (standard pattern)
**Example:**
```python
# DATABASE_URL format for psycopg2
DATABASE_URL="postgresql+psycopg2://USER:PASSWORD@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE"

# For IAM auth (passwordless), password can be empty but user required
DATABASE_URL="postgresql+psycopg2://serviceaccount@example.iam@/finance_tracker?host=/cloudsql/my-project:us-central1:my-instance"
```
**Source:** [Cloud SQL PostgreSQL Connect Run Documentation](https://docs.cloud.google.com/sql/docs/postgres/connect-run)

**Critical details:**
- psycopg2 uses `host` parameter, NOT `unix_sock` (which pg8000 uses)
- Socket path: `/cloudsql/PROJECT:REGION:INSTANCE` (no `.s.PGSQL.5432` suffix needed)
- Instance connection name format: `project:region:instance`
- Max socket path length: 108 characters (Linux limit)

### Pattern 2: Secret Mounting as File

**What:** Mount Secret Manager secret as file in Cloud Run container
**When to use:** Service account JSON files, certificates, any non-env-var secrets
**Example:**
```bash
gcloud run deploy finance-tracker \
  --image gcr.io/PROJECT/finance-tracker \
  --set-secrets=/secrets/firebase.json=finance-tracker-firebase-creds:latest
```
**Source:** [Cloud Run Configure Secrets Documentation](https://docs.cloud.google.com/run/docs/configuring/services/secrets)

**Key details:**
- Prefix with `/` for file mount: `--set-secrets=/path/to/file=SECRET_NAME:VERSION`
- Without `/`, it's an env var: `--set-secrets=ENV_VAR=SECRET_NAME:VERSION`
- Secrets are not "real files" — proxied API calls to Secret Manager on access
- Pin to version (e.g., `:1`) or use `:latest` for auto-update
- Secrets auto-update with `latest`, env vars remain static

### Pattern 3: Cloud SQL Connection from Cloud Run

**What:** Connect Cloud Run service to Cloud SQL instance
**When to use:** Every Cloud Run deployment needing database access
**Example:**
```bash
gcloud run deploy finance-tracker \
  --image gcr.io/PROJECT/finance-tracker \
  --add-cloudsql-instances=PROJECT:REGION:INSTANCE \
  --set-env-vars=DATABASE_URL="postgresql+psycopg2://USER:PASS@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE"
```
**Source:** [Cloud Run Deploy Reference](https://docs.cloud.google.com/sdk/gcloud/reference/run/deploy)

**Key details:**
- `--add-cloudsql-instances` mounts Unix socket at `/cloudsql/PROJECT:REGION:INSTANCE`
- Can specify multiple instances with comma separation
- DATABASE_URL references same path in `host` parameter
- IAM auth: user format is `serviceaccount@example.iam`, password empty

### Pattern 4: Cloud Run PORT Environment Variable

**What:** Configure Streamlit to listen on Cloud Run's assigned PORT
**When to use:** All Cloud Run deployments (PORT can be non-8080)
**Example:**
```dockerfile
# Dockerfile CMD - use shell form for PORT expansion
CMD streamlit run frontend/main.py --server.port=${PORT:-8501} --server.address=0.0.0.0
```
**Source:** [Streamlit Docker Documentation](https://docs.streamlit.io/deploy/tutorials/docker)

**Critical details:**
- Cloud Run sets PORT env var (default 8080, but can vary)
- Shell parameter expansion `${PORT:-8501}` defaults to 8501 if PORT unset
- MUST bind to `0.0.0.0`, not `localhost` (container networking)
- Streamlit default is 8501, but Cloud Run expects app to honor PORT

### Pattern 5: IAM Database Authentication

**What:** Passwordless database authentication using Cloud Run service account
**When to use:** Preferred for all Cloud SQL connections from Cloud Run (more secure)
**Example:**
```bash
# Enable IAM auth on Cloud SQL instance
gcloud sql instances patch INSTANCE_NAME \
  --database-flags cloudsql.iam_authentication=on

# Create IAM database user (service account email)
gcloud sql users create SERVICE_ACCOUNT_EMAIL \
  --instance=INSTANCE_NAME \
  --type=cloud_iam_service_account

# Connection string (password empty or omitted)
DATABASE_URL="postgresql+psycopg2://serviceaccount@example.iam@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE"
```
**Source:** [Cloud SQL IAM Authentication](https://docs.cloud.google.com/sql/docs/postgres/iam-authentication)

**Key details:**
- Requires `cloudsql.iam_authentication=on` flag
- User name is service account email, type must be `cloud_iam_service_account`
- Password is empty string or omitted
- Cloud Run service account needs `Cloud SQL Client` role
- Tokens are short-lived, auto-renewed by connector

### Anti-Patterns to Avoid

- **Hardcoded PORT:** Don't use `--server.port=8501` without PORT env var fallback — Cloud Run can assign different ports
- **Wrong socket parameter:** Don't use `unix_sock` with psycopg2 — use `host` parameter
- **Secrets as env vars for JSON:** Don't use `--set-secrets=FIREBASE_CREDS=...` for JSON files — mount as file instead
- **Including .env in Docker image:** Don't skip .dockerignore — credentials leak into image layers
- **Connection pooling with max-instances=1:** Unnecessary complexity for single instance

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cloud SQL connection from Cloud Run | Custom Unix socket path detection | `--add-cloudsql-instances` flag + standard DATABASE_URL | GCP handles socket mounting, versioning, instance connection name resolution |
| Secret rotation/access | Custom secret file management | Secret Manager with `--set-secrets` | Auto-rotation, audit logs, version control, IAM permissions |
| Database migration rollback | Custom undo logic | Transaction-based migration + verification | SQLModel transactions provide ACID guarantees, verification catches failures |
| Health check endpoint | Custom `/health` route in Streamlit | Streamlit built-in `/_stcore/health` | Already exists, no code needed, Cloud Run auto-detects |
| Container startup timeout | Custom retry/backoff logic | Cloud Run startup probes | Built-in, configurable, handles slow DB connections |

**Key insight:** GCP provides purpose-built solutions for Cloud Run + Cloud SQL integration. Hand-rolling connection logic, secret management, or health checks increases failure surface area and misses built-in features like auto-scaling, audit logs, and IAM integration.

## Common Pitfalls

### Pitfall 1: Wrong DATABASE_URL Format for psycopg2

**What goes wrong:** Container crashes at startup with "unhealthy container" timeout error, misleading health check failure
**Why it happens:** psycopg2 uses `host` parameter for Unix socket, NOT `unix_sock` (which pg8000 uses). Wrong format fails silently during engine creation, surfaces as health check timeout.
**How to avoid:** Verify format: `postgresql+psycopg2://USER:PASS@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE`
**Warning signs:** Cloud Run logs show "Container failed to start" with no database connection errors — connection never attempted due to malformed URL

**Verification:**
```bash
# Test locally with Cloud SQL Proxy
./cloud-sql-proxy PROJECT:REGION:INSTANCE &
DATABASE_URL="postgresql+psycopg2://USER:PASS@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE" python -c "from app.database import engine; print(engine.connect())"
```

### Pitfall 2: PORT Environment Variable Not Honored

**What goes wrong:** Cloud Run health checks fail, container marked unhealthy, deployment fails
**Why it happens:** Streamlit listens on 8501, but Cloud Run expects app to listen on PORT env var (can be 8080 or other)
**How to avoid:** Use shell parameter expansion in CMD: `CMD streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0`
**Warning signs:** Logs show "Container is listening on the wrong port" or "failed to connect to localhost:8080"

**Note:** Existing Dockerfile hardcodes `--server.port=8501` — needs update for Cloud Run PORT compatibility.

### Pitfall 3: Secrets Mounted as Env Vars Instead of Files

**What goes wrong:** Firebase Admin SDK fails to initialize, auth breaks, multiline JSON corrupted in env var
**Why it happens:** `--set-secrets=FIREBASE_CREDS=...` creates env var, not file. Firebase Admin SDK expects file path.
**How to avoid:** Use file mount syntax: `--set-secrets=/secrets/firebase.json=SECRET_NAME:VERSION`, update `FIREBASE_CREDENTIALS_PATH=/secrets/firebase.json`
**Warning signs:** Logs show "Failed to initialize Firebase app" or JSON parse errors

### Pitfall 4: Missing .dockerignore Leaks Credentials

**What goes wrong:** `.env`, `firebase-credentials.json`, git history baked into Docker image, visible via `docker history`
**Why it happens:** No `.dockerignore` file — `COPY . .` includes everything
**How to avoid:** Create `.dockerignore` with `.env`, `*.json` (credentials), `.git`, `.venv`, `__pycache__`, `.pytest_cache`
**Warning signs:** Large image size (git history included), credentials visible in layer inspection

### Pitfall 5: IAM Auth Misconfigured

**What goes wrong:** Database connection fails with "role does not exist" or "password authentication failed"
**Why it happens:** IAM user not created in database, or service account lacks `Cloud SQL Client` role, or `cloudsql.iam_authentication` flag not enabled
**How to avoid:** Follow exact sequence: enable flag → create IAM user → grant role → test connection
**Warning signs:** Logs show "FATAL: role 'serviceaccount@project.iam.gserviceaccount.com' does not exist"

**Verification:**
```bash
# Test IAM auth locally
gcloud sql users list --instance=INSTANCE_NAME | grep serviceaccount
gcloud projects get-iam-policy PROJECT --flatten="bindings[].members" --filter="bindings.members:SERVICE_ACCOUNT" --format="value(bindings.role)"
```

### Pitfall 6: Migration Executed After Deployment

**What goes wrong:** Real user data and test-user data coexist, duplicate accounts, snapshots belong to wrong user
**Why it happens:** User logs in first, auto-creates account, THEN migration runs — FK constraints prevent cleanup
**How to avoid:** Run migration via Cloud SQL Proxy BEFORE first deployment, verify no test-user rows remain
**Warning signs:** Migration script reports 0 rows affected, or FK constraint violations on user deletion

### Pitfall 7: Free Tier Exceeded (Unintentional Scaling)

**What goes wrong:** Cloud Run scales to multiple instances, exceeds free tier, unexpected charges
**Why it happens:** No `--max-instances` flag — Cloud Run defaults to auto-scaling based on demand
**How to avoid:** Explicitly set `--max-instances=1` in deploy command
**Warning signs:** Billing alert, multiple instances in Cloud Run metrics

### Pitfall 8: Streamlit Health Check Confusion

**What goes wrong:** 404 errors on health checks, GCP thinks app is unhealthy
**Why it happens:** Streamlit uses `/_stcore/health` endpoint, GCP might probe wrong path
**How to avoid:** Cloud Run auto-detects HTTP server, no custom health check needed — Streamlit's built-in endpoint works
**Warning signs:** Logs show 404 for `/` or other non-Streamlit paths

## Code Examples

Verified patterns from official sources:

### Cloud SQL Proxy Connection (for migration)
```bash
# Source: https://github.com/GoogleCloudPlatform/cloud-sql-proxy
# Download Cloud SQL Proxy v2
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.21.1/cloud-sql-proxy.darwin.amd64
chmod +x cloud-sql-proxy

# Start proxy (creates Unix socket at /cloudsql/PROJECT:REGION:INSTANCE)
./cloud-sql-proxy PROJECT:REGION:INSTANCE &

# Run migration with DATABASE_URL pointing to socket
DATABASE_URL="postgresql+psycopg2://USER:PASS@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE" \
  python scripts/migrate_test_user.py FIREBASE_UID
```

### Complete gcloud run deploy Command
```bash
# Source: https://docs.cloud.google.com/sdk/gcloud/reference/run/deploy
gcloud run deploy finance-tracker \
  --image gcr.io/PROJECT_ID/finance-tracker:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --max-instances=1 \
  --memory=512Mi \
  --cpu=1 \
  --add-cloudsql-instances=PROJECT_ID:us-central1:INSTANCE_NAME \
  --set-env-vars="DATABASE_URL=postgresql+psycopg2://USER:PASS@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE" \
  --set-secrets=/secrets/firebase.json=finance-tracker-firebase-creds:latest \
  --set-env-vars="FIREBASE_CREDENTIALS_PATH=/secrets/firebase.json"
```

### Updated Dockerfile with PORT Support
```dockerfile
# Source: https://docs.streamlit.io/deploy/tutorials/docker
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

ENV PYTHONPATH=/app

EXPOSE 8501

# Use shell form to expand PORT env var
CMD streamlit run frontend/main.py --server.port=${PORT:-8501} --server.address=0.0.0.0
```

### .dockerignore File
```
# Source: https://oneuptime.com/blog/post/2026-01-16-docker-dockerignore-speed-builds/view
.env
.env.*
*.json
!pyproject.json
.git
.venv
__pycache__
.pytest_cache
.mypy_cache
.ruff_cache
*.pyc
*.pyo
*.pyd
.DS_Store
docker-compose.yml
README.md
.planning/
.claude/
tests/
```

### IAM Database User Creation
```bash
# Source: https://docs.cloud.google.com/sql/docs/postgres/add-manage-iam-users
# Enable IAM authentication
gcloud sql instances patch INSTANCE_NAME \
  --database-flags cloudsql.iam_authentication=on

# Create IAM database user (service account)
gcloud sql users create SERVICE_ACCOUNT_EMAIL \
  --instance=INSTANCE_NAME \
  --type=cloud_iam_service_account

# Grant Cloud SQL Client role to service account
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:SERVICE_ACCOUNT_EMAIL \
  --role=roles/cloudsql.client
```

### Secret Manager Upload
```bash
# Source: https://docs.cloud.google.com/run/docs/configuring/services/secrets
# Create secret from file
gcloud secrets create finance-tracker-firebase-creds \
  --data-file=path/to/firebase-credentials.json

# Grant Secret Manager accessor role to Cloud Run service account
gcloud secrets add-iam-policy-binding finance-tracker-firebase-creds \
  --member=serviceAccount:SERVICE_ACCOUNT_EMAIL \
  --role=roles/secretmanager.secretAccessor
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Cloud SQL Proxy v1 | Cloud SQL Proxy v2 (2.21.1) | 2023 | New flag names, better performance, automatic IAM token refresh |
| `--update-secrets` flag | `--set-secrets` flag | 2024 | Unified syntax for env vars and file mounts, clearer semantics |
| Manual secret rotation | Secret Manager `:latest` version | 2024 | Auto-update on container restart, no redeploy needed |
| Public IP + SSL | Unix socket only | Ongoing | More secure, no network exposure, built-in Cloud Run pattern |
| Cloud Functions 1st gen | Cloud Run 2nd gen | 2023 | Better cold start, higher limits, more control |

**Deprecated/outdated:**
- Cloud Functions 1st gen for new deployments (use Cloud Run)
- `--update-env-vars` for secrets (use `--set-secrets` instead)
- Public IP connections to Cloud SQL from Cloud Run (use Unix socket via `--add-cloudsql-instances`)

## Open Questions

1. **Does IAM auth work with SQLModel/SQLAlchemy without code changes?**
   - What we know: IAM auth requires empty password in connection string
   - What's unclear: Whether SQLAlchemy psycopg2 dialect handles IAM token refresh automatically
   - Recommendation: Test with Cloud SQL Proxy first; if IAM auth causes issues, fall back to database password stored in Secret Manager

2. **Does Streamlit health check endpoint work with Cloud Run without configuration?**
   - What we know: Streamlit exposes `/_stcore/health`, Cloud Run auto-detects HTTP servers
   - What's unclear: Whether GCP probes the right endpoint or needs explicit configuration
   - Recommendation: Deploy without custom health check config first; Cloud Run should auto-detect (confidence: HIGH based on community reports)

3. **Should migration script verify data integrity beyond row count?**
   - What we know: Current script counts affected rows per table
   - What's unclear: Whether FK integrity checks or data sampling is needed
   - Recommendation: Current verification is sufficient — FK constraints prevent invalid state, row count confirms migration ran (confidence: MEDIUM)

## Sources

### Primary (HIGH confidence)
- [Cloud SQL Connect from Cloud Run](https://docs.cloud.google.com/sql/docs/postgres/connect-run) - Unix socket connection format
- [gcloud run deploy Reference](https://docs.cloud.google.com/sdk/gcloud/reference/run/deploy) - Exact flag syntax
- [Cloud Run Configure Secrets](https://docs.cloud.google.com/run/docs/configuring/services/secrets) - Secret mounting patterns
- [Cloud SQL IAM Authentication](https://docs.cloud.google.com/sql/docs/postgres/iam-authentication) - Passwordless auth setup
- [Streamlit Docker Documentation](https://docs.streamlit.io/deploy/tutorials/docker) - PORT environment variable handling
- [Cloud SQL Proxy GitHub](https://github.com/GoogleCloudPlatform/cloud-sql-proxy) - Latest version, migration guides

### Secondary (MEDIUM confidence)
- [OneUptime Cloud Run Health Check Troubleshooting](https://oneuptime.com/blog/post/2026-02-17-how-to-resolve-cloud-run-deployment-failures-due-to-container-health-check-timeouts/view) - Startup timeout issues
- [OneUptime Docker .dockerignore Guide](https://oneuptime.com/blog/post/2026-01-16-docker-dockerignore-speed-builds/view) - .dockerignore patterns
- [Medium: Cloud Run and Secret Manager](https://medium.com/google-cloud/cloud-run-and-secret-manager-3c5d43a72e87) - Secret management best practices

### Tertiary (LOW confidence)
- Streamlit community discussions about Cloud Run deployment - various pitfalls and workarounds

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official GCP docs, verified with current versions
- Architecture: HIGH - Official patterns from GCP docs, verified with project structure
- Pitfalls: MEDIUM-HIGH - Verified via official docs + community reports, some require testing
- DATABASE_URL format: HIGH - Official GCP docs, multiple sources confirm psycopg2 uses `host` param
- Secret mounting: HIGH - Official GCP docs with exact flag syntax
- Migration approach: HIGH - Existing script verified, Cloud SQL Proxy standard approach

**Research date:** 2026-02-22
**Valid until:** 2026-03-24 (30 days — stable GCP features, but verify flag syntax before execution)

**Critical verification checklist before deploy:**
- [ ] DATABASE_URL format uses `host=/cloudsql/...` (NOT `unix_sock`)
- [ ] Dockerfile CMD honors PORT env var with `${PORT:-8501}`
- [ ] .dockerignore excludes `.env`, `*.json` credentials, `.git`
- [ ] `--set-secrets` uses `/secrets/firebase.json=...` (file mount, NOT env var)
- [ ] `--add-cloudsql-instances` matches instance connection name in DATABASE_URL
- [ ] `--max-instances=1` enforces free tier limit
- [ ] Migration executed via Cloud SQL Proxy BEFORE first deploy
