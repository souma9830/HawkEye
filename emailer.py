import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

def send_alert_email(recipient, subject, body, attachments=None):
    """Send an email alert with optional attachments"""
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    sender_email = smtp_user
    
    if not all([smtp_server, smtp_user, smtp_password, recipient]):
        print(f"[EMAIL ERROR] Missing configuration parameters")
        return False

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject

    msg.attach(MIMEText(body, "plain"))

    if attachments:
        for path in attachments:
            if os.path.isfile(path):
                with open(path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(path))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(path)}"'
                    msg.attach(part)
            else:
                print(f"[EMAIL WARNING] Attachment not found: {path}")

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            print(f"[EMAIL SENT] to {recipient}")
            return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False