"""
config.py
---------
Centralised configuration loader for the AI Morning Brief.

Priority order (highest to lowest):
  1. config.ini  — local development overrides (git-ignored, never committed)
  2. Environment variables — used in AWS Lambda (injected by Terraform)
  3. Hard-coded defaults — safe fallbacks for non-secret settings only

Secrets (api keys, gmail_app_password) must never be hard-coded.
In production, leave config.ini blank and rely on environment variables.

Switching LLM providers:
  Change LLM_MODEL to the desired provider/model string (e.g. "openai/gpt-4o-mini")
  and set the corresponding API key environment variable (e.g. OPENAI_API_KEY).
  LiteLLM resolves the right key automatically from the model prefix.
"""

import configparser
import os

# ---------------------------------------------------------------------------
# Load config.ini from the project root (one level above src/).
# Silently ignored when the file does not exist (e.g. in Lambda).
# ---------------------------------------------------------------------------
_cfg = configparser.ConfigParser()
_cfg.read(os.path.join(os.path.dirname(__file__), "..", "config.ini"))


def _conf(section: str, key: str, env_fallback: str = None, default: str = "") -> str:
    """
    Resolve a config value using a three-tier fallback chain.

    Args:
        section:      INI file section name (e.g. "llm").
        key:          INI file key (e.g. "model").
        env_fallback: Name of the environment variable to check when the
                      INI key is absent or the file does not exist.
        default:      Value returned when both INI and env var are absent.

    Returns:
        The resolved configuration value as a stripped string.
    """
    try:
        return _cfg.get(section, key).strip()
    except (configparser.NoSectionError, configparser.NoOptionError):
        if env_fallback:
            return os.environ.get(env_fallback, default)
        return default


# ---------------------------------------------------------------------------
# LLM (via LiteLLM — provider-agnostic)
# ---------------------------------------------------------------------------
# Model string in LiteLLM format: "provider/model-name"
# Examples: "anthropic/claude-haiku-4-5-20251001", "openai/gpt-4o-mini",
#           "gemini/gemini-1.5-flash"
LLM_MODEL = _conf("llm", "model", env_fallback="LLM_MODEL",
                   default="anthropic/claude-haiku-4-5-20251001")

# API key for the configured provider.
# LiteLLM reads standard env vars (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)
# automatically. We load from config.ini here and inject into the environment
# so LiteLLM can find it during local development.
_LLM_API_KEY = _conf("llm", "api_key", env_fallback="ANTHROPIC_API_KEY")

# Map LiteLLM provider prefixes to their expected environment variable names.
_PROVIDER_ENV_KEYS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai":    "OPENAI_API_KEY",
    "gemini":    "GEMINI_API_KEY",
    "google":    "GOOGLE_API_KEY",
}

if _LLM_API_KEY and "/" in LLM_MODEL:
    _provider = LLM_MODEL.split("/")[0].lower()
    _env_key_name = _PROVIDER_ENV_KEYS.get(_provider)
    if _env_key_name:
        # Inject into env so LiteLLM can pick it up without extra configuration.
        os.environ.setdefault(_env_key_name, _LLM_API_KEY)

# ---------------------------------------------------------------------------
# Tavily (web search)
# ---------------------------------------------------------------------------
TAVILY_API_KEY = _conf("tavily", "api_key", env_fallback="TAVILY_API_KEY")

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
GMAIL_ADDRESS = _conf("email", "gmail_address", env_fallback="GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = _conf("email", "gmail_app_password", env_fallback="GMAIL_APP_PASSWORD")

# If no explicit recipient is set, the brief is sent to the sender's own address.
TO_EMAIL = _conf("email", "to_email", env_fallback="TO_EMAIL") or GMAIL_ADDRESS

# ---------------------------------------------------------------------------
# Brief content
# ---------------------------------------------------------------------------
# Maximum number of source article links included in each email.
MAX_LINKS = int(_conf("brief", "max_source_links", default="2"))

# Comma-separated list of news topics injected into the AI system prompt.
TOPICS = _conf(
    "brief",
    "topics",
    default="AI Models & Research, Big Tech (Google/Apple/Microsoft/Meta), Agentic AI",
)

# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------
# Cosmetic label shown in the email footer. Does not affect the cron schedule.
DELIVERY_LABEL = _conf("schedule", "delivery_label", default="6:00 AM")
