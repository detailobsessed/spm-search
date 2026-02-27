"""Tests for the SPI query string builder."""

from __future__ import annotations

from spm_search_mcp.models import Platform, ProductType
from spm_search_mcp.scraper import build_query


class TestBuildQuery:
    """Verify that structured params assemble into correct SPI filter syntax."""

    def test_freetext_only(self):
        assert build_query("networking") == "networking"

    def test_empty_query(self):
        assert not build_query()

    def test_author_filter(self):
        assert build_query("fluent", author="vapor") == "fluent author:vapor"

    def test_keyword_filter(self):
        assert build_query(keyword="accessibility") == "keyword:accessibility"

    def test_min_stars(self):
        assert build_query("http", min_stars=500) == "http stars:>=500"

    def test_max_stars(self):
        assert build_query(max_stars=100) == "stars:<=100"

    def test_stars_range(self):
        result = build_query("json", min_stars=50, max_stars=1000)
        assert "stars:>=50" in result
        assert "stars:<=1000" in result

    def test_single_platform(self):
        assert build_query("ui", platforms=[Platform.IOS]) == "ui platform:ios"

    def test_multiple_platforms(self):
        result = build_query("testing", platforms=[Platform.IOS, Platform.LINUX])
        assert result == "testing platform:ios,linux"

    def test_license_compatible(self):
        assert build_query(license_filter="compatible") == "license:compatible"

    def test_license_specific(self):
        assert build_query(license_filter="mit") == "license:mit"

    def test_last_activity_after(self):
        result = build_query("charts", last_activity_after="2024-01-01")
        assert result == "charts last_activity:>=2024-01-01"

    def test_last_activity_before(self):
        result = build_query("charts", last_activity_before="2023-12-31")
        assert result == "charts last_activity:<=2023-12-31"

    def test_last_activity_date_window(self):
        result = build_query(last_activity_after="2024-01-01", last_activity_before="2024-12-31")
        assert "last_activity:>=2024-01-01" in result
        assert "last_activity:<=2024-12-31" in result

    def test_last_commit_after(self):
        result = build_query(last_commit_after="2024-06-15")
        assert result == "last_commit:>=2024-06-15"

    def test_last_commit_before(self):
        result = build_query(last_commit_before="2023-12-31")
        assert result == "last_commit:<=2023-12-31"

    def test_last_commit_date_window(self):
        result = build_query(last_commit_after="2024-01-01", last_commit_before="2024-12-31")
        assert "last_commit:>=2024-01-01" in result
        assert "last_commit:<=2024-12-31" in result

    def test_product_type_library(self):
        assert build_query(product_type=ProductType.LIBRARY) == "product:library"

    def test_product_type_executable(self):
        assert build_query(product_type=ProductType.EXECUTABLE) == "product:executable"

    def test_all_filters_combined(self):
        """All filters combine with spaces (SPI uses AND logic)."""
        result = build_query(
            "networking",
            author="apple",
            keyword="server",
            min_stars=100,
            platforms=[Platform.IOS, Platform.MACOS],
            license_filter="mit",
            last_activity_after="2024-01-01",
            last_activity_before="2024-06-30",
            product_type=ProductType.LIBRARY,
        )
        parts = result.split()
        assert "networking" in parts
        assert "author:apple" in parts
        assert "keyword:server" in parts
        assert "stars:>=100" in parts
        assert "platform:ios,macos" in parts
        assert "license:mit" in parts
        assert "last_activity:>=2024-01-01" in parts
        assert "last_activity:<=2024-06-30" in parts
        assert "product:library" in parts

    def test_visionos_platform(self):
        result = build_query(platforms=[Platform.VISIONOS])
        assert result == "platform:visionos"

    def test_macro_product_type(self):
        result = build_query(product_type=ProductType.MACRO)
        assert result == "product:macro"
