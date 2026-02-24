"""Unit tests for scraper helper functions (no I/O)."""

from __future__ import annotations

from unittest.mock import MagicMock

from bs4 import BeautifulSoup, Tag

from spm_search_mcp.scraper import (
    _build_search_url,
    _extract_metadata,
    _parse_package_from_li,
    parse_search_results,
)


def _tag(html: str, selector: str) -> Tag:
    soup = BeautifulSoup(html, "lxml")
    el = soup.select_one(selector)
    assert isinstance(el, Tag)
    return el


class TestBuildSearchUrl:
    def test_page_one_omits_page_param(self):
        url = _build_search_url("networking")
        assert "page=" not in url
        assert "query=networking" in url

    def test_page_two_appends_page_param(self):
        url = _build_search_url("networking", page=2)
        assert "&page=2" in url
        assert "query=networking" in url


class TestExtractMetadata:
    def test_no_metadata_ul_returns_defaults(self):
        link = _tag("<div><a href='/o/r'><h4>Pkg</h4></a></div>", "a")
        stars, last_activity, has_docs = _extract_metadata(link)
        assert stars is None
        assert last_activity is None
        assert has_docs is False

    def test_has_docs_flag_detected(self):
        link = _tag(
            '<div><a href="/o/r"><ul class="metadata"><li class="has_docs">Has docs</li></ul></a></div>',
            "a",
        )
        _, _, has_docs = _extract_metadata(link)
        assert has_docs is True

    def test_stars_with_no_digit_word_stays_none(self):
        link = _tag(
            '<div><a href="/o/r"><ul class="metadata"><li class="stars">many stars</li></ul></a></div>',
            "a",
        )
        stars, _, _ = _extract_metadata(link)
        assert stars is None

    def test_activity_text_captured(self):
        link = _tag(
            '<div><a href="/o/r"><ul class="metadata"><li class="activity">Active 3 days ago</li></ul></a></div>',
            "a",
        )
        _, last_activity, _ = _extract_metadata(link)
        assert last_activity == "Active 3 days ago"


class TestParsePackageFromLi:
    def test_no_anchor_returns_none(self):
        li = _tag("<ul><li><span>no link</span></li></ul>", "li")
        assert _parse_package_from_li(li) is None

    def test_href_with_single_path_part_returns_none(self):
        li = _tag("<ul><li><a href='/singlepart'><h4>Bad</h4></a></li></ul>", "li")
        assert _parse_package_from_li(li) is None

    def test_valid_li_parsed_correctly(self):
        li = _tag(
            "<ul><li><a href='/owner/repo'><h4>MyPkg</h4><p>A description</p></a></li></ul>",
            "li",
        )
        result = _parse_package_from_li(li)
        assert result is not None
        assert result.name == "MyPkg"
        assert result.author == "owner"
        assert result.description == "A description"

    def test_exception_inside_returns_none(self):
        bad_li = MagicMock(spec=Tag)
        bad_li.find.side_effect = ValueError("simulated parse error")
        assert _parse_package_from_li(bad_li) is None


class TestParseSearchResultsEdgeCases:
    def test_all_uls_have_classes_returns_empty(self):
        html = """
        <html><body>
        <section class="package-results">
            <ul class="filter-list"><li>Filter</li></ul>
            <ul class="pagination"><li>Page</li></ul>
        </section>
        </body></html>
        """
        assert parse_search_results(html) == []

    def test_unparsable_result_skipped(self):
        html = """
        <html><body>
        <section class="package-results">
            <ul>
                <li><a href="/singlepart"><h4>Bad</h4></a></li>
                <li><a href="/owner/repo"><h4>Good</h4><p>Desc</p></a></li>
            </ul>
        </section>
        </body></html>
        """
        results = parse_search_results(html)
        assert len(results) == 1
        assert results[0].name == "Good"
