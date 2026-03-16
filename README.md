# Worth Flow

A personal net worth tracker — record asset balances and liabilities over time, visualize trends, and understand your financial position at a glance. No transaction tracking; just clean snapshots.

## Features

- Track asset accounts (cash savings, investments, pension) with daily balance snapshots
- Track liabilities (mortgage, loans, credit cards)
- Interactive charts: net worth trend, asset allocation, liability breakdown, pension breakdown
- Backfill historical balances for any date
- CSV import/export for snapshot history
- Pension accounts tracked separately (excluded from net worth calculation)
- Custom account and liability types
- Single-user, privacy-first — no multi-tenant infrastructure

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit (Python) |
| ORM | SQLModel (SQLAlchemy + Pydantic) |
| Database | PostgreSQL 15 |
| Auth | Firebase Admin SDK + Google OAuth |
| Charts | Plotly |
| Package manager | uv |
| Infrastructure | Google Cloud Run + Cloud SQL |
| IaC | Terraform |

## Architecture

```
┌─────────────────────────────────────┐
│           Streamlit Frontend        │
│  main.py → auth gate → sidebar nav  │
│  pages: dashboard, accounts,        │
│         liabilities, pension,       │
│         history, configure          │
└──────────────┬──────────────────────┘
               │ direct function calls (no REST API)
┌──────────────▼──────────────────────┐
│           App Services              │
│  auth_service  snapshot_service     │
│  account_service  liability_service │
│  type_service                       │
└──────────────┬──────────────────────┘
               │ SQLModel / SQLAlchemy
┌──────────────▼──────────────────────┐
│           PostgreSQL                │
│  AccountType  AccountEntry          │
│  LiabilityType  LiabilityEntry      │
│  Snapshot (JSONB detail)            │
└─────────────────────────────────────┘
```

**No REST API.** Streamlit pages call service functions directly. This keeps the stack simple and avoids unnecessary HTTP overhead for a single-user app.

**Snapshots, not transactions.** Each day you record a balance per account. A `Snapshot` row captures the full net worth breakdown (assets, liabilities, detail JSON) for that date. Trends come from querying snapshot history — no ledger reconciliation required.

## Data Model

```
AccountType          LiabilityType
  id                   id
  name                 name
  user_id (nullable)   user_id (nullable)
  is_pension           ─────────────────
  ─────────────────       ↓ has many
     ↓ has many       LiabilityEntry
  AccountEntry           id
    id                   user_id
    user_id              entry_date
    entry_date           liability_type_id
    account_type_id      amount
    balance
    currency          Snapshot
    exchange_rate        id
                         user_id
                         snapshot_date
                         total_assets
                         total_liabilities
                         net_worth
                         detail_json (JSONB)
```

- `AccountType` and `LiabilityType` rows with `user_id = NULL` are system defaults seeded at startup.
- Users can create custom types (stored with their `user_id`).
- `Snapshot.detail_json` stores a full breakdown of all account/liability values at the time of capture.

## Local Development

