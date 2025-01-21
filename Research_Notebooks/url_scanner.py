import streamlit as st
from tensorflow.keras.models import load_model
from urllib.parse import urlparse
import numpy as np
import re
from typing import List, Tuple, Dict
import plotly.graph_objects as go
from datetime import datetime
import sqlite3
import hashlib
import tldextract
import validators


# Cache the model loading
@st.cache_resource
def load_model_resources():
    try:
        # Load the pre-trained model
        model = load_model('D:\Project\Research_Notebooks\Malicious_URL_Prediction.h5')
        return model
    except Exception as e:
        st.error(f"Error loading model resources: {str(e)}")
        return None


class URLFeatureExtractor:
    @staticmethod
    def fd_length(url: str) -> int:
        try:
            return len(urlparse(url).path.split('/')[1])
        except:
            return 0

    @staticmethod
    def count_characteristics(url: str) -> Tuple[int, int, int]:
        return (sum(c.isdigit() for c in url),
                sum(c.isalpha() for c in url),
                url.count('/'))

    @staticmethod
    def has_ip_address(url: str) -> int:
        ip_pattern = re.compile(
            r'(([01]?\d\d?|2[0-4]\d|25[0-5])\.){3}([01]?\d\d?|2[0-4]\d|25[0-5])'
            r'|((0x[0-9a-fA-F]{1,2}\.){3}0x[0-9a-fA-F]{1,2})'
            r'|(?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}'
        )
        return -1 if ip_pattern.search(url) else 1

    @staticmethod
    def extract_features(url: str) -> np.ndarray:
        parsed_url = urlparse(url)
        digits, letters, dirs = URLFeatureExtractor.count_characteristics(url)

        # Extract only the 5 features expected by the model
        features = [
            len(parsed_url.netloc),  # hostname_length
            len(parsed_url.path),    # path_length
            URLFeatureExtractor.fd_length(url),  # fd_length
            url.count('.'),          # count.
            URLFeatureExtractor.has_ip_address(url)  # use_of_ip
        ]
        return np.array([features])


class URLDatabase:
    def __init__(self, db_path: str = "url_history.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS url_scans (
                id TEXT PRIMARY KEY,
                url TEXT,
                timestamp DATETIME,
                prediction REAL,
                is_malicious BOOLEAN
            )
        ''')
        self.conn.commit()

    def add_scan(self, url: str, prediction: float):
        url_id = hashlib.md5(url.encode()).hexdigest()
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO url_scans (id, url, timestamp, prediction, is_malicious)
            VALUES (?, ?, ?, ?, ?)
        ''', (url_id, url, datetime.now(), prediction, prediction >= 0.5))
        self.conn.commit()

    def get_recent_scans(self, limit: int = 10) -> List[tuple]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT url, timestamp, prediction, is_malicious 
            FROM url_scans 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()


