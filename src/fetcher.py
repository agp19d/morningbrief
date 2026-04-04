"""
fetcher.py
----------
Fetches the daily AI Morning Brief using Tavily for web search and
LiteLLM for language-model completion.

Flow:
  1. Run one Tavily search per configured topic to gather fresh news.
  2. Format all search results into a single context string.
  3. Call the configured LLM via LiteLLM, passing the context and a
     system prompt.
  4. Parse, validate, and return the structured JSON brief.

Switching providers requires only a change to ``LLM_MODEL`` in config --
no code changes needed (LiteLLM handles the provider abstraction).

Public interface::

    fetch_brief() -> dict
"""

import json
import logging
import os
from datetime import datetime, timezone

import litellm
from tavily import TavilyClient

from config import LLM_MODEL, MAX_LINKS, TAVILY_API_KEY, TOPICS

logger = logging.getLogger("morning_brief.fetcher")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_MAX_TOKENS: int = 4000
_RESULTS_PER_TOPIC: int = 5

_PROMPT_PATH: str = os.path.join(
    os.path.dirname(__file__), "prompts", "system_prompt.txt",
)

# Required top-level keys in the LLM's JSON response.
_REQUIRED_BRIEF_KEYS: set[str] = {"date", "headline", "bullets", "sources"}

# Suppress LiteLLM's verbose success logging in Lambda CloudWatch logs.
litellm.success_callback = []


# ---------------------------------------------------------------------------
# Prompt loader
# ---------------------------------------------------------------------------

def _load_system_prompt() -> str:
    """Load and format the system prompt from ``system_prompt.txt``.

    Injects runtime config values into the ``{topics}`` and
    ``{max_links}`` placeholders defined in the prompt file.

    Returns:
        The fully formatted system prompt string.

    Raises:
        FileNotFoundError: If ``system_prompt.txt`` does not exist.
    """
    with open(_PROMPT_PATH, "r", encoding="utf-8") as fh:
        template = fh.read()
    return template.format(topics=TOPICS, max_links=MAX_LINKS)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def _search_topics() -> list[dict]:
    """Run one Tavily search per topic and return all results combined.

    Each topic from ``TOPICS`` is searched independently so the LLM
    receives balanced coverage across all configured areas.

    Returns:
        List of Tavily result dicts, each containing at minimum:
        ``title``, ``url``, ``content``, and ``score``.
    """
    client = TavilyClient(api_key=TAVILY_API_KEY)
    topic_list = [t.strip() for t in TOPICS.split(",")]
    results: list[dict] = []

    for topic in topic_list:
        logger.info("Searching: %s", topic)
        response = client.search(
            query=f"{topic} news today",
            search_depth="basic",
            max_results=_RESULTS_PER_TOPIC,
        )
        results.extend(response.get("results", []))

    logger.info("Tavily returned %d total results", len(results))
    return results


def _format_context(results: list[dict]) -> str:
    """Convert Tavily search results into a readable context string.

    Args:
        results: List of Tavily result dicts.

    Returns:
        A formatted string with title, URL, and a content snippet per
        result, separated by ``---`` dividers.
    """
    lines: list[str] = []
    for result in results:
        lines.append(f"Title: {result.get('title', 'Untitled')}")
        lines.append(f"URL:   {result.get('url', '')}")
        content = result.get("content", "").strip()[:600]
        lines.append(f"Excerpt: {content}")
        lines.append("---")
    return "\n".join(lines)


def _validate_brief(brief: dict) -> dict:
    """Validate that the parsed brief contains all required fields.

    Args:
        brief: The parsed JSON dict from the LLM response.

    Returns:
        The validated brief dict (unchanged).

    Raises:
        ValueError: If required keys are missing or ``bullets``/``sources``
                    are not lists.
    """
    missing = _REQUIRED_BRIEF_KEYS - brief.keys()
    if missing:
        raise ValueError(
            f"LLM response missing required keys: {', '.join(sorted(missing))}"
        )

    if not isinstance(brief.get("bullets"), list):
        raise ValueError("'bullets' must be a list")

    if not isinstance(brief.get("sources"), list):
        raise ValueError("'sources' must be a list")

    return brief


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def fetch_brief() -> dict:
    """Search today's news and generate the morning brief via LiteLLM.

    Steps:
        1. Search each topic with Tavily.
        2. Format results as LLM context.
        3. Call the configured LLM model via LiteLLM.
        4. Strip any accidental Markdown fences and parse the JSON.
        5. Validate the response structure.

    Returns:
        Parsed brief as a dict with keys:
        ``date``, ``headline``, ``bullets``, ``sources``, ``deepDive``.

    Raises:
        RuntimeError: If Tavily returns no results.
        json.JSONDecodeError: If the model's response is not valid JSON.
        ValueError: If the response is missing required fields.
        litellm.exceptions.APIError: On LLM provider API failures.
    """
    system_prompt = _load_system_prompt()

    today = datetime.now(tz=timezone.utc).strftime("%A, %B %d, %Y").replace(" 0", " ")

    # --- Step 1: Search ---
    results = _search_topics()
    if not results:
        raise RuntimeError(
            "Tavily returned no search results — check TAVILY_API_KEY"
        )

    context = _format_context(results)

    # --- Step 2: Generate brief ---
    logger.info("Calling LLM: %s", LLM_MODEL)
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
                    "Generate the morning brief JSON using only URLs "
                    "from the search results above."
                ),
            },
        ],
    )

    # --- Step 3: Parse and validate ---
    raw: str = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    brief = json.loads(raw)
    return _validate_brief(brief)
