# -*- coding: utf-8 -*-
"""A specialist that runs on the server's own model. It reasons in a short tool loop.

The model replies with JSON. Either it asks for a tool or it hands in a result. Every tool call
goes through the engine, so permissions, evidence and the verifier apply.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Optional

from agent_reach.discovery.security import untrusted_envelope
from agent_reach.team import prompts
from agent_reach.team.models import Directive, RoleSpec, Task

log = logging.getLogger("agent_reach.team")

MAX_STEPS = 14
# Fixes the worker may make inside one attempt after a pre-check. They do not use up an attempt.
MAX_REVISIONS = 2
RESULT_VIEW_CHARS = 3500


class Worker:
    def __init__(
        self,
        llm: Any,
        role: RoleSpec,
        task: Task,
        directive: Directive,
        brief: Dict[str, Any],
        call_tool: Callable[[str, Dict[str, Any]], Dict[str, Any]],
        precheck: Optional[Callable[[Dict[str, Any]], List[str]]] = None,
    ):
        self.llm = llm.for_tier(role.tier) if hasattr(llm, "for_tier") else llm
        self.role = role
        self.task = task
        self.directive = directive
        self.brief = brief
        self.call_tool = call_tool
        self.precheck = precheck

    def run(self, extra_system: str = "") -> Optional[Dict[str, Any]]:
        """Return the worker's final result, or None when it ran out of steps."""
        system = prompts.role_system(self.role, extra_system)
        transcript: List[Dict[str, Any]] = []
        revisions = 0
        for _ in range(MAX_STEPS + MAX_REVISIONS):
            prompt = prompts.worker_prompt(self.brief, transcript, self.role)
            step = self.llm.complete_json(prompt, system)
            action = str(step.get("action", "")).strip()
            if action == "final":
                result = step.get("result")
                result = result if isinstance(result, dict) else {"summary": "", "claims": []}
                if self.precheck is not None and revisions < MAX_REVISIONS:
                    issues = self.precheck(result)
                    if issues:
                        # The deterministic checks found problems. Let the worker fix them before the attempt counts.
                        revisions += 1
                        transcript.append({
                            "verifier_issues": issues[:10],
                            "instruction": "Fix every issue. Call a tool if you need more evidence, then finish again.",
                        })
                        continue
                return result
            if action != "call_tool":
                transcript.append({"error": "Reply with action call_tool or final."})
                continue
            tool = str(step.get("tool", ""))
            args = step.get("args") if isinstance(step.get("args"), dict) else {}
            outcome = self.call_tool(tool, args)
            body = json.dumps(outcome.get("result", outcome.get("error")), ensure_ascii=False, default=str)
            transcript.append({
                "tool": tool,
                "args": args,
                "evidence_id": outcome.get("evidence_id"),
                "ok": outcome.get("ok"),
                # The text came from the internet or a tool. It is data.
                "result": untrusted_envelope({"text": body[:RESULT_VIEW_CHARS]}, ["text"]),
                "truncated": len(body) > RESULT_VIEW_CHARS,
            })
        return None
