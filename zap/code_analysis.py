import ast
import time
import re
import pandas as pd
import streamlit as st
from typing import Dict, List, Any, Optional
import hashlib
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum
import random
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecuritySeverity(Enum):
    """Enumeration for security issue severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

@dataclass
class SecurityIssue:
    """Data structure for security-related code issues"""
    severity: SecuritySeverity
    issue_type: str
    description: str
    recommendation: str
    code_snippet: Optional[str] = None
    line_number: Optional[int] = None

class SecurityAwareCodeAnalyzer:
    """
    Enhanced code analysis tool with focus on security vulnerabilities
    and integration with live data generation.
    """

    SECURITY_PATTERNS = {
        'sql_injection': (
            r'execute\s*\(\s*[\'"`][^\'"`]*%s[^\'"`]*[\'"`]',
            SecuritySeverity.CRITICAL,
            'Potential SQL Injection vulnerability detected'
        ),
        'hardcoded_secrets': (
            r'password|secret|key|token|credential',
            SecuritySeverity.HIGH,
            'Potential hardcoded secrets detected'
        ),
        'unsafe_deserialization': (
            r'pickle\.loads|yaml\.load\s*\([^)]*\)',
            SecuritySeverity.HIGH,
            'Unsafe deserialization detected'
        ),
        'command_injection': (
            r'os\.system|subprocess\.call|eval\s*\(',
            SecuritySeverity.CRITICAL,
            'Potential command injection vulnerability'
        ),
        'insecure_hash': (
            r'md5|sha1',
            SecuritySeverity.MEDIUM,
            'Usage of cryptographically insecure hash function'
        ),
        'xss_vulnerability': (
            r'print\s*\([^)]*\<script\>',
            SecuritySeverity.HIGH,
            'Potential Cross-Site Scripting (XSS) vulnerability detected'
        ),
        'insecure_random': (
            r'random\.\w+\(\)',
            SecuritySeverity.MEDIUM,
            'Usage of insecure random number generator'
        ),
        'file_inclusion': (
            r'open\s*\([^)]*\.\.\/',
            SecuritySeverity.HIGH,
            'Potential file inclusion vulnerability detected'
        )
    }

    def __init__(self):
        self.analysis_history = []

    @staticmethod
    def _calculate_security_score(issues: List[SecurityIssue]) -> float:
        """Calculate a security score based on detected issues"""
        severity_weights = {
            SecuritySeverity.CRITICAL: 10,
            SecuritySeverity.HIGH: 7,
            SecuritySeverity.MEDIUM: 4,
            SecuritySeverity.LOW: 2,
            SecuritySeverity.INFO: 1
        }

        base_score = 100
        for issue in issues:
            base_score -= severity_weights[issue.severity]
        return max(0, base_score)

    def _detect_security_vulnerabilities(self, code: str) -> List[SecurityIssue]:
        """Detect potential security vulnerabilities in the code"""
        security_issues = []

        for pattern_name, (pattern, severity, description) in self.SECURITY_PATTERNS.items():
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                line_number = code[:match.start()].count('\n') + 1
                snippet = code[max(0, match.start() - 50):min(len(code), match.end() + 50)]

                security_issues.append(SecurityIssue(
                    severity=severity,
                    issue_type=pattern_name,
                    description=description,
                    recommendation=self._get_security_recommendation(pattern_name),
                    code_snippet=snippet,
                    line_number=line_number
                ))

        return security_issues

    @staticmethod
    def _get_security_recommendation(issue_type: str) -> str:
        """Get specific security recommendations based on issue type"""
        recommendations = {
            'sql_injection': 'Use parameterized queries or ORM instead of string concatenation.',
            'hardcoded_secrets': 'Store secrets in environment variables or secure secret management systems.',
            'unsafe_deserialization': 'Use safe alternatives like json.loads() or yaml.safe_load().',
            'command_injection': 'Use subprocess.run with shell=False and proper argument splitting.',
            'insecure_hash': 'Use secure hashing algorithms like SHA-256 or better.',
            'xss_vulnerability': 'Sanitize user input and avoid rendering raw HTML.',
            'insecure_random': 'Use cryptographically secure random number generators like `secrets` module.',
            'file_inclusion': 'Validate and sanitize file paths to prevent directory traversal.'
        }
        return recommendations.get(issue_type, 'Review and fix the security issue according to best practices')

    def analyze_code(self, code: str) -> Dict[str, Any]:
        """
        Perform comprehensive security-focused code analysis
        """
        start_time = time.time()

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            logger.error(f"Syntax error in code analysis: {str(e)}")
            return {
                'status': 'error',
                'message': f"Syntax Error: {str(e)}",
                'analysis_time': time.time() - start_time
            }
        except Exception as e:
            logger.error(f"Unexpected error in code analysis: {str(e)}")
            return {
                'status': 'error',
                'message': f"Unexpected Error: {str(e)}",
                'analysis_time': time.time() - start_time
            }

        security_issues = self._detect_security_vulnerabilities(code)

        analysis_results = {
            'status': 'success',
            'security_score': self._calculate_security_score(security_issues),
            'security_issues': security_issues,
            'code_metrics': {
                'loc': len(code.splitlines()),
                'complexity': self._calculate_complexity(tree),
                'security_issues_count': len(security_issues)
            },
            'analysis_time': time.time() - start_time,
            'timestamp': datetime.now().isoformat()
        }

        # Store analysis history
        self.analysis_history.append({
            'timestamp': analysis_results['timestamp'],
            'security_score': analysis_results['security_score'],
            'hash': hashlib.sha256(code.encode()).hexdigest()[:8]
        })

        return analysis_results

    @staticmethod
    def _calculate_complexity(tree: ast.AST) -> int:
        """Calculate code complexity score"""
        complexity = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler)):
                complexity += 1
        return complexity

def generate_live_data():
    """Function to generate live data for analysis"""
    # Example of randomly generated code with potential vulnerabilities
    code_samples = [
        "os.system('rm -rf /')",
        "password = 'mysecret'",
        "import pickle; pickle.loads(b'invalid_pickle_data')",
        "eval('2 + 2')",
        "hashlib.md5('test'.encode())"
    ]
    return random.choice(code_samples)

def display_security_analysis():
    """
    Enhanced Streamlit UI for security-focused code analysis
    """
    st.markdown("## 🔒 Security-Focused Code Analysis")

    # Add a text area for code input
    code_input = st.text_area("Paste your Python code for security analysis", height=300)

    # Add a button to generate live data for analysis
    if st.button("Generate Random Code for Analysis"):
        code_input = generate_live_data()
        st.text_area("Generated Code", value=code_input, height=300)

    # Single button for running code and analyzing security
    if st.button("Run Code and Analyze Security"):
        if code_input:
            st.session_state.code_input = code_input
            analyzer = SecurityAwareCodeAnalyzer()

            # Execute the code
            execution_status = "success"
            execution_message = "Code executed successfully!"
            try:
                exec(code_input)
            except Exception as e:
                execution_status = "error"
                execution_message = f"Error executing code: {str(e)}"
                st.error(execution_message)

            # Analyze the code
            analysis_results = analyzer.analyze_code(code_input)
            if analysis_results['status'] == 'error':
                st.error(analysis_results['message'])
                return

            # Display execution status
            st.markdown("### 🚀 Code Execution Status")
            if execution_status == "success":
                st.success(execution_message)
            else:
                st.error(execution_message)

            # Display security analysis results
            st.markdown("### 🔍 Security Analysis Results")

            # Security Score Display
            col1, col2, col3 = st.columns(3)
            with col1:
                score_color = 'green' if analysis_results['security_score'] >= 80 else 'orange' if analysis_results[
                                                                                                      'security_score'] >= 60 else 'red'
                st.markdown(f"""
                <div style='text-align: center; padding: 20px; background-color: rgba(255,255,255,0.1); border-radius: 10px;'>
                    <h3 style='color: {score_color}'>Security Score</h3>
                    <h2 style='color: {score_color}'>{analysis_results['security_score']}/100</h2>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.metric("Security Issues", analysis_results['code_metrics']['security_issues_count'])

            with col3:
                st.metric("Code Complexity", analysis_results['code_metrics']['complexity'])

            # Security Issues
            if analysis_results['security_issues']:
                st.markdown("### 🚨 Security Issues Detected")
                for issue in analysis_results['security_issues']:
                    with st.expander(f"{issue.severity.value}: {issue.issue_type}"):
                        st.markdown(f"**Description:** {issue.description}")
                        st.markdown(f"**Location:** Line {issue.line_number}")
                        if issue.code_snippet:
                            st.code(issue.code_snippet, language='python')
                        st.info(f"💡 **Recommendation:** {issue.recommendation}")

            # Analysis History
            if analyzer.analysis_history:
                st.markdown("### 📊 Analysis History")
                history_df = pd.DataFrame(analyzer.analysis_history)
                st.line_chart(history_df.set_index('timestamp')['security_score'])

            # Code Preview
            st.markdown("### 📝 Analyzed Code")
            st.code(code_input, language='python')
        else:
            st.warning("Please enter some code to analyze.")
