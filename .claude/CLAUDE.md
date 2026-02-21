# Finance Tracker (Net Worth Tracker)

## What this is
Personal net worth tracker — track asset accounts and liabilities over time with graphs. No transaction tracking.

## Stack
- Python, Streamlit, SQLModel, PostgreSQL, Firebase Auth, Plotly
- Deployed on Google Cloud Run + Cloud SQL (free tier)
- Package management: uv

## Architecture
- No REST API — Streamlit calls service functions directly
- Single user (deployed on cloud, but only one user)
- Daily snapshots with JSONB detail for historical net worth breakdown
- Firebase UID as users PK

## Commands
```bash
# Local dev
docker-compose up

# Run streamlit
python -m streamlit run frontend/main.py

# Run tests
pytest tests/

# Manage dependencies
uv sync
uv add <package>
```

## Code style
- SQLModel models in app/models.py (SQLModel = SQLAlchemy + Pydantic combined)
- Business logic in app/services/
- Streamlit pages in frontend/pages/
- Keep services independent of Streamlit (no st.* calls in services)

