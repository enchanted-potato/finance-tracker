---
phase: quick-4
plan: 4
type: execute
wave: 1
depends_on: []
files_modified:
  - app/models.py
  - app/services/liability_service.py
  - app/services/snapshot_service.py
  - frontend/pages/liabilities.py
  - scripts/migrate_liabilities.py
autonomous: true
requirements: [QUICK-4]

must_haves:
  truths:
    - "liability_entries table exists with unique constraint on (user_id, entry_date, liability_type_id)"
    - "old Liability model and liabilities table are no longer referenced in business logic"
    - "capture_snapshot() reads total_liabilities from liability_entries for the given date"
    - "liabilities page shows an editable st.data_editor table (Month, Date, Type, Amount)"
    - "saving edits syncs the snapshot for every affected date"
    - "total liabilities summary appears below the table"
  artifacts:
    - path: "app/models.py"
      provides: "LiabilityEntry SQLModel, Liability class removed"
    - path: "app/services/liability_service.py"
      provides: "CRUD for LiabilityEntry (upsert, list, delete by id)"
    - path: "app/services/snapshot_service.py"
      provides: "capture_snapshot reads liability_entries for given date"
    - path: "frontend/pages/liabilities.py"
      provides: "st.data_editor UI with inline edit, add row, delete, save"
    - path: "scripts/migrate_liabilities.py"
      provides: "one-shot script: create liability_entries table, drop liabilities table"
  key_links:
    - from: "frontend/pages/liabilities.py"
      to: "app/services/liability_service.py"
      via: "upsert_liability_entry / delete_liability_entry calls"
    - from: "frontend/pages/liabilities.py"
      to: "app/services/snapshot_service.py"
      via: "capture_snapshot(date=affected_date) after save"
    - from: "app/services/snapshot_service.py"
      to: "app/models.py LiabilityEntry"
      via: "select LiabilityEntry where user_id and entry_date == snapshot_date"
---

<objective>
Replace the named-liability account model with a date-keyed `liability_entries` table.
Each row records one (date, liability_type) balance. The liabilities page becomes an
inline-editable table; every save syncs the relevant snapshot.

Purpose: Enables historical liability tracking per type per date, matching how asset
snapshots already work.
Output: New LiabilityEntry model, rewritten service, updated snapshot logic, rewritten
UI page, and a migration script.
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/execute-plan.md
@./.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md

Key patterns from existing codebase:
- SQLModel models: `sa_column_kwargs={"server_default": sa_text("now()")}` for timestamps
- No FK constraint enforcement for user_id (string field, no DB-level FK — Phase 05 decision)
- Sessions obtained via `next(get_session())` in Streamlit pages, closed in finally block
- Services are pure Python, no st.* calls
- capture_snapshot() signature: `capture_snapshot(*, session, user_id, snapshot_date=None)`
  — when called from the UI after a liability edit, always pass the affected date explicitly

Existing models to keep: AccountType, Account, LiabilityType, Snapshot
Model to REMOVE: Liability (class + __tablename__ = "liabilities")
Model to ADD: LiabilityEntry (see Task 1)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add LiabilityEntry model, rewrite liability_service, update snapshot_service</name>
  <files>
    app/models.py
    app/services/liability_service.py
    app/services/snapshot_service.py
    scripts/migrate_liabilities.py
  </files>
  <action>
**app/models.py**

Remove the `Liability` class entirely (including its Index import reference).
Add `LiabilityEntry` after `LiabilityType`:

```python
from datetime import date as date_type  # add to imports

class LiabilityEntry(SQLModel, table=True):
    """One balance record per (user, date, liability_type)."""

    __tablename__ = "liability_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "entry_date", "liability_type_id"),
        {"extend_existing": True},
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(max_length=128)
    liability_type_id: int = Field(foreign_key="liability_types.id")
    entry_date: date_type = Field()
    amount: Decimal = Field(default=Decimal("0"), max_digits=14, decimal_places=2)
    currency: str = Field(default="GBP", max_length=3)
    created_at: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": sa_text("now()")},
    )
    updated_at: datetime = Field(
        default=None,
        sa_column_kwargs={
            "server_default": sa_text("now()"),
            "onupdate": sa_text("now()"),
        },
    )
```

Also remove the unused `Index` import if it is only used by `Liability`.

---

**app/services/liability_service.py**

Full replacement — keep `list_liability_types`, remove all old Liability CRUD.
New functions:

