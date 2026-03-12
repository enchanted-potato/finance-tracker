"""Pension account management — date-based editable table."""

from datetime import date
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st

from app.database import get_session
from app.services.account_service import (
    _get_pension_type_id,
    delete_account_entry,
    list_pension_accounts,
    upsert_account_entry,
)
from app.services.snapshot_service import capture_snapshot


def _get_user_id() -> str:
    return st.session_state["user_id"]


def render() -> None:
    """Render the pension management page."""
    user_id = _get_user_id()

    session = next(get_session())
    try:
        pension_type_id = _get_pension_type_id(session, user_id)
        pension_accounts = list_pension_accounts(session=session, user_id=user_id)
    finally:
        session.close()

    if pension_type_id is None:
        st.error("Pension account type not found. Please ensure the database is seeded.")
        return

    latest_date = max((a.entry_date for a in pension_accounts), default=None)
    latest_accounts = [a for a in pension_accounts if a.entry_date == latest_date] if latest_date else []
    latest_total = sum(float(a.balance) for a in latest_accounts)
    label = f"Total Pension ({latest_date.strftime('%b %Y')})" if latest_date else "Total Pension"

    col, _ = st.columns([1, 3])
    with col:
        st.markdown(f"""
<div style="background: rgba(100, 100, 100, 0.10); border-radius: 12px; padding: 20px 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); min-height: 100px;">
    <div style="font-size: 13px; color: #555; font-weight: 500; margin-bottom: 4px;">{label}</div>
    <div style="font-size: 26px; font-weight: 700; color: #141413;">£{latest_total:,.2f}</div>
    <div style="font-size: 13px; margin-top: 4px; visibility: hidden;">-</div>
</div>
<div style="margin-bottom: 16px;"></div>
""", unsafe_allow_html=True)

    # Build DataFrame from existing accounts
    rows = [
        {
            "_id": a.id,
            "Date": a.entry_date,
            "Month": a.entry_date.strftime("%b %Y"),
            "Provider": a.name,
            "Balance (£)": float(a.balance),
        }
        for a in pension_accounts
    ]
    df = pd.DataFrame(rows, columns=["_id", "Date", "Month", "Provider", "Balance (£)"])

    column_config = {
        "_id": None,  # hidden
        "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
        "Month": st.column_config.TextColumn("Month", disabled=True),
        "Provider": st.column_config.TextColumn("Provider", required=True),
        "Balance (£)": st.column_config.NumberColumn("Balance (£)", min_value=0, format="£%.2f"),
    }

    st.caption("Edit balances inline. Use the checkbox column to delete rows. Add rows at the bottom.")

    edited = st.data_editor(
        df,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        key="pension_editor",
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
                provider = row.get("Provider", "")
                if not provider or (isinstance(provider, float) and pd.isna(provider)):
                    errors.append("Row missing provider name — skipping.")
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
                    balance = Decimal(str(row.get("Balance (£)", 0) or 0))
                except InvalidOperation:
                    errors.append(f"Invalid balance for '{provider}' — skipping.")
                    continue

                upsert_account_entry(
                    session=session,
                    user_id=user_id,
                    name=str(provider),
                    account_type_id=pension_type_id,
                    entry_date=entry_date,
                    balance=balance,
                    currency="GBP",
                    exchange_rate=Decimal("1"),
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

    if not pension_accounts:
        st.info("No pension providers yet. Add a row above and save.")
