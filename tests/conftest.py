"""Shared test fixtures for the Morning Brief test suite."""

import pytest


@pytest.fixture()
def sample_brief() -> dict:
    """A minimal valid brief dict matching the LLM output schema."""
    return {
        "date": "Friday, April 4, 2026",
        "headline": "OpenAI launches GPT-5 with real-time reasoning",
        "bullets": [
            {
                "topic": "AI Models & Research",
                "icon": "\U0001f9e0",
                "text": "GPT-5 benchmarks surpass previous SOTA on MMLU.",
            },
            {
                "topic": "Big Tech",
                "icon": "\U0001f3e2",
                "text": "Google responds with Gemini 2.5 announcement.",
            },
            {
                "topic": "Agentic AI",
                "icon": "\U0001f916",
                "text": "Agentic frameworks see 3x adoption in enterprise.",
            },
            {
                "topic": "Quick Hit",
                "icon": "\u26a1",
                "text": "NVIDIA stock hits all-time high on AI demand.",
            },
            {
                "topic": "Worth Watching",
                "icon": "\U0001f440",
                "text": "EU AI Act enforcement begins next quarter.",
            },
        ],
        "sources": [
            {
                "title": "OpenAI Launches GPT-5",
                "url": "https://example.com/gpt5",
                "outlet": "TechCrunch",
            },
            {
                "title": "Google Announces Gemini 2.5",
                "url": "https://example.com/gemini",
                "outlet": "The Verge",
            },
        ],
        "deepDive": {
            "title": "Deep Dive: GPT-5 Architecture",
            "body": "The new model introduces a hybrid reasoning engine.",
            "source_url": "https://example.com/gpt5-deep",
        },
    }


@pytest.fixture()
def tavily_results() -> list[dict]:
    """Simulated Tavily search results."""
    return [
        {
            "title": "OpenAI Launches GPT-5",
            "url": "https://example.com/gpt5",
            "content": "OpenAI today announced GPT-5, a new model with real-time reasoning.",
            "score": 0.95,
        },
        {
            "title": "Google Announces Gemini 2.5",
            "url": "https://example.com/gemini",
            "content": "Google responds to OpenAI with Gemini 2.5 featuring agents.",
            "score": 0.90,
        },
    ]
