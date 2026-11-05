# -*- coding: utf-8 -*-
"""The tools a specialist can launch, with a permission check per role.

The toolbox wraps the verified `reach_*` functions of the MCP server plus a few read-only
`team_*` helpers. A specialist reaches a tool only when its role lists the tool. Restricted
tools (publish, approve, settings, accounts) never reach a specialist, whatever the role says.
"""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from agent_reach.discovery.security import untrusted_envelope
from agent_reach.team.models import RoleSpec
from agent_reach.team.roles import RESTRICTED_TOOLS

MAX_RESULT_CHARS = 60000


@dataclass
class ToolDef:
    name: str
    description: str
    params: Dict[str, bool]  # parameter name -> required
    fn: Callable[..., Any]
    restricted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "params": [p + ("" if req else "?") for p, req in self.params.items()],
            "restricted": self.restricted,
        }


def _describe(fn: Callable[..., Any]) -> str:
    doc = inspect.getdoc(fn) or ""
    return doc.strip().splitlines()[0] if doc.strip() else fn.__name__


def _unwrap(obj: Any) -> Optional[Callable[..., Any]]:
    """MCP SDK lines differ on what the decorator returns. Accept a function or a tool object."""
    if inspect.isfunction(obj):
        return obj
    inner = getattr(obj, "fn", None)
    return inner if callable(inner) else None


def _def_from(name: str, fn: Callable[..., Any]) -> ToolDef:
    sig = inspect.signature(fn)
    params = {
        p.name: p.default is inspect.Parameter.empty
        for p in sig.parameters.values()
        if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
    }
    return ToolDef(name=name, description=_describe(fn), params=params, fn=fn, restricted=name in RESTRICTED_TOOLS)


class Toolbox:
    """Registry plus permission-checked launcher.

    `svc_getter` returns the DiscoveryOrchestrator that holds storage and services.
    `extra` adds or overrides tools (tests use it to run without a network).
    """

    def __init__(self, svc_getter: Callable[[], Any], extra: Optional[Dict[str, ToolDef]] = None):
        self._svc = svc_getter
        self._tools: Dict[str, ToolDef] = {}
        self._extra = dict(extra or {})
        self._loaded = False

    # ── Registry ──

    def _load(self) -> None:
        if self._loaded:
            return
        from agent_reach.mcp import server  # late import: the server imports the team package

        for attr in dir(server):
            if not attr.startswith("reach_"):
                continue
            fn = _unwrap(getattr(server, attr))
            if fn is not None:
                self._tools[attr] = _def_from(attr, fn)
        for name, fn in self._internal().items():
            self._tools[name] = _def_from(name, fn)
        self._tools.update(self._extra)
        self._loaded = True

    def tools(self) -> Dict[str, ToolDef]:
        self._load()
        return self._tools

    def catalog(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in sorted(self.tools().values(), key=lambda t: t.name)]

    def allowed_for(self, role: RoleSpec) -> List[str]:
        tools = self.tools()
        return [n for n in role.tools if n in tools and not tools[n].restricted]

    # ── Launch ──

    def call(self, role: RoleSpec, name: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run one tool for a role. Never raises. Returns {"ok": bool, "result": ...} or an error."""
        tools = self.tools()
        tool = tools.get(name)
        if tool is None:
            return {"ok": False, "error": f"Unknown tool {name}.", "available": self.allowed_for(role)}
        if tool.restricted or name not in role.tools:
            return {
                "ok": False,
                "error": f"The {role.name} role may not use {name}.",
                "available": self.allowed_for(role),
            }
        args = dict(args or {})
        unknown = [a for a in args if a not in tool.params]
        if unknown:
            return {"ok": False, "error": f"Unknown argument(s) for {name}: {', '.join(unknown)}.", "params": list(tool.params)}
        missing = [p for p, req in tool.params.items() if req and p not in args]
        if missing:
            return {"ok": False, "error": f"Missing argument(s) for {name}: {', '.join(missing)}.", "params": list(tool.params)}
        try:
            result = tool.fn(**args)
        except Exception as exc:  # a tool failure goes back to the worker as data
            return {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:300]}"}
        try:
            safe = json.loads(json.dumps(result, default=str))
        except (TypeError, ValueError):
            safe = {"value": str(result)}
        failed = isinstance(safe, dict) and bool(safe.get("error"))
        return {"ok": not failed, "result": safe}

    # ── Read-only team helpers ──

    def _internal(self) -> Dict[str, Callable[..., Any]]:
        svc_getter = self._svc

        def team_read_profile() -> Dict[str, Any]:
            """Return the saved business profile (read only)."""
            profile = svc_getter().storage.get_latest_business_profile()
            return profile.model_dump() if profile else {"error": "No profile saved yet."}

        def team_read_items(limit: int = 30, platform: str = "") -> Dict[str, Any]:
            """Return harvested threads from the database, newest first (read only, untrusted text)."""
            items = svc_getter().storage.list_discovered_items(limit=limit, platform=platform or None)
            rows = []
            for it in items:
                view = {
                    "item_id": it.id, "url": it.url, "platform": it.platform, "community": it.community,
                    "author": it.author, "title": it.title, "content": (it.content or "")[:1200],
                    "thread_health": it.thread_health,
                }
                rows.append(untrusted_envelope(view, ["title", "content"]))
            return {"count": len(rows), "items": rows}

        def team_read_replies(status: str = "", limit: int = 30) -> Dict[str, Any]:
            """Return saved reply drafts with their lint reports (read only)."""
            replies = svc_getter().storage.list_replies(status=status or None, limit=max(1, min(limit, 100)))
            return {
                "count": len(replies),
                "replies": [
                    {
                        "reply_id": r.id, "lead_id": r.lead_id, "status": r.status, "platform": r.platform,
                        "pitch_level": r.pitch_level, "value_first": r.value_first,
                        "product_aware": r.product_aware, "lint_passed": {k: bool(v.get("passed")) for k, v in r.lint.items()},
                    }
                    for r in replies
                ],
            }

        return {
            "team_read_profile": team_read_profile,
            "team_read_items": team_read_items,
            "team_read_replies": team_read_replies,
        }
