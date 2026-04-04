"""Tests for the renderer module."""

from renderer import render_html, render_plain


class TestRenderHtml:
    """Tests for render_html()."""

    def test_returns_html_string(self, sample_brief):
        html = render_html(sample_brief)
        assert "<html" in html
        assert "</html>" in html

    def test_contains_headline(self, sample_brief):
        html = render_html(sample_brief)
        assert sample_brief["headline"] in html

    def test_contains_date(self, sample_brief):
        html = render_html(sample_brief)
        assert sample_brief["date"] in html

    def test_contains_bullet_text(self, sample_brief):
        html = render_html(sample_brief)
        for bullet in sample_brief["bullets"]:
            assert bullet["text"] in html

    def test_contains_source_urls(self, sample_brief):
        html = render_html(sample_brief)
        for source in sample_brief["sources"]:
            assert source["url"] in html

    def test_contains_deep_dive(self, sample_brief):
        html = render_html(sample_brief)
        assert sample_brief["deepDive"]["body"] in html


class TestRenderPlain:
    """Tests for render_plain()."""

    def test_returns_plain_text(self, sample_brief):
        text = render_plain(sample_brief)
        assert "<html" not in text

    def test_contains_headline(self, sample_brief):
        text = render_plain(sample_brief)
        assert sample_brief["headline"] in text

    def test_contains_bullet_text(self, sample_brief):
        text = render_plain(sample_brief)
        for bullet in sample_brief["bullets"]:
            assert bullet["text"] in text

    def test_contains_source_urls(self, sample_brief):
        text = render_plain(sample_brief)
        for source in sample_brief["sources"]:
            assert source["url"] in text
