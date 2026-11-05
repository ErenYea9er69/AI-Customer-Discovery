# -*- coding: utf-8 -*-
"""Command line for the company layer.

    agent-reach team ask "Find customers for https://my-site.com"   plan and run on the server's model
    agent-reach team status [DIRECTIVE_ID]
    agent-reach team run DIRECTIVE_ID
    agent-reach team report DIRECTIVE_ID
    agent-reach team next DIRECTIVE_ID                               the one next action
    agent-reach team cancel DIRECTIVE_ID [--reason "why"]
    agent-reach team checkpoint TASK_ID approve|reject --message "the owner's words"
    agent-reach team memory [list|add "note"|forget ID]
    agent-reach team roster

Every command prints JSON.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Sequence


def _out(data: Any) -> int:
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    return 1 if isinstance(data, dict) and data.get("error") else 0


def cmd_team(args: Sequence[str]) -> int:
    from agent_reach.mcp.team_tools import get_engine

    usage = "Usage: agent-reach team <ask|status|run|next|cancel|report|checkpoint|memory|roster> [args]"
    if not args or args[0] in ("-h", "--help", "help"):
        print(usage)
        return 0 if args else 1
    sub, rest = args[0], list(args[1:])
    engine = get_engine()
    if sub == "ask":
        p = argparse.ArgumentParser(prog="agent-reach team ask")
        p.add_argument("message", nargs="+")
        ns = p.parse_args(rest)
        return _out(engine.ask(" ".join(ns.message), background=False))
    if sub == "status":
        return _out(engine.status(rest[0] if rest else ""))
    if sub == "run":
        if not rest:
            return _out({"error": "Give a directive id."})
        return _out(engine.run(rest[0]))
    if sub == "report":
        if not rest:
            return _out({"error": "Give a directive id."})
        return _out(engine.report(rest[0]))
    if sub == "checkpoint":
        p = argparse.ArgumentParser(prog="agent-reach team checkpoint")
        p.add_argument("task_id")
        p.add_argument("decision", choices=("approve", "reject"))
        p.add_argument("--message", required=True, help="the owner's own words")
        ns = p.parse_args(rest)
        # The owner types this at their own terminal, so the answer counts as given by the owner directly.
        return _out(engine.resolve_checkpoint(ns.task_id, ns.decision, ns.message, via="cli"))
    if sub == "next":
        if not rest:
            return _out({"error": "Give a directive id."})
        return _out(engine.next_step(rest[0]))
    if sub == "cancel":
        p = argparse.ArgumentParser(prog="agent-reach team cancel")
        p.add_argument("directive_id")
        p.add_argument("--reason", default="")
        ns = p.parse_args(rest)
        return _out(engine.cancel_directive(ns.directive_id, ns.reason))
    if sub == "memory":
        action = rest[0] if rest else "list"
        if action == "add":
            return _out(engine.remember(" ".join(rest[1:])))
        if action == "forget" and len(rest) > 1 and rest[1].isdigit():
            return _out(engine.forget(int(rest[1])))
        if action == "list":
            return _out(engine.recall())
        return _out({"error": "Use: memory list, memory add \"note\", or memory forget ID."})
    if sub == "roster":
        return _out(engine.describe_team())
    return _out({"error": f"Unknown team command: {sub}", "usage": usage})
