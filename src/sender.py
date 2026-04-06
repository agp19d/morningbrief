"""
sender.py
---------
Sends the morning brief as a multipart email via AWS SES.

Attaches both a plain-text fallback and an HTML version, following
the MIME ``multipart/alternative`` standard.  Email clients display the
last attached part they support -- HTML for modern clients, plain text
for everything else.

Public interface::

    send_email(brief: dict) -> None
"""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import boto3

from config import SES_FROM_EMAIL, SES_REGION, TO_EMAIL
from renderer import render_html, render_plain

logger = logging.getLogger("morning_brief.sender")


def send_email(brief: dict) -> None:
    """Render and send the morning brief to the configured recipient.

    Uses AWS SES ``send_raw_email`` so we can send a full MIME
    multipart/alternative message (HTML + plain-text fallback).
    Credentials come from the Lambda execution role automatically.

    Args:
        brief: Parsed brief dict from :func:`fetcher.fetch_brief`.

    Raises:
        botocore.exceptions.ClientError: On any SES API failure.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"\U0001f9e0 AI Morning Brief \u2014 {brief.get('date', 'Today')}"
    msg["From"] = SES_FROM_EMAIL
    msg["To"] = TO_EMAIL

    # Plain text first, HTML second — clients render the last supported part.
    msg.attach(MIMEText(render_plain(brief), "plain", "utf-8"))
    msg.attach(MIMEText(render_html(brief), "html", "utf-8"))

    client = boto3.client("ses", region_name=SES_REGION)

    logger.info("Sending email via SES from %s to %s", SES_FROM_EMAIL, TO_EMAIL)
    client.send_raw_email(
        Source=SES_FROM_EMAIL,
        Destinations=[TO_EMAIL],
        RawMessage={"Data": msg.as_string()},
    )

    logger.info("Email delivered to %s", TO_EMAIL)
