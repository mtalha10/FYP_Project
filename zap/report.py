# report.py
from io import BytesIO, StringIO
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
import json
from datetime import datetime

class ReportGenerator:
    @staticmethod
    def generate_pdf_report(scan_id, url, metrics):
        """
        Generate a detailed PDF report for the scan.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph(f"Security Scan Report for {url}", styles['Title']))
        story.append(Spacer(1, 12))

        # Summary
        story.append(Paragraph("Scan Summary", styles['Heading2']))
        summary_data = [
            ["Total Alerts", metrics['total_alerts']],
            ["High Risks", metrics['risk_distribution'].get('High', 0)],
            ["Medium Risks", metrics['risk_distribution'].get('Medium', 0)],
            ["Low Risks", metrics['risk_distribution'].get('Low', 0)]
        ]
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 12))

        # Risk Distribution Chart
        story.append(Paragraph("Risk Distribution", styles['Heading2']))
        plt.figure(figsize=(6, 4))
        plt.pie(metrics['risk_distribution'].values(), labels=metrics['risk_distribution'].keys(), autopct='%1.1f%%')
        plt.title("Risk Distribution")
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        story.append(Image(img_buffer, width=300, height=200))
        story.append(Spacer(1, 12))

        # Top Vulnerabilities
        story.append(Paragraph("Top Vulnerabilities", styles['Heading2']))
        vuln_data = [["Vulnerability", "Count"]] + list(metrics['top_vulnerabilities'].items())
        vuln_table = Table(vuln_data)
        vuln_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(vuln_table)

        doc.build(story)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_csv_report(metrics):
        """
        Generate a CSV report containing detailed scan results.
        """
        output = StringIO()

        # Create DataFrames for different sections
        summary_df = pd.DataFrame({
            'Metric': ['Total Alerts', 'High Risks', 'Medium Risks', 'Low Risks'],
            'Value': [
                metrics['total_alerts'],
                metrics['risk_distribution'].get('High', 0),
                metrics['risk_distribution'].get('Medium', 0),
                metrics['risk_distribution'].get('Low', 0)
            ]
        })

        vulns_df = pd.DataFrame({
            'Vulnerability': metrics['top_vulnerabilities'].keys(),
            'Count': metrics['top_vulnerabilities'].values()
        })

        # Write to CSV
        summary_df.to_csv(output, index=False)
        output.write('\n\nTop Vulnerabilities\n')
        vulns_df.to_csv(output, index=False)

        output.seek(0)
        return output.getvalue()

    @staticmethod
    def generate_json_report(metrics):
        """
        Generate a JSON report with detailed scan results.
        """
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_alerts': metrics['total_alerts'],
                'risk_distribution': metrics['risk_distribution']
            },
            'vulnerabilities': metrics['top_vulnerabilities'],
            'raw_metrics': metrics
        }
        return json.dumps(report_data, indent=2)