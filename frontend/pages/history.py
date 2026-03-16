import csv
import io
from decimal import Decimal

import streamlit as st

from app.database import get_session
from app.services.snapshot_service import (
    delete_snapshot,
    get_snapshot_history,
    import_csv_liabilities,
    import_csv_snapshots,
    update_snapshot,
)


def _get_user_id() -> str:
    return st.session_state["user_id"]


def _inject_styles() -> None:
    st.markdown(
        """
        <style>

        /* Table header */
        .hist-header {
            display: grid;
            grid-template-columns: 14% 18% 18% 18% 18% 14%;
            padding: 10px 4px;
            border-bottom: 1px solid rgba(230,237,243,0.12);
            margin-bottom: 2px;
        }
        .hist-th {
            font-family: monospace;
            font-size: 10px;
            letter-spacing: 0.12em;
            color: #8b949e;
            text-transform: uppercase;
            font-weight: 500;
        }
        .hist-th.right { text-align: right; padding-right: 8px; }

        /* Year divider */
        .year-divider {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 18px 0 6px 0;
        }
        .year-label {
            font-family: monospace;
            font-size: 11px;
            color: #58a6ff;
            letter-spacing: 0.18em;
            font-weight: 600;
        }
        .year-line {
            flex: 1;
            height: 1px;
            background: rgba(230,237,243,0.1);
        }

        /* Tighten Streamlit's default block gap between rows */
        [data-testid="stHorizontalBlock"] {
            gap: 0 !important;
        }
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }
        [data-testid="column"] > [data-testid="stVerticalBlockBorderWrapper"] > div > [data-testid="stVerticalBlock"] {
            gap: 0 !important;
        }
        /* Remove padding from column children */
        [data-testid="stColumn"] > div {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }
        /* Shrink button height */
        [data-testid="stButton"] button {
            padding-top: 2px !important;
            padding-bottom: 2px !important;
            min-height: 0 !important;
            line-height: 1.2 !important;
        }

        /* Cell styles */
        .cell-date {
            font-family: monospace;
            font-size: 13px;
            color: #8b949e;
            font-weight: 500;
            padding: 6px 4px;
        }
        .cell-money {
            font-family: monospace;
            font-size: 13px;
            color: #e6edf3;
            text-align: right;
            padding: 6px 8px 6px 4px;
        }
        .cell-nw {
            font-family: monospace;
            font-size: 13px;
            color: #e6edf3;
            font-weight: 600;
            text-align: right;
            padding: 6px 8px 6px 4px;
        }
        .cell-badge {
            text-align: right;
            padding: 6px 8px 6px 4px;
        }

        /* Change badges */
        .badge-pos {
            display: inline-block;
            font-family: monospace;
            font-size: 12px;
            font-weight: 500;
            color: #3fb950;
            background: rgba(63,185,80,0.12);
            padding: 3px 8px;
            border-radius: 3px;
        }
        .badge-neg {
            display: inline-block;
            font-family: monospace;
            font-size: 12px;
            font-weight: 500;
            color: #f85149;
            background: rgba(248,81,73,0.12);
            padding: 3px 8px;
            border-radius: 3px;
        }
        .badge-neu {
            display: inline-block;
            font-family: monospace;
            font-size: 12px;
            color: rgba(230,237,243,0.35);
            background: rgba(230,237,243,0.05);
            padding: 3px 8px;
            border-radius: 3px;
        }

        /* Row separator */
        .row-sep {
            border: none;
            border-top: 1px solid rgba(230,237,243,0.07);
            margin: 2px 0;
        }

        /* Detail panel */
        .detail-wrap {
            background: rgba(230,237,243,0.04);
            border-radius: 6px;
            padding: 14px 18px;
            margin: 2px 0 6px 0;
        }
        .detail-title {
            font-family: monospace;
            font-size: 10px;
            letter-spacing: 0.14em;
            color: #8b949e;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .detail-row {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid rgba(230,237,243,0.06);
            font-size: 13px;
        }
        .detail-row:last-child { border-bottom: none; }
        .detail-name { color: #8b949e; }
        .detail-val {
            font-family: monospace;
            color: #e6edf3;
        }
        .detail-suffix {
            color: rgba(230,237,243,0.35);
            font-size: 11px;
            margin-left: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _change_badge(current: Decimal | None, previous: Decimal | None) -> str:
    if current is None or previous is None:
        return '<span class="badge-neu">—</span>'
    delta = current - previous
    if delta > 0:
        return f'<span class="badge-pos">+£{delta:,.0f}</span>'
    if delta < 0:
        return f'<span class="badge-neg">−£{abs(delta):,.0f}</span>'
    return '<span class="badge-neu">£0</span>'


@st.dialog("Edit Snapshot")
def _edit_modal(snap, user_id: str) -> None:
    st.markdown(
        f"<span style='font-family:IBM Plex Mono,monospace;color:#58a6ff;font-size:14px'>"
        f"{snap.snapshot_date.strftime('%B %Y')}</span>",
        unsafe_allow_html=True,
    )
    st.markdown("")

    new_assets = st.number_input(
        "Total Assets",
        value=float(snap.total_assets) if snap.total_assets is not None else 0.0,
        step=100.0,
        format="%.2f",
    )
    no_liabilities = st.checkbox(
        "No liabilities data",
        value=snap.total_liabilities is None,
    )
    new_liabilities = None
    if not no_liabilities:
        new_liabilities = st.number_input(
            "Total Liabilities",
            value=float(snap.total_liabilities) if snap.total_liabilities is not None else 0.0,
            step=100.0,
            format="%.2f",
        )

    st.markdown("")
    col_save, col_delete = st.columns([2, 1])
    with col_save:
        if st.button("Save changes", type="primary", use_container_width=True):
            with next(get_session()) as session:
                update_snapshot(
                    session=session,
                    snapshot_id=snap.id,
                    total_assets=Decimal(str(new_assets)),
                    total_liabilities=Decimal(str(new_liabilities)) if new_liabilities is not None else None,
                )
            st.rerun()
    with col_delete:
        if st.button("Delete", use_container_width=True):
            with next(get_session()) as session:
                delete_snapshot(session=session, snapshot_id=snap.id, user_id=user_id)
            st.rerun()


def render() -> None:
    """Render the history page."""
    _inject_styles()
    st.header("Net Worth History")
    user_id = _get_user_id()

    session = next(get_session())
    try:
        snapshots = get_snapshot_history(session=session, user_id=user_id)
    finally:
        session.close()

    if not snapshots:
        st.info(
            "No snapshots yet. Update an account or liability balance "
            "to create your first snapshot."
        )

    snapshots_desc = _latest_per_month(snapshots) if snapshots else []

    # Table column header
    st.markdown(
        """
        <div class="hist-header">
          <div class="hist-th">Month</div>
          <div class="hist-th right">Assets</div>
          <div class="hist-th right">Liabilities</div>
          <div class="hist-th right">Net Worth</div>
          <div class="hist-th right">Change</div>
          <div class="hist-th"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    current_year = None
    for i, snap in enumerate(snapshots_desc):
        year = snap.snapshot_date.year
        if year != current_year:
            current_year = year
            st.markdown(
                f'<div class="year-divider">'
                f'<span class="year-label">{year}</span>'
                f'<div class="year-line"></div>'
                f"</div>",
                unsafe_allow_html=True,
            )

        previous_nw = snapshots_desc[i + 1].net_worth if i + 1 < len(snapshots_desc) else None
        badge = _change_badge(snap.net_worth, previous_nw)

        assets_str = f"£{snap.total_assets:,.2f}" if snap.total_assets is not None else "—"
        liab_str = f"£{snap.total_liabilities:,.2f}" if snap.total_liabilities is not None else "—"
        nw_str = f"£{snap.net_worth:,.2f}" if snap.net_worth is not None else "—"

        col_date, col_assets, col_liab, col_nw, col_change, col_btns = st.columns(
            [2.2, 2.2, 2.2, 2.2, 2.2, 2]
        )
        col_date.markdown(f'<div class="cell-date">{snap.snapshot_date.strftime("%b %Y")}</div>', unsafe_allow_html=True)
        col_assets.markdown(f'<div class="cell-money">{assets_str}</div>', unsafe_allow_html=True)
        col_liab.markdown(f'<div class="cell-money">{liab_str}</div>', unsafe_allow_html=True)
        col_nw.markdown(f'<div class="cell-nw">{nw_str}</div>', unsafe_allow_html=True)
        col_change.markdown(f'<div class="cell-badge">{badge}</div>', unsafe_allow_html=True)

        with col_btns:
            btn_col_edit, btn_col_det = st.columns(2)
            if btn_col_edit.button("Edit", key=f"edit_{snap.id}", use_container_width=True):
                _edit_modal(snap, user_id)

            show_key = f"show_{snap.id}"
            if show_key not in st.session_state:
                st.session_state[show_key] = False
            det_label = "▲" if st.session_state[show_key] else "▼"
            if btn_col_det.button(det_label, key=f"det_{snap.id}", use_container_width=True):
                st.session_state[show_key] = not st.session_state[show_key]

        if st.session_state.get(f"show_{snap.id}") and snap.detail_json:
            detail = snap.detail_json
            accounts = detail.get("accounts", [])
            liabilities = detail.get("liabilities", [])

            acct_rows = ""
            for acct in accounts:
                balance_gbp = Decimal(acct.get("balance_gbp") or acct["balance"])
                currency = acct.get("currency", "GBP")
                suffix = (
                    f'<span class="detail-suffix">({currency} {Decimal(acct["balance"]):,.2f})</span>'
                    if currency != "GBP"
                    else ""
                )
                name = acct.get("name") or acct.get("type_name", "Unknown")
                acct_rows += (
                    f'<div class="detail-row">'
                    f'<span class="detail-name">{name}{suffix}</span>'
                    f'<span class="detail-val">£{balance_gbp:,.2f}</span>'
                    f"</div>"
                )

            liab_rows = ""
            for liab in liabilities:
                name = liab.get("name") or f"Type {liab.get('type_id', '?')}"
                amount = Decimal(liab.get("amount") or liab.get("balance", "0"))
                liab_rows += (
                    f'<div class="detail-row">'
                    f'<span class="detail-name">{name}</span>'
                    f'<span class="detail-val">£{amount:,.2f}</span>'
                    f"</div>"
                )

            d_col1, d_col2 = st.columns(2)
            if acct_rows:
                d_col1.markdown(
                    f'<div class="detail-wrap">'
                    f'<div class="detail-title">Accounts</div>'
                    f"{acct_rows}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            if liab_rows:
                d_col2.markdown(
                    f'<div class="detail-wrap">'
                    f'<div class="detail-title">Liabilities</div>'
                    f"{liab_rows}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        st.markdown('<hr class="row-sep">', unsafe_allow_html=True)

    # CSV actions at the bottom
    st.markdown("---")
    st.subheader("Import / Export CSV")
    if True:
        st.subheader("Export")
        csv_data = _build_csv(snapshots_desc)
        st.download_button(
            label="Download net_worth_history.csv",
            data=csv_data,
            file_name="net_worth_history.csv",
            mime="text/csv",
        )

        st.divider()
        st.subheader("Import Snapshots")
        st.caption("Format: Date, Total Assets, Total Liabilities, Net Worth")
        col_tpl, col_upload = st.columns([1, 2])
        with col_tpl:
            st.download_button(
                label="Download template",
                data="Date,Total Assets,Total Liabilities,Net Worth\n2025-01-01,50000.00,10000.00,40000.00",
                file_name="snapshots_template.csv",
                mime="text/csv",
                key="dl_snapshots_template",
            )
        with col_upload:
            uploaded_snapshots = st.file_uploader(
                "Upload CSV",
                type=["csv"],
                key="upload_snapshots",
                label_visibility="collapsed",
            )
        if uploaded_snapshots is not None:
            file_content = uploaded_snapshots.read().decode("utf-8")
            session = next(get_session())
            try:
                imported, skipped, errors = import_csv_snapshots(
                    session=session,
                    user_id=user_id,
                    file_content=file_content,
                )
                if errors:
                    st.error("Import completed with errors:\n" + "\n".join(errors))
                else:
                    st.success(
                        f"Import successful! {imported} snapshots imported, "
                        f"{skipped} skipped (already exist)."
                    )
                st.rerun()
            finally:
                session.close()

        st.divider()
        st.subheader("Import Liabilities")
        st.caption("Updates existing snapshots only — leaves assets unchanged")
        col_tpl2, col_upload2 = st.columns([1, 2])
        with col_tpl2:
            st.download_button(
                label="Download template",
                data="Date,Total Liabilities\n2025-01-01,0.00",
                file_name="liabilities_template.csv",
                mime="text/csv",
                key="dl_liabilities_template",
            )
        with col_upload2:
            uploaded_liabilities = st.file_uploader(
                "Upload CSV",
                type=["csv"],
                key="upload_liabilities",
                label_visibility="collapsed",
            )
        if uploaded_liabilities is not None:
            file_content = uploaded_liabilities.read().decode("utf-8")
            session = next(get_session())
            try:
                updated, skipped, errors = import_csv_liabilities(
                    session=session,
                    user_id=user_id,
                    file_content=file_content,
                )
                if errors:
                    st.error("Import completed with errors:\n" + "\n".join(errors))
                else:
                    st.success(f"Done! {updated} updated, {skipped} skipped (date not found).")
                st.rerun()
            finally:
                session.close()


def _latest_per_month(snapshots: list) -> list:
    """Return one snapshot per calendar month — the latest date in that month.

    Input is ascending by date; output is descending (most recent first).
    """
    seen: dict[tuple[int, int], object] = {}
    for snap in snapshots:
        key = (snap.snapshot_date.year, snap.snapshot_date.month)
        seen[key] = snap
    return list(reversed(list(seen.values())))


def _format_change(current: Decimal | None, previous: Decimal | None) -> str:
    if current is None or previous is None:
        return "-"
    delta = current - previous
    if delta >= 0:
        return f"+£{delta:,.2f}"
    return f"-£{abs(delta):,.2f}"


def _build_csv(snapshots: list) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Total Assets", "Total Liabilities", "Net Worth"])
    for snap in snapshots:
        writer.writerow(
            [
                snap.snapshot_date.strftime("%Y-%m-%d"),
                str(snap.total_assets) if snap.total_assets is not None else "",
                str(snap.total_liabilities) if snap.total_liabilities is not None else "",
                str(snap.net_worth) if snap.net_worth is not None else "",
            ]
        )
    return output.getvalue()
