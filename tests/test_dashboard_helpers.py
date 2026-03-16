"""Tests for dashboard helper functions (DASH-02 and DASH-03).

These tests are intentionally in RED state — they test post-fix behaviour
that plan 02 will implement. DASH-02 tests will fail with ImportError until
plan 02 adds _build_net_worth_card_html. DASH-03 will fail with an
AssertionError until the chart axis format bug is fixed.

Imports are deferred into each test body so pytest can collect all 4 tests
even before the helper exists.
"""

import datetime
from decimal import Decimal
from types import SimpleNamespace


# ---------------------------------------------------------------------------
# DASH-02: negative / positive delta colour in HTML card
# ---------------------------------------------------------------------------

def test_net_worth_delta_negative_color():
    """Negative delta should produce red color in the HTML card string."""
    from frontend.pages.dashboard import _build_net_worth_card_html

    html = _build_net_worth_card_html(
        net_worth=Decimal("5000.00"),
        delta=Decimal("-200.00"),
    )
    assert "red" in html.lower()


def test_net_worth_delta_positive_color():
    """Positive delta should produce green color in the HTML card string."""
    from frontend.pages.dashboard import _build_net_worth_card_html

    html = _build_net_worth_card_html(
        net_worth=Decimal("5000.00"),
        delta=Decimal("200.00"),
    )
    assert "green" in html.lower()


# ---------------------------------------------------------------------------
# DASH-03: line chart y-axis tick format
# ---------------------------------------------------------------------------

def test_line_chart_tick_format(monkeypatch):
    """Line chart y-axis must use tickprefix='£' and tickformat=',.0f' separately."""
    from frontend.pages.dashboard import _render_line_chart
    import frontend.pages.dashboard as dashboard_module

    captured = {}

    def mock_plotly_chart(fig, **kwargs):
        captured["fig"] = fig

    monkeypatch.setattr(dashboard_module, "st", _make_mock_st(mock_plotly_chart))

    # Create minimal fake snapshot objects
    snap = SimpleNamespace(
        snapshot_date=SimpleNamespace(
            date=lambda: datetime.date(2025, 1, 1)
        ),
        net_worth=Decimal("10000"),
        total_assets=Decimal("15000"),
        total_liabilities=Decimal("5000"),
    )
    _render_line_chart([snap, snap])

    fig = captured["fig"]
    layout = fig.layout
    assert layout.yaxis.tickprefix == "£", (
        f"Expected tickprefix='£', got {layout.yaxis.tickprefix!r}"
    )
    assert layout.yaxis.tickformat == ",.0f", (
        f"Expected tickformat=',.0f', got {layout.yaxis.tickformat!r}"
    )


def test_line_chart_no_combined_tick_format(monkeypatch):
    """Line chart must NOT use the combined yaxis_tickformat='£,.0f' (broken in Plotly)."""
    from frontend.pages.dashboard import _render_line_chart
    import frontend.pages.dashboard as dashboard_module

    captured = {}

    def mock_plotly_chart(fig, **kwargs):
        captured["fig"] = fig

    monkeypatch.setattr(dashboard_module, "st", _make_mock_st(mock_plotly_chart))

    snap = SimpleNamespace(
        snapshot_date=SimpleNamespace(
            date=lambda: datetime.date(2025, 1, 1)
        ),
        net_worth=Decimal("10000"),
        total_assets=Decimal("15000"),
        total_liabilities=Decimal("5000"),
    )
    _render_line_chart([snap, snap])

    fig = captured["fig"]
    layout = fig.layout
    # tickformat on its own should be ',.0f', not '£,.0f'
    assert layout.yaxis.tickformat != "£,.0f", (
        "yaxis_tickformat='£,.0f' is the broken combined format — use "
        "tickprefix='£' and tickformat=',.0f' separately"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _MockSt:
    """Minimal mock of the streamlit module for testing chart helpers."""

    def __init__(self, plotly_chart_fn):
        self.plotly_chart = plotly_chart_fn

    # Stub any other st.* calls made during _render_line_chart
    def __getattr__(self, name):
        return lambda *a, **kw: None


def _make_mock_st(plotly_chart_fn):
    return _MockSt(plotly_chart_fn)
