"""Tests for the FastMCP server tool functions."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from spm_search_mcp.models import SearchResponse


def _empty_search_response(query: str = "") -> SearchResponse:
    return SearchResponse(
        query=query,
        results=[],
        result_count=0,
        page=1,
        has_more=False,
        spi_search_url="https://swiftpackageindex.com/search",
        next_step="No results.",
    )


class TestSearchSwiftPackages:
    @pytest.mark.anyio
    async def test_delegates_to_search_packages(self):
        from spm_search_mcp.server import search_swift_packages

        mock_response = _empty_search_response("networking")
        with patch(
            "spm_search_mcp.server.search_packages",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await search_swift_packages(query="networking")

        assert result is mock_response

    @pytest.mark.anyio
    async def test_passes_all_params_through(self):
        from spm_search_mcp.models import Platform, ProductType
        from spm_search_mcp.server import search_swift_packages

        mock_response = _empty_search_response("swift")
        with patch(
            "spm_search_mcp.server.search_packages",
            new=AsyncMock(return_value=mock_response),
        ) as mock_fn:
            await search_swift_packages(
                query="swift",
                author="apple",
                min_stars=100,
                platforms=[Platform.IOS],
                product_type=ProductType.LIBRARY,
                page=2,
            )

        mock_fn.assert_called_once_with(
            "swift",
            author="apple",
            keyword=None,
            min_stars=100,
            max_stars=None,
            platforms=[Platform.IOS],
            license_filter=None,
            last_activity_after=None,
            last_commit_after=None,
            product_type=ProductType.LIBRARY,
            page=2,
        )


class TestGetPackageReadme:
    @pytest.mark.anyio
    async def test_positive_max_length_passed_through(self):
        from spm_search_mcp.server import get_package_readme

        with patch(
            "spm_search_mcp.server.fetch_readme",
            new=AsyncMock(return_value="# README"),
        ) as mock_fn:
            result = await get_package_readme("apple", "swift-nio", max_length=2000)

        assert result == "# README"
        mock_fn.assert_called_once_with("apple", "swift-nio", max_length=2000)

    @pytest.mark.anyio
    async def test_max_length_zero_becomes_large_limit(self):
        from spm_search_mcp.server import get_package_readme

        with patch(
            "spm_search_mcp.server.fetch_readme",
            new=AsyncMock(return_value="# Full README"),
        ) as mock_fn:
            result = await get_package_readme("apple", "swift-nio", max_length=0)

        assert result == "# Full README"
        mock_fn.assert_called_once_with("apple", "swift-nio", max_length=999_999)
