# spm-search-mcp

[![ci](https://github.com/detailobsessed/spm-search-mcp/workflows/ci/badge.svg)](https://github.com/detailobsessed/spm-search-mcp/actions?query=workflow%3Aci)
[![codecov](https://codecov.io/gh/detailobsessed/spm-search-mcp/graph/badge.svg)](https://codecov.io/gh/detailobsessed/spm-search-mcp)
[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/docs-gofastmcp.com-orange)](https://gofastmcp.com)
[![MCP](https://img.shields.io/badge/MCP-protocol-5B5BD6)](https://modelcontextprotocol.io)

An [MCP](https://modelcontextprotocol.io) server that lets coding agents search the [Swift Package Index](https://swiftpackageindex.com). No API key required.

Built with [FastMCP](https://gofastmcp.com) and designed using [arcade patterns](https://www.arcade.dev/patterns) for optimal agent comprehension.

## Quick install

From the repo root, run the command for your MCP client:

```bash
# Claude Desktop
fastmcp install claude-desktop src/spm_search_mcp/server.py:mcp --with-editable . -n "Swift Package Index"

# Claude Code
fastmcp install claude-code src/spm_search_mcp/server.py:mcp --with-editable . -n "Swift Package Index"

# Cursor
fastmcp install cursor src/spm_search_mcp/server.py:mcp --with-editable . -n "Swift Package Index"

# Any client — print the JSON snippet to paste
fastmcp install mcp-json src/spm_search_mcp/server.py:mcp --with-editable . -n "Swift Package Index"
```

## Manual MCP client configuration

### Via GitHub (no install needed)

```jsonc
// add to your mcpServers:
"spm-search-mcp": {
  "command": "uvx",
  "args": [
    "--from", "git+https://github.com/detailobsessed/spm-search-mcp",
    "spm-search-mcp"
  ]
}
```

Requires [uv](https://docs.astral.sh/uv/) (`brew install uv` on macOS).

### From source (development)

```jsonc
// add to your mcpServers:
"spm-search-mcp": {
  "command": "uv",
  "args": [
    "run",
    "--with", "fastmcp",
    "--with-editable", "/path/to/spm-search-mcp",
    "fastmcp", "run",
    "/path/to/spm-search-mcp/src/spm_search_mcp/server.py:mcp"
  ]
}
```

## Tools

### `search_swift_packages`

Search for Swift packages by keyword, author, stars, platform, license, and more. All of SPI's [filter syntax](https://swiftpackageindex.com/faq#search-filters) is exposed as typed parameters — agents never need to learn the DSL.

| Parameter | Type | Description |
| --- | --- | --- |
| `query` | `str` | Free-text search (e.g. `"networking"`, `"json parsing"`) |
| `author` | `str` | Repository owner. Prefix with `!` to exclude (e.g. `"!vapor"`) |
| `keyword` | `str` | Package keyword tag. Prefix with `!` to exclude (e.g. `"!deprecated"`) |
| `min_stars` | `int` | Minimum GitHub star count |
| `max_stars` | `int` | Maximum GitHub star count |
| `platforms` | `list` | Compatible platforms: `ios`, `macos`, `watchos`, `tvos`, `visionos`, `linux` |
| `license_filter` | `str` | `"compatible"` for App Store, SPDX ID like `"mit"`, `"apache-2.0"`, or prefix `!` to exclude |
| `last_activity_after` | `str` | ISO8601 date — only packages active after this date |
| `last_activity_before` | `str` | ISO8601 date — only packages active before this date (combine with `after` for a window) |
| `last_commit_after` | `str` | ISO8601 date — only packages with commits after this date |
| `last_commit_before` | `str` | ISO8601 date — only packages with commits before this date |
| `product_type` | `str` | `library`, `executable`, `plugin`, or `macro` |
| `page` | `int` | Page number for pagination (default 1) |

All parameters are optional. At least one must be provided. Parameters combine with AND logic.

### `list_search_filters`

Returns valid values for the `platforms` and `product_type` parameters. Call this first if unsure what values are accepted.

_No parameters._ Returns a dict with `platforms` and `product_types` keys.

### `get_package_readme`

Fetch a package's README from GitHub. Returns truncated content by default (4000 chars) to save tokens.

| Parameter | Type | Description |
| --- | --- | --- |
| `owner` | `str` | GitHub repository owner (e.g. `"Alamofire"`) |
| `repo` | `str` | GitHub repository name (e.g. `"Alamofire"`) |
| `max_length` | `int` | Max chars to return (default 4000). Set to `0` for full content. |

## Example usage

Once connected, an agent can:

```text
# Search for networking libraries with 500+ stars
search_swift_packages(query="networking", min_stars=500)

# Find iOS-compatible packages
search_swift_packages(platforms=["ios"], min_stars=100)

# Discover valid platform and product_type values
list_search_filters()

# Browse a specific author's packages
search_swift_packages(author="apple")

# Exclude an author
search_swift_packages(query="networking", author="!vapor", min_stars=500)

# Exclude deprecated packages
search_swift_packages(query="json", keyword="!deprecated")

# Packages active in a date window (first half of 2024)
search_swift_packages(last_activity_after="2024-01-01", last_activity_before="2024-06-30", min_stars=100)

# Find abandoned packages (no commits since 2022)
search_swift_packages(last_commit_before="2022-01-01", min_stars=200)

# Read a package's README
get_package_readme(owner="Alamofire", repo="Alamofire")

# Get full README (no truncation)
get_package_readme(owner="apple", repo="swift-nio", max_length=0)
```

## Error handling

All errors return structured, actionable messages instead of raw exceptions:

- **RETRYABLE** — transient failures (timeouts, rate limits, server errors). The agent can retry.
- **PERMANENT** — the request itself is wrong (404, 403). The agent should change its approach.

Every error message tells the agent what happened, why, and how to fix it.

## Design

This server implements these [arcade patterns](https://www.arcade.dev/patterns):

- **QUERY_TOOL** — all tools are read-only, safe to retry
- **DISCOVERY_TOOL** — `list_search_filters()` exposes valid enum values before searching
- **CONSTRAINED_INPUT** — enums for platforms and product types
- **SMART_DEFAULTS** — all parameters optional with sensible defaults
- **NEXT_ACTION_HINT** — every response suggests what to do next
- **GUI_URL** — every result includes SPI + GitHub URLs
- **TOKEN_EFFICIENT_RESPONSE** — truncated README with opt-in full
- **PAGINATED_RESULT** — `has_more` flag with page navigation
- **ERROR_CLASSIFICATION** — RETRYABLE vs PERMANENT error tagging
- **RECOVERY_GUIDE** — actionable error messages with fix instructions
- **PROGRESSIVE_DETAIL** — `max_length=0` for full README content

## Development

```bash
uv sync                  # install dependencies
uv run pytest            # run tests
uv run poe test-cov      # run with coverage (90%+ required)
uv run ruff check .      # lint
uv run ty check .        # type check
prek run --all-files     # run all pre-commit hooks
```
