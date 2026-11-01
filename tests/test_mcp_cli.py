# -*- coding: utf-8 -*-
"""Tests for CLI integration of `agent-reach mcp`."""

from unittest.mock import patch
import pytest

from agent_reach.runtime.cli import main


def test_cli_mcp_help(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["mcp", "--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "Model Context Protocol" in captured.out or "FastMCP" in captured.out or "agent-reach mcp" in captured.out


@patch("agent_reach.mcp.server.main")
def test_cli_mcp_run(mock_server_main):
    code = main(["mcp"])
    assert code == 0
    mock_server_main.assert_called_once()

