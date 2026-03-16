"""Account management page — date-based editable table."""

from datetime import date
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st

from app.database import get_session
from app.services.account_service import (
    delete_account_entry,
    list_account_types,
    list_non_pension_entries,
    upsert_account_entry,
)
from app.services.snapshot_service import capture_snapshot


def _get_user_id() -> str:
    return st.session_state["user_id"]


def render() -> None:
    """Render the accounts management page."""
    user_id = _get_user_id()

    session = next(get_session())
    try:
        account_types = list_account_types(session=session, user_id=user_id)
        entries = list_non_pension_entries(session=session, user_id=user_id)
    finally:
        session.close()

    non_pension_types = [at for at in account_types if not at.is_pension]
    type_name_to_id = {at.name: at.id for at in non_pension_types}
    type_id_to_name = {at.id: at.name for at in non_pension_types}
    type_names = [at.name for at in non_pension_types]

    latest_date = max((e.entry_date for e in entries), default=None)
    latest_total = sum(float(e.balance) for e in entries if e.entry_date == latest_date) if latest_date else 0.0
    label = f"Total Assets ({latest_date.strftime('%b %Y')})" if latest_date else "Total Assets"

    col, _ = st.columns([1, 3])
    with col:
        st.markdown(f"""
<div style="background: rgba(20, 167, 96, 0.10); border-radius: 12px; padding: 20px 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); min-height: 100px;">
    <div style="font-size: 13px; color: #8b949e; font-weight: 500; margin-bottom: 4px;">{label}</div>
    <div style="font-size: 26px; font-weight: 700; color: #e6edf3;">£{latest_total:,.2f}</div>
    <div style="font-size: 13px; margin-top: 4px; visibility: hidden;">-</div>
</div>
<div style="margin-bottom: 16px;"></div>
""", unsafe_allow_html=True)

    # Build DataFrame from existing entries
    rows = [
        {
            "_id": e.id,
            "Date": e.entry_date,
            "Month": e.entry_date.strftime("%b %Y"),
            "Type": type_id_to_name.get(e.account_type_id, ""),
            "Currency": e.currency,
            "Balance": float(e.balance),
            "Rate (to £)": float(e.exchange_rate),
        }
        for e in entries
    ]
    df = pd.DataFrame(rows, columns=["_id", "Date", "Month", "Type", "Currency", "Balance", "Rate (to £)"])

    column_config = {
        "_id": None,  # hidden
        "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
        "Month": st.column_config.TextColumn("Month", disabled=True),
        "Type": st.column_config.SelectboxColumn("Type", options=type_names, required=True),
        "Currency": st.column_config.TextColumn("Currency", max_chars=3),
        "Balance": st.column_config.NumberColumn("Balance", min_value=0, format="%.2f"),
        "Rate (to £)": st.column_config.NumberColumn("Rate (to £)", min_value=0, format="%.6f"),
    }

    st.caption(
        "Edit balances inline. One row per account type per date. "
        "For foreign currency accounts set Currency and Rate (to £). "
        "Use the checkbox column to delete rows."
    )

    edited = st.data_editor(
        df,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        key="accounts_editor",
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
                    affected = delete_account_entry(
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

                try:
                    balance = Decimal(str(row.get("Balance", 0) or 0))
                except InvalidOperation:
                    errors.append(f"Invalid balance for type '{type_name}' — skipping.")
                    continue

                currency = str(row.get("Currency") or "GBP").strip().upper() or "GBP"
                try:
                    exchange_rate = Decimal(str(row.get("Rate (to £)", 1) or 1))
                except InvalidOperation:
                    exchange_rate = Decimal("1")

                upsert_account_entry(
                    session=session,
                    user_id=user_id,
                    account_type_id=type_name_to_id[type_name],
                    entry_date=entry_date,
                    balance=balance,
                    currency=currency,
                    exchange_rate=exchange_rate,
                )
                affected_dates.add(entry_date)

            # Sync snapshots for each affected date
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

    if not entries:
        st.info("No accounts yet. Add a row above and save.")
