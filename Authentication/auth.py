import streamlit as st
from Authentication.userdb import DatabaseOperations
import time

def logout():
    """Log out the current user."""
    if 'username' in st.session_state:
        del st.session_state.username
    st.session_state.authenticated = False
    return True

class AuthenticationManager:
    def __init__(self):  # Corrected the constructor name
        self.db = DatabaseOperations()


    def get_current_user_profile(self):
        """Retrieve the current user's profile data."""
        if 'username' in st.session_state:
            username = st.session_state.username
            return self.db.get_user_profile(username)
        return None

    def update_current_user_profile(self, updates):
        """Update the current user's profile with the provided updates."""
        if 'username' in st.session_state:
            username = st.session_state.username
            return self.db.update_user_profile(username, updates)
        return False, "User not authenticated"

    def change_password(self, current_password, new_password):
        """Change the current user's password."""
        if 'username' in st.session_state:
            username = st.session_state.username
            return self.db.change_user_password(username, current_password, new_password)
        return False, "User not authenticated"

    def delete_current_user(self, password):
        """Delete the current user's account."""
        if 'username' in st.session_state:
            username = st.session_state.username
            return self.db.delete_user(username, password)
        return False, "User not authenticated"

def login_page():

    # Create two columns for form and image
    st.title("Login Page ")
    col1, col2 = st.columns([1, 1])  # Form and image columns

    with col1:
        # Form Box on Left
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("Username", placeholder="Enter your username", label_visibility="collapsed")
            password = st.text_input("Password", type="password", placeholder="Enter your password", label_visibility="collapsed")
            remember = st.checkbox("Remember me", label_visibility="collapsed")

            submitted = st.form_submit_button("Sign In")
            if submitted:
                with st.spinner("Authenticating..."):
                    # Simulate lightweight server-side check instead of delay
                    is_authenticated = DatabaseOperations.verify_user(username, password)
                    if is_authenticated:
                        st.success("Login successful!")
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error("Invalid username or password")

        st.markdown("<div class='auth-divider'><span>OR</span></div>", unsafe_allow_html=True)

        if st.button("Create New Account"):
            st.session_state.page = "register"
            st.rerun()

    with col2:
        st.image("assets/login.png", use_container_width=True)  # Image displayed on the right

def register_page():
    st.title("Sign up Here!")
    # Create two columns for form and image
    col1, col2 = st.columns([1, 1])  # Form and image columns

    with col1:
        # Form Box on Left
        with st.form("register_form", clear_on_submit=True):
            username = st.text_input("Username", placeholder="Choose a username", label_visibility="collapsed")
            email = st.text_input("Email", placeholder="Enter your email", label_visibility="collapsed")
            password = st.text_input("Password", type="password", placeholder="Create a strong password", label_visibility="collapsed")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", label_visibility="collapsed")

            terms = st.checkbox("I agree to the Terms of Service and Privacy Policy", label_visibility="collapsed")

            submitted = st.form_submit_button("Create Account")
            if submitted:
                if not terms:
                    st.error("Please accept the terms and conditions")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    with st.spinner("Creating your account..."):
                        success, message = DatabaseOperations.add_user(username, password, email)
                        if success:
                            st.success(message)
                            st.session_state.page = "login"
                            st.rerun()
                        else:
                            st.error(message)

        st.markdown("<div class='auth-divider'><span>OR</span></div>", unsafe_allow_html=True)

        if st.button("Back to Login"):
            st.session_state.page = "login"
            st.rerun()

    with col2:
        st.image("assets/signup.png", use_container_width=True)  # Image displayed on the right

def init_db():
    """Initialize the database with enhanced feedback"""
    with st.spinner("Initializing database..."):
        DatabaseOperations.init_db()
        time.sleep(0.5)