"""
renderer.py
-----------
Renders email content from Jinja2 templates and a brief dict.

Templates live in src/templates/ and are kept separate from Python code
so they can be edited without touching application logic.

Templates receive:
    brief         — the full parsed brief dict
    max_links     — max number of source links to display (from config)
    delivery_label — footer label string (from config)

Public interface:
    render_html(brief: dict) -> str
    render_plain(brief: dict) -> str
"""

import os

from jinja2 import Environment, FileSystemLoader, select_autoescape

from config import DELIVERY_LABEL, MAX_LINKS

# ---------------------------------------------------------------------------
# Jinja2 environment
# ---------------------------------------------------------------------------
_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

# Autoescape HTML only — plain text template must not be escaped.
_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=select_autoescape(enabled_extensions=("html",)),
    trim_blocks=True,    # Remove newline after block tags (cleaner HTML output)
    lstrip_blocks=True,  # Strip leading whitespace from block tags
)

# ---------------------------------------------------------------------------
# Shared template context
# ---------------------------------------------------------------------------

def _base_context(brief: dict) -> dict:
    """
    Build the shared context dict passed to every template.

    Args:
        brief: Parsed brief dict from fetcher.fetch_brief().

    Returns:
        Context dict with brief, max_links, and delivery_label.
    """
    return {
        "brief": brief,
        "max_links": MAX_LINKS,
        "delivery_label": DELIVERY_LABEL,
    }


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def render_html(brief: dict) -> str:
    """
    Render the HTML email from email.html.

    Args:
        brief: Parsed brief dict.

    Returns:
        Rendered HTML string.
    """
    template = _env.get_template("email.html")
    return template.render(**_base_context(brief))


def render_plain(brief: dict) -> str:
    """
    Render the plain-text email fallback from email.txt.

    Args:
        brief: Parsed brief dict.

    Returns:
        Rendered plain text string.
    """
    template = _env.get_template("email.txt")
    return template.render(**_base_context(brief))
