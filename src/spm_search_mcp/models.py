"""Data models for Swift Package Index search results.

Uses StrEnum for constrained inputs (CONSTRAINED_INPUT pattern) so agents
can only pass valid values. Pydantic models define the output shape for
structured, token-efficient responses (RESPONSE_SHAPER pattern).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


# LEARN: StrEnum (Python 3.11+) values serialize as plain strings in JSON schemas,
# which means LLMs see them as literal string options — much clearer than int enums.
class Platform(StrEnum):
    """Platforms that SPI tracks build compatibility for."""

    IOS = "ios"
    MACOS = "macos"
    WATCHOS = "watchos"
    TVOS = "tvos"
    VISIONOS = "visionos"
    LINUX = "linux"


class ProductType(StrEnum):
    """Types of Swift package products."""

    LIBRARY = "library"
    EXECUTABLE = "executable"
    PLUGIN = "plugin"
    MACRO = "macro"


class PackageResult(BaseModel):
    """A single search result from the Swift Package Index.

    Flat structure optimized for agent consumption (RESPONSE_SHAPER pattern).
    Every result includes GUI URLs so agents can surface links to users (GUI_URL pattern).
    """

    name: str = Field(description="Package name (e.g. 'Alamofire')")
    description: str = Field(description="Short package description")
    url: str = Field(description="Swift Package Index URL for the package")
    github_url: str = Field(description="GitHub repository URL")
    author: str = Field(description="Repository owner (user or organization)")
    stars: int | None = Field(default=None, description="Star count, if available")
    last_activity: str | None = Field(default=None, description="Human-readable last activity (e.g. '3 days ago')")
    has_docs: bool = Field(default=False, description="Whether the package has documentation on SPI")
    keywords: list[str] = Field(default_factory=list, description="Matching keywords from the search")


class SearchResponse(BaseModel):
    """Paginated search results with next-action hints (NEXT_ACTION_HINT pattern)."""

    query: str = Field(description="The raw SPI query string that was executed")
    results: list[PackageResult] = Field(description="List of matching packages")
    result_count: int = Field(description="Number of results on this page")
    page: int = Field(description="Current page number (1-indexed)")
    has_more: bool = Field(description="Whether more results are available on the next page")
    spi_search_url: str = Field(description="Direct URL to view these results on swiftpackageindex.com")
    next_step: str = Field(
        description="Suggested next action for the agent",
    )
