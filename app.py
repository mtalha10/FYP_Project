import streamlit as st


# Configure page
st.set_page_config(
    page_title="Web Vulnerability Scanner",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

from Research_Notebooks import url_scanner
from userAdmin import profile, contact, documentation
import home
from zap import zap_scanner, schedule, code_analysis, method_tester
from Authentication.auth import login_page, register_page, init_db
from components.styles import load_styles
import navbar

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'page' not in st.session_state:
    st.session_state.page = "login"
if 'current_view' not in st.session_state:
    st.session_state.current_view = "home"

# Load styles
load_styles()

# Initialize database
init_db()

# Page routing
PAGE_ROUTES = {
    "home": home.show_home_page,
    "url_scanner": url_scanner.show_url_scanner_page,
    "zap_tool": zap_scanner.show_zap_page,
    "schedule": schedule.show_schedule_page_wrapper,
    "code_analysis": code_analysis.display_security_analysis,
    "method_tester": method_tester.http_method_tester,  # Added HTTP Method Tester
    "profile": profile.show_profile_page,
    "contact_us": contact.show_contact_page,
    "documentation": documentation.show_documentation_page,
}


def render_footer():
    """Renders a footer at the bottom of the page."""
    st.markdown(
        """
        <hr style="margin-top: 2rem; margin-bottom: 1rem; border: none; border-top: 1px solid #ccc;" />
        <div style="text-align: center; font-size: 0.9rem; color: #555;">
            <p>
                © 2025 Web Vulnerability Scanner · Built by Talha - Hamza - Ali using Python & Streamlit
            </p>
            <p>
                <a href="https://example.com/terms" target="_blank" style="margin-right: 1rem; text-decoration: none; color: #6366f1;">Terms of Service</a>
                <a href="https://example.com/privacy" target="_blank" style="margin-right: 1rem; text-decoration: none; color: #6366f1;">Privacy Policy</a>
                <a href="https://example.com/contact" target="_blank" style="text-decoration: none; color: #6366f1;">Contact Us</a>
            </p>
            <p>
                Version 1.0.0
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def main_app():
    """Main application logic."""
    navbar.show_sidebar_navbar()  # Render the sidebar

    # Render current page
    page_function = PAGE_ROUTES.get(st.session_state.current_view)
    if page_function:
        page_function()
    else:
        st.session_state.current_view = "home"

    # Render footer
    render_footer()


# Main routing logic
if st.session_state.authenticated:
    main_app()
else:
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "register":
        register_page()