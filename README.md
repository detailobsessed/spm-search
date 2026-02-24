# spm-search-mcp

[![ci](https://github.com/detailobsessed/spm-search-mcp/workflows/ci/badge.svg)](https://github.com/detailobsessed/spm-search-mcp/actions?query=workflow%3Aci)
[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)

An MCP server that lets coding agents search the [Swift Package Index](https://swiftpackageindex.com). No API key required.

## Tools

### `search_swift_packages`

Search for Swift packages by keyword, author, stars, platform, license, and more. All of SPI's [filter syntax](https://swiftpackageindex.com/faq#search-filters) is exposed as typed parameters — agents never need to learn the DSL.

### `get_package_readme`

Fetch a package's README from GitHub. Returns truncated content by default (4000 chars) to save tokens, with an option for full content.

## Installation

```bash
uv tool install spm-search-mcp
```

Or install from source:

```bash
git clone https://github.com/detailobsessed/spm-search-mcp.git
cd spm-search-mcp
uv sync
```

## MCP client configuration

### Windsurf / Cursor

Add to your MCP config (`~/.codeium/windsurf/mcp_config.json` or equivalent):

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

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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
      "args": ["run", "--directory", "/path/to/spm-search-mcp", "spm-search-mcp"]
    }
  }
}
```

## Example usage

Once connected, an agent can:

- Search for networking libraries: `search_swift_packages(query="networking", min_stars=500)`
- Find iOS-compatible packages: `search_swift_packages(platforms=["ios"], min_stars=100)`
- Browse a specific author: `search_swift_packages(author="apple")`
- Read a package's README: `get_package_readme(owner="Alamofire", repo="Alamofire")`

## Development

```bash
uv sync              # install dependencies
uv run pytest        # run tests
uv run ruff check .  # lint
uv run ty check .    # type check
```
