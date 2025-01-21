import smtplib
from email.mime.multipart import MIMEMultipart  # Import MIMEMultipart
from email.mime.text import MIMEText  # Import MIMEText for the email body
import streamlit as st  # Only if using Streamlit secrets

def send_email(subject, body_plain, body_html, to_email):
    # Email settings
    sender_email = "2012324@szabist-isb.pk"  # Replace with your email
    sender_password = "hearthacker69" # Access the password from Streamlit secrets

    # Create a MIMEMultipart message
    msg = MIMEMultipart('alternative')  # 'alternative' for plain text and HTML
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach the plain text and HTML versions of the email body
    part1 = MIMEText(body_plain, 'plain')
    part2 = MIMEText(body_html, 'html')
    msg.attach(part1)
    msg.attach(part2)

    try:
        # Connect to the SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Enable TLS encryption
        server.login(sender_email, sender_password)  # Log in to the email account

        # Send the email
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()

        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception details: {str(e)}")

# Example usage
send_email(
    subject="Test Email",
    body_plain="This is a plain text email.",
    body_html="<h1>This is an HTML email.</h1>",
    to_email="recipient@example.com"
)