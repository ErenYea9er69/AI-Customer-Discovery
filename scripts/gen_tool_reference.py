#!/usr/bin/env python3
"""Write skills/customer-discovery/references/tool-reference.md from the live MCP server.

Run `python scripts/gen_tool_reference.py` after you add or change a tool. CI runs it with
--check and fails when the file is stale.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "skills" / "customer-discovery" / "references" / "tool-reference.md"


def _g(obj, *names):
    """Read an attribute under either SDK naming (camelCase in 1.x, snake_case in 2.x)."""
    for name in names:
        value = getattr(obj, name, None)
        if value is not None:
            return value
    return None


def render() -> str:
    sys.path.insert(0, str(ROOT))
    from agent_reach.mcp import server

    tools = asyncio.run(server.mcp.list_tools())
    lines = [
        "# MCP tool reference",
        "",
        "Generated from the server by `scripts/gen_tool_reference.py`. Do not edit by hand.",
        "",
    ]
    for tool in sorted(tools, key=lambda t: t.name):
        ann = tool.annotations
        read_only = bool(ann and _g(ann, "readOnlyHint", "read_only_hint"))
        open_world = bool(ann and _g(ann, "openWorldHint", "open_world_hint"))
        kind = "reads only" if read_only else ("reads public pages and writes locally" if open_world else "writes locally")
        lines += [f"## {tool.name}", "", f"Effect: {kind}.", ""]
        doc = (tool.description or "").strip()
        lines += [doc, ""]
        schema = _g(tool, "inputSchema", "input_schema") or {}
        props = schema.get("properties", {})
        required = set(schema.get("required", []))
        if props:
            lines.append("Arguments:")
            lines.append("")
            for name, spec in props.items():
                typ = spec.get("type") or "/".join(
                    t.get("type", "any") for t in spec.get("anyOf", []) if t.get("type") != "null"
                ) or "any"
                default = "" if name in required else f", default {spec.get('default')!r}"
                lines.append(f"- `{name}` ({typ}{', required' if name in required else default})")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    ns = parser.parse_args()
    text = render()
    if ns.check:
        if not TARGET.exists() or TARGET.read_text(encoding="utf-8") != text:
            print(f"{TARGET} is stale. Run: python scripts/gen_tool_reference.py", file=sys.stderr)
            return 1
        return 0
    TARGET.write_text(text, encoding="utf-8")
    print(f"wrote {TARGET} ({len(text)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
