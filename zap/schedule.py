import streamlit as st
from datetime import datetime
import pandas as pd
import sqlite3
import json
from zapv2 import ZAPv2
import time
import threading
from typing import Dict, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScanScheduler:
    def __init__(self):
        self.conn = sqlite3.connect('scans.db', check_same_thread=False)
        self.create_tables()
        self.zap = None
        self.scheduler_thread = None
        self.is_running = False

    def create_tables(self):
        """Create necessary database tables if they don't exist."""
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_url TEXT NOT NULL,
            scan_type TEXT NOT NULL,
            schedule_time DATETIME NOT NULL,
            recurring TEXT,
            scan_options TEXT,
            status TEXT DEFAULT 'scheduled',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        self.conn.commit()

    def connect_to_zap(self, proxy_url: str = 'http://localhost:8080'):
        """Connect to ZAP instance."""
        try:
            self.zap = ZAPv2(proxies={'http': proxy_url, 'https': proxy_url})
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ZAP: {str(e)}")
            return False

    def schedule_scan(self, target_url: str, scan_type: str, schedule_time: datetime,
                      recurring: str = None, scan_options: Dict = None):
        """Schedule a new scan."""
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO scheduled_scans (target_url, scan_type, schedule_time, recurring, scan_options)
        VALUES (?, ?, ?, ?, ?)
        ''', (target_url, scan_type, schedule_time.isoformat(),
              recurring, json.dumps(scan_options) if scan_options else None))
        self.conn.commit()
        return cursor.lastrowid

    def get_scheduled_scans(self) -> List[Dict]:
        """Retrieve all scheduled scans."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM scheduled_scans ORDER BY schedule_time')
        columns = [description[0] for description in cursor.description]
        scans = []
        for row in cursor.fetchall():
            scan_dict = dict(zip(columns, row))
            if scan_dict['scan_options']:
                scan_dict['scan_options'] = json.loads(scan_dict['scan_options'])
            scans.append(scan_dict)
        return scans

    def run_scan(self, scan_id: int):
        """Execute the actual scan using ZAP."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM scheduled_scans WHERE id = ?', (scan_id,))
        scan = dict(zip([d[0] for d in cursor.description], cursor.fetchone()))

        try:
            if not self.zap:
                self.connect_to_zap()

            # Update scan status
            cursor.execute('UPDATE scheduled_scans SET status = ? WHERE id = ?',
                           ('running', scan_id))
            self.conn.commit()

            # Start the scan based on scan type
            if scan['scan_type'] == 'full':
                self.zap.spider.scan(scan['target_url'])
                self.zap.ascan.scan(scan['target_url'])
            elif scan['scan_type'] == 'quick':
                self.zap.spider.scan(scan['target_url'])

            # Update scan status to completed
            cursor.execute('UPDATE scheduled_scans SET status = ? WHERE id = ?',
                           ('completed', scan_id))
            self.conn.commit()

        except Exception as e:
            logger.error(f"Scan failed: {str(e)}")
            cursor.execute('UPDATE scheduled_scans SET status = ? WHERE id = ?',
                           ('failed', scan_id))
            self.conn.commit()

    def start_scheduler(self):
        """Start the scheduler thread."""
        if not self.is_running:
            self.is_running = True
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()

    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.is_running:
            current_time = datetime.now()
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT id FROM scheduled_scans 
            WHERE schedule_time <= ? AND status = 'scheduled'
            ''', (current_time.isoformat(),))

            for (scan_id,) in cursor.fetchall():
                self.run_scan(scan_id)

            time.sleep(60)  # Check every minute

def show_schedule_page_wrapper():
    """Streamlit page for scan scheduling interface."""
    st.title("Schedule Scans")

    scheduler = ScanScheduler()

    # Display current time
    st.write(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Form for scheduling new scans
    with st.form("schedule_scan_form"):
        target_url = st.text_input("Target URL", placeholder="https://example.com")
        scan_type = st.selectbox("Scan Type", ["quick", "full"])
        schedule_date = st.date_input("Schedule Date")
        schedule_time = st.time_input("Schedule Time")
        recurring = st.selectbox("Recurring", ["None", "Daily", "Weekly", "Monthly"])

        if st.form_submit_button("Schedule Scan"):
            schedule_datetime = datetime.combine(schedule_date, schedule_time)
            if schedule_datetime < datetime.now():
                st.error("Cannot schedule scans in the past!")
            else:
                scan_id = scheduler.schedule_scan(
                    target_url=target_url,
                    scan_type=scan_type,
                    schedule_time=schedule_datetime,
                    recurring=recurring if recurring != "None" else None
                )
                st.success(f"Scan scheduled successfully! Scan ID: {scan_id}")

    # Display scheduled scans
    st.subheader("Scheduled Scans")
    scans = scheduler.get_scheduled_scans()
    if scans:
        df = pd.DataFrame(scans)
        df['schedule_time'] = pd.to_datetime(df['schedule_time'])
        df['created_at'] = pd.to_datetime(df['created_at'])
        st.dataframe(df[['id', 'target_url', 'scan_type', 'schedule_time', 'recurring', 'status']])
    else:
        st.info("No scans scheduled yet.")

    # Start the scheduler if there are scheduled scans
    if scans:
        scheduler.start_scheduler()