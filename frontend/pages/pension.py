"""Pension account management — editable table."""

from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st

from app.database import get_session
from app.services.account_service import (
    _get_pension_type_id,
    create_account,
    deactivate_account,
    list_pension_accounts,
    update_balance,
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

    total = sum(a.balance for a in pension_accounts)
    col, _ = st.columns([1, 3])
    with col:
        st.markdown(f"""
<div style="background: rgba(100, 100, 100, 0.10); border-radius: 12px; padding: 20px 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); min-height: 100px;">
    <div style="font-size: 13px; color: #555; font-weight: 500; margin-bottom: 4px;">Total Pension</div>
    <div style="font-size: 26px; font-weight: 700; color: #141413;">£{total:,.2f}</div>
    <div style="font-size: 13px; margin-top: 4px; visibility: hidden;">-</div>
</div>
<div style="margin-bottom: 16px;"></div>
""", unsafe_allow_html=True)

    # Build DataFrame from existing accounts
    rows = [
        {"_id": a.id, "Provider": a.name, "Balance (£)": float(a.balance)}
        for a in pension_accounts
    ]
    df = pd.DataFrame(rows, columns=["_id", "Provider", "Balance (£)"])

    column_config = {
        "_id": None,  # hidden
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
                provider = row.get("Provider", "")
                if not provider or (isinstance(provider, float) and pd.isna(provider)):
                    errors.append("Row missing provider name — skipping.")
                    continue

                try:
                    balance = Decimal(str(row.get("Balance (£)", 0) or 0))
                except InvalidOperation:
                    errors.append(f"Invalid balance for '{provider}' — skipping.")
                    continue

                raw_id = row.get("_id")
                if raw_id is None or (isinstance(raw_id, float) and pd.isna(raw_id)):
                    # New row
                    create_account(
                        session=session,
                        user_id=user_id,
                        account_type_id=pension_type_id,
                        name=str(provider),
                        balance=balance,
                    )
                    changed = True
                else:
                    account_id = int(raw_id)
                    original = next((a for a in pension_accounts if a.id == account_id), None)
                    if original and (original.balance != balance or original.name != str(provider)):
                        if original.name != str(provider):
                            original.name = str(provider)
                            session.add(original)
                            session.commit()
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

    if not pension_accounts:
        st.info("No pension providers yet. Add a row above and save.")
