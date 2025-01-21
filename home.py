import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def create_summary_metrics():
    """Create enhanced summary metrics with better styling."""
    # [Previous metrics code remains the same...]
    try:
        metrics = {
            'total_scans': 150,
            'total_high_risks': 5,
            'total_medium_risks': 12,
            'total_low_risks': 25,
            'success_rate': 96.7
        }

        cols = st.columns(5)

        with cols[0]:
            st.metric(
                "Active Scans",
                metrics['total_scans'],
                delta="+1 from last week",
                help="Total number of active security scans"
            )

        with cols[1]:
            st.metric(
                "Critical Alerts",
                f"↑ {metrics['total_high_risks']}",
                delta="-2 from last week",
                delta_color="inverse",
                help="Number of high-risk security alerts"
            )

        with cols[2]:
            st.metric(
                "Medium Alerts",
                f"→ {metrics['total_medium_risks']}",
                delta="No change",
                help="Number of medium-risk security alerts"
            )

        with cols[3]:
            st.metric(
                "Low Alerts",
                f"↓ {metrics['total_low_risks']}",
                delta="+3 from last week",
                delta_color="inverse",
                help="Number of low-risk security alerts"
            )

        with cols[4]:
            success_rate = metrics['success_rate']
            st.metric(
                "Success Rate",
                f"{success_rate:.1f}%",
                delta=f"{success_rate - 95:.1f}%",
                help="Percentage of scans completed successfully"
            )

    except Exception as e:
        st.error(f"Error loading summary metrics: {e}")


def create_all_charts(alerts_df):
    """Create all charts in a grid layout."""
    # Create two columns for charts
    col1, col2 = st.columns(2)

    with col1:
        # Daily Trends Chart
        fig_trends = go.Figure()

        for alert_type, color in zip(['high', 'medium', 'low'], ['#dc2626', '#f97316', '#eab308']):
            fig_trends.add_trace(go.Scatter(
                x=alerts_df['date'],
                y=alerts_df[alert_type],
                name=f'{alert_type.capitalize()} Alerts',
                line=dict(color=color, width=2),
                fill='tonexty'
            ))

        fig_trends.update_layout(
            title='Alert Trends',
            height=400,
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        st.plotly_chart(fig_trends, use_container_width=True)

        # Cumulative Trends
        fig_cumulative = go.Figure()

        for alert_type, color in zip(['high', 'medium', 'low'], ['#dc2626', '#f97316', '#eab308']):
            fig_cumulative.add_trace(go.Scatter(
                x=alerts_df['date'],
                y=alerts_df[alert_type].cumsum(),
                name=f'Cumulative {alert_type.capitalize()}',
                line=dict(color=color, width=2),
                stackgroup='one'
            ))

        fig_cumulative.update_layout(
            title='Cumulative Alerts',
            height=400,
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        st.plotly_chart(fig_cumulative, use_container_width=True)

    with col2:
        # Distribution Pie Chart
        total_alerts = alerts_df['high'].sum() + alerts_df['medium'].sum() + alerts_df['low'].sum()

        fig_pie = go.Figure(data=[go.Pie(
            labels=['Critical', 'Medium', 'Low'],
            values=[alerts_df['high'].sum(), alerts_df['medium'].sum(), alerts_df['low'].sum()],
            hole=.4,
            marker=dict(colors=['#dc2626', '#f97316', '#eab308'])
        )])

        fig_pie.update_layout(
            title='Alert Distribution',
            height=400,
            annotations=[dict(text=f'Total\n{total_alerts}', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )

        st.plotly_chart(fig_pie, use_container_width=True)

        # Alert Bar Chart
        fig_bar = go.Figure()

        fig_bar.add_trace(go.Bar(
            x=alerts_df['date'],
            y=alerts_df['high'] + alerts_df['medium'] + alerts_df['low'],
            name='Total Alerts',
            marker_color='#3b82f6'
        ))

        fig_bar.update_layout(
            title='Daily Total Alerts',
            height=400,
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        st.plotly_chart(fig_bar, use_container_width=True)

def show_tool_card(icon, title, description, features, button_text, view_state):
    """Display a tool card with consistent styling."""
    st.markdown(f"""
        <div class="tool-card">
            <h3>{icon} {title}</h3>
            <p>{description}</p>
            <ul>
                {''.join([f'<li>{feature}</li>' for feature in features])}
            </ul>
        </div>
    """, unsafe_allow_html=True)

    if st.button(f"Launch {button_text}", key=f"btn_{title.lower().replace(' ', '_')}"):
        st.session_state.current_view = view_state
        st.rerun()


def show_home_page():
    """Display the enhanced home page with live dashboard."""
    st.title("🛡️ Web Security Suite")

    # Project description
    st.markdown("""
        ### Enterprise Security Dashboard

        This advanced security platform provides real-time monitoring, vulnerability assessment,
        and threat detection capabilities for your web applications. Monitor key metrics,
        track security trends, and manage security tools from a single dashboard.
    """)

    # Metrics section
    st.markdown("## 📈 Security Overview")
    create_summary_metrics()

    # Charts section
    st.markdown("## 📊 Security Analytics")
    # Sample data - replace with actual data
    alerts_df = pd.DataFrame({
        'date': pd.date_range(start='2024-01-14', periods=7),
        'high': [2, 1, 3, 0, 1, 2, 1],
        'medium': [4, 3, 5, 4, 2, 3, 4],
        'low': [8, 6, 7, 5, 4, 6, 5]
    })
    create_all_charts(alerts_df)

    # Tools section
    st.markdown("## 🛠️ Security Tools")
    col1, col2 = st.columns(2)

    with col1:
        show_tool_card(
            "🌐", "OWASP ZAP Scanner",
            "Enterprise-grade vulnerability detection and assessment.",
            ["Advanced crawling & scanning", "Custom scan policies", "Detailed reporting"],
            "ZAP Scanner", "zap_tool"
        )

        show_tool_card(
            "📅", "Scan Scheduler",
            "Automated security scan management.",
            ["Smart scheduling", "Schedule Automation", "Customizable alerts"],
            "Scheduler", "schedule"
        )

    with col2:
        show_tool_card(
            "🔍", "Malicious URL Scanner",
            "AI-powered URL analysis and threat detection.",
            ["Real-time monitoring", "Behavioral analysis", "Threat intelligence"],
            "URL Scanner", "url_scanner"
        )

        show_tool_card(
            "🔒", "Code Analysis",
            "Advanced source code security scanner.",
            ["Python Code Analysis", "Dependency checking", "Compliance validation"],
            "Code Scanner", "code_analysis"
        )