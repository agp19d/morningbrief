"""
config.py
---------
Centralised configuration loader for the AI Morning Brief.

Priority order (highest to lowest):
  1. config.ini  -- local development overrides (git-ignored, never committed)
  2. Environment variables -- used in AWS Lambda (injected by Terraform)
  3. Hard-coded defaults -- safe fallbacks for non-secret settings only

Secrets (API keys, gmail_app_password) must never be hard-coded.
In production, leave config.ini absent and rely on environment variables.

Switching LLM providers:
  Change LLM_MODEL to the desired provider/model string
  (e.g. ``"openai/gpt-4o-mini"``) and set the corresponding API key
  environment variable (e.g. ``OPENAI_API_KEY``).
  LiteLLM resolves the right key automatically from the model prefix.
"""

import configparser
import os


class ConfigError(Exception):
    """Raised when a required configuration value is missing."""


# ---------------------------------------------------------------------------
# Load config.ini from the project root (one level above src/).
# Silently ignored when the file does not exist (e.g. in Lambda).
# ---------------------------------------------------------------------------
_cfg = configparser.ConfigParser()
_cfg.read(os.path.join(os.path.dirname(__file__), "..", "config.ini"))


def _conf(
    section: str,
    key: str,
    env_fallback: str | None = None,
    default: str = "",
    required: bool = False,
) -> str:
    """Resolve a config value using a three-tier fallback chain.

    Args:
        section:      INI file section name (e.g. ``"llm"``).
        key:          INI file key (e.g. ``"model"``).
        env_fallback: Name of the environment variable to check when the
                      INI key is absent or the file does not exist.
        default:      Value returned when both INI and env var are absent.
        required:     If ``True``, raise :class:`ConfigError` when the
                      resolved value is empty.

    Returns:
        The resolved configuration value as a stripped string.

    Raises:
        ConfigError: If *required* is ``True`` and no value is found.
    """
    try:
        value = _cfg.get(section, key).strip()
    except (configparser.NoSectionError, configparser.NoOptionError):
        value = os.environ.get(env_fallback, default) if env_fallback else default

    if required and not value:
        sources = f"config.ini [{section}].{key}"
        if env_fallback:
            sources += f" or ${env_fallback}"
        raise ConfigError(f"Required config missing: {sources}")

    return value


# ---------------------------------------------------------------------------
# LLM (via LiteLLM -- provider-agnostic)
# ---------------------------------------------------------------------------
LLM_MODEL: str = _conf(
    "llm", "model",
    env_fallback="LLM_MODEL",
    default="anthropic/claude-haiku-4-5-20251001",
)

# API key for the configured provider.
# LiteLLM reads standard env vars (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)
# automatically.  We load from config.ini here and inject into the
# environment so LiteLLM can find it during local development.
_LLM_API_KEY: str = _conf("llm", "api_key", env_fallback="ANTHROPIC_API_KEY")

# Map LiteLLM provider prefixes to their expected environment variable names.
_PROVIDER_ENV_KEYS: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai":    "OPENAI_API_KEY",
    "gemini":    "GEMINI_API_KEY",
    "google":    "GOOGLE_API_KEY",
}

if _LLM_API_KEY and "/" in LLM_MODEL:
    _provider = LLM_MODEL.split("/")[0].lower()
    _env_key_name = _PROVIDER_ENV_KEYS.get(_provider)
    if _env_key_name:
        os.environ.setdefault(_env_key_name, _LLM_API_KEY)

# ---------------------------------------------------------------------------
# Tavily (web search)
# ---------------------------------------------------------------------------
TAVILY_API_KEY: str = _conf(
    "tavily", "api_key",
    env_fallback="TAVILY_API_KEY",
)

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
GMAIL_ADDRESS: str = _conf(
    "email", "gmail_address",
    env_fallback="GMAIL_ADDRESS",
)
GMAIL_APP_PASSWORD: str = _conf(
    "email", "gmail_app_password",
    env_fallback="GMAIL_APP_PASSWORD",
)

# If no explicit recipient is set, the brief is sent to the sender's own address.
TO_EMAIL: str = (
    _conf("email", "to_email", env_fallback="TO_EMAIL") or GMAIL_ADDRESS
)

# ---------------------------------------------------------------------------
# Brief content
# ---------------------------------------------------------------------------
MAX_LINKS: int = int(_conf("brief", "max_source_links", default="2"))

TOPICS: str = _conf(
    "brief",
    "topics",
    default="AI Models & Research, Big Tech (Google/Apple/Microsoft/Meta), Agentic AI, AI Automation",
)

# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------
DELIVERY_LABEL: str = _conf("schedule", "delivery_label", default="6:00 AM")


def validate_runtime_config() -> None:
    """Verify that all secrets required at runtime are present.

    Call this early in the Lambda handler so failures surface immediately
    with a clear message rather than mid-pipeline.

    Raises:
        ConfigError: If any required secret is empty.
    """
    missing: list[str] = []
    if not TAVILY_API_KEY:
        missing.append("TAVILY_API_KEY")
    if not GMAIL_ADDRESS:
        missing.append("GMAIL_ADDRESS")
    if not GMAIL_APP_PASSWORD:
        missing.append("GMAIL_APP_PASSWORD")

    # Check that the LLM provider key is available in the environment.
    if "/" in LLM_MODEL:
        provider = LLM_MODEL.split("/")[0].lower()
        env_key = _PROVIDER_ENV_KEYS.get(provider)
        if env_key and not os.environ.get(env_key):
            missing.append(env_key)

    if missing:
        raise ConfigError(
            f"Missing required secrets: {', '.join(missing)}. "
            "Set them in config.ini (local) or as environment variables (Lambda)."
        )