class URLSecurityAnalyzer:
    def __init__(self):
        self.risk_factors = {
            'length': {'weight': 0.15, 'threshold': 75},
            'special_chars': {'weight': 0.2, 'threshold': 10},
            'subdomain_depth': {'weight': 0.15, 'threshold': 3},
            'path_depth': {'weight': 0.1, 'threshold': 4},
            'suspicious_keywords': {'weight': 0.25},
            'tld_risk': {'weight': 0.15}
        }

        self.high_risk_tlds = {'tk', 'ml', 'ga', 'cf', 'gq', 'xyz', 'work', 'click', 'bid'}

        self.suspicious_keywords = [
            'login', 'signin', 'verify', 'security', 'update', 'account',
            'payment', 'confirm', 'password', 'banking', 'secure', 'authenticate'
        ]

    def analyze_url_structure(self, url: str) -> Dict:
        parsed = urlparse(url)
        extracted = tldextract.extract(url)

        # Detailed analysis components
        analysis = {
            'url_length': len(url),
            'special_chars_count': len(re.findall(r'[^a-zA-Z0-9./\-]', url)),
            'subdomain_depth': len(extracted.subdomain.split('.')),
            'path_depth': len([x for x in parsed.path.split('/') if x]),
            'found_keywords': [kw for kw in self.suspicious_keywords if kw in url.lower()],
            'tld': extracted.suffix,
            'uses_https': parsed.scheme == 'https',
            'has_ip_address': bool(re.search(r'\d+\.\d+\.\d+\.\d+', url)),
            'excessive_dots': url.count('.') > 3,
            'numeric_domain': bool(re.search(r'\d+', extracted.domain)),
            'domain_length': len(extracted.domain),
            'path_length': len(parsed.path),
            'query_length': len(parsed.query)
        }

        return analysis

    def calculate_risk_score(self, analysis: Dict) -> Tuple[float, Dict]:
        risk_scores = {}

        # Length risk
        risk_scores['length'] = min(analysis['url_length'] / self.risk_factors['length']['threshold'], 1.0)

        # Special characters risk
        risk_scores['special_chars'] = min(
            analysis['special_chars_count'] / self.risk_factors['special_chars']['threshold'], 1.0)

        # Subdomain depth risk
        risk_scores['subdomain_depth'] = min(
            analysis['subdomain_depth'] / self.risk_factors['subdomain_depth']['threshold'], 1.0)

        # Path depth risk
        risk_scores['path_depth'] = min(analysis['path_depth'] / self.risk_factors['path_depth']['threshold'], 1.0)

        # Suspicious keywords risk
        risk_scores['suspicious_keywords'] = min(len(analysis['found_keywords']) / 3, 1.0)

        # TLD risk
        risk_scores['tld_risk'] = 1.0 if analysis['tld'] in self.high_risk_tlds else 0.0

        # Calculate weighted average
        total_risk = sum(score * self.risk_factors[factor]['weight']
                         for factor, score in risk_scores.items())

        return total_risk, risk_scores

    def get_security_insights(self, analysis: Dict, risk_scores: Dict) -> Dict:
        insights = {
            'high_risk_factors': [],
            'moderate_risk_factors': [],
            'low_risk_factors': [],
            'security_positives': []
        }

        # Analyze individual components
        if analysis['url_length'] > 75:
            insights['high_risk_factors'].append(
                "Unusually long URL length which is often associated with phishing attempts"
            )

        if analysis['special_chars_count'] > 10:
            insights['high_risk_factors'].append(
                "High number of special characters which may be used to obfuscate malicious URLs"
            )

        if analysis['subdomain_depth'] > 3:
            insights['moderate_risk_factors'].append(
                "Multiple subdomain levels which could indicate URL manipulation"
            )

        if analysis['found_keywords']:
            insights['moderate_risk_factors'].append(
                f"Contains suspicious keywords: {', '.join(analysis['found_keywords'])}"
            )

        if analysis['tld'] in self.high_risk_tlds:
            insights['high_risk_factors'].append(
                f"Uses a high-risk TLD ({analysis['tld']}) commonly associated with malicious websites"
            )

        if analysis['has_ip_address']:
            insights['high_risk_factors'].append(
                "Uses an IP address instead of a domain name, which is suspicious for legitimate websites"
            )

        if analysis['uses_https']:
            insights['security_positives'].append(
                "Uses HTTPS protocol for secure communication"
            )

        if not analysis['excessive_dots']:
            insights['security_positives'].append(
                "Normal number of dots in the domain name"
            )

        return insights


