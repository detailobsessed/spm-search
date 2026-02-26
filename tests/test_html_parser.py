"""Tests for the SPI HTML parser using a real fixture."""

from __future__ import annotations

from pathlib import Path

import pytest

from spm_search_mcp.scraper import _has_more_pages, parse_search_results

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def networking_html() -> str:
    """Load the real SPI search results HTML fixture.

    This fixture was captured from:
    https://swiftpackageindex.com/search?query=networking+stars%3A%3E%3D500+platform%3Aios
    """
    return (FIXTURES_DIR / "spi_search_networking.html").read_text(encoding="utf-8")


class TestParseSearchResults:
    """Verify HTML parsing against a real SPI response."""

    def test_returns_results(self, networking_html: str):
        results = parse_search_results(networking_html)
        assert len(results) > 0

    def test_result_count(self, networking_html: str):
        results = parse_search_results(networking_html)
        assert len(results) == 16

    def test_first_result_name(self, networking_html: str):
        results = parse_search_results(networking_html)
        assert results[0].name == "Networking"

    def test_first_result_author(self, networking_html: str):
        results = parse_search_results(networking_html)
        assert results[0].author == "freshOS"

    def test_first_result_stars(self, networking_html: str):
        results = parse_search_results(networking_html)
        assert results[0].stars is not None
        assert results[0].stars > 0

    def test_first_result_description(self, networking_html: str):
        results = parse_search_results(networking_html)
        assert len(results[0].description) > 0

    def test_urls_constructed(self, networking_html: str):
        results = parse_search_results(networking_html)
        first = results[0]
        assert first.url == "https://swiftpackageindex.com/freshOS/Networking"
        assert first.github_url == "https://github.com/freshOS/Networking"

    def test_last_activity_present(self, networking_html: str):
        results = parse_search_results(networking_html)
        assert results[0].last_activity is not None
        assert "ago" in results[0].last_activity.lower() or "active" in results[0].last_activity.lower()

    def test_keywords_extracted(self, networking_html: str):
        results = parse_search_results(networking_html)
        assert "networking" in results[0].keywords

    def test_alamofire_stars_in_thousands(self, networking_html: str):
        """Verify comma-separated star counts parse correctly (e.g. '42,352 stars')."""
        results = parse_search_results(networking_html)
        alamofire = next((r for r in results if r.name == "Alamofire"), None)
        assert alamofire is not None
        assert alamofire.stars is not None
        assert alamofire.stars > 40000

    def test_all_results_have_required_fields(self, networking_html: str):
        results = parse_search_results(networking_html)
        for result in results:
            assert result.name
            assert result.url.startswith("https://swiftpackageindex.com/")
            assert result.github_url.startswith("https://github.com/")
            assert result.author

    def test_empty_html_returns_empty(self):
        assert parse_search_results("") == []

    def test_html_without_results_returns_empty(self):
        html = "<html><body><main><div class='inner'></div></main></body></html>"
        assert parse_search_results(html) == []


class TestHasMorePages:
    """Verify pagination detection."""

    def test_no_pagination_in_fixture(self, networking_html: str):
        """The fixture query (networking stars>=500 ios) fits on one page."""
        assert _has_more_pages(networking_html) is False

    def test_empty_html(self):
        assert _has_more_pages("") is False

    def test_pagination_with_next_link(self):
        html = """
        <html><body>
        <ul class="pagination">
            <li class="next"><a href="/search?query=swift&page=2">Next Page</a></li>
        </ul>
        </body></html>
        """
        assert _has_more_pages(html) is True

    def test_pagination_without_next(self):
        html = """
        <html><body>
        <ul class="pagination">
            <li class="previous"><a href="/search?query=swift&page=1">Previous Page</a></li>
        </ul>
        </body></html>
        """
        assert _has_more_pages(html) is False
