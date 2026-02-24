"""CLI entry point for the spm-search-mcp server."""

from __future__ import annotations


def main() -> None:
    """Run the MCP server via stdio transport.

    This is the entry point registered in pyproject.toml as the
    `spm-search-mcp` console script.
    """
    # LEARN: Importing here (not at module level) keeps `import spm_search_mcp` fast.
    # The server + all its deps only load when you actually run the CLI.
    from spm_search_mcp.server import mcp  # noqa: PLC0415 — lazy import keeps `import spm_search_mcp` fast

    mcp.run()


if __name__ == "__main__":
    main()
