"""
AI Morning Brief — AWS Lambda Function
Runs every morning at 6:00 AM Panama time (11:00 UTC)
Config is read from config.ini (falls back to env vars for secrets)
"""

import json
import os
import smtplib
import urllib.request
import configparser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


# ── Load config.ini ──────────────────────────────────────────────
cfg = configparser.ConfigParser()
cfg.read(os.path.join(os.path.dirname(__file__), "config.ini"))

def conf(section, key, env_fallback=None, default=""):
    try:
        return cfg.get(section, key).strip()
    except (configparser.NoSectionError, configparser.NoOptionError):
        return os.environ.get(env_fallback, default) if env_fallback else default

ANTHROPIC_API_KEY  = conf("anthropic", "api_key",           "ANTHROPIC_API_KEY")
GMAIL_ADDRESS      = conf("email",     "gmail_address",      "GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = conf("email",     "gmail_app_password", "GMAIL_APP_PASSWORD")
TO_EMAIL           = conf("email",     "to_email",           "TO_EMAIL") or GMAIL_ADDRESS
MAX_LINKS          = int(conf("brief", "max_source_links",   default="2"))
TOPICS             = conf("brief",     "topics",             default="AI Models & Research, Big Tech (Google/Apple/Microsoft/Meta), Agentic AI")
DELIVERY_LABEL     = conf("schedule",  "delivery_label",     default="6:00 AM")


# ── System prompt ────────────────────────────────────────────────
SYSTEM_PROMPT = f"""You are an AI tech journalist writing a sharp, punchy morning brief.
Research today's top news in: {TOPICS}.
Use web search to find today's real news. Return ONLY a valid JSON object — no markdown fences, no preamble, no explanation.

The JSON must follow this exact structure:
{{
  "date": "Friday, March 20, 2026",
  "headline": "One punchy sentence summarizing the single biggest story today",
  "bullets": [
    {{ "topic": "AI Models & Research", "icon": "🧠", "text": "Punchy bullet on the top model or research story." }},
    {{ "topic": "Big Tech",             "icon": "🏢", "text": "Punchy bullet on Google/Apple/Microsoft/Meta." }},
    {{ "topic": "Agentic AI",           "icon": "🤖", "text": "Punchy bullet on agentic AI developments." }},
    {{ "topic": "Quick Hit",            "icon": "⚡", "text": "A fast fact or surprising stat from today." }},
    {{ "topic": "Worth Watching",       "icon": "👀", "text": "A trend or story building momentum." }}
  ],
  "sources": [
    {{ "title": "Exact article headline", "url": "https://real-url.com/article", "outlet": "TechCrunch" }},
    {{ "title": "Exact article headline", "url": "https://real-url.com/article", "outlet": "The Verge" }}
  ],
  "deepDive": {{
    "title": "Deep Dive: [topic name]",
    "body": "3-4 sentences expanding on the most important story — context, implications, what to watch.",
    "source_url": "https://real-url.com/article"
  }}
}}

Rules:
- "sources" must contain exactly {MAX_LINKS} real URLs from your web search results.
- "source_url" in deepDive must be a real URL you visited — never fabricate links.
- Do not include placeholder or example URLs."""


# ── Anthropic API (with tool-use loop) ───────────────────────────
def anthropic_request(payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "web-search-2025-03-05",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_brief() -> dict:
    today = datetime.now().strftime("%A, %B %-d, %Y")
    messages = [{
        "role": "user",
        "content": (
            f"Today is {today}. Search the web for today's top AI and tech news. "
            "Return the JSON morning brief including real source URLs you found. Output only the JSON object."
        ),
    }]

    for _ in range(10):
        data = anthropic_request({
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 4000,
            "tools": [{"type": "web_search_20250305", "name": "web_search"}],
            "system": SYSTEM_PROMPT,
            "messages": messages,
        })

        if data.get("stop_reason") == "end_turn":
            text_block = next((b for b in data["content"] if b["type"] == "text"), None)
            if not text_block:
                raise ValueError("No text block in final API response")
            raw = text_block["text"].strip().replace("```json", "").replace("```", "").strip()
            return json.loads(raw)

        if data.get("stop_reason") == "tool_use":
            messages.append({"role": "assistant", "content": data["content"]})
            messages.append({
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": b["id"], "content": b.get("content", "")}
                    for b in data["content"] if b["type"] == "tool_use"
                ],
            })
            continue

        raise ValueError(f"Unexpected stop_reason: {data.get('stop_reason')}")

    raise RuntimeError("Tool-use loop exceeded max rounds")


# ── Email HTML builder ───────────────────────────────────────────
def build_html(brief: dict) -> str:
    # Bullet rows
    bullets_html = ""
    for b in brief.get("bullets", []):
        bullets_html += f"""
        <tr>
          <td style="padding:13px 0;border-bottom:1px solid #1a2e1a;vertical-align:top;width:34px;font-size:22px;">{b['icon']}</td>
          <td style="padding:13px 0 13px 16px;border-bottom:1px solid #1a2e1a;">
            <div style="color:#a3e635;font-size:10px;letter-spacing:2px;text-transform:uppercase;font-family:monospace;margin-bottom:5px;">{b['topic']}</div>
            <div style="color:#d1fae5;font-size:15px;line-height:1.6;font-family:Georgia,serif;">{b['text']}</div>
          </td>
        </tr>"""

    # Source links
    sources = brief.get("sources", [])[:MAX_LINKS]
    sources_html = ""
    if sources:
        links = ""
        for s in sources:
            outlet_tag = f"<span style='color:#5a7a5a;font-size:11px;font-family:monospace;'> — {s.get('outlet','')}</span>" if s.get("outlet") else ""
            links += f"""
            <div style="margin-bottom:10px;line-height:1.5;">
              <a href="{s['url']}" style="color:#a3e635;font-size:14px;font-family:Georgia,serif;text-decoration:none;">↗ {s['title']}</a>{outlet_tag}
            </div>"""
        sources_html = f"""
  <div style="margin-top:22px;background:#0a150a;border:1px solid #1e3a1e;border-radius:8px;padding:18px 20px;">
    <div style="color:#a3e635;font-size:10px;letter-spacing:2px;text-transform:uppercase;font-family:monospace;margin-bottom:14px;">📰 Read More</div>
    {links}
  </div>"""

    # Deep dive
    dd = brief.get("deepDive", {})
    dd_link = (
        f'<div style="margin-top:14px;"><a href="{dd["source_url"]}" style="color:#a3e635;font-size:12px;font-family:monospace;text-decoration:none;">↗ Read full article</a></div>'
        if dd.get("source_url") else ""
    )

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#050a05;">
<div style="max-width:620px;margin:0 auto;padding:32px 20px;background:#050a05;">

  <div style="border-bottom:2px solid #a3e635;padding-bottom:18px;margin-bottom:24px;">
    <div style="color:#a3e635;font-size:10px;letter-spacing:4px;text-transform:uppercase;font-family:monospace;">Morning Brief &bull; {brief.get('date','')}</div>
    <div style="color:#fff;font-size:22px;font-weight:bold;margin-top:10px;line-height:1.3;font-family:Georgia,serif;">{brief.get('headline','')}</div>
  </div>

  <table style="width:100%;border-collapse:collapse;">{bullets_html}</table>

  {sources_html}

  <div style="margin-top:22px;background:#0d1a0d;border:1px solid #2d4a2d;border-radius:8px;padding:22px;">
    <div style="color:#a3e635;font-size:10px;letter-spacing:2px;text-transform:uppercase;font-family:monospace;margin-bottom:10px;">🔬 {dd.get('title','Deep Dive')}</div>
    <div style="color:#d1fae5;font-size:14px;line-height:1.8;font-family:Georgia,serif;">{dd.get('body','')}</div>
    {dd_link}
  </div>

  <div style="margin-top:28px;text-align:center;color:#2d4a2d;font-size:11px;font-family:monospace;letter-spacing:1px;">
    Generated by Claude &bull; AI Morning Brief &bull; {DELIVERY_LABEL}
  </div>

</div>
</body>
</html>"""


def build_plain(brief: dict) -> str:
    lines = [
        f"AI Morning Brief — {brief.get('date','')}",
        f"\n{brief.get('headline','')}",
        "",
    ]
    for b in brief.get("bullets", []):
        lines.append(f"{b['icon']} {b['topic']}: {b['text']}")
    sources = brief.get("sources", [])[:MAX_LINKS]
    if sources:
        lines += ["", "Read More:"]
        for s in sources:
            lines.append(f"  • {s['title']} ({s.get('outlet','')}) — {s['url']}")
    dd = brief.get("deepDive", {})
    if dd:
        lines += ["", f"Deep Dive — {dd.get('title','')}", dd.get("body","")]
        if dd.get("source_url"):
            lines.append(dd["source_url"])
    return "\n".join(lines)


# ── Send email ───────────────────────────────────────────────────
def send_email(brief: dict):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🧠 AI Morning Brief — {brief.get('date', 'Today')}"
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = TO_EMAIL
    msg.attach(MIMEText(build_plain(brief), "plain"))
    msg.attach(MIMEText(build_html(brief),  "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, TO_EMAIL, msg.as_string())


# ── Lambda entry point ───────────────────────────────────────────
def lambda_handler(event, context):
    print("🧠 Fetching AI Morning Brief...")
    brief = fetch_brief()
    print(f"✅ Brief: {brief.get('headline','')[:80]}")
    for s in brief.get("sources", []):
        print(f"   🔗 {s.get('outlet','')} — {s.get('url','')}")

    print("📧 Sending email...")
    send_email(brief)
    print(f"✅ Sent to {TO_EMAIL}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "status": "sent",
            "headline": brief.get("headline"),
            "sources": brief.get("sources", []),
        }),
    }
