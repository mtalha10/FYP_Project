# pages/contact.py
import streamlit as st


def show_contact_page():
    st.title("Contact Us")

    # Add your contact form here
    with st.form("contact_form"):
        st.text_input("Name")
        st.text_input("Email")
        st.text_area("Message")
        st.form_submit_button("Send Message")