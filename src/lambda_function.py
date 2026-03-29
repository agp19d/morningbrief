"""
lambda_function.py
------------------
AWS Lambda entry point for the AI Morning Brief.

This module is intentionally thin — it only wires together the three
pipeline stages (fetch → render → send) and returns a structured
response to the Lambda runtime.

Handler: src.lambda_function.lambda_handler
"""

import json

from config import TO_EMAIL
from fetcher import fetch_brief
from sender import send_email


def lambda_handler(event: dict, context: object) -> dict:
    """
    AWS Lambda handler — fetch, render, and send the morning brief.

    Triggered daily by an EventBridge (CloudWatch Events) cron rule.
    Can also be invoked manually via the AWS Console or CLI for testing.

    Args:
        event:   Lambda event payload (unused for scheduled invocations).
        context: Lambda runtime context (unused).

    Returns:
        Dict with statusCode 200 and a JSON body containing:
            status    — "sent"
            headline  — the brief's top headline
            sources   — list of source dicts {title, url, outlet}

    Raises:
        Exception: Any unhandled error causes Lambda to mark the
                   invocation as failed and log the traceback to CloudWatch.
    """
    print("Fetching AI Morning Brief...")
    brief = fetch_brief()
    print(f"Brief ready: {brief.get('headline', '')[:80]}")
    for s in brief.get("sources", []):
        print(f"  Source: {s.get('outlet', '')} — {s.get('url', '')}")

    print(f"Sending email to {TO_EMAIL}...")
    send_email(brief)
    print("Email sent.")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "status": "sent",
            "headline": brief.get("headline"),
            "sources": brief.get("sources", []),
        }),
    }
