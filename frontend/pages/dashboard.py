from datetime import date, timedelta
from decimal import Decimal

import plotly.graph_objects as go
import streamlit as st

from app.database import get_session
from app.services.account_service import list_account_types, list_non_pension_accounts, list_pension_accounts
from app.services.liability_service import list_liability_entries, list_liability_types
from app.services.snapshot_service import get_snapshot_history


def _get_user_id() -> str:
    return st.session_state["user_id"]


def render() -> None:
    """Render the dashboard page."""
    st.header("Portfolio")
    user_id = _get_user_id()

    session = next(get_session())
    try:
        accounts = list_non_pension_accounts(session=session, user_id=user_id)
        pension_accounts = list_pension_accounts(session=session, user_id=user_id)
        all_liability_entries = list_liability_entries(session=session, user_id=user_id)
        # Use only the most recent date's entries for current totals/pie
        latest_liab_date = all_liability_entries[0].entry_date if all_liability_entries else None
        liabilities = [e for e in all_liability_entries if e.entry_date == latest_liab_date]
        account_types = list_account_types(session=session, user_id=user_id)
        liability_types = list_liability_types(session=session, user_id=user_id)
        all_snapshots = get_snapshot_history(session=session, user_id=user_id)
    finally:
        session.close()

    at_map = {at.id: at.name for at in account_types}
    lt_map = {lt.id: lt.name for lt in liability_types}

    # --- Headline numbers ---
    # Prefer live account/liability balances; fall back to latest snapshot
    # when no active records exist (e.g. data imported as snapshots only).
    total_assets = sum((a.balance for a in accounts), Decimal("0"))
    total_liabilities = sum((lb.amount for lb in liabilities), Decimal("0"))
    total_pension = sum((a.balance for a in pension_accounts), Decimal("0"))
    if total_assets == 0 and total_liabilities == 0 and all_snapshots:
        latest = all_snapshots[-1]
        total_assets = latest.total_assets if latest.total_assets is not None else Decimal("0")
        total_liabilities = latest.total_liabilities if latest.total_liabilities is not None else Decimal("0")
    net_worth = total_assets - total_liabilities

    col1, col2, col3, col4 = st.columns(4)

    nw_delta = Decimal("0")
    if len(all_snapshots) >= 2 and all_snapshots[-2].net_worth is not None:
        nw_delta = net_worth - all_snapshots[-2].net_worth

    with col1:
        st.markdown(_build_net_worth_card_html(net_worth, nw_delta), unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
<div style="background: rgba(20, 167, 96, 0.10); border-radius: 12px; padding: 20px 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); min-height: 100px;">
    <div style="font-size: 13px; color: #555; font-weight: 500; margin-bottom: 4px;">Total Assets</div>
    <div style="font-size: 26px; font-weight: 700; color: #141413;">£{total_assets:,.2f}</div>
    <div style="font-size: 13px; margin-top: 4px; visibility: hidden;">-</div>
</div>
""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
<div style="background: rgba(232, 33, 33, 0.10); border-radius: 12px; padding: 20px 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); min-height: 100px;">
    <div style="font-size: 13px; color: #555; font-weight: 500; margin-bottom: 4px;">Total Liabilities</div>
    <div style="font-size: 26px; font-weight: 700; color: #141413;">£{total_liabilities:,.2f}</div>
    <div style="font-size: 13px; margin-top: 4px; visibility: hidden;">-</div>
</div>
""", unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
<div style="background: rgba(100, 100, 100, 0.10); border-radius: 12px; padding: 20px 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); min-height: 100px;">
    <div style="font-size: 13px; color: #555; font-weight: 500; margin-bottom: 4px;">Total Pension</div>
    <div style="font-size: 26px; font-weight: 700; color: #141413;">£{total_pension:,.2f}</div>
    <div style="font-size: 13px; margin-top: 4px; visibility: hidden;">-</div>
</div>
""", unsafe_allow_html=True)

    if not all_snapshots:
        st.info(
            "No snapshots yet. Update an account or liability balance "
            "to create your first snapshot."
        )
        return

    # --- Time range filter ---
    range_option = st.radio(
        "Time range",
        options=["6 Months", "1 Year", "All Time"],
        index=2,
        horizontal=True,
        label_visibility="collapsed",
    )
    filtered_snapshots = _filter_snapshots(all_snapshots, range_option)

    # --- Net worth / assets over time (line chart) ---
    st.subheader("Amount over time")
    _render_line_chart(filtered_snapshots)

    # --- Pie charts side by side ---
    col_asset_pie, col_liability_pie = st.columns(2)
    with col_asset_pie:
        st.subheader("Asset Allocation")
        _render_asset_pie(accounts, at_map)
    with col_liability_pie:
        st.subheader("Liability Breakdown")
        _render_liability_pie(liabilities, lt_map)

    # --- Pension breakdown bar chart ---
    if pension_accounts:
        st.subheader("Pension Breakdown")
        _render_pension_bar(pension_accounts)


