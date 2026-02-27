"""Async tests for search_packages and fetch_readme with mocked HTTP clients."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from spm_search_mcp.scraper import fetch_readme, search_packages


def _make_http_mock(status_code: int = 200, text: str = "") -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    response.raise_for_status = MagicMock()
    return response


def _patch_curl_session(mock_client: AsyncMock):
    """Return a patch context that wires mock_client as the CurlSession instance."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    return patch("spm_search_mcp.scraper.CurlSession", return_value=mock_ctx)


def _patch_client(mock_client: AsyncMock):
    """Return a patch context that wires mock_client as the httpx.AsyncClient instance."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    return patch("spm_search_mcp.scraper.httpx.AsyncClient", return_value=mock_ctx)


class TestSearchPackages:
    @pytest.mark.anyio
    async def test_empty_query_returns_no_results_without_http(self):
        result = await search_packages()
        assert result.result_count == 0
        assert result.results == []
        assert "Provide a search query" in result.next_step

    @pytest.mark.anyio
    async def test_valid_query_parses_results(self):
        html = """
        <html><body>
        <section class="package-results">
            <ul>
                <li><a href="/apple/swift-nio">
                    <h4>SwiftNIO</h4><p>Fast networking</p>
                    <ul class="metadata"><li class="stars">10000 stars</li></ul>
                </a></li>
            </ul>
        </section>
        </body></html>
        """
        mock_client = AsyncMock()
        mock_client.get.return_value = _make_http_mock(200, html)

        with _patch_curl_session(mock_client):
            result = await search_packages(query="networking")

        assert result.result_count == 1
        assert result.results[0].name == "SwiftNIO"
        assert result.results[0].stars == 10000
        assert "get_package_readme" in result.next_step

    @pytest.mark.anyio
    async def test_no_results_suggests_broadening(self):
        html = "<html><body><section class='package-results'><ul></ul></section></body></html>"
        mock_client = AsyncMock()
        mock_client.get.return_value = _make_http_mock(200, html)

        with _patch_curl_session(mock_client):
            result = await search_packages(query="xyznotfound123")

        assert result.result_count == 0
        assert "broadening" in result.next_step

    @pytest.mark.anyio
    async def test_has_more_includes_next_page_hint(self):
        html = """
        <html><body>
        <section class="package-results">
            <ul>
                <li><a href="/owner/repo"><h4>Pkg</h4></a></li>
            </ul>
        </section>
        <ul class="pagination">
            <li class="next"><a href="/search?query=swift&page=2">Next</a></li>
        </ul>
        </body></html>
        """
        mock_client = AsyncMock()
        mock_client.get.return_value = _make_http_mock(200, html)

        with _patch_curl_session(mock_client):
            result = await search_packages(query="swift", page=1)

        assert result.has_more is True
        assert "page=2" in result.next_step


class TestFetchReadme:
    @pytest.mark.anyio
    async def test_found_on_main_with_truncation(self):
        content = "A" * 5000
        mock_client = AsyncMock()
        mock_client.get.return_value = _make_http_mock(200, content)

        with _patch_client(mock_client):
            result = await fetch_readme("owner", "repo", max_length=4000)

        assert result.startswith("A" * 4000)
        assert "truncated" in result
        assert "5000 chars" in result

    @pytest.mark.anyio
    async def test_max_length_zero_returns_full_content(self):
        content = "B" * 5000
        mock_client = AsyncMock()
        mock_client.get.return_value = _make_http_mock(200, content)

        with _patch_client(mock_client):
            result = await fetch_readme("owner", "repo", max_length=0)

        assert result == content
        assert "truncated" not in result

    @pytest.mark.anyio
    async def test_content_within_limit_not_truncated(self):
        content = "Short README"
        mock_client = AsyncMock()
        mock_client.get.return_value = _make_http_mock(200, content)

        with _patch_client(mock_client):
            result = await fetch_readme("owner", "repo", max_length=4000)

        assert result == content

    @pytest.mark.anyio
    async def test_main_404_falls_back_to_master(self):
        readme_content = "# README on master branch"
        # 5 filenames on main (all 404) + README.md on master (200)
        responses = [_make_http_mock(404)] * 5 + [_make_http_mock(200, readme_content)]
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=responses)

        with _patch_client(mock_client):
            result = await fetch_readme("owner", "repo")

        assert result == readme_content

    @pytest.mark.anyio
    async def test_not_found_anywhere_returns_message(self):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=_make_http_mock(404))

        with _patch_client(mock_client):
            result = await fetch_readme("owner", "repo")

        assert "README not found" in result
        assert "owner/repo" in result
