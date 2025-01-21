# zap/zapdb.py
import sqlite3
import pandas as pd
import json
from contextlib import contextmanager
from logging import getLogger

logger = getLogger(__name__)

@contextmanager
def get_db_connection():
    """Context manager for database connections with proper error handling"""
    conn = None
    try:
        conn = sqlite3.connect('schedule.db', check_same_thread=False, timeout=30)
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def init_database():
    """Initialize the SQLite database schema."""
    with get_db_connection() as conn:
        conn.executescript("""
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_url TEXT NOT NULL CHECK(target_url LIKE 'http%'),
                frequency TEXT NOT NULL CHECK(frequency IN ('daily', 'weekly', 'monthly')),
                scan_time TEXT NOT NULL,
                scan_types TEXT NOT NULL,
                last_scan TEXT,
                next_scan TEXT,
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'paused', 'completed')),
                priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high')),
                notification_email TEXT CHECK(
                    notification_email IS NULL OR 
                    notification_email LIKE '%@%.%'
                ),
                max_duration INTEGER DEFAULT 3600 CHECK(max_duration > 0),
                retry_count INTEGER DEFAULT 3 CHECK(retry_count >= 0),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                tags TEXT,
                description TEXT,
                version INTEGER DEFAULT 1,
                UNIQUE(target_url, frequency, scan_time)
            );

            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_id INTEGER NOT NULL,
                scan_date TEXT NOT NULL,
                total_alerts INTEGER DEFAULT 0 CHECK(total_alerts >= 0),
                high_risks INTEGER DEFAULT 0 CHECK(high_risks >= 0),
                medium_risks INTEGER DEFAULT 0 CHECK(medium_risks >= 0),
                low_risks INTEGER DEFAULT 0 CHECK(low_risks >= 0),
                scan_duration INTEGER CHECK(scan_duration > 0),
                scan_status TEXT CHECK(scan_status IN ('success', 'failed', 'in_progress')),
                error_message TEXT,
                raw_results TEXT,
                false_positives INTEGER DEFAULT 0 CHECK(false_positives >= 0),
                verified_vulnerabilities INTEGER DEFAULT 0 CHECK(verified_vulnerabilities >= 0),
                version INTEGER DEFAULT 1,
                FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_schedules_status ON schedules(status, next_scan);
            CREATE INDEX IF NOT EXISTS idx_scan_results_schedule ON scan_results(schedule_id, scan_date);
            CREATE INDEX IF NOT EXISTS idx_schedules_target ON schedules(target_url);
        """)



def get_active_schedules():
    """Get all active schedules with error handling"""
    try:
        with get_db_connection() as conn:
            query = '''
                SELECT * FROM schedules 
                WHERE status = ? 
                ORDER BY next_scan
            '''
            return pd.read_sql_query(query, conn, params=("active",))
    except Exception as e:
        logger.error(f"Error fetching active schedules: {e}")
        return pd.DataFrame()

def add_schedule(config: dict):
    """Add a new scan schedule with improved validation"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO schedules (
                    target_url, frequency, scan_time, scan_types,
                    next_scan, priority, notification_email,
                    description, tags, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                config['target_url'],
                config['frequency'],
                config['scan_time'],
                json.dumps(config['scan_types']),
                config['next_scan'],
                config['priority'],
                config['notification_email'],
                config['description'],
                json.dumps(config['tags']) if config.get('tags') else None,
                config['created_at'],
                config['updated_at']
            ))
            conn.commit()
        logger.info(f"Added new schedule for {config['target_url']}")
        return True
    except Exception as e:
        logger.error(f"Error adding schedule: {e}")
        return False

def add_scan_result(schedule_id: int, result: dict):
    """Add a new scan result"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scan_results (
                    schedule_id, scan_date, total_alerts, high_risks,
                    medium_risks, low_risks, scan_duration, scan_status,
                    error_message, raw_results, false_positives, verified_vulnerabilities
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                schedule_id,
                result['scan_date'],
                result.get('total_alerts', 0),
                result.get('high_risks', 0),
                result.get('medium_risks', 0),
                result.get('low_risks', 0),
                result['scan_duration'],
                result['scan_status'],
                result.get('error_message'),
                result.get('raw_results'),
                result.get('false_positives', 0),
                result.get('verified_vulnerabilities', 0)
            ))
            conn.commit()
        logger.info(f"Added new scan result for schedule {schedule_id}")
        return True
    except Exception as e:
        logger.error(f"Error adding scan result: {e}")
        return False

def get_historical_data(schedule_id: int) -> pd.DataFrame:
    """Retrieve historical scan data for a given schedule ID"""
    try:
        with get_db_connection() as conn:
            query = '''
                SELECT 
                    sr.scan_date, 
                    sr.total_alerts, 
                    sr.high_risks, 
                    sr.medium_risks, 
                    sr.low_risks, 
                    sr.scan_duration
                FROM 
                    scan_results sr
                JOIN 
                    schedules s ON sr.schedule_id = s.id
                WHERE 
                    s.id =? 
                ORDER BY 
                    sr.scan_date DESC
            '''
            return pd.read_sql_query(query, conn, params=(schedule_id,))
    except Exception as e:
        logger.error(f"Error fetching historical data for schedule {schedule_id}: {e}")
        return pd.DataFrame()

