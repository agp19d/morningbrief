"""Tests for the config module."""

import os
from unittest.mock import patch

import pytest

# Import after patching to avoid side effects from config.ini
import config
from config import ConfigError, _conf, validate_runtime_config


class TestConf:
    """Tests for the _conf() three-tier fallback."""

    def test_env_fallback_when_ini_missing(self):
        with patch.dict(os.environ, {"TEST_VAR": "from_env"}):
            value = _conf("nonexistent", "key", env_fallback="TEST_VAR")
        assert value == "from_env"

    def test_default_when_all_missing(self):
        value = _conf("nonexistent", "key", default="fallback")
        assert value == "fallback"

    def test_empty_string_default(self):
        value = _conf("nonexistent", "key")
        assert value == ""

    def test_required_raises_on_missing(self):
        with pytest.raises(ConfigError, match="Required config missing"):
            _conf("nonexistent", "key", required=True)

    def test_required_with_env_fallback_message(self):
        with pytest.raises(ConfigError, match=r"\$MY_VAR"):
            _conf("nonexistent", "key", env_fallback="MY_VAR", required=True)


class TestValidateRuntimeConfig:
    """Tests for validate_runtime_config()."""

    def test_raises_when_tavily_key_missing(self):
        with patch.object(config, "TAVILY_API_KEY", ""):
            with pytest.raises(ConfigError, match="TAVILY_API_KEY"):
                validate_runtime_config()

    def test_raises_when_gmail_address_missing(self):
        with patch.object(config, "GMAIL_ADDRESS", ""):
            with pytest.raises(ConfigError, match="GMAIL_ADDRESS"):
                validate_runtime_config()

    def test_raises_when_gmail_password_missing(self):
        with patch.object(config, "GMAIL_APP_PASSWORD", ""):
            with pytest.raises(ConfigError, match="GMAIL_APP_PASSWORD"):
                validate_runtime_config()

    def test_passes_when_all_present(self):
        with (
            patch.object(config, "TAVILY_API_KEY", "key"),
            patch.object(config, "GMAIL_ADDRESS", "a@b.com"),
            patch.object(config, "GMAIL_APP_PASSWORD", "pass"),
            patch.object(config, "LLM_MODEL", "anthropic/claude-haiku-4-5-20251001"),
            patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}),
        ):
            validate_runtime_config()  # Should not raise
