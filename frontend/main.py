"""Streamlit entry point with sidebar navigation."""

import os

import streamlit as st
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu
from sqlmodel import SQLModel

from app.config import settings
from app.database import engine, get_session
from app.seed import seed_default_types
from app.services.auth_service import (
    get_or_create_user,
    init_firebase_admin,
    verify_firebase_token,
)
from frontend.pages import accounts, configure, dashboard, goals, history, liabilities, pension

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
        if st.session_state.pop("_access_denied", False):
            st.error("Access denied. Please sign in with an authorised account.")
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
            # Trigger logout so Firebase resets to login screen on next render
            st.session_state["_logout_requested"] = True
            st.session_state["_access_denied"] = True
            st.rerun()

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
    session = next(get_session())
    try:
        seed_default_types(session=session)
    finally:
        session.close()
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
            /* Import Poppins, Material Icons, and Material Symbols Rounded */
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
            @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
            @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

            /* Apply Poppins font everywhere except icons */
            *:not(span.material-icons):not(.material-icons) {
                font-family: 'Poppins', Arial, sans-serif !important;
            }

            /* Ensure Material Icons font is never overridden by inheritance */
            .material-icons, span.material-icons {
                font-family: 'Material Icons' !important;
            }

            /* Restore Material Symbols Rounded for Streamlit's own UI icons (e.g. expander arrow) */
            details summary [aria-hidden="true"],
            details summary svg,
            details > summary > div > span:first-child,
            details > summary > span:first-child,
            [data-testid="stExpanderToggleIcon"],
            [data-testid="stExpanderHeader"] span:first-child {
                font-family: 'Material Symbols Rounded' !important;
            }

            /* Hide sidebar collapse button (uses Material Symbols which conflict with font override) */
            [data-testid="collapsedControl"],
            [data-testid="stSidebarCollapseButton"],
            [data-testid="stSidebarCollapsedControl"],
            button[kind="header"] {
                display: none !important;
            }

            /* Main background color - Midnight */
            .stApp {
                background-color: #161b22 !important;
            }

            /* Hide default Streamlit navigation */
            [data-testid="stSidebarNav"] {
                display: none;
            }

            /* option_menu icon color fix in dark theme */
            [data-testid="stSidebar"] .nav-link-selected i {
                color: #58a6ff !important;
            }


            /* Drop shadow on all Plotly chart containers */
            .stPlotlyChart,
            [data-testid="stPlotlyChart"] {
                box-shadow: 0 4px 12px rgba(0,0,0,0.4);
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
    st.sidebar.markdown(
        """
        <div style="
            padding: 8px 0 4px 0;
            letter-spacing: -0.5px;
        ">
            <span style="
                font-family: 'Poppins', sans-serif;
                font-size: 26px;
                font-weight: 700;
                background: linear-gradient(135deg, #58a6ff 0%, #79c0ff 60%, #a5d6ff 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            ">Worth</span><span style="
                font-size: 20px;
                -webkit-text-fill-color: #79c0ff;
                background: none;
                font-weight: 700;
            ">↗</span><span style="
                font-family: 'Poppins', sans-serif;
                font-size: 26px;
                font-weight: 300;
                color: #8b949e;
            ">flow</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    user_display = st.session_state.get("user_name") or st.session_state.get("user_email", "")
    st.sidebar.markdown(f"<span style='color:#8b949e;font-size:15px'>Logged in: {user_display}</span>", unsafe_allow_html=True)
    st.sidebar.divider()

    # Navigation menu with Bootstrap icons
    page_names = ["Dashboard", "Accounts", "Liabilities", "Pension", "Goals", "Trends", "Configure"]
    page_icons = ["grid", "wallet2", "credit-card", "piggy-bank", "trophy", "graph-up-arrow", "gear"]
    current_index = page_names.index(st.session_state["selected_page"])

    with st.sidebar:
        selected = option_menu(
            menu_title=None,
            options=page_names,
            icons=page_icons,
            default_index=current_index,
            styles={
                "container": {"padding": "0", "background-color": "transparent"},
                "icon": {"color": "#8b949e", "font-size": "16px"},
                "nav-link": {
                    "color": "#e6edf3",
                    "font-size": "16px",
                    "font-weight": "400",
                    "padding": "10px 16px",
                    "border-radius": "8px",
                    "--hover-color": "rgba(255,255,255,0.05)",
                },
                "nav-link-selected": {
                    "background-color": "rgba(88,166,255,0.1)",
                    "color": "#58a6ff",
                    "font-weight": "600",
                    "border-left": "3px solid #58a6ff",
                },
            },
            key="nav_menu",
        )

    if selected != st.session_state["selected_page"]:
        st.session_state["selected_page"] = selected
        st.rerun()

    # Logout button at bottom of sidebar
    st.sidebar.divider()
    if st.sidebar.button("Log out", key="nav_logout", use_container_width=True):
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
        case "Goals":
            goals.render()
        case "Trends":
            history.render()
        case "Configure":
            configure.render()


if __name__ == "__main__":
    main()
