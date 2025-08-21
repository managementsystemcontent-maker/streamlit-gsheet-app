import os
import smtplib
from email.message import EmailMessage

def send_email(subject: str, html_body: str, to_emails, attachments=None,
               sender=None, password=None, smtp_host=None, smtp_port=None):
    sender = sender or os.getenv("EMAIL_SENDER")
    password = password or os.getenv("EMAIL_PASSWORD")
    smtp_host = smtp_host or os.getenv("EMAIL_SMTP", "smtp.gmail.com")
    smtp_port = int(smtp_port or os.getenv("EMAIL_PORT", "465"))

    if isinstance(to_emails, str):
        # allow comma-separated
        to_emails = [e.strip() for e in to_emails.split(",") if e.strip()]

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(to_emails)
    msg.set_content("HTML only")
    msg.add_alternative(html_body, subtype="html")

    for att in attachments or []:
        filename, mime, data = att  # mime like "text/calendar"
        maintype, subtype = mime.split("/", 1)
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)

    with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
        server.login(sender, password)
        server.send_message(msg)