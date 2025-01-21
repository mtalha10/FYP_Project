# File: userAdmin/profile.py
import streamlit as st
import os
import uuid
from PIL import Image
from Authentication.auth import AuthenticationManager
from datetime import datetime, timezone
import re

def logout():
    """Logout function to clear session state."""
    st.session_state.authenticated = False
    return True

def show_profile_page():
    """Display and manage user profile information."""
    st.title("User Profile")

    # Initialize Authentication Manager
    auth_manager = AuthenticationManager()

    # Check if username is in session state
    if 'username' not in st.session_state:
        st.error("Session username not initialized!")
        return

    # Get current user profile
    profile = auth_manager.get_current_user_profile()

    if not profile:
        st.error("Could not load profile data.")
        return

    # Create columns for layout
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Profile Picture")

        # Display current profile picture
        profile_picture = profile.get('profile_picture')
        default_picture = "assets/default_profile.png"
        if not os.path.isfile(default_picture):
            st.error("Default profile picture not found!")

        if profile_picture and os.path.isfile(profile_picture):
            try:
                st.image(profile_picture, width=200)
            except Exception:
                st.image(default_picture, width=200)
        else:
            st.image(default_picture, width=200)

        # Profile picture upload
        uploaded_file = st.file_uploader("Upload new profile picture", type=['png', 'jpg', 'jpeg'])
        if uploaded_file is not None:
            try:
                # Create directory if it doesn't exist
                os.makedirs('profile_pictures', exist_ok=True)

                # Generate a unique filename and save image
                file_extension = os.path.splitext(uploaded_file.name)[-1]
                unique_filename = f"profile_pictures/{uuid.uuid4()}{file_extension}"
                image = Image.open(uploaded_file)
                image = image.resize((200, 200))
                image.save(unique_filename)

                # Update database with new profile picture path
                success, message = auth_manager.update_current_user_profile({
                    'profile_picture': unique_filename
                })
                if success:
                    st.success("Profile picture updated successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to update profile picture: {message}")
            except Exception as e:
                st.error(f"Error processing image: {str(e)}")

    with col2:
        # Profile Information Form
        with st.form("profile_form"):
            st.subheader("Profile Information")

            # Display username (non-editable)
            st.text_input("Username", value=profile.get('username', ''), disabled=True)

            # Display email (non-editable)
            st.text_input("Email", value=profile.get('email', ''), disabled=True)

            # Editable fields with default values
            new_full_name = st.text_input("Full Name", value=profile.get('full_name', ''), help="Enter your full name.")
            new_bio = st.text_area("Bio", value=profile.get('bio', ''), height=100, help="Tell us something about yourself.")

            # Account created date
            st.text_input(
                "Account Created",
                value=profile.get('created_at', datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")),
                disabled=True
            )

            submitted = st.form_submit_button("Save Changes")

            if submitted:
                updates = {
                    'full_name': new_full_name,
                    'bio': new_bio
                }
                success, message = auth_manager.update_current_user_profile(updates)
                if success:
                    st.success("Profile updated successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to update profile: {message}")

    # Password Change Section
    st.markdown("---")
    with st.expander("Change Password"):
        with st.form("password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password", help="Password must be at least 8 characters long and include uppercase, lowercase, a number, and a symbol.")
            confirm_password = st.text_input("Confirm New Password", type="password")

            password_submitted = st.form_submit_button("Change Password")

            if password_submitted:
                if new_password != confirm_password:
                    st.error("New passwords do not match!")
                elif not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', new_password):
                    st.error("Password must include uppercase, lowercase, number, and special character!")
                else:
                    success, message = auth_manager.change_password(current_password, new_password)
                    if success:
                        st.success("Password changed successfully!")
                    else:
                        st.error(message)

    # Account Deletion Section
    st.markdown("---")
    with st.expander("Delete Account", expanded=False):
        st.warning("Warning: This action cannot be undone!")
        with st.form("delete_account_form"):
            confirm_password = st.text_input("Confirm your password", type="password")
            understand = st.checkbox("I understand that this action cannot be undone")

            delete_submitted = st.form_submit_button("Delete Account")

            if delete_submitted:
                if not understand:
                    st.error("Please confirm that you understand this action cannot be undone.")
                else:
                    success, message = auth_manager.delete_current_user(confirm_password)
                    if success:
                        st.success("Account deleted successfully!")
                        st.session_state.clear()
                        st.rerun()
                    else:
                        st.error(message)

    # Logout Button
    st.markdown("---")
    if st.button("Logout"):
        if logout():
            st.rerun()
