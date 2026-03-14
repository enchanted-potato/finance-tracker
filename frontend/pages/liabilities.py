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
from app.services.snapshot_service import get_snapshot_history, sync_snapshot_liabilities


def _get_user_id() -> str:
    return st.session_state["user_id"]


def render() -> None:
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

    latest_date = max((e.entry_date for e in entries), default=None)
    latest_total = sum(float(e.amount) for e in entries if e.entry_date == latest_date) if latest_date else 0.0
    label = f"Total Liabilities ({latest_date.strftime('%b %Y')})" if latest_date else "Total Liabilities"
    col, _ = st.columns([1, 3])
    with col:
        st.markdown(f"""
<div style="background: rgba(232, 33, 33, 0.10); border-radius: 12px; padding: 20px 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); min-height: 100px;">
    <div style="font-size: 13px; color: #8b949e; font-weight: 500; margin-bottom: 4px;">{label}</div>
    <div style="font-size: 26px; font-weight: 700; color: #e6edf3;">£{latest_total:,.2f}</div>
    <div style="font-size: 13px; margin-top: 4px; visibility: hidden;">-</div>
</div>
<div style="margin-bottom: 16px;"></div>
""", unsafe_allow_html=True)

    # Build DataFrame from existing entries
    rows = []
    for e in entries:
        rows.append({
            "_id": e.id,
            "Date": e.entry_date,
            "Month": e.entry_date.strftime("%b %Y"),
            "Type": type_id_to_name.get(e.liability_type_id, ""),
            "Amount (£)": float(e.amount),
        })

    df = pd.DataFrame(rows, columns=["_id", "Date", "Month", "Type", "Amount (£)"])

    # Column config for data_editor
    column_config = {
        "_id": None,            # hidden
        "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
        "Month": st.column_config.TextColumn("Month", disabled=True),
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

                # Parse date — DateColumn returns date objects, strings, or Timestamps
                raw_date = row.get("Date")
                if raw_date is None or (isinstance(raw_date, float) and pd.isna(raw_date)):
                    errors.append("Row missing date — skipping.")
                    continue
                if isinstance(raw_date, str):
                    from datetime import datetime as _dt
                    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                        try:
                            raw_date = _dt.strptime(raw_date, fmt).date()
                            break
                        except ValueError:
                            continue
                    else:
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

            # Also recapture any later snapshots in the same months so the History page
            # (which shows the latest snapshot per month) reflects the change.
            all_snapshots = get_snapshot_history(session=session, user_id=user_id)
            for snap in all_snapshots:
                snap_date = snap.snapshot_date.date()
                for affected_date in list(affected_dates):
                    if (
                        snap_date.year == affected_date.year
                        and snap_date.month == affected_date.month
                        and snap_date > affected_date
                    ):
                        affected_dates.add(snap_date)

            for snap_date in affected_dates:
                sync_snapshot_liabilities(session=session, user_id=user_id, snapshot_date=snap_date)

        finally:
            session.close()

        if errors:
            for err in errors:
                st.error(err)
        if affected_dates:
            st.success(f"Saved. Snapshots updated for {len(affected_dates)} date(s).")
            st.rerun()

    if not entries:
        st.info("No liabilities yet. Add a row above and save.")
