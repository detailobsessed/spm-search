"""Tests for the FastMCP server tool registration and wiring."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from spm_search_mcp import scraper
from spm_search_mcp.server import get_package_readme, list_search_filters, mcp, search_swift_packages


class TestServerToolRegistration:
    """Verify the FastMCP server exposes the expected tools."""

    @pytest.mark.anyio
    async def test_tools_are_registered(self):
        """Both search and readme tools should be discoverable."""
        # LEARN: FastMCP v3 uses list_tools() returning a list of Tool objects
        tools = await mcp.list_tools()
        tool_names = {t.name for t in tools}
        assert "search_swift_packages" in tool_names
        assert "get_package_readme" in tool_names
        assert "list_search_filters" in tool_names

    @pytest.mark.anyio
    async def test_search_tool_has_description(self):
        tools = await mcp.list_tools()
        search_tool = next(t for t in tools if t.name == "search_swift_packages")
        assert search_tool.description is not None
        assert "Swift Package Index" in search_tool.description
        assert "QUERY" in search_tool.description

    @pytest.mark.anyio
    async def test_readme_tool_has_description(self):
        tools = await mcp.list_tools()
        readme_tool = next(t for t in tools if t.name == "get_package_readme")
        assert readme_tool.description is not None
        assert "README" in readme_tool.description


class TestListSearchFilters:
    """Verify the discovery tool returns valid enum values."""

    def test_returns_platforms_and_product_types(self):
        result = list_search_filters()
        assert "platforms" in result
        assert "product_types" in result

    def test_platforms_contains_expected_values(self):
        result = list_search_filters()
        assert "ios" in result["platforms"]
        assert "macos" in result["platforms"]
        assert "linux" in result["platforms"]

    def test_product_types_contains_expected_values(self):
        result = list_search_filters()
        assert "library" in result["product_types"]
        assert "executable" in result["product_types"]
        assert "macro" in result["product_types"]


# LEARN: We reuse the fake client pattern from test_error_handling to test the
# server tools end-to-end without hitting the network.

_active_fake_curl_client: Any = None
_active_fake_httpx_client: Any = None


def _fake_curl_factory(*_args: Any, **_kwargs: Any) -> Any:
    """Swallow CurlSession kwargs."""
    return _active_fake_curl_client


def _fake_httpx_factory(**_kwargs: Any) -> Any:
    """Swallow httpx.AsyncClient kwargs."""
    return _active_fake_httpx_client


class _OkSearchClient:
    """Returns a minimal valid SPI search page (used with CurlSession mock)."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, url):
        from unittest.mock import MagicMock

        html = """<html><body><main><div class="inner">
        <section class="package-results">
        <ul><li><a href="/test/pkg"><h4>TestPkg</h4><p>A test package</p>
        <ul class="metadata"><li class="identifier"><small>test/pkg</small></li>
        <li class="stars"><small>42 stars</small></li></ul></a></li></ul>
        <ul class="pagination"></ul></section></div></main></body></html>"""
        resp = MagicMock()
        resp.status_code = 200
        resp.text = html
        return resp


