"""
lambda_function.py
------------------
AWS Lambda entry point for the AI Morning Brief.

This module is intentionally thin -- it only wires together the three
pipeline stages (fetch -> render -> send) and returns a structured
response to the Lambda runtime.

Handler: ``lambda_function.lambda_handler``
"""

import json
import logging

from config import TO_EMAIL, validate_runtime_config
from fetcher import fetch_brief
from sender import send_email

logger = logging.getLogger("morning_brief")
logger.setLevel(logging.INFO)


def lambda_handler(event: dict, context: object) -> dict:
    """AWS Lambda handler -- fetch, render, and send the morning brief.

    Triggered daily by an EventBridge (CloudWatch Events) cron rule.
    Can also be invoked manually via the AWS Console or CLI for testing.

    Args:
        event:   Lambda event payload (unused for scheduled invocations).
        context: Lambda runtime context (unused).

    Returns:
        Dict with ``statusCode`` 200 on success (body contains the brief
        headline and sources) or 500 on failure (body contains the error).
    """
    try:
        validate_runtime_config()

        logger.info("Fetching AI Morning Brief...")
        brief = fetch_brief()

        headline = brief.get("headline", "")
        logger.info("Brief ready: %s", headline[:80])
        for source in brief.get("sources", []):
            logger.info(
                "  Source: %s — %s",
                source.get("outlet", ""),
                source.get("url", ""),
            )

        logger.info("Sending email to %s...", TO_EMAIL)
        send_email(brief)
        logger.info("Email sent successfully.")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "sent",
                "headline": brief.get("headline"),
                "sources": brief.get("sources", []),
            }),
        }

    except Exception:
        logger.exception("Morning Brief pipeline failed")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "error",
                "error": "Pipeline failed — check CloudWatch logs for details.",
            }),
        }
