# External Integrations

**Analysis Date:** 2026-02-14

## APIs & External Services

**Firebase Authentication:**
- Service: Google Firebase Authentication
- What it's used for: User identity and authentication (email/password + Google sign-in planned for Phase 4)
- SDK/Client: `firebase-admin` package
- Auth: Credentials loaded from path specified in `FIREBASE_CREDENTIALS_PATH` env var
- Status: Currently declared in dependencies but not yet integrated; hardcoded test user in `frontend/main.py` (see `TEST_USER_ID = "test-user"`)
- Implementation location: `app/config.py` (configuration), User model mirrors Firebase UID in `app/models.py`

## Data Storage

**Databases:**
- Type/Provider: PostgreSQL (Google Cloud SQL in production, local Postgres in dev)
- Connection: Via environment variable `DATABASE_URL`
- Client: SQLModel + SQLAlchemy (wraps psycopg2-binary driver)
- Configuration: `app/database.py` creates engine and session generator
- Models: `app/models.py` contains SQLModel table definitions:
  - `User` - Firebase auth mirror with id, email, display_name, created_at
  - `Account` - Asset accounts with balance, currency (GBP), timestamps
  - `Liability` - Liability accounts with balance, currency, timestamps
  - `AccountType` - User-custom or predefined account categories
  - `LiabilityType` - User-custom or predefined liability categories
  - `Snapshot` - Point-in-time net worth records with JSONB detail field for historical breakdown

**File Storage:**
- Local filesystem only - CSV import/export for snapshots in `frontend/pages/history.py`
- CSV operations handled via `csv` module and `io.BytesIO`
- Import method: `import_csv_snapshots()` in `app/services/snapshot_service.py`

**Caching:**
- None implemented
- State management via Streamlit session state in `frontend/main.py`

## Authentication & Identity

**Auth Provider:**
- Service: Firebase Authentication (Google)
- Implementation: Currently using hardcoded test user in `frontend/main.py`
- Approach:
  - Planned: Firebase token verification (structure in place via `firebase_credentials_path`)
  - Current: Test user with ID `"test-user"` created on app startup in `_ensure_test_user()` function
  - User stored in database with Firebase UID pattern

## Monitoring & Observability

**Error Tracking:**
- None (external service)
- Error handling: Built-in Python exceptions logged locally via loguru

**Logs:**
- Framework: loguru
- Implementation: Direct loguru usage in service functions
- Files using logging: `app/services/account_service.py`, `app/services/snapshot_service.py`, `app/services/liability_service.py`
- Log output: Console/application logs (no external log aggregation)

## CI/CD & Deployment

**Hosting:**
- Platform: Google Cloud Run (containerized)
- Deployment: Docker image built from `Dockerfile`
- Base image: `python:3.12-slim`
- Build process:
  - Copies `pyproject.toml` and `uv.lock` for dependency caching
  - Uses `uv sync --frozen --no-dev` for production dependency installation
  - Exposes port 8501 for Streamlit
  - Entry command: `uv run streamlit run frontend/main.py --server.port=8501 --server.address=0.0.0.0`

**CI Pipeline:**
- Not detected - no GitHub Actions, GitLab CI, or other CI service configured

## Environment Configuration

**Required env vars:**
- `DATABASE_URL` (required) - PostgreSQL connection string
- `FIREBASE_CREDENTIALS_PATH` (optional, default empty string) - Path to Firebase service account JSON
- `DEBUG` (optional, default False) - Enable debug mode

**Example .env:**
See `.env.example`:
```
DATABASE_URL=postgresql://finance:finance@localhost:5432/finance_tracker
FIREBASE_CREDENTIALS_PATH=
DEBUG=true
```

**Secrets location:**
- Local dev: `.env` file (git-ignored)
- Production: Google Cloud Run environment variables or Secret Manager
- Configuration loading: `app/config.py` via `pydantic-settings` BaseSettings class

## Webhooks & Callbacks

**Incoming:**
- None - Single user app with no external event triggers

**Outgoing:**
- None - No external API calls or webhooks triggered

## Google Cloud Integration

**Services Used:**
- Google Cloud Run - Application hosting
- Google Cloud SQL - PostgreSQL database instance (free-tier db-f1-micro)
- Google Cloud Secret Manager (planned) - For storing Firebase credentials and database passwords

**Docker Deployment:**
- Image built from `Dockerfile` in project root
- Container runs Streamlit server on port 8501
- Database connection via `DATABASE_URL` env var pointing to Cloud SQL PostgreSQL instance

---

*Integration audit: 2026-02-14*