```python
def upsert_liability_entry(
    *, session, user_id, liability_type_id, entry_date, amount, currency="GBP"
) -> LiabilityEntry:
    """Insert or update a single liability entry.
    Uses the unique constraint (user_id, entry_date, liability_type_id).
    """
    existing = session.exec(
        select(LiabilityEntry).where(
            LiabilityEntry.user_id == user_id,
            LiabilityEntry.entry_date == entry_date,
            LiabilityEntry.liability_type_id == liability_type_id,
        )
    ).first()
    if existing:
        existing.amount = amount
        existing.currency = currency
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    entry = LiabilityEntry(
        user_id=user_id,
        liability_type_id=liability_type_id,
        entry_date=entry_date,
        amount=amount,
        currency=currency,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def delete_liability_entry(*, session, entry_id, user_id) -> None:
    """Hard-delete a liability entry. Raises ValueError if not found."""
    entry = session.exec(
        select(LiabilityEntry).where(
            LiabilityEntry.id == entry_id,
            LiabilityEntry.user_id == user_id,
        )
    ).first()
    if entry is None:
        raise ValueError(f"LiabilityEntry {entry_id} not found for user {user_id}")
    date_affected = entry.entry_date
    session.delete(entry)
    session.commit()
    return date_affected  # caller uses this to sync snapshot


def list_liability_entries(*, session, user_id) -> list[LiabilityEntry]:
    """All entries for a user, newest date first."""
    return list(
        session.exec(
            select(LiabilityEntry)
            .where(LiabilityEntry.user_id == user_id)
            .order_by(LiabilityEntry.entry_date.desc(), LiabilityEntry.liability_type_id)
        ).all()
    )
```

Keep `list_liability_types` unchanged.

---

**app/services/snapshot_service.py**

Update `capture_snapshot()`:
- Change import: remove `Liability`, add `LiabilityEntry`
- Replace the liabilities query block (lines 35-38):

```python
liabilities = list(
    session.exec(
        select(LiabilityEntry).where(
            LiabilityEntry.user_id == user_id,
            LiabilityEntry.entry_date == snapshot_date,
        )
    ).all()
)
```

- Update total_liabilities calculation: `lb.amount` instead of `lb.balance`
- Update detail_json liabilities list: use `lb.amount`, remove `lb.name` (not a field),
  use `"entry_date": str(lb.entry_date)` instead of `"name"`:

```python
"liabilities": [
    {
        "id": lb.id,
        "entry_date": str(lb.entry_date),
        "amount": str(lb.amount),
        "type_id": lb.liability_type_id,
    }
    for lb in liabilities
],
```

---

**scripts/migrate_liabilities.py**

One-shot migration script (run manually via `docker-compose exec app python scripts/migrate_liabilities.py`):

```python
"""Migration: create liability_entries table and drop liabilities table.

Run once against the live database. Safe to re-run (IF NOT EXISTS / IF EXISTS).
"""
from sqlalchemy import text
from app.database import engine
from app.models import SQLModel

def main():
    SQLModel.metadata.create_all(engine, checkfirst=True)  # creates liability_entries
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS liabilities CASCADE"))
        conn.commit()
    print("Migration complete: liability_entries created, liabilities dropped.")

if __name__ == "__main__":
    main()
```
  </action>
  <verify>
    <automated>cd /Users/kristiakarakatsani/Repos/finance-tracker && python -c "from app.models import LiabilityEntry, LiabilityType, Account, Snapshot; from app.services.liability_service import upsert_liability_entry, delete_liability_entry, list_liability_entries, list_liability_types; from app.services.snapshot_service import capture_snapshot; print('imports OK')"</automated>
  </verify>
  <done>
    - LiabilityEntry imported from app.models without error
    - Liability class no longer exists in app.models
    - capture_snapshot imports LiabilityEntry (not Liability)
    - All new service functions importable
    - Migration script exists and is runnable
  </done>
</task>

<task type="auto">
  <name>Task 2: Rewrite liabilities page with st.data_editor</name>
  <files>frontend/pages/liabilities.py</files>
  <action>
Full replacement. The page loads all entries + liability types, builds a DataFrame for
`st.data_editor`, and on save writes back only changed/new/deleted rows, then calls
`capture_snapshot` for each distinct affected date.

Implement as follows:

