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
