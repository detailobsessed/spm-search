"""Tests for error classification and recovery guidance in the scraper."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
from curl_cffi.requests.errors import RequestsError as CurlRequestsError

from spm_search_mcp import scraper
from spm_search_mcp.scraper import _classify_http_error, _error_response


class TestClassifyHttpError:
    """Verify HTTP status codes map to correct RETRYABLE/PERMANENT classification."""

    def test_429_is_retryable(self):
        msg = _classify_http_error(429)
        assert msg.startswith("RETRYABLE")
        assert "rate limit" in msg.lower()

    def test_403_is_permanent(self):
        msg = _classify_http_error(403)
        assert msg.startswith("PERMANENT")

    def test_404_is_permanent(self):
        msg = _classify_http_error(404)
        assert msg.startswith("PERMANENT")

    def test_500_is_retryable(self):
        msg = _classify_http_error(500)
        assert msg.startswith("RETRYABLE")
        assert "500" in msg

    def test_502_is_retryable(self):
        msg = _classify_http_error(502)
        assert msg.startswith("RETRYABLE")

    def test_503_is_retryable(self):
        msg = _classify_http_error(503)
        assert msg.startswith("RETRYABLE")

    def test_unknown_status_is_permanent(self):
        msg = _classify_http_error(418)
        assert msg.startswith("PERMANENT")
        assert "418" in msg


class TestErrorResponse:
    """Verify _error_response builds valid SearchResponse objects."""

    def test_returns_zero_results(self):
        resp = _error_response("test", 1, "https://example.com", next_step="retry")
        assert resp.result_count == 0
        assert resp.results == []

    def test_preserves_query(self):
        resp = _error_response("networking", 2, "https://example.com", next_step="retry")
        assert resp.query == "networking"
        assert resp.page == 2

    def test_has_more_is_false(self):
        resp = _error_response("test", 1, "https://example.com", next_step="retry")
        assert resp.has_more is False

    def test_next_step_passed_through(self):
        resp = _error_response("test", 1, "https://example.com", next_step="RETRYABLE: do something")
        assert resp.next_step == "RETRYABLE: do something"


# LEARN: Separate fake client classes for SPI (CurlSession) and GitHub (httpx.AsyncClient)
# since we switched SPI to curl_cffi for Cloudflare bypass.


def _fake_curl_factory(*_args: Any, **_kwargs: Any) -> Any:
    """Swallow CurlSession kwargs."""
    return _active_fake_curl_client


def _fake_httpx_factory(**_kwargs: Any) -> Any:
    """Swallow httpx.AsyncClient kwargs."""
    return _active_fake_httpx_client


_active_fake_curl_client: Any = None
_active_fake_httpx_client: Any = None


class _CurlTimeoutClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, url):
        msg = "timed out"
        raise CurlRequestsError(msg)


class _CurlConnectErrorClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, url):
        msg = "connection refused"
        raise CurlRequestsError(msg)


class _CurlServerErrorClient:
    """Returns a response with status 503."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, url):
        from unittest.mock import MagicMock

        resp = MagicMock()
        resp.status_code = 503
        return resp


class TestSearchPackagesErrorHandling:
    """Verify search_packages catches HTTP errors and returns structured responses."""

    @pytest.mark.anyio
    async def test_timeout_returns_retryable(self, monkeypatch):
        """Simulate a timeout and verify the response is RETRYABLE."""
        global _active_fake_curl_client  # noqa: PLW0603
        _active_fake_curl_client = _CurlTimeoutClient()
        monkeypatch.setattr(scraper, "CurlSession", _fake_curl_factory)
        resp = await scraper.search_packages("networking")
        assert resp.result_count == 0
        assert "RETRYABLE" in resp.next_step

    @pytest.mark.anyio
    async def test_connect_error_returns_retryable(self, monkeypatch):
        """Simulate a connection failure."""
        global _active_fake_curl_client  # noqa: PLW0603
        _active_fake_curl_client = _CurlConnectErrorClient()
        monkeypatch.setattr(scraper, "CurlSession", _fake_curl_factory)
        resp = await scraper.search_packages("networking")
        assert resp.result_count == 0
        assert "RETRYABLE" in resp.next_step

    @pytest.mark.anyio
    async def test_503_returns_retryable(self, monkeypatch):
        """Simulate a 503 server error."""
        global _active_fake_curl_client  # noqa: PLW0603
        _active_fake_curl_client = _CurlServerErrorClient()
        monkeypatch.setattr(scraper, "CurlSession", _fake_curl_factory)
        resp = await scraper.search_packages("networking")
        assert resp.result_count == 0
        assert "RETRYABLE" in resp.next_step
        assert "503" in resp.next_step


class TestFetchReadmeErrorHandling:
    """Verify fetch_readme catches HTTP errors and returns recovery messages."""

    @pytest.mark.anyio
    async def test_timeout_returns_retryable(self, monkeypatch):
        global _active_fake_httpx_client  # noqa: PLW0603

        class _TimeoutClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def get(self, url):
                msg = "timed out"
                raise httpx.TimeoutException(msg)

        _active_fake_httpx_client = _TimeoutClient()
        monkeypatch.setattr(httpx, "AsyncClient", _fake_httpx_factory)
        result = await scraper.fetch_readme("apple", "swift-nio")
        assert "RETRYABLE" in result
        assert "apple/swift-nio" in result
