"""Scraper for Swift Package Index search results.

Builds structured queries from typed parameters (CONSTRAINED_INPUT pattern),
fetches the HTML search page, and parses results into PackageResult models
(RESPONSE_SHAPER pattern). No API key needed — this uses the public search UI.
"""

from __future__ import annotations

import logging
from urllib.parse import quote_plus, urljoin

import httpx
from bs4 import BeautifulSoup, Tag

from spm_search_mcp.models import PackageResult, Platform, ProductType, SearchResponse

logger = logging.getLogger(__name__)

SPI_BASE_URL = "https://swiftpackageindex.com"
SPI_SEARCH_URL = f"{SPI_BASE_URL}/search"

# LEARN: A realistic User-Agent avoids being blocked by simple bot filters.
# Some sites reject the default 'python-httpx/...' UA string.
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; spm-search-mcp/0.1; +https://github.com/detailobsessed/spm-search)",
    "Accept": "text/html",
}


def build_query(  # noqa: PLR0913
    query: str = "",
    *,
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
) -> str:
    """Assemble structured parameters into SPI's query filter syntax.

    This is the core value-add: agents pass typed params, we build the DSL string.
    """
    # LEARN: We build a list of parts and join them — cleaner than string concatenation
    # and avoids issues with leading/trailing spaces.
    parts: list[str] = []

    if query:
        parts.append(query)

    if author:
        parts.append(f"author:{author}")

    if keyword:
        parts.append(f"keyword:{keyword}")

    if min_stars is not None:
        parts.append(f"stars:>={min_stars}")

    if max_stars is not None:
        parts.append(f"stars:<={max_stars}")

    if platforms:
        # LEARN: SPI expects comma-separated platforms: platform:ios,linux
        platform_str = ",".join(p.value for p in platforms)
        parts.append(f"platform:{platform_str}")

    if license_filter:
        parts.append(f"license:{license_filter}")

    if last_activity_after:
        parts.append(f"last_activity:>={last_activity_after}")

    if last_activity_before:
        parts.append(f"last_activity:<={last_activity_before}")

    if last_commit_after:
        parts.append(f"last_commit:>={last_commit_after}")

    if last_commit_before:
        parts.append(f"last_commit:<={last_commit_before}")

    if product_type:
        parts.append(f"product:{product_type.value}")

    return " ".join(parts)


def _build_search_url(query_string: str, page: int = 1) -> str:
    """Build the full SPI search URL with query and page parameters."""
    url = f"{SPI_SEARCH_URL}?query={quote_plus(query_string)}"
    if page > 1:
        url += f"&page={page}"
    return url


def _extract_metadata(link: Tag) -> tuple[int | None, str | None, bool]:
    """Extract stars, last_activity, has_docs from a result's <ul class='metadata'>."""
    stars = None
    last_activity = None
    has_docs = False
    metadata_ul = link.find("ul", class_="metadata")
    if not isinstance(metadata_ul, Tag):
        return stars, last_activity, has_docs

    for meta_li in metadata_ul.find_all("li", recursive=False):
        if not isinstance(meta_li, Tag):
            continue
        classes = meta_li.get("class") or []
        text = meta_li.get_text(strip=True)

        if isinstance(classes, list) and "stars" in classes:
            # LEARN: Handle comma-separated thousands (e.g. "42,352 stars")
            for word in text.replace(",", "").split():
                if word.isdigit():
                    stars = int(word)
                    break
        elif isinstance(classes, list) and "activity" in classes:
            last_activity = text
        elif isinstance(classes, list) and "has_docs" in classes:
            has_docs = True

    return stars, last_activity, has_docs


def _extract_keywords(link: Tag) -> list[str]:
    """Extract matching keywords from a result's <ul class='keywords'>."""
    keywords: list[str] = []
    kw_ul = link.find("ul", class_="keywords")
    if not isinstance(kw_ul, Tag):
        return keywords
    for kw_li in kw_ul.find_all("li"):
        kw_text = kw_li.get_text(strip=True)
        if kw_text and not kw_text.lower().startswith("matching keyword"):
            keywords.append(kw_text)
    return keywords


