"""FastMCP server exposing Swift Package Index search tools.

Applies arcade patterns throughout:
- QUERY_TOOL: All tools are read-only, safe to retry
- DISCOVERY_TOOL: list_search_filters() exposes valid enum values
- TOOL_DESCRIPTION: LLM-optimized docstrings with dependency/next-action hints
- CONSTRAINED_INPUT: Enums for platforms and product types
- SMART_DEFAULTS: Most params optional, sensible defaults
- NEXT_ACTION_HINT: Responses suggest what to do next
- GUI_URL: Every result includes SPI + GitHub URLs
- RECOVERY_GUIDE: Actionable error messages
"""

from __future__ import annotations

import logging

from fastmcp import FastMCP

from spm_search_mcp.models import Platform, ProductType, SearchResponse
from spm_search_mcp.scraper import fetch_readme, search_packages

logger = logging.getLogger(__name__)

# LEARN: FastMCP() name appears in MCP client UIs (e.g. Claude Desktop sidebar).
# instructions= is the "system prompt" sent to the agent describing the server's purpose.
mcp = FastMCP(
    name="Swift Package Index",
    instructions=(
        "Search the Swift Package Index (swiftpackageindex.com) for Swift packages. "
        "Use list_search_filters() first to discover valid platform and product_type values. "
        "Use search_swift_packages to find packages by keyword, author, stars, platform, license, or product type. "
        "Use get_package_readme to fetch a package's README after finding it in search results. "
        "No API key required."
    ),
)


@mcp.tool
async def search_swift_packages(  # noqa: PLR0913, PLR0917
    query: str = "",
    author: str | None = None,
    keyword: str | None = None,
    min_stars: int | None = None,
    max_stars: int | None = None,
    platforms: list[Platform] | None = None,
    license_filter: str | None = None,
    last_activity_after: str | None = None,
    last_activity_before: str | None = None,
    last_commit_after: str | None = None,
    last_commit_before: str | None = None,
    product_type: ProductType | None = None,
    page: int = 1,
) -> SearchResponse:
    """Search the Swift Package Index for packages matching your criteria.

    This is a QUERY tool — read-only, safe to call multiple times.

    At least one parameter must be provided. Parameters are combined with AND logic.

    Args:
        query: Free-text search (e.g. "networking", "json parsing").
        author: Filter by repository owner (e.g. "apple", "vapor").
            Prefix with "!" to exclude (e.g. "!vapor").
        keyword: Filter by package keyword tag (e.g. "server", "ui").
            Prefix with "!" to exclude (e.g. "!deprecated").
        min_stars: Minimum GitHub star count (e.g. 100, 1000).
        max_stars: Maximum GitHub star count.
        platforms: Filter by compatible platform(s). Multiple = AND (must support all).
            Valid: ios, macos, watchos, tvos, visionos, linux.
        license_filter: License filter. Use "compatible" for App Store compatible,
            or a specific SPDX ID like "mit", "apache-2.0", "lgpl-2.1".
            Prefix with "!" to exclude (e.g. "!gpl-3.0").
        last_activity_after: ISO8601 date (YYYY-MM-DD). Only packages with maintenance
            activity after this date. Example: "2024-01-01".
        last_activity_before: ISO8601 date (YYYY-MM-DD). Only packages with maintenance
            activity before this date. Combine with last_activity_after for a date window.
        last_commit_after: ISO8601 date (YYYY-MM-DD). Only packages with commits
            after this date.
        last_commit_before: ISO8601 date (YYYY-MM-DD). Only packages with commits
            before this date. Combine with last_commit_after for a date window.
        product_type: Filter by product type: library, executable, plugin, or macro.
        page: Page number for pagination (default 1). Check has_more in the response.

    If you are unsure what values are valid for platforms or product_type, call
    list_search_filters() first. After getting results, use get_package_readme(owner, repo)
    to read the README of any package that looks interesting.
    """
    # LEARN: FastMCP automatically validates types from the function signature.
    # If an agent passes an invalid Platform string, FastMCP returns a typed error
    # before our code even runs — that's the CONSTRAINED_INPUT pattern in action.
    return await search_packages(
        query,
        author=author,
        keyword=keyword,
        min_stars=min_stars,
        max_stars=max_stars,
        platforms=platforms,
        license_filter=license_filter,
        last_activity_after=last_activity_after,
        last_activity_before=last_activity_before,
        last_commit_after=last_commit_after,
        last_commit_before=last_commit_before,
        product_type=product_type,
        page=page,
    )


@mcp.tool
def list_search_filters() -> dict[str, list[str]]:
    """Return all valid values for the constrained parameters of search_swift_packages.

    This is a DISCOVERY tool — call this first if you are unsure what values
    are accepted for the platforms or product_type parameters.

    Returns a dict with keys 'platforms' and 'product_types', each containing
    the list of accepted string values.
    """
    return {
        "platforms": [p.value for p in Platform],
        "product_types": [p.value for p in ProductType],
    }


@mcp.tool
async def get_package_readme(
    owner: str,
    repo: str,
    max_length: int = 4000,
) -> str:
    """Fetch the README of a Swift package from GitHub.

    This is a QUERY tool — read-only, safe to call multiple times.

    Use this after search_swift_packages to get details about a specific package.
    The owner and repo values come from search results (e.g. "apple" and "swift-nio").

    Args:
        owner: GitHub repository owner (user or org). Example: "Alamofire".
        repo: GitHub repository name. Example: "Alamofire".
        max_length: Maximum characters to return (default 4000). Set to 0 for full content.
            Larger values use more tokens.

    Returns the README content as markdown. If the README is longer than max_length,
    it is truncated with a note about the full length.

    After reading the README, you can suggest the package to the user with its
    Swift Package Index URL: https://swiftpackageindex.com/{owner}/{repo}
    """
    # LEARN: max_length=0 means "no limit" — this is the PROGRESSIVE_DETAIL pattern.
    # Default is truncated for token efficiency; agents can opt in to full content.
    effective_max = max_length if max_length > 0 else 999_999
    return await fetch_readme(owner, repo, max_length=effective_max)
