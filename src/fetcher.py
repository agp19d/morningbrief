"""
fetcher.py
----------
Fetches the daily AI Morning Brief using Tavily for web search and
LiteLLM for language model completion.

Flow:
  1. Run one Tavily search per configured topic to gather fresh news.
  2. Format all search results into a single context string.
  3. Call the configured LLM via LiteLLM, passing the context and system prompt.
  4. Parse and return the structured JSON brief from the model's response.

Switching providers requires only a change to LLM_MODEL in config — no
code changes needed (LiteLLM handles the provider abstraction).

Public interface:
    fetch_brief() -> dict
"""

import json
import os
from datetime import datetime

import litellm
from tavily import TavilyClient

from config import LLM_MODEL, MAX_LINKS, TAVILY_API_KEY, TOPICS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_MAX_TOKENS = 4000

# Number of search results to retrieve per topic query.
_RESULTS_PER_TOPIC = 5

# Path to the system prompt template file.
_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.txt")

# Suppress LiteLLM's verbose success logging in Lambda CloudWatch logs.
litellm.success_callback = []


# ---------------------------------------------------------------------------
# Prompt loader
# ---------------------------------------------------------------------------

def _load_system_prompt() -> str:
    """
    Load and format the system prompt from system_prompt.txt.

    Injects runtime config values into the {topics} and {max_links}
    placeholders defined in the prompt file.

    Returns:
        The fully formatted system prompt string.

    Raises:
        FileNotFoundError: If system_prompt.txt does not exist.
    """
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        template = f.read()
    return template.format(topics=TOPICS, max_links=MAX_LINKS)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def _search_topics() -> list[dict]:
    """
    Run one Tavily search per topic and return all results combined.

    Each topic from TOPICS is searched independently so the LLM receives
    balanced coverage across all configured areas.

    Returns:
        List of Tavily result dicts, each containing:
        title, url, content, score, and (optionally) published_date.
    """
    client = TavilyClient(api_key=TAVILY_API_KEY)
    topic_list = [t.strip() for t in TOPICS.split(",")]
    results = []

    for topic in topic_list:
        response = client.search(
            query=f"{topic} news today",
            search_depth="basic",       # "basic" is faster; "advanced" is deeper
            max_results=_RESULTS_PER_TOPIC,
        )
        results.extend(response.get("results", []))

    return results


def _format_context(results: list[dict]) -> str:
    """
    Convert Tavily search results into a readable context string for the LLM.

    Args:
        results: List of Tavily result dicts.

    Returns:
        A formatted string with title, URL, and a content snippet per result.
    """
    lines = []
    for r in results:
        lines.append(f"Title: {r.get('title', 'Untitled')}")
        lines.append(f"URL:   {r.get('url', '')}")
        # Truncate long snippets to keep the context window manageable.
        content = r.get("content", "").strip()[:600]
        lines.append(f"Excerpt: {content}")
        lines.append("---")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def fetch_brief() -> dict:
    """
    Search today's news and generate the morning brief via LiteLLM.

    Steps:
        1. Search each topic with Tavily.
        2. Format results as LLM context.
        3. Call the configured LLM model via LiteLLM.
        4. Strip any accidental markdown fences and parse the JSON response.

    Returns:
        Parsed brief as a dict with keys:
            date, headline, bullets, sources, deepDive.

    Raises:
        RuntimeError: If Tavily returns no results.
        json.JSONDecodeError: If the model's response is not valid JSON.
        litellm.exceptions.APIError: On LLM provider API failures.
    """
    system_prompt = _load_system_prompt()

    # Cross-platform today string — %-d is Linux-only, so strip via replace.
    today = datetime.now().strftime("%A, %B %d, %Y").replace(" 0", " ")

    # --- Step 1: Search ---
    results = _search_topics()
    if not results:
        raise RuntimeError("Tavily returned no search results — check TAVILY_API_KEY")

    context = _format_context(results)

    # --- Step 2: Generate brief ---
    response = litellm.completion(
        model=LLM_MODEL,
        max_tokens=_MAX_TOKENS,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Today is {today}.\n\n"
                    f"Here are today's search results:\n\n{context}\n\n"
                    "Generate the morning brief JSON using only URLs from the search results above."
                ),
            },
        ],
    )

    # --- Step 3: Parse response ---
    raw = response.choices[0].message.content.strip()

    # Strip accidental markdown fences before parsing.
    raw = raw.replace("```json", "").replace("```", "").strip()

    return json.loads(raw)