```python
"""Liability entries page — date-based editable table."""

import pandas as pd
import streamlit as st
from datetime import date

from app.database import get_session
from app.services.liability_service import (
    delete_liability_entry,
    list_liability_entries,
    list_liability_types,
    upsert_liability_entry,
)
from app.services.snapshot_service import capture_snapshot


def _get_user_id() -> str:
    return st.session_state["user_id"]


def render() -> None:
    st.header("Liabilities")
    user_id = _get_user_id()

    session = next(get_session())
    try:
        liability_types = list_liability_types(session=session, user_id=user_id)
        entries = list_liability_entries(session=session, user_id=user_id)
    finally:
        session.close()

    type_name_to_id = {lt.name: lt.id for lt in liability_types}
    type_id_to_name = {lt.id: lt.name for lt in liability_types}
    type_names = [lt.name for lt in liability_types]

    # Build DataFrame from existing entries
    rows = []
    for e in entries:
        rows.append({
            "_id": e.id,
            "Month": e.entry_date.strftime("%b %Y"),
            "Date": e.entry_date.strftime("%d/%m/%Y"),
            "_entry_date": e.entry_date,
            "Type": type_id_to_name.get(e.liability_type_id, ""),
            "Amount (£)": float(e.amount),
        })

    df = pd.DataFrame(rows, columns=["_id", "Month", "Date", "_entry_date", "Type", "Amount (£)"])

    # Column config for data_editor
    column_config = {
        "_id": None,            # hidden
        "_entry_date": None,    # hidden
        "Month": st.column_config.TextColumn("Month", disabled=True),
        "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
        "Type": st.column_config.SelectboxColumn("Type", options=type_names, required=True),
        "Amount (£)": st.column_config.NumberColumn("Amount (£)", min_value=0, format="£%.2f"),
    }

    st.caption("Edit amounts inline. Use the checkbox column to delete rows. Add rows at the bottom.")

    edited = st.data_editor(
        df,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        key="liabilities_editor",
    )

    if st.button("Save changes", type="primary"):
        affected_dates: set[date] = set()
        errors: list[str] = []

        session = next(get_session())
        try:
            # Detect deletions: rows in original df not in edited (by _id)
            original_ids = set(df["_id"].dropna().astype(int))
            edited_ids = set(edited["_id"].dropna().astype(int)) if "_id" in edited.columns else set()
            deleted_ids = original_ids - edited_ids

            for del_id in deleted_ids:
                try:
                    affected = delete_liability_entry(
                        session=session, entry_id=int(del_id), user_id=user_id
                    )
                    if affected:
                        affected_dates.add(affected)
                except ValueError as exc:
                    errors.append(str(exc))

            # Upsert all rows in edited df
            for _, row in edited.iterrows():
                type_name = row.get("Type", "")
                if not type_name or type_name not in type_name_to_id:
                    errors.append(f"Unknown type '{type_name}' — skipping row.")
                    continue

                # Parse date from "Date" column (data_editor returns date objects for DateColumn)
                raw_date = row.get("Date") or row.get("_entry_date")
                if raw_date is None:
                    errors.append("Row missing date — skipping.")
                    continue
                if isinstance(raw_date, str):
                    try:
                        from datetime import datetime as _dt
                        raw_date = _dt.strptime(raw_date, "%d/%m/%Y").date()
                    except ValueError:
                        errors.append(f"Could not parse date '{raw_date}' — skipping.")
                        continue
                entry_date = raw_date if isinstance(raw_date, date) else raw_date.date()

                amount = row.get("Amount (£)", 0) or 0
                from decimal import Decimal
                upsert_liability_entry(
                    session=session,
                    user_id=user_id,
                    liability_type_id=type_name_to_id[type_name],
                    entry_date=entry_date,
                    amount=Decimal(str(amount)),
                )
                affected_dates.add(entry_date)

            # Sync snapshot for each affected date
            for snap_date in affected_dates:
                capture_snapshot(session=session, user_id=user_id, snapshot_date=snap_date)

        finally:
            session.close()

        if errors:
            for err in errors:
                st.error(err)
        if affected_dates:
            st.success(f"Saved. Snapshots updated for {len(affected_dates)} date(s).")
            st.rerun()

    # Summary
    if not entries:
        st.info("No liabilities yet. Add a row above and save.")
    else:
        total = sum(float(e.amount) for e in entries)
        # Show total for most recent date only (most useful summary)
        latest_date = max(e.entry_date for e in entries)
        latest_total = sum(float(e.amount) for e in entries if e.entry_date == latest_date)
        st.metric(
            f"Total Liabilities ({latest_date.strftime('%b %Y')})",
            f"£{latest_total:,.2f}",
        )
```

Note: `st.data_editor` with `num_rows="dynamic"` adds a "+" row at the bottom automatically.
Deleted rows are tracked by comparing original `_id` set vs edited `_id` set — rows removed
by the user will have their `_id` absent from the edited DataFrame.
  </action>
  <verify>
    <automated>cd /Users/kristiakarakatsani/Repos/finance-tracker && python -c "import ast, sys; ast.parse(open('frontend/pages/liabilities.py').read()); print('syntax OK')"</automated>
  </verify>
  <done>
    - liabilities.py parses without syntax errors
    - Imports reference LiabilityEntry service functions (not old Liability ones)
    - st.data_editor used with num_rows="dynamic"
    - Save button calls capture_snapshot for each affected date
    - Total liabilities metric shown for most recent date
  </done>
</task>

</tasks>

<verification>
After both tasks:

1. `python -c "from app.models import LiabilityEntry; print(LiabilityEntry.__tablename__)"` prints `liability_entries`
2. `python -c "from app.models import Liability"` raises ImportError (class removed)
3. `python -c "from frontend.pages.liabilities import render; print('ok')"` succeeds
4. Run migration: `python scripts/migrate_liabilities.py` — prints "Migration complete"
5. Start app (`docker-compose up`) and navigate to Liabilities page — data_editor table loads, add/edit/delete row, click Save, snapshot syncs for that date
</verification>

<success_criteria>
- liability_entries table is the sole source for liability data
- Liabilities page renders an editable table with Month, Date, Type, Amount columns
- Saving changes persists to DB and updates the snapshot for each affected date
- No reference to old `Liability` model or `liabilities` table in service/UI code
- Migration script drops the old table cleanly
</success_criteria>

<output>
After completion, create `.planning/quick/4-refactor-liabilities-to-new-liability-en/4-SUMMARY.md`
</output>
