# zap_scanner.py
import sqlite3
import streamlit as st
import time
import logging
import pandas as pd
from datetime import datetime
from zapv2 import ZAPv2
from zap.zapdb import ZAPDatabase  # Import the ZAPDatabase class
from zap.report import ReportGenerator  # Import the ReportGenerator class

# Configure logging
logging.basicConfig(
    filename="zap_scanner.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Initialize ZAP configuration
ZAP_API_KEY = st.secrets["ZAP_API_KEY"]
ZAP_PROXY = {
    "http": "http://127.0.0.1:8080",
    "https": "http://127.0.0.1:8080"
}

SCAN_MODE_INFO = {
    "Quick Scan": "A rapid scan that checks for basic vulnerabilities. Duration: 5-10 minutes. Best for initial assessment.",
    "Full Scan": "Comprehensive security assessment including spider crawl and active scanning. Duration: 30-60 minutes. Recommended for production deployments.",
    "API Scan": "Specialized scan for API endpoints. Tests for API-specific vulnerabilities like improper authentication and data exposure. Duration: 15-30 minutes."
}

# Add scan policy descriptions
SCAN_POLICY_INFO = {
    "Default": "Balanced security testing with moderate intensity. Suitable for most web applications.",
    "High Security": "Aggressive testing with additional security checks. May increase false positives but provides maximum coverage.",
    "Quick": "Lightweight policy focusing on critical vulnerabilities only. Minimizes scan duration.",
    "Custom": "User-defined policy with configurable rules and thresholds. Requires manual configuration."
}

class ZAPScanner:
    def __init__(self):
        """
        Initialize the ZAP Scanner with API connection and database.
        """
        try:
            self.zap = ZAPv2(apikey=ZAP_API_KEY, proxies=ZAP_PROXY)
            self.db = ZAPDatabase()  # Initialize the database
            logging.info("ZAP Scanner initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing ZAP Scanner: {str(e)}")
            raise

    def start_scan(self, url, scan_mode, scan_policy):
        """
        Start a new ZAP scan with specified mode and policy.
        Returns scan ID or None if failed.
        """
        try:
            logging.info(f"Starting {scan_mode} scan for {url}")
            self.zap.urlopen(url)

            if scan_mode == "API Scan":
                scan_id = self.zap.ascan.scan(url=url, scanpolicyname=scan_policy)
                logging.info(f"Started API scan with ID: {scan_id}")
                return scan_id

            elif scan_mode == "Full Scan":
                # Start spider scan
                spider_scan_id = self.zap.spider.scan(url=url)
                logging.info(f"Started spider scan with ID: {spider_scan_id}")

                # Wait for spider to complete
                while int(self.zap.spider.status(spider_scan_id)) < 100:
                    time.sleep(2)

                # Start active scan
                scan_id = self.zap.ascan.scan(url=url, scanpolicyname=scan_policy)
                logging.info(f"Started active scan with ID: {scan_id}")
                return scan_id

            else:  # Quick Scan
                scan_id = self.zap.spider.scan(url=url)
                logging.info(f"Started quick scan with ID: {scan_id}")
                return scan_id

        except Exception as e:
            logging.error(f"Error starting scan: {str(e)}")
            return None

    def get_scan_status(self, scan_id):
        """
        Get current scan status with improved error handling and validation.
        Returns percentage complete (0-100).
        """
        try:
            # First check if scan_id exists
            if not scan_id:
                logging.error("Invalid scan ID: empty or None")
                return 0

            # Handle different scan types
            spider_status = 0
            ascan_status = 0

            try:
                spider_status = int(self.zap.spider.status(scan_id))
            except (ValueError, TypeError) as e:
                logging.debug(f"Spider status check failed: {str(e)}")

            try:
                ascan_status = int(self.zap.ascan.status(scan_id))
            except (ValueError, TypeError) as e:
                logging.debug(f"Active scan status check failed: {str(e)}")

            # Return the maximum progress between spider and active scan
            return max(spider_status, ascan_status)

        except Exception as e:
            logging.error(f"Error getting scan status: {str(e)}")
            return 0

    def get_alerts(self):
        """
        Fetch all alerts from the scan.
        """
        try:
            return self.zap.core.alerts()
        except Exception as e:
            logging.error(f"Error fetching alerts: {str(e)}")
            raise

    def generate_report(self, scan_id, url, metrics, format='pdf'):
        """
        Generate a report in the specified format (PDF, CSV, or JSON).
        Delegates to the ReportGenerator class.
        """
        if format == 'pdf':
            return ReportGenerator.generate_pdf_report(scan_id, url, metrics)
        elif format == 'csv':
            return ReportGenerator.generate_csv_report(metrics)
        elif format == 'json':
            return ReportGenerator.generate_json_report(metrics)
        else:
            raise ValueError(f"Unsupported report format: {format}")

def show_zap_page():
    """
    Display the main ZAP Scanner page with advanced options and visualizations.
    """
    # Update the database schema before proceeding
    db = ZAPDatabase()
    db.update_database_schema()

    st.title("🛡️ Advanced OWASP ZAP Security Scanner")

    # Initialize scanner
    scanner = ZAPScanner()

    # Create buttons for navigation
    col1, col2 = st.columns(2)
    with col1:
        scan_button = st.button("Scan")
    with col2:
        history_button = st.button("History")

    # Use session state to track the active section
    if "active_section" not in st.session_state:
        st.session_state.active_section = "Scan"  # Default section

    # Update the active section based on button clicks
    if scan_button:
        st.session_state.active_section = "Scan"
    if history_button:
        st.session_state.active_section = "History"

    # Display the active section
    if st.session_state.active_section == "Scan":
        display_scan_section(scanner)  # Pass the scanner object
    elif st.session_state.active_section == "History":
        display_scan_history(db)


def display_scan_section(scanner):
    """
    Display the enhanced Scan section with hover instructions and multiple report formats.
    """
    target_url = st.text_input("Target URL", "https://example.com")

    # Add hover instructions for scan modes
    scan_mode = st.selectbox(
        "Scan Mode",
        list(SCAN_MODE_INFO.keys()),
        help="\n".join(f"{mode}: {desc}" for mode, desc in SCAN_MODE_INFO.items())
    )

    # Add hover instructions for scan policies
    scan_policy = st.selectbox(
        "Scan Policy",
        list(SCAN_POLICY_INFO.keys()),
        help="\n".join(f"{policy}: {desc}" for policy, desc in SCAN_POLICY_INFO.items())
    )

    if st.button("Start Scan"):
        with st.spinner("Running scan..."):
            try:
                start_time = time.time()
                scan_id = scanner.start_scan(target_url, scan_mode, scan_policy)

                if not scan_id:
                    st.error("Failed to start scan. Please check logs for details.")
                    return

                progress_bar = st.progress(0)
                status_text = st.empty()

                # Monitor scan progress
                while True:
                    status = scanner.get_scan_status(scan_id)
                    progress_bar.progress(status)
                    status_text.text(f"Scan progress: {status}%")

                    if status >= 100:
                        break

                    time.sleep(2)

                progress_bar.progress(100)
                status_text.text("Scan completed. Analyzing results...")

                alerts = scanner.get_alerts()
                if alerts:
                    alerts_df = pd.DataFrame(alerts)
                    duration = time.time() - start_time

                    metrics = {
                        'total_alerts': len(alerts),
                        'risk_distribution': alerts_df['risk'].value_counts().to_dict(),
                        'top_vulnerabilities': alerts_df['name'].value_counts().head(5).to_dict()
                    }

                    scanner.db.save_scan_results(scan_id, target_url, metrics, scan_mode, scan_policy, duration)

                    # Generate and display report
                    st.success("Scan completed successfully!")
                    st.write("Scan Summary:")
                    st.json(metrics)

                    # Enhanced reporting options
                    st.subheader("Download Reports")

                    # PDF Report
                    pdf_report = scanner.generate_report(scan_id, target_url, metrics, format='pdf')
                    st.download_button(
                        label="Download PDF Report",
                        data=pdf_report,
                        file_name="security_scan_report.pdf",
                        mime="application/pdf"
                    )

                    # CSV Report
                    csv_report = scanner.generate_report(scan_id, target_url, metrics, format='csv')
                    st.download_button(
                        label="Download CSV Report",
                        data=csv_report,
                        file_name="security_scan_report.csv",
                        mime="text/csv"
                    )

                    # JSON Report
                    json_report = scanner.generate_report(scan_id, target_url, metrics, format='json')
                    st.download_button(
                        label="Download JSON Report",
                        data=json_report,
                        file_name="security_scan_report.json",
                        mime="application/json"
                    )

                else:
                    st.warning("Scan completed but no alerts were found.")

            except Exception as e:
                st.error(f"Error during scan: {str(e)}")
                logging.error(f"Scan error: {str(e)}")

def display_scan_history(db):
    """
    Display the scan history with filtering and sorting options.
    """
    st.subheader("Scan History")

    try:
        history_df = pd.read_sql_query("SELECT * FROM scan_history ORDER BY timestamp DESC", db.conn)

        # Filtering options
        st.sidebar.subheader("Filter Scans")
        date_range = st.sidebar.date_input("Date Range",
                                           [datetime.now().date() - pd.Timedelta(days=30), datetime.now().date()])
        risk_level = st.sidebar.multiselect("Risk Level", ["High", "Medium", "Low"])

        # Apply filters
        mask = (pd.to_datetime(history_df['timestamp']).dt.date >= date_range[0]) & (
                    pd.to_datetime(history_df['timestamp']).dt.date <= date_range[1])
        if risk_level:
            risk_columns = [col.lower() + '_risks' for col in risk_level]
            risk_mask = history_df[risk_columns].sum(axis=1) > 0
            mask &= risk_mask
        filtered_df = history_df[mask]

        # Display filtered results
        st.dataframe(filtered_df)

        # Export options
        if st.button("Export Filtered Results"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="scan_history.csv",
                mime="text/csv"
            )

    except sqlite3.Error as e:
        st.error(f"Database error: {str(e)}")
        logging.error(f"Error in display_scan_history: {str(e)}")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        logging.error(f"Unexpected error in display_scan_history: {str(e)}")

if __name__ == "__main__":
    show_zap_page()