def _parse_package_from_li(li: Tag) -> PackageResult | None:
    """Parse a single <li> search result element into a PackageResult.

    Returns None if the element can't be parsed (GRACEFUL_DEGRADATION pattern).

    SPI HTML structure per result::

        <li>
          <a href="/owner/repo">
            <h4>Package Name</h4>
            <p>Description text</p>
            <ul class="keywords matching">...</ul>
            <ul class="metadata">
              <li class="identifier"><small>owner/repo</small></li>
              <li class="activity"><small>Active 22 days ago</small></li>
              <li class="stars"><small>1,377 stars</small></li>
              <li class="has_docs">...</li>  (optional)
            </ul>
          </a>
        </li>
    """
    try:
        # LEARN: SPI wraps the entire result in a single <a> tag (not classed)
        link = li.find("a")
        if not isinstance(link, Tag):
            return None

        raw_href = link.get("href", "")
        href = (raw_href[0] if raw_href else "") if isinstance(raw_href, list) else str(raw_href or "")

        path_parts = href.strip("/").split("/")
        if len(path_parts) < 2:  # noqa: PLR2004
            return None

        author, repo = path_parts[0], path_parts[1]
        name_el = link.find("h4")
        desc_el = link.find("p")
        stars, last_activity, has_docs = _extract_metadata(link)

        return PackageResult(
            name=name_el.get_text(strip=True) if isinstance(name_el, Tag) else repo,
            description=desc_el.get_text(strip=True) if isinstance(desc_el, Tag) else "",
            url=urljoin(SPI_BASE_URL, href),
            github_url=f"https://github.com/{author}/{repo}",
            author=author,
            stars=stars,
            last_activity=last_activity,
            has_docs=has_docs,
            keywords=_extract_keywords(link),
        )
    except Exception:
        logger.exception("Failed to parse search result element")
        return None


def parse_search_results(html: str) -> list[PackageResult]:
    """Parse SPI search results HTML into a list of PackageResult models.

    Uses GRACEFUL_DEGRADATION: if individual results fail to parse,
    we skip them and return what we can.
    """
    soup = BeautifulSoup(html, "lxml")
    results: list[PackageResult] = []

    # LEARN: SPI nests results in: section.package-results > ul (classless)
    # The section also contains a <ul class="filter-list"> and <ul class="pagination">,
    # so we find the <ul> that has NO class attribute — that's the results list.
    package_section = soup.find("section", class_="package-results")
    if not isinstance(package_section, Tag):
        logger.warning("Could not find section.package-results in HTML — SPI may have changed their markup")
        return results

    package_list = None
    for ul in package_section.find_all("ul", recursive=False):
        if not ul.get("class"):
            package_list = ul
            break

    if not isinstance(package_list, Tag):
        logger.warning("Could not find classless <ul> inside package-results — SPI may have changed their markup")
        return results

    for li in package_list.find_all("li", recursive=False):
        if isinstance(li, Tag):
            result = _parse_package_from_li(li)
            if result is not None:
                results.append(result)

    return results


def _has_more_pages(html: str) -> bool:
    """Check if there's a 'next' pagination link in the HTML."""
    soup = BeautifulSoup(html, "lxml")
    # LEARN: SPI uses <ul class="pagination"> with <li class="next"> containing the next-page link.
    pagination = soup.find("ul", class_="pagination")
    if isinstance(pagination, Tag):
        next_li = pagination.find("li", class_="next")
        if isinstance(next_li, Tag) and next_li.find("a"):
            return True
    return False


def _error_response(query: str, page: int, search_url: str, *, next_step: str) -> SearchResponse:
    """Build a SearchResponse for error cases (ERROR_CLASSIFICATION pattern).

    Returns a valid SearchResponse with zero results and an actionable next_step,
    so the agent always gets structured data — never a raw exception.
    """
    return SearchResponse(
        query=query,
        results=[],
        result_count=0,
        page=page,
        has_more=False,
        spi_search_url=search_url,
        next_step=next_step,
    )


def _classify_http_error(status_code: int) -> str:
    """Classify an HTTP status code into an agent-friendly recovery message.

    LEARN: The RECOVERY_GUIDE pattern means every error answers three questions:
    (1) what went wrong, (2) why, (3) how to fix it. We prefix with RETRYABLE
    or PERMANENT so the agent knows whether to retry or change its approach.
    """
    # LEARN: Match statement (Python 3.10+) is cleaner than if/elif chains for
    # mapping discrete values to outcomes.
    match status_code:
        case 429:
            return "RETRYABLE: Rate limited by Swift Package Index. Wait 60 seconds, then retry the same search."
        case 403:
            return "PERMANENT: Access denied by Swift Package Index (403). The site may be blocking automated requests."
        case 404:
            return "PERMANENT: Search endpoint not found (404). SPI may have changed their URL structure."
        case s if 500 <= s < 600:  # noqa: PLR2004
            return f"RETRYABLE: Swift Package Index returned server error ({s}). The site may be under maintenance. Retry in 30 seconds."
        case _:
            return f"PERMANENT: Unexpected HTTP {status_code} from Swift Package Index. Check {SPI_BASE_URL} manually."