class URLScannerApp:
    def __init__(self):
        self.db = URLDatabase()
        self.model = load_model_resources()
        self.security_analyzer = URLSecurityAnalyzer()

    def predict_url(self, url: str) -> Tuple[float, np.ndarray]:
        """
        Predict whether a URL is malicious using the pre-trained model.

        Args:
            url (str): The URL to predict.

        Returns:
            Tuple[float, np.ndarray]: A tuple containing the prediction probability
                                      and the extracted features.
        """
        if self.model is None:
            st.error("Model not loaded. Please check the model file.")
            return None, None

        try:
            # Extract features from the URL
            features = URLFeatureExtractor.extract_features(url)

            # Predict using the pre-trained model
            prediction = self.model.predict(features)[0][0]  # Get the probability

            # Log the prediction to the database
            self.db.add_scan(url, prediction)

            return prediction, features
        except Exception as e:
            st.error(f"Error predicting URL: {str(e)}")
            return None, None

    def display_security_analysis(self, url: str, prediction: float):
        analysis = self.security_analyzer.analyze_url_structure(url)
        risk_score, risk_scores = self.security_analyzer.calculate_risk_score(analysis)
        insights = self.security_analyzer.get_security_insights(analysis, risk_scores)

        st.markdown("### Detailed Security Analysis")

        # Create three columns for different aspects of the analysis
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Risk Assessment")

            # Display overall risk score with color coding
            risk_color = "red" if risk_score > 0.7 else "orange" if risk_score > 0.4 else "green"
            st.markdown(f"""
                <div style='padding: 10px; border-radius: 5px; background-color: {risk_color}25;'>
                    <h4 style='color: {risk_color}'>Risk Score: {risk_score:.2%}</h4>
                </div>
            """, unsafe_allow_html=True)

            # Display ML model prediction
            pred_color = "red" if prediction > 0.5 else "green"
            st.markdown(f"""
                <div style='padding: 10px; border-radius: 5px; background-color: {pred_color}25;'>
                    <h4 style='color: {pred_color}'>ML Confidence: {prediction:.2%}</h4>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            # Create a radar chart for risk factors
            risk_factors = {
                'URL Length': risk_scores['length'],
                'Special Chars': risk_scores['special_chars'],
                'Subdomain': risk_scores['subdomain_depth'],
                'Path Depth': risk_scores['path_depth'],
                'Keywords': risk_scores['suspicious_keywords'],
                'TLD Risk': risk_scores['tld_risk']
            }

            fig = go.Figure(data=go.Scatterpolar(
                r=list(risk_factors.values()),
                theta=list(risk_factors.keys()),
                fill='toself'
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                showlegend=False,
                title="Risk Factor Analysis"
            )
            st.plotly_chart(fig)

        # Display detailed insights
        st.markdown("#### Security Insights")

        if insights['high_risk_factors']:
            st.markdown("##### ⚠️ High Risk Factors")
            for factor in insights['high_risk_factors']:
                st.markdown(f"- {factor}")

        if insights['moderate_risk_factors']:
            st.markdown("##### ⚠ Moderate Risk Factors")
            for factor in insights['moderate_risk_factors']:
                st.markdown(f"- {factor}")

        if insights['security_positives']:
            st.markdown("##### ✅ Security Positives")
            for positive in insights['security_positives']:
                st.markdown(f"- {positive}")

    def show_url_scanner_page(self):
        st.markdown("""
            <h1 style='text-align: center; color: #14559E'>Malicious URL Scanner</h1>
            <h3 style='text-align: center; color: #494848;'>Advanced Security Analysis System</h3>
        """, unsafe_allow_html=True)

        url = st.text_input("Enter URL to analyze", "https://www.google.com")

        if st.button("Perform Security Analysis", key="analyze_button"):
            if self.model is not None and validators.url(url):
                with st.spinner("Performing comprehensive security analysis..."):
                    prediction, features = self.predict_url(url)
                    if prediction is not None:
                        self.display_security_analysis(url, prediction)
            else:
                st.error("Please enter a valid URL")

        with st.expander("About the Analysis Engine"):
            st.markdown("""
                #### Advanced Security Analysis System

                This system combines multiple analysis techniques:

                1. **Machine Learning Analysis**
                   - Uses a deep neural network trained on millions of URLs
                   - Identifies patterns associated with malicious websites

                2. **Structural Analysis**
                   - Evaluates URL composition and structure
                   - Identifies suspicious patterns and anomalies

                3. **Risk Factor Assessment**
                   - Analyzes multiple risk indicators
                   - Provides weighted risk scoring

                4. **Security Best Practices**
                   - Checks for HTTPS implementation
                   - Evaluates domain configuration

                The system provides a comprehensive security assessment based on current cybersecurity standards and best practices.
            """)

    def run(self):
        self.show_url_scanner_page()

# app.py (Main application file)
def show_url_scanner_page():
    scanner = URLScannerApp()
    scanner.run()