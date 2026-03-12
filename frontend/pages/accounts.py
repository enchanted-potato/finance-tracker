"""Account management page — date-based editable table."""

from datetime import date
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st

from app.database import get_session
from app.services.account_service import (
    delete_account_entry,
    list_account_types,
    list_non_pension_accounts,
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
        accounts = list_non_pension_accounts(session=session, user_id=user_id)
    finally:
        session.close()

    non_pension_types = [at for at in account_types if at.name != "Pension"]
    type_name_to_id = {at.name: at.id for at in non_pension_types}
    type_id_to_name = {at.id: at.name for at in non_pension_types}
    type_names = [at.name for at in non_pension_types]

    latest_date = max((a.entry_date for a in accounts), default=None)
    latest_accounts = [a for a in accounts if a.entry_date == latest_date] if latest_date else []
    latest_total = sum(float(a.balance * a.exchange_rate) for a in latest_accounts)
    label = f"Total Assets ({latest_date.strftime('%b %Y')})" if latest_date else "Total Assets"

    col, _ = st.columns([1, 3])
    with col:
        st.markdown(f"""
<div style="background: rgba(20, 167, 96, 0.10); border-radius: 12px; padding: 20px 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); min-height: 100px;">
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
            "Name": a.name,
            "Type": type_id_to_name.get(a.account_type_id, ""),
            "Balance": float(a.balance),
            "Currency": a.currency,
            "Rate (to GBP)": float(a.exchange_rate),
        }
        for a in accounts
    ]
    df = pd.DataFrame(rows, columns=["_id", "Date", "Month", "Name", "Type", "Balance", "Currency", "Rate (to GBP)"])

    column_config = {
        "_id": None,  # hidden
        "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
        "Month": st.column_config.TextColumn("Month", disabled=True),
        "Name": st.column_config.TextColumn("Name", required=True),
        "Type": st.column_config.SelectboxColumn("Type", options=type_names, required=True),
        "Balance": st.column_config.NumberColumn("Balance", min_value=0, format="%.2f"),
        "Currency": st.column_config.TextColumn("Currency", help="ISO 4217 code, e.g. GBP, EUR, USD"),
        "Rate (to GBP)": st.column_config.NumberColumn(
            "Rate (to GBP)",
            min_value=0,
            format="%.6f",
            help="Exchange rate: 1 unit of this currency = X GBP. Use 1.0 for GBP accounts.",
        ),
    }

    st.caption(
        "Edit balances inline. Set Currency + Rate for foreign accounts "
        "(e.g. EUR balance × rate = GBP contribution to net worth). "
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
                name = row.get("Name", "")
                if not name or (isinstance(name, float) and pd.isna(name)):
                    errors.append("Row missing name — skipping.")
                    continue

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
                    errors.append(f"Invalid balance for '{name}' — skipping.")
                    continue

                raw_currency = row.get("Currency", "GBP")
                currency = str(raw_currency).strip().upper() if raw_currency else "GBP"
                if not currency:
                    currency = "GBP"

                try:
                    exchange_rate = Decimal(str(row.get("Rate (to GBP)", 1) or 1))
                    if exchange_rate <= 0:
                        errors.append(f"Exchange rate for '{name}' must be positive — skipping.")
                        continue
                except InvalidOperation:
                    errors.append(f"Invalid exchange rate for '{name}' — skipping.")
                    continue

                upsert_account_entry(
                    session=session,
                    user_id=user_id,
                    name=str(name),
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

    if not accounts:
        st.info("No accounts yet. Add a row above and save.")
