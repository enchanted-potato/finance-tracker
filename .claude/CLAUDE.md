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

## Known issues / conventions

### No `st.expander()` — use toggle buttons instead
The global CSS in `main.py` applies Poppins font via `*:not(.material-icons)`, which overrides the Material Symbols Rounded font that Streamlit uses to render expander arrow icons. This causes the raw ligature text (e.g. `_arrow_down`) to appear instead of an arrow symbol.

**Fix:** Use a session-state toggle button with plain Unicode `▼`/`▲` characters instead of `st.expander()`. These render correctly in any font. See `frontend/pages/history.py` and `frontend/pages/goals.py` for examples.