class _OkReadmeClient:
    """Returns a README on first request."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, url):
        request = httpx.Request("GET", url)
        if "README.md" in url and "main" in url:
            return httpx.Response(status_code=200, text="# Hello\nThis is a test README.", request=request)
        return httpx.Response(status_code=404, request=request)


class TestSearchToolIntegration:
    """Test search_swift_packages server tool end-to-end."""

    @pytest.mark.anyio
    async def test_empty_query_returns_guidance(self):
        """Empty query should return next_step guidance, not an error."""
        # LEARN: Calling the server tool function directly (not scraper) covers server.py line 81
        resp = await search_swift_packages()
        assert resp.result_count == 0
        assert "filter" in resp.next_step.lower()

    @pytest.mark.anyio
    async def test_search_returns_results(self, monkeypatch):
        global _active_fake_curl_client  # noqa: PLW0603
        _active_fake_curl_client = _OkSearchClient()
        monkeypatch.setattr(scraper, "CurlSession", _fake_curl_factory)
        resp = await search_swift_packages(query="test")
        assert resp.result_count > 0
        assert resp.results[0].name == "TestPkg"
        assert "get_package_readme" in resp.next_step


class TestReadmeToolIntegration:
    """Test get_package_readme server tool end-to-end."""

    @pytest.mark.anyio
    async def test_readme_found(self, monkeypatch):
        global _active_fake_httpx_client  # noqa: PLW0603
        _active_fake_httpx_client = _OkReadmeClient()
        monkeypatch.setattr(httpx, "AsyncClient", _fake_httpx_factory)
        # Calls through server.py lines 123-124
        result = await get_package_readme(owner="test", repo="pkg")
        assert "# Hello" in result

    @pytest.mark.anyio
    async def test_readme_max_length_zero_means_no_limit(self, monkeypatch):
        """max_length=0 should pass 999_999 to fetch_readme (PROGRESSIVE_DETAIL)."""
        global _active_fake_httpx_client  # noqa: PLW0603
        _active_fake_httpx_client = _OkReadmeClient()
        monkeypatch.setattr(httpx, "AsyncClient", _fake_httpx_factory)
        # This exercises the max_length=0 branch on server.py line 123
        result = await get_package_readme(owner="test", repo="pkg", max_length=0)
        assert "# Hello" in result

    @pytest.mark.anyio
    async def test_readme_not_found(self, monkeypatch):
        """All filenames 404 → should return a helpful not-found message."""

        class _NotFoundClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def get(self, url):
                request = httpx.Request("GET", url)
                return httpx.Response(status_code=404, request=request)

        global _active_fake_httpx_client  # noqa: PLW0603
        _active_fake_httpx_client = _NotFoundClient()
        monkeypatch.setattr(httpx, "AsyncClient", _fake_httpx_factory)
        result = await get_package_readme(owner="nonexist", repo="repo")
        assert "not found" in result.lower()
        assert "nonexist/repo" in result

    @pytest.mark.anyio
    async def test_readme_truncation(self, monkeypatch):
        """Long README should be truncated with a note."""

        class _LongReadmeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def get(self, url):
                request = httpx.Request("GET", url)
                if "README.md" in url and "main" in url:
                    return httpx.Response(status_code=200, text="x" * 10000, request=request)
                return httpx.Response(status_code=404, request=request)

        global _active_fake_httpx_client  # noqa: PLW0603
        _active_fake_httpx_client = _LongReadmeClient()
        monkeypatch.setattr(httpx, "AsyncClient", _fake_httpx_factory)
        result = await get_package_readme(owner="test", repo="pkg", max_length=100)
        assert "truncated" in result
        assert "10000" in result

    @pytest.mark.anyio
    async def test_rate_limit_returns_retryable(self, monkeypatch):
        """GitHub 429 should return a RETRYABLE message."""

        class _RateLimitClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def get(self, url):
                request = httpx.Request("GET", url)
                return httpx.Response(status_code=429, request=request)

        global _active_fake_httpx_client  # noqa: PLW0603
        _active_fake_httpx_client = _RateLimitClient()
        monkeypatch.setattr(httpx, "AsyncClient", _fake_httpx_factory)
        result = await get_package_readme(owner="test", repo="pkg")
        assert "RETRYABLE" in result

    @pytest.mark.anyio
    async def test_connect_error_returns_retryable(self, monkeypatch):
        """Connection failure should return a RETRYABLE message."""

        class _ConnectErrorClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def get(self, url):
                msg = "connection refused"
                raise httpx.ConnectError(msg)

        global _active_fake_httpx_client  # noqa: PLW0603
        _active_fake_httpx_client = _ConnectErrorClient()
        monkeypatch.setattr(httpx, "AsyncClient", _fake_httpx_factory)
        result = await get_package_readme(owner="test", repo="pkg")
        assert "RETRYABLE" in result
