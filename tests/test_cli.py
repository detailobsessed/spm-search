"""Tests for the CLI entry point."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from spm_search_mcp.cli import main


def test_main_calls_mcp_run():
    with patch("spm_search_mcp.server.mcp") as mock_mcp:
        mock_mcp.run = MagicMock()
        main()
        mock_mcp.run.assert_called_once()
