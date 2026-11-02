# -*- coding: utf-8 -*-
"""One import path for both MCP Python SDK lines.

SDK 1.x ships `mcp.server.fastmcp.FastMCP`. SDK 2.x renamed it to
`mcp.server.mcpserver.MCPServer`. The tool, resource and prompt decorators and
`run(transport=...)` behave the same in both, so the server code stays one file.
"""

from __future__ import annotations

from typing import Any, Optional

try:  # SDK 2.x
    from mcp.server.mcpserver import MCPServer as _Server
    SDK_LINE = "2.x"
except ImportError:  # SDK 1.x
    from mcp.server.fastmcp import FastMCP as _Server  # type: ignore[assignment,no-redef,attr-defined,unused-ignore]
    SDK_LINE = "1.x"

from mcp.types import ToolAnnotations

__all__ = ["SDK_LINE", "make_server", "read_only", "writes", "network"]


def make_server(name: str, instructions: str) -> Any:
    return _Server(name, instructions=instructions)


def _annotations(title: str, read_only_hint: bool, destructive: bool, idempotent: bool, open_world: bool) -> ToolAnnotations:
    # The 1.x and 2.x models both accept the protocol field names through their aliases.
    return ToolAnnotations.model_validate({
        "title": title,
        "readOnlyHint": read_only_hint,
        "destructiveHint": destructive,
        "idempotentHint": idempotent,
        "openWorldHint": open_world,
    })


def read_only(title: str, open_world: bool = False) -> ToolAnnotations:
    """The tool reads local state only (or public pages when open_world is true)."""
    return _annotations(title, True, False, True, open_world)


def writes(title: str, idempotent: bool = True, destructive: bool = False) -> ToolAnnotations:
    """The tool writes to the local database only."""
    return _annotations(title, False, destructive, idempotent, False)


def network(title: str, idempotent: bool = True) -> ToolAnnotations:
    """The tool reads public pages or APIs and writes results to the local database."""
    return _annotations(title, False, False, idempotent, True)


def version_of_sdk() -> Optional[str]:
    try:
        from importlib.metadata import version

        return version("mcp")
    except Exception:
        return None
