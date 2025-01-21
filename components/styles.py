# components/styles.py
import streamlit as st

def load_styles():
    st.markdown("""
    <style>
    /* Modern Light Mode Color Scheme */
    :root {
        --primary: #6366f1;
        --primary-dark: #4f46e5;
        --secondary: #ec4899;
        --background: #f9fafb;
        --surface: #ffffff;
        --text: #1f2937;
        --text-secondary: #4b5563;
        --success: #16a34a;
        --error: #dc2626;
        --border: #e5e7eb;
    }

    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, var(--background), #f3f4f6);
    }

    /* Authentication Container */
    .auth-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 2rem;
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border-radius: 1rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border: 1px solid var(--border);
    }

    /* Input Fields */
    .stTextInput > div > div {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 0.5rem !important;
        color: var(--text) !important;
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
        background: linear-gradient(45deg, var(--primary), var(--primary-dark)) !important;
        color: white !important;
        border: none !important;
        border-radius: 0.5rem !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }

    /* Sidebar Navigation */
    .components-1d391kg {
        background: var(--surface);
        border-right: 1px solid var(--border);
    }

    .nav-link {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        color: var(--text-secondary);
        text-decoration: none;
        border-radius: 0.5rem;
        margin: 0.25rem 0;
        transition: all 0.3s ease;
    }

    .nav-link:hover {
        background: rgba(99, 102, 241, 0.1);
        color: var(--primary);
    }

    .nav-link.active {
        background: var(--primary);
        color: white;
    }

    /* Custom Messages */
    .success-message {
        padding: 1rem;
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid var(--success);
        border-radius: 0.5rem;
        color: var(--success);
        margin: 1rem 0;
    }

    .error-message {
        padding: 1rem;
        background: rgba(220, 38, 38, 0.1);
        border: 1px solid var(--error);
        border-radius: 0.5rem;
        color: var(--error);
        margin: 1rem 0;
    }

    /* Extended Modern Light Mode Styles */
    :root {
        --primary-light: #a5b4fc;
        --secondary-dark: #db2777;
        --surface-light: #f3f4f6;
        --warning: #f59e0b;
        --gradient-start: #818cf8;
        --gradient-end: #ec4899;
    }

    .header-container {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 2rem;
    }

    .gradient-text {
        background: linear-gradient(45deg, var(--gradient-start), var(--gradient-end));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }

    .tool-card {
        background: var(--surface);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid var(--border);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .tool-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.2);
    }

    .metrics-card {
        background: var(--surface);
        border-radius: 1rem;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid var(--border);
    }

    .security-score {
        background: var(--surface);
        border-radius: 1rem;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
    }

    .score-circle {
        width: 150px;
        height: 150px;
        margin: 0 auto;
        position: relative;
        background: conic-gradient(
            var(--primary) calc(var(--score) * 1%),
            var(--surface-light) calc(var(--score) * 1%)
        );
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .score-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text);
    }

    @media (max-width: 768px) {
        .tool-card, .metrics-card, .security-score {
            padding: 1rem;
        }

        .score-circle {
            width: 100px;
            height: 100px;
        }

        .score-value {
            font-size: 1.5rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
