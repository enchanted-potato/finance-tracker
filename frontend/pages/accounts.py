"""Account management page — editable table."""

from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st

from app.database import get_session
from app.services.account_service import (
    create_account,
    deactivate_account,
    list_account_types,
    list_non_pension_accounts,
    update_balance,
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

    total = sum(a.balance for a in accounts)
    col, _ = st.columns([1, 3])
    with col:
        st.markdown(f"""
<div style="background: rgba(20, 167, 96, 0.10); border-radius: 12px; padding: 20px 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); min-height: 100px;">
    <div style="font-size: 13px; color: #555; font-weight: 500; margin-bottom: 4px;">Total Assets</div>
    <div style="font-size: 26px; font-weight: 700; color: #141413;">£{total:,.2f}</div>
    <div style="font-size: 13px; margin-top: 4px; visibility: hidden;">-</div>
</div>
<div style="margin-bottom: 16px;"></div>
""", unsafe_allow_html=True)

    # Build DataFrame from existing accounts
    rows = [
        {
            "_id": a.id,
            "Name": a.name,
            "Type": type_id_to_name.get(a.account_type_id, ""),
            "Balance (£)": float(a.balance),
        }
        for a in accounts
    ]
    df = pd.DataFrame(rows, columns=["_id", "Name", "Type", "Balance (£)"])

    column_config = {
        "_id": None,  # hidden
        "Name": st.column_config.TextColumn("Name", required=True),
        "Type": st.column_config.SelectboxColumn("Type", options=type_names, required=True),
        "Balance (£)": st.column_config.NumberColumn("Balance (£)", min_value=0, format="£%.2f"),
    }

    st.caption("Edit balances inline. Use the checkbox column to delete rows. Add rows at the bottom.")

    edited = st.data_editor(
        df,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        key="accounts_editor",
    )

    if st.button("Save changes", type="primary"):
        errors: list[str] = []
        changed = False

        session = next(get_session())
        try:
            # Detect deletions
            original_ids = set(df["_id"].dropna().astype(int))
            edited_ids = set(edited["_id"].dropna().astype(int)) if "_id" in edited.columns else set()
            deleted_ids = original_ids - edited_ids

            for del_id in deleted_ids:
                try:
                    deactivate_account(session=session, account_id=int(del_id), user_id=user_id)
                    changed = True
                except ValueError as exc:
                    errors.append(str(exc))

            # Update or create rows
            for _, row in edited.iterrows():
                name = row.get("Name", "")
                if not name or (isinstance(name, float) and pd.isna(name)):
                    errors.append("Row missing name — skipping.")
                    continue

                type_name = row.get("Type", "")
                if not type_name or type_name not in type_name_to_id:
                    errors.append(f"Unknown type '{type_name}' — skipping row.")
                    continue

                try:
                    balance = Decimal(str(row.get("Balance (£)", 0) or 0))
                except InvalidOperation:
                    errors.append(f"Invalid balance for '{name}' — skipping.")
                    continue

                raw_id = row.get("_id")
                if raw_id is None or (isinstance(raw_id, float) and pd.isna(raw_id)):
                    # New row
                    create_account(
                        session=session,
                        user_id=user_id,
                        account_type_id=type_name_to_id[type_name],
                        name=str(name),
                        balance=balance,
                    )
                    changed = True
                else:
                    account_id = int(raw_id)
                    original = next((a for a in accounts if a.id == account_id), None)
                    if original:
                        if original.name != str(name):
                            original.name = str(name)
                            session.add(original)
                            session.commit()
                            changed = True
                        if original.balance != balance:
                            update_balance(
                                session=session,
                                account_id=account_id,
                                user_id=user_id,
                                new_balance=balance,
                            )
                            changed = True

            if changed:
                capture_snapshot(session=session, user_id=user_id)

        finally:
            session.close()

        if errors:
            for err in errors:
                st.error(err)
        if changed:
            st.success("Saved.")
            st.rerun()

    if not accounts:
        st.info("No accounts yet. Add a row above and save.")
