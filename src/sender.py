"""
sender.py
---------
Sends the morning brief as a multipart email via Gmail SMTP.

Attaches both a plain-text fallback and an HTML version, following
the MIME multipart/alternative standard. Email clients display the
last attached part they support — HTML for modern clients, plain text
for everything else.

Public interface:
    send_email(brief: dict) -> None
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, TO_EMAIL
from renderer import render_html, render_plain


def send_email(brief: dict) -> None:
    """
    Render and send the morning brief to the configured recipient.

    Connects to Gmail's SMTP server over SSL (port 465) and authenticates
    using the configured Gmail App Password.

    Args:
        brief: Parsed brief dict from fetcher.fetch_brief().

    Raises:
        smtplib.SMTPAuthenticationError: If Gmail credentials are invalid.
        smtplib.SMTPException: On any other SMTP failure.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🧠 AI Morning Brief — {brief.get('date', 'Today')}"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = TO_EMAIL

    # Plain text must be attached first; HTML second.
    # Clients render the last supported part (prefer HTML over plain text).
    msg.attach(MIMEText(render_plain(brief), "plain", "utf-8"))
    msg.attach(MIMEText(render_html(brief), "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, TO_EMAIL, msg.as_string())
