# Technology Stack

**Analysis Date:** 2026-02-14

## Languages

**Primary:**
- Python 3.12 - All backend and frontend code (Streamlit is Python-based)

## Runtime

**Environment:**
- Python 3.12.x (pinned in `.python-version`)

**Package Manager:**
- uv (modern Python package manager)
- Lockfile: `uv.lock` present
- Dependency declaration: `pyproject.toml`

## Frameworks

**Core:**
- Streamlit - Web UI framework for data apps
- SQLModel - ORM combining SQLAlchemy and Pydantic for database models

**UI & Visualization:**
- Plotly - Interactive charts and graphs (imported as `plotly.graph_objects`)
- Pandas - Data manipulation and analysis

**Testing:**
- pytest - Test runner
- pytest-mock - Mocking framework for tests

**Build/Dev:**
- Ruff - Python linter and formatter
- mypy - Static type checker (dev dependency)

**Logging:**
- loguru - Structured logging

**Configuration:**
- pydantic-settings - Environment variable management with type validation

## Key Dependencies

**Critical:**
- `streamlit` - Web framework for Streamlit application (`frontend/main.py`, `frontend/pages/*.py`)
- `sqlmodel` - Database ORM used in `app/models.py` and all service layers (`app/services/`)
- `psycopg2-binary` - PostgreSQL database driver for SQLModel connections
- `firebase-admin` - Firebase Authentication SDK (currently declared but not yet integrated; see `app/config.py`)
- `plotly` - Interactive visualization library used in `frontend/pages/dashboard.py` and `frontend/pages/history.py`

**Infrastructure:**
- `pandas` - Data processing used in `app/services/snapshot_service.py` for CSV operations
- `loguru` - Logging in service functions (`app/services/account_service.py`, `app/services/snapshot_service.py`, `app/services/liability_service.py`)
- `pydantic-settings` - Configuration loading from `.env` file in `app/config.py`

## Configuration

**Environment:**
- `.env` file loaded at runtime via `pydantic-settings`
- Configuration class: `Settings` in `app/config.py`

**Key configs required:**
- `DATABASE_URL` - PostgreSQL connection string (format: `postgresql://user:password@host:port/dbname`)
- `FIREBASE_CREDENTIALS_PATH` - Path to Firebase service account JSON (optional in current test phase)
- `DEBUG` - Boolean flag for debug mode (default: False)

**Build:**
- `pyproject.toml` - Project metadata and dependency groups
- `Dockerfile` - Multi-stage Docker build using Python 3.12-slim base image
- `docker-compose.yml` - Local development environment (PostgreSQL + Streamlit app)

## Platform Requirements

**Development:**
- Python 3.12+
- Docker & Docker Compose (for local development with `docker-compose up`)
- uv package manager

**Production:**
- Google Cloud Run (containerized deployment)
- Google Cloud SQL (PostgreSQL, free-tier `db-f1-micro`)
- Docker container image built from `Dockerfile`

**Deployment Commands:**
- Local dev: `docker-compose up`
- Streamlit dev: `uv run streamlit run frontend/main.py`
- Tests: `pytest tests/`
- Dependency management: `uv sync`, `uv add <package>`

---

*Stack analysis: 2026-02-14*