async def search_packages(  # noqa: PLR0913
    query: str = "",
    *,
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
    """Execute a search against the Swift Package Index and return structured results."""
    query_string = build_query(
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
    )

    if not query_string.strip():
        return SearchResponse(
            query="",
            results=[],
            result_count=0,
            page=page,
            has_more=False,
            spi_search_url=SPI_SEARCH_URL,
            next_step="Provide a search query or at least one filter (e.g. author, keyword, min_stars).",
        )

    search_url = _build_search_url(query_string, page)

    # LEARN: ERROR_CLASSIFICATION pattern — we catch specific httpx exceptions and return
    # agent-friendly SearchResponse objects instead of letting raw tracebacks propagate.
    # This means the agent ALWAYS gets structured data back, even on failure.
    try:
        async with httpx.AsyncClient(headers=HTTP_HEADERS, timeout=15.0, follow_redirects=True) as client:
            response = await client.get(search_url)
            response.raise_for_status()
    except httpx.TimeoutException:
        return _error_response(
            query_string,
            page,
            search_url,
            next_step="RETRYABLE: Swift Package Index took too long to respond. Retry the same search — transient timeouts are common.",
        )
    except httpx.ConnectError:
        return _error_response(
            query_string,
            page,
            search_url,
            next_step="RETRYABLE: Could not connect to swiftpackageindex.com. The site may be temporarily down. Retry in 30 seconds.",
        )
    except httpx.HTTPStatusError as exc:
        return _error_response(
            query_string,
            page,
            search_url,
            next_step=_classify_http_error(exc.response.status_code),
        )

    html = response.text
    results = parse_search_results(html)
    has_more = _has_more_pages(html)

    # Build next-action hint (NEXT_ACTION_HINT pattern)
    if results:
        next_step = (
            f"Use get_package_readme(owner, repo) to read the README of any result. Pass page={page + 1} to see more results."
            if has_more
            else "Use get_package_readme(owner, repo) to read the README of any result."
        )
    else:
        next_step = "No results found. Try broadening your search — remove filters or use different keywords."

    return SearchResponse(
        query=query_string,
        results=results,
        result_count=len(results),
        page=page,
        has_more=has_more,
        spi_search_url=search_url,
        next_step=next_step,
    )


def _truncate_readme(content: str, max_length: int) -> str:
    """Truncate README content if it exceeds max_length (TOKEN_EFFICIENT_RESPONSE pattern)."""
    if max_length > 0 and len(content) > max_length:
        truncation_msg = f"\n\n... [truncated — full README is {len(content)} chars. Pass max_length=0 for full.]"
        return content[:max_length] + truncation_msg
    return content


async def fetch_readme(owner: str, repo: str, *, max_length: int = 4000) -> str:
    """Fetch a package's README from GitHub raw content.

    SPI detail pages return 403 for scrapers, so we go to GitHub directly.
    Returns truncated content by default (TOKEN_EFFICIENT_RESPONSE pattern).
    """
    # LEARN: raw.githubusercontent.com serves raw file content without GitHub's HTML wrapper.
    # We try common README filenames in order of likelihood.
    filenames = ["README.md", "README.rst", "README.txt", "README", "readme.md"]
    branches = ["main", "master"]

    try:
        async with httpx.AsyncClient(headers=HTTP_HEADERS, timeout=15.0, follow_redirects=True) as client:
            for branch in branches:
                for filename in filenames:
                    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{filename}"
                    response = await client.get(url)
                    if response.status_code == 200:  # noqa: PLR2004
                        return _truncate_readme(response.text, max_length)
                    if response.status_code == 429:  # noqa: PLR2004
                        return f"RETRYABLE: GitHub rate limited the request for {owner}/{repo}. Wait 60 seconds, then retry."
    except httpx.TimeoutException:
        return f"RETRYABLE: GitHub took too long to respond for {owner}/{repo}. Retry the same request."
    except httpx.ConnectError:
        return f"RETRYABLE: Could not connect to GitHub for {owner}/{repo}. Retry in 30 seconds."

    return (
        f"README not found for {owner}/{repo}. The repository may be private, archived, "
        f"or use a non-standard default branch. Check https://github.com/{owner}/{repo} manually."
    )
