# spm-search-mcp

[![ci](https://github.com/detailobsessed/spm-search/workflows/ci/badge.svg)](https://github.com/detailobsessed/spm-search/actions?query=workflow%3Aci)
[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)

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

### Published package (once on PyPI)

```json
{
  "mcpServers": {
    "spm-search": {
      "command": "uvx",
      "args": ["spm-search-mcp"]
    }
  }
}
```

### From source (development)

```json
{
  "mcpServers": {
    "spm-search": {
      "command": "uv",
      "args": [
        "run",
        "--with", "fastmcp",
        "--with-editable", "/path/to/spm-search",
        "fastmcp", "run",
        "/path/to/spm-search/src/spm_search_mcp/server.py:mcp"
      ]
    }
  }
}
```

## Tools

### `search_swift_packages`

Search for Swift packages by keyword, author, stars, platform, license, and more. All of SPI's [filter syntax](https://swiftpackageindex.com/faq#search-filters) is exposed as typed parameters — agents never need to learn the DSL.

| Parameter | Type | Description |
| --- | --- | --- |
| `query` | `str` | Free-text search (e.g. `"networking"`, `"json parsing"`) |
| `author` | `str` | Repository owner (e.g. `"apple"`, `"vapor"`) |
| `keyword` | `str` | Package keyword tag (e.g. `"server"`, `"ui"`) |
| `min_stars` | `int` | Minimum GitHub star count |
| `max_stars` | `int` | Maximum GitHub star count |
| `platforms` | `list` | Compatible platforms: `ios`, `macos`, `watchos`, `tvos`, `visionos`, `linux` |
| `license_filter` | `str` | `"compatible"` for App Store, or SPDX ID like `"mit"`, `"apache-2.0"` |
| `last_activity_after` | `str` | ISO8601 date — only active packages (e.g. `"2024-01-01"`) |
| `last_commit_after` | `str` | ISO8601 date — only recently committed packages |
| `product_type` | `str` | `library`, `executable`, `plugin`, or `macro` |
| `page` | `int` | Page number for pagination (default 1) |

All parameters are optional. At least one must be provided. Parameters combine with AND logic.

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

# Browse a specific author's packages
search_swift_packages(author="apple")

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

- **QUERY_TOOL** — both tools are read-only, safe to retry
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
