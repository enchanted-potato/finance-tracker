"""Streamlit entry point with sidebar navigation."""

import os

import streamlit as st
import streamlit.components.v1 as components
from sqlalchemy import text as sa_text
from sqlmodel import SQLModel

from app.config import settings
from app.database import engine, get_session
from app.seed import seed_default_types
from app.services.auth_service import (
    get_or_create_user,
    init_firebase_admin,
    verify_firebase_token,
)
from frontend.pages import accounts, configure, dashboard, history, liabilities, pension

# Declare custom Firebase auth component
_AUTH_COMPONENT_DIR = os.path.join(os.path.dirname(__file__), "auth_component")
_auth_component = components.declare_component("firebase_auth", path=_AUTH_COMPONENT_DIR)


def _firebase_auth_widget(firebase_config: dict, action: str = "") -> dict | None:
    """Render Firebase auth component and return auth state.

    Args:
        firebase_config: Firebase web config (apiKey, authDomain, projectId)
        action: Optional action to pass to component (e.g., "logout")

    Returns:
        Auth state dict with status and optional token, or None if not ready
    """
    return _auth_component(
        firebase_config=firebase_config, action=action, default=None, key="firebase_auth"
    )


def _auth_gate() -> None:
    """Enforce Firebase authentication before allowing access to app.

    Blocks all page content until user is authenticated via Firebase.
    Handles login, logout, and session persistence across page navigation.
    """
    # Build Firebase config from settings
    firebase_config = {
        "apiKey": settings.firebase_web_api_key,
        "authDomain": settings.firebase_auth_domain,
        "projectId": settings.firebase_project_id,
    }

    # Bypass auth in local dev
    if settings.dev_user_id and not st.session_state.get("user_id"):
        st.session_state["user_id"] = settings.dev_user_id
        st.session_state["user_email"] = "dev@local"
        st.session_state["user_name"] = "Dev User"
        return

    # Handle logout request BEFORE checking auth status
    if st.session_state.get("_logout_requested"):
        # Tell component to sign out (this clears Firebase localStorage)
        _firebase_auth_widget(firebase_config, action="logout")
        # Clear Python session state
        st.session_state.pop("user_id", None)
        st.session_state.pop("user_email", None)
        st.session_state.pop("user_name", None)
        st.session_state.pop("_logout_requested", None)
        # Stop here - component will handle signOut and send unauthenticated on next render
        st.stop()

    # If already authenticated, allow access
    if st.session_state.get("user_id"):
        return

    # Render auth widget
    result = _firebase_auth_widget(firebase_config)

    # Handle auth states
    if result is None:
        # First render, component not ready yet
        st.stop()

    if result.get("status") == "initializing":
        # Component is checking auth state - just wait
        st.stop()

    if result.get("status") == "unauthenticated":
        # User not logged in, component shows login UI
        # Hide sidebar on login screen
        st.markdown(
            """
            <style>
            [data-testid='stSidebar'] {
                display: none;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

    if result.get("status") == "authenticated":
        # User logged in, verify token and create session
        token = result.get("token")
        if not token:
            st.error("Authentication failed. Please try again.")
            st.stop()

        # Verify token with Firebase Admin SDK
        decoded = verify_firebase_token(token)
        if not decoded:
            st.error("Authentication failed. Please try again.")
            st.stop()

        # Extract user info from token
        uid = decoded["uid"]
        email = decoded.get("email", "")
        name = decoded.get("name", "")

        # Validate user ID
        session = next(get_session())
        try:
            user_id = get_or_create_user(session, uid, email, name)
        except ValueError as e:
            st.error(f"Authentication error: {e}")
            st.stop()
        finally:
            session.close()

        # Store user in session state
        st.session_state["user_id"] = uid
        st.session_state["user_email"] = email
        st.session_state["user_name"] = name

        # Rerun to proceed past the gate
        st.rerun()


def _init_db() -> None:
    """Create tables, seed defaults, and initialize Firebase Admin SDK."""
    SQLModel.metadata.create_all(engine)
    # Add columns introduced after initial table creation
    with engine.connect() as conn:
        conn.execute(
            sa_text(
                "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS "
                "exchange_rate NUMERIC(10, 6) NOT NULL DEFAULT 1"
            )
        )
        conn.commit()
    session = next(get_session())
    try:
        seed_default_types(session=session)
    finally:
        session.close()

    # Initialize Firebase Admin SDK
    init_firebase_admin()


def main() -> None:
    """Run the Streamlit app."""
    st.set_page_config(
        page_title="Net Worth Tracker",
        page_icon="\U0001f4b0",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS for navigation and background with Anthropic branding
    st.markdown(
        """
        <style>
            /* Import Poppins and Material Icons fonts */
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
            @import url('https://fonts.googleapis.com/icon?family=Material+Icons');

            /* Apply Poppins font everywhere except icons */
            *:not(span.material-icons):not(.material-icons) {
                font-family: 'Poppins', Arial, sans-serif !important;
            }

            /* Ensure Material Icons font is never overridden by inheritance */
            .material-icons, span.material-icons {
                font-family: 'Material Icons' !important;
            }

            /* Hide sidebar collapse button (uses Material Symbols which conflict with font override) */
            [data-testid="collapsedControl"],
            [data-testid="stSidebarCollapseButton"],
            [data-testid="stSidebarCollapsedControl"],
            button[kind="header"] {
                display: none !important;
            }

            /* Main background color - Anthropic Light */
            .stApp {
                background-color: #faf9f5 !important;
            }

            /* Hide default Streamlit navigation */
            [data-testid="stSidebarNav"] {
                display: none;
            }

            /* Navigation button styling */
            .stButton > button {
                border: none !important;
                background: none !important;
                box-shadow: none !important;
                padding: 12px 16px !important;
                width: 100% !important;
                text-align: left !important;
                border-radius: 8px !important;
                color: #141413 !important;
                font-size: 16px !important;
                font-weight: 400 !important;
                transition: background-color 0.2s !important;
            }

            .stButton > button:hover {
                background-color: #e8e6dc !important;
                border: none !important;
            }

            .stButton > button:focus {
                box-shadow: none !important;
                border: none !important;
            }

            .stButton > button:active {
                background-color: #b0aea5 !important;
            }

            /* Active sidebar nav: left border accent, no background */
            [data-testid="stSidebar"] .stButton > button[kind="primary"] {
                background-color: transparent !important;
                color: #141413 !important;
                font-weight: 600 !important;
                border-left: 3px solid #141413 !important;
                padding-left: 13px !important;
            }

            [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
                background-color: #e8e6dc !important;
            }

            /* Drop shadow on all Plotly chart containers */
            .stPlotlyChart,
            [data-testid="stPlotlyChart"] {
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                border-radius: 8px;
                overflow: hidden;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # One-time DB init
    if "db_initialized" not in st.session_state:
        _init_db()
        st.session_state["db_initialized"] = True

    # Auth gate - blocks until user is authenticated
    _auth_gate()

    # Initialize selected page in session state
    if "selected_page" not in st.session_state:
        st.session_state["selected_page"] = "Dashboard"

    # Sidebar header with authenticated user info
    st.sidebar.title("Net Worth Tracker")
    user_display = st.session_state.get("user_name") or st.session_state.get("user_email", "")
    st.sidebar.markdown(f"Logged in as **{user_display}**")
    st.sidebar.divider()

    # Navigation menu with icons
    pages = {
        "Dashboard": "📊",
        "Accounts": "💰",
        "Liabilities": "💳",
        "Pension": "🏦",
        "History": "📈",
        "Configure": "⚙️",
    }

    for page, icon in pages.items():
        is_active = st.session_state["selected_page"] == page
        if st.sidebar.button(
            f"{icon}  {page}",
            key=f"nav_{page}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state["selected_page"] = page
            st.rerun()

    # Logout button at bottom of sidebar
    st.sidebar.divider()
    if st.sidebar.button("🚪  Log out", key="nav_logout", use_container_width=True):
        st.session_state["_logout_requested"] = True
        st.rerun()

    # Render selected page
    match st.session_state["selected_page"]:
        case "Dashboard":
            dashboard.render()
        case "Accounts":
            accounts.render()
        case "Liabilities":
            liabilities.render()
        case "Pension":
            pension.render()
        case "History":
            history.render()
        case "Configure":
            configure.render()


if __name__ == "__main__":
    main()