**Prerequisites:** Docker, Python 3.12+, [uv](https://docs.astral.sh/uv/)

```bash
# Clone and install dependencies
git clone <repo>
uv sync

# Start PostgreSQL and Streamlit
docker ocompose up
```

App runs at `http://localhost:8501`. Authentication is bypassed in local dev via `DEV_USER_ID`.

**Environment variables (`.env`):**

```env
DATABASE_URL=postgresql://finance:finance@db:5432/finance_tracker
DEV_USER_ID=local-dev-user          # bypasses Firebase auth locally
DEBUG=true

# Firebase (local dev only — Cloud Run uses ADC, no key file needed)
FIREBASE_CREDENTIALS_PATH=path/to/serviceAccountKey.json
FIREBASE_WEB_API_KEY=
FIREBASE_AUTH_DOMAIN=
FIREBASE_PROJECT_ID=

# Optional: restrict access to a single Firebase UID
ALLOWED_FIREBASE_UID=
```

**Run tests:**

```bash
pytest tests/
```

Tests use an in-memory SQLite session and mocked Firebase — no running database required.

## Authentication

```
Browser                    Streamlit                Firebase
  │                            │                       │
  │── opens app ──────────────>│                       │
  │<─ shows login button ──────│                       │
  │── clicks Google Sign-In ──>│                       │
  │<────────────── OAuth redirect ──────────────────── │
  │── ID token ───────────────>│                       │
  │                            │── verify token ──────>│
  │                            │<─ decoded claims ──── │
  │                            │  stores in session     │
  │<─ authenticated app ───────│                       │
```

- In **local dev**, set `DEV_USER_ID` to skip Firebase entirely.
- In **production**, the frontend renders a custom React component (`/frontend/auth_component/`) that handles Google OAuth and returns the Firebase ID token to the Streamlit backend.
- `ALLOWED_FIREBASE_UID` locks the app to a single user — anyone else is rejected after token verification.
- The token is stored in Streamlit session state so navigating between pages doesn't trigger re-authentication.

## Cloud Deployment

### Infrastructure Overview

```
Google Cloud
├── Cloud Run          — Streamlit app (scales to 0 when idle)
├── Cloud SQL          — PostgreSQL 15 (db-f1-micro, 10 GB HDD)
├── Cloud Scheduler    — Start/stop Cloud SQL on a schedule
├── Artifact Registry  — Docker images
└── IAM                — Service accounts, no passwords
```

All infrastructure is managed with Terraform in `/terraform/`.

### Deploy

```bash
# Build and push image
docker build --platform linux/amd64 -t gcr.io/<PROJECT>/finance-tracker:latest .
docker push gcr.io/<PROJECT>/finance-tracker:latest

# Deploy to Cloud Run
gcloud run deploy finance-tracker \
  --image gcr.io/<PROJECT>/finance-tracker:latest \
  --region us-central1

# Or use the justfile shortcut
just deploy
```

### Terraform

```bash
cd terraform
terraform init
terraform apply
```

## Cost Saving Strategies

Running this on GCP can be nearly free with a few deliberate choices:

### 1. Cloud Run scales to zero
Cloud Run only charges for actual request processing time. When nobody is using the app, it scales to zero instances and costs nothing.

### 2. Cloud SQL scheduled start/stop
Cloud SQL charges for uptime regardless of queries. A `db-f1-micro` instance costs ~$7–9/month if left running 24/7. Two Cloud Scheduler jobs (free tier) cut this significantly:

| Job | Schedule | Action |
|---|---|---|
| `start-db` | 8:00 AM (Europe/London) | Activate Cloud SQL instance |
| `stop-db` | 11:00 PM (Europe/London) | Deactivate Cloud SQL instance |

This limits the database to ~15 hours/day, reducing the monthly cost to ~$4–5.

### 3. Free tier resources
- **Cloud SQL**: `db-f1-micro`, HDD storage, no automated backups
- **Cloud Run**: 2M requests/month free; 360,000 GB-seconds free
- **Cloud Scheduler**: 3 jobs/month free
- **Artifact Registry**: 0.5 GB free storage

### 4. IAM database authentication
Using IAM auth instead of a password removes the need to rotate credentials and eliminates one attack surface. The Cloud Run service account is granted `roles/cloudsql.client` — no password stored anywhere.

## Security

### Authentication & Authorization
- Firebase Auth handles identity — no passwords stored in this application
- `ALLOWED_FIREBASE_UID` restricts access to a single Firebase UID; all other authenticated users are rejected
- ID tokens are verified server-side on every session using the Firebase Admin SDK

### Database
- IAM authentication — the Cloud Run service account connects without a password
- Cloud SQL has no public IP; connections go through the Cloud SQL Auth Proxy
- Minimum required IAM roles: `roles/cloudsql.client` (connect), `roles/cloudsql.editor` (start/stop via Scheduler)

### Secrets management
- No secrets in code or Docker images
- Local dev uses a `.env` file (gitignored)
- Production uses Cloud Run environment variables set at deploy time
- Firebase service account key is only used locally; Cloud Run uses Application Default Credentials (ADC)

## Project Structure

```
├── app/
│   ├── models.py           # SQLModel table definitions
│   ├── database.py         # Engine + session factory
│   ├── config.py           # Settings from env vars
│   ├── seed.py             # Default account/liability types
│   └── services/
│       ├── auth_service.py
│       ├── snapshot_service.py
│       ├── account_service.py
│       ├── liability_service.py
│       └── type_service.py
├── frontend/
│   ├── main.py             # Entry point, auth gate, navigation
│   ├── auth_component/     # Custom React Firebase login component
│   └── pages/
│       ├── dashboard.py
│       ├── accounts.py
│       ├── liabilities.py
│       ├── pension.py
│       ├── history.py
│       └── configure.py
├── terraform/              # GCP infrastructure (Cloud Run, Cloud SQL, Scheduler)
├── tests/                  # Pytest tests
├── Dockerfile
├── docker-compose.yml      # Local dev
├── pyproject.toml
└── justfile                # Command shortcuts (just dev, just deploy)
```
