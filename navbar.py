# navbar
import streamlit as st

def show_sidebar_navbar():
    """Render the sidebar navigation bar."""
    # Custom CSS for sidebar styling
    st.markdown("""
        <style>
            .sidebar .sidebar-content {
                background-color: #2E2E2E;
                color: white;
            }
            .sidebar .sidebar-content a {
                color: white;
                text-decoration: none;
            }
            .sidebar .sidebar-content button {
                background-color: #2E2E2E;
                color: white;
                border: none;
                padding: 8px 12px;
                text-align: left;
                width: 100%;
                cursor: pointer;
                border-radius: 4px;
                font-size: 16px;
                margin-bottom: 5px;
            }
            .sidebar .sidebar-content button:hover {
                background-color: #575757;
            }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        # Branding
        st.markdown("<h2 style='color:Black;'>⚡ WebSecScanner</h2>", unsafe_allow_html=True)
        st.write("")  # Spacer

        # Navigation menu buttons
        nav_items = {
            "Home": "home",
            "URL Scan": "url_scanner",
            "ZAP Tool": "zap_tool",
            "Schedule": "schedule",
            "Code Analysis": "code_analysis",
            "HTTP Method Tester": "method_tester",
            "Profile": "profile",
            # "Contact Us": "contact_us",

        }

        for label, page in nav_items.items():
            if st.button(label, key=f"nav_{page}"):
                st.session_state["current_view"] = page
                st.rerun()

        st.write("")  # Spacer

        # User actions
        if st.button("Logout", key="logout_button"):
            st.session_state.clear()
            st.session_state["authenticated"] = False
            st.session_state["page"] = "login"
            st.rerun()