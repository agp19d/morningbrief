"""
sender.py
---------
Sends the morning brief as a multipart email via Gmail SMTP.

Attaches both a plain-text fallback and an HTML version, following
the MIME ``multipart/alternative`` standard.  Email clients display the
last attached part they support -- HTML for modern clients, plain text
for everything else.

Public interface::

    send_email(brief: dict) -> None
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, TO_EMAIL
from renderer import render_html, render_plain

logger = logging.getLogger("morning_brief.sender")

# Gmail SMTP constants
_SMTP_HOST: str = "smtp.gmail.com"
_SMTP_PORT: int = 465
_SMTP_TIMEOUT_SECS: int = 30


def send_email(brief: dict) -> None:
    """Render and send the morning brief to the configured recipient.

    Connects to Gmail's SMTP server over SSL (port 465) with a
    connection timeout and authenticates using the configured Gmail
    App Password.

    Args:
        brief: Parsed brief dict from :func:`fetcher.fetch_brief`.

    Raises:
        smtplib.SMTPAuthenticationError: If Gmail credentials are invalid.
        smtplib.SMTPException: On any other SMTP failure.
        TimeoutError: If the SMTP connection cannot be established within
                      the timeout window.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"\U0001f9e0 AI Morning Brief \u2014 {brief.get('date', 'Today')}"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = TO_EMAIL

    # Plain text first, HTML second — clients render the last supported part.
    msg.attach(MIMEText(render_plain(brief), "plain", "utf-8"))
    msg.attach(MIMEText(render_html(brief), "html", "utf-8"))

    logger.info("Connecting to %s:%d", _SMTP_HOST, _SMTP_PORT)
    with smtplib.SMTP_SSL(_SMTP_HOST, _SMTP_PORT, timeout=_SMTP_TIMEOUT_SECS) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, TO_EMAIL, msg.as_string())

    logger.info("Email delivered to %s", TO_EMAIL)
