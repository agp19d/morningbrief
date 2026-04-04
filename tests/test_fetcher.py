"""Tests for the fetcher module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from fetcher import _format_context, _validate_brief, fetch_brief


class TestFormatContext:
    """Tests for _format_context()."""

    def test_formats_results_with_dividers(self, tavily_results):
        context = _format_context(tavily_results)
        assert "Title: OpenAI Launches GPT-5" in context
        assert "URL:   https://example.com/gpt5" in context
        assert "---" in context

    def test_truncates_long_content(self):
        results = [{
            "title": "Test",
            "url": "https://example.com",
            "content": "x" * 1000,
        }]
        context = _format_context(results)
        # Content is truncated to 600 chars
        excerpt_line = [l for l in context.split("\n") if l.startswith("Excerpt:")][0]
        assert len(excerpt_line) <= len("Excerpt: ") + 600

    def test_handles_missing_fields(self):
        results = [{}]
        context = _format_context(results)
        assert "Title: Untitled" in context


class TestValidateBrief:
    """Tests for _validate_brief()."""

    def test_valid_brief_passes(self, sample_brief):
        result = _validate_brief(sample_brief)
        assert result is sample_brief

    def test_missing_key_raises(self, sample_brief):
        del sample_brief["headline"]
        with pytest.raises(ValueError, match="headline"):
            _validate_brief(sample_brief)

    def test_bullets_not_list_raises(self, sample_brief):
        sample_brief["bullets"] = "not a list"
        with pytest.raises(ValueError, match="bullets"):
            _validate_brief(sample_brief)

    def test_sources_not_list_raises(self, sample_brief):
        sample_brief["sources"] = "not a list"
        with pytest.raises(ValueError, match="sources"):
            _validate_brief(sample_brief)


class TestFetchBrief:
    """Integration-style tests for fetch_brief() with mocked externals."""

    @patch("fetcher.litellm")
    @patch("fetcher.TavilyClient")
    def test_fetch_brief_success(self, mock_tavily_cls, mock_litellm, sample_brief):
        # Mock Tavily
        mock_client = MagicMock()
        mock_tavily_cls.return_value = mock_client
        mock_client.search.return_value = {
            "results": [{"title": "Test", "url": "https://x.com", "content": "c"}],
        }

        # Mock LiteLLM
        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps(sample_brief)
        mock_litellm.completion.return_value = MagicMock(choices=[mock_choice])

        result = fetch_brief()
        assert result["headline"] == sample_brief["headline"]
        assert isinstance(result["bullets"], list)

    @patch("fetcher._search_topics", return_value=[])
    def test_fetch_brief_no_results_raises(self, _mock):
        with pytest.raises(RuntimeError, match="no search results"):
            fetch_brief()