def _build_net_worth_card_html(net_worth: Decimal, delta: Decimal) -> str:
    """Build styled HTML for the Net Worth metric card.

    :param net_worth: Current net worth value.
    :param delta: Change from previous snapshot (positive = gain, negative = loss).
    :returns: HTML string for rendering via st.markdown(unsafe_allow_html=True).
    """
    delta_color = "red" if delta < 0 else "green"
    sign = "+" if delta >= 0 else ""
    delta_str = f"{sign}£{abs(delta):,.2f}"
    return f"""
<div style="
    background: rgba(33, 150, 243, 0.10);
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    min-height: 100px;
">
    <div style="font-size: 13px; color: #555; font-weight: 500; margin-bottom: 4px;">Net Worth</div>
    <div style="font-size: 26px; font-weight: 700; color: #141413;">£{net_worth:,.2f}</div>
    <div style="font-size: 13px; color: {delta_color}; font-weight: 500; margin-top: 4px;">{delta_str}</div>
</div>
"""


def _filter_snapshots(snapshots: list, range_option: str) -> list:
    """Filter snapshots by the selected time range."""
    if range_option == "All Time":
        return snapshots
    today = date.today()
    if range_option == "6 Months":
        cutoff = today - timedelta(days=182)
    else:
        cutoff = today - timedelta(days=365)
    return [s for s in snapshots if s.snapshot_date.date() >= cutoff]


def _render_line_chart(snapshots: list) -> None:
    """Render a Plotly line chart with net worth, total assets, and total liabilities."""
    dates = [s.snapshot_date.date() for s in snapshots]
    net_worth_values = [float(s.net_worth) if s.net_worth is not None else None for s in snapshots]
    assets_values = [float(s.total_assets) if s.total_assets is not None else None for s in snapshots]
    liabilities_values = [float(s.total_liabilities) if s.total_liabilities is not None else None for s in snapshots]

    fig = go.Figure()

    # Add Net Worth line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=net_worth_values,
            mode="lines+markers",
            name="Net Worth",
            line={"color": "#2218E7", "width": 2},
            marker={"size": 6},
            connectgaps=True,
        )
    )

    # Add Total Assets line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=assets_values,
            mode="lines+markers",
            name="Total Assets",
            line={"color": "#14A760", "width": 2},
            marker={"size": 6},
            connectgaps=True,
        )
    )

    # Add Total Liabilities line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=liabilities_values,
            mode="lines+markers",
            name="Total Liabilities",
            line={"color": "#E82121", "width": 2},
            marker={"size": 6},
            connectgaps=True,
        )
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis=dict(
            title="Amount",
            tickprefix="£",
            tickformat=",.0f",
        ),
        hovermode="x unified",
        margin={"l": 60, "r": 20, "t": 20, "b": 40},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_asset_pie(accounts: list, type_map: dict[int, str]) -> None:
    """Render a donut chart of assets by account type."""
    if not accounts:
        st.info("No asset accounts.")
        return

    grouped: dict[str, float] = {}
    for acct in accounts:
        type_name = type_map.get(acct.account_type_id, "Unknown")
        grouped[type_name] = grouped.get(type_name, 0) + float(acct.balance)

    # Bright, vibrant color palette
    colors = ["#0973de", "#FFC107", "#10D078", "#FF6B6B", "#A855F7", "#FF8042", "#00D9C9"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=list(grouped.keys()),
                values=list(grouped.values()),
                hole=0.4,
                textinfo="label+percent",
                marker=dict(colors=colors),
            )
        ]
    )
    fig.update_layout(
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_liability_pie(liabilities: list, type_map: dict[int, str]) -> None:
    """Render a donut chart of liabilities by type."""
    if not liabilities:
        st.info("No liabilities.")
        return

    grouped: dict[str, float] = {}
    for liab in liabilities:
        type_name = type_map.get(liab.liability_type_id, "Unknown")
        grouped[type_name] = grouped.get(type_name, 0) + float(liab.amount)

    # Bright, vibrant color palette
    colors = ["#0973de", "#FFC107", "#10D078", "#FF6B6B", "#A855F7", "#FF8042", "#00D9C9"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=list(grouped.keys()),
                values=list(grouped.values()),
                hole=0.4,
                textinfo="label+percent",
                marker=dict(colors=colors),
            )
        ]
    )
    fig.update_layout(
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_pension_bar(pension_accounts: list) -> None:
    """Render a stacked bar chart of pension value per provider."""
    colors = ["#A855F7", "#7C3AED", "#6D28D9", "#5B21B6", "#4C1D95", "#C084FC", "#DDD6FE"]
    fig = go.Figure()
    for i, account in enumerate(pension_accounts):
        fig.add_trace(
            go.Bar(
                name=account.name,
                x=["Pension"],
                y=[float(account.balance)],
                marker_color=colors[i % len(colors)],
                width=0.3,
            )
        )
    fig.update_layout(
        barmode="stack",
        yaxis=dict(
            title="Amount",
            tickprefix="£",
            tickformat=",.0f",
        ),
        margin={"l": 60, "r": 20, "t": 20, "b": 40},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)
