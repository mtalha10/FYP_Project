import streamlit as st

def show_documentation_page():
    """Display the complete documentation on a single page."""
    st.title("📚 Documentation")

    # Getting Started
    st.header("Getting Started")
    st.subheader("Installation Guide")
    st.write("Step-by-step guide for setting up the scanner.")
    st.markdown("Detailed instructions coming soon...")
    st.subheader("Quick Start Tutorial")
    st.write("Basic usage and first scan walkthrough.")
    st.markdown("Detailed tutorial coming soon...")
    st.subheader("System Requirements")
    st.write("Hardware and software requirements.")
    st.markdown("Details coming soon...")

    # Features
    st.header("Features")
    st.subheader("Scan Types")
    st.write("Different types of security scans available.")
    st.subheader("Security Policies")
    st.write("Understanding and customizing security policies.")
    st.subheader("Report Generation")
    st.write("How to generate and interpret security reports.")

    # Advanced Usage
    st.header("Advanced Usage")
    st.subheader("API Integration")
    st.write("Using the scanner's API endpoints.")
    st.subheader("Custom Rules")
    st.write("Creating and managing custom scanning rules.")
    st.subheader("Automation")
    st.write("Setting up automated scanning workflows.")

    # Contact Support
    st.header("Need Help?")
    st.write("If you have any questions, feel free to reach out.")
    st.markdown("""
        - [User Guide](#)
        - [API Reference](#)
        - [Contact Support](#)
    """)