def get_scan_statistics() -> dict:
    """Aggregate scan statistics across all schedules"""
    try:
        with get_db_connection() as conn:
            query = '''
                SELECT 
                    COUNT(DISTINCT s.id) AS total_schedules,
                    COUNT(sr.id) AS total_scans,
                    SUM(CASE WHEN sr.scan_status = 'success' THEN 1 ELSE 0 END) AS successful_scans,
                    SUM(sr.total_alerts) AS total_alerts,
                    SUM(sr.high_risks) AS total_high_risks,
                    SUM(sr.medium_risks) AS total_medium_risks,
                    SUM(sr.low_risks) AS total_low_risks,
                    AVG(sr.scan_duration) AS avg_duration
                FROM 
                    scan_results sr
                JOIN 
                    schedules s ON sr.schedule_id = s.id
            '''
            stats = pd.read_sql_query(query, conn).iloc[0].to_dict()
            # Calculate success rate
            if stats['total_scans'] > 0:
                stats['success_rate'] = (stats['successful_scans'] / stats['total_scans']) * 100
            else:
                stats['success_rate'] = 0
            # Risk distribution
            stats['risk_distribution'] = {
                'high': stats['total_high_risks'],
                'medium': stats['total_medium_risks'],
                'low': stats['total_low_risks']
            }
            # Status distribution
            query = '''
                SELECT 
                    scan_status, 
                    COUNT(id) AS count
                FROM 
                    scan_results
                GROUP BY 
                    scan_status
            '''
            status_dist = pd.read_sql_query(query, conn).set_index('scan_status')['count'].to_dict()
            stats['status_distribution'] = status_dist
            return stats
    except Exception as e:
        logger.error(f"Error fetching scan statistics: {e}")
        return {}

# zapdb.py

import sqlite3
from datetime import datetime
import logging
import json
import pandas as pd

class ZAPDatabase:
    def __init__(self, db_name='zap_scans.db'):
        """
        Initialize the ZAP database connection.
        """
        self.db_name = db_name
        self.conn = self.init_database()

    def init_database(self):
        """
        Initialize SQLite database for storing detailed scan history.
        """
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS scan_history
                        (scan_id TEXT PRIMARY KEY, 
                         url TEXT, 
                         timestamp TEXT, 
                         total_alerts INTEGER, 
                         high_risks INTEGER, 
                         medium_risks INTEGER, 
                         low_risks INTEGER,
                         scan_duration REAL, 
                         scan_mode TEXT, 
                         scan_policy TEXT,
                         top_vulnerabilities TEXT)''')
            conn.commit()
            logging.info("Database initialized successfully")
            return conn
        except sqlite3.Error as e:
            logging.error(f"Database initialization error: {str(e)}")
            raise

    def save_scan_results(self, scan_id, url, metrics, scan_mode, scan_policy, duration):
        """
        Save detailed scan results to database.
        """
        try:
            c = self.conn.cursor()
            c.execute('''INSERT OR REPLACE INTO scan_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (scan_id, url, datetime.now().isoformat(),
                       metrics['total_alerts'],
                       metrics['risk_distribution'].get('High', 0),
                       metrics['risk_distribution'].get('Medium', 0),
                       metrics['risk_distribution'].get('Low', 0),
                       duration,
                       scan_mode,
                       scan_policy,
                       json.dumps(metrics['top_vulnerabilities'])))
            self.conn.commit()
            logging.info(f"Scan results saved for scan ID: {scan_id}")
        except sqlite3.Error as e:
            logging.error(f"Error saving scan results: {str(e)}")
            raise

    def cleanup_old_scans(self, days_to_keep=30):
        """
        Remove scan data older than the specified number of days.
        """
        try:
            c = self.conn.cursor()
            c.execute("""
                DELETE FROM scan_history 
                WHERE timestamp < date('now', ?)
            """, (f'-{days_to_keep} days',))
            self.conn.commit()
            logging.info(f"Cleaned up scans older than {days_to_keep} days")
        except sqlite3.Error as e:
            logging.error(f"Error cleaning up old scans: {str(e)}")

    def update_database_schema(self):
        """
        Update the database schema to include the missing scan_mode and scan_policy columns.
        """
        try:
            c = self.conn.cursor()
            c.execute("PRAGMA table_info(scan_history)")
            columns = [column[1] for column in c.fetchall()]

            if 'scan_mode' not in columns:
                c.execute("ALTER TABLE scan_history ADD COLUMN scan_mode TEXT")
                self.conn.commit()
                logging.info("Added 'scan_mode' column to the database schema.")

            if 'scan_policy' not in columns:
                c.execute("ALTER TABLE scan_history ADD COLUMN scan_policy TEXT")
                self.conn.commit()
                logging.info("Added 'scan_policy' column to the database schema.")
        except sqlite3.Error as e:
            logging.error(f"Error updating database schema: {str(e)}")
            raise

    def fix_metrics_query(self):
        """
        Update the metrics query to handle potential missing data.
        """
        try:
            # Use COALESCE to handle potential NULL values in scan_duration
            metrics_df = pd.read_sql_query("""
                SELECT COUNT(*) as total_scans,
                       SUM(high_risks) as total_high_risks,
                       SUM(medium_risks) as total_medium_risks,
                       SUM(low_risks) as total_low_risks,
                       AVG(COALESCE(scan_duration, 0)) as avg_duration
                FROM scan_history
                WHERE timestamp >= date('now', '-30 days')
            """, self.conn)
            return metrics_df
        except sqlite3.Error as e:
            logging.error(f"Error fixing metrics query: {str(e)}")
            raise

    def close(self):
        """
        Close the database connection.
        """
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed.")