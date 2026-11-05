# -*- coding: utf-8 -*-
"""Data models for the company layer: roles, directives, tasks, evidence and verdicts."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class RoleSpec(BaseModel):
    """One specialist in the company. The charter is its standing prompt."""
    name: str
    title: str
    charter: str
    skills: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    # "fast" suits checking work. "smart" suits writing and analysis.
    tier: Literal["fast", "smart"] = "smart"
    builtin: bool = True
    # Extra deterministic check applied to the role's output (name of a check in verifier.py).
    check: str = ""
    # An automatic role runs in the engine without a model and without the host assistant.
    auto: bool = False


class Evidence(BaseModel):
    """What one tool call returned. Claims must point at these."""
    id: str
    tool: str
    ok: bool = True
    args: Dict[str, Any] = Field(default_factory=dict)
    # Full result as text. Quotes are checked against it.
    text: str = ""
    urls: List[str] = Field(default_factory=list)
    at: float = Field(default_factory=time.time)


class Verdict(BaseModel):
    """Result of verifying a task's output."""
    passed: bool
    issues: List[str] = Field(default_factory=list)
    checks: Dict[str, bool] = Field(default_factory=dict)
    # "pass", "fail", "unavailable" or "skipped". The auditor model is optional.
    auditor: str = "skipped"
    # Things the checks accepted but the CEO should know, such as claims labeled as assumptions.
    notes: List[str] = Field(default_factory=list)
    # "high": every check and an independent auditor passed. "medium": the checks passed and no auditor ran.
    # "low": the checks passed but the auditor was unreliable or unavailable for a risky role.
    trust: str = "medium"
    at: float = Field(default_factory=time.time)


TaskStatus = Literal[
    "pending",       # waits for dependencies
    "ready",         # can start
    "running",       # a worker or the host AI holds it
    "done",          # output verified
    "escalated",     # failed verification too many times. The CEO must decide.
    "needs_owner",   # waits for the human owner
    "blocked",       # a dependency did not finish
    "skipped",
]


class Task(BaseModel):
    id: str = Field(default_factory=lambda: new_id("task"))
    directive_id: str
    role: str
    title: str
    instruction: str = ""
    kind: Literal["work", "checkpoint"] = "work"
    # For checkpoints: confirm_profile, review_replies or a custom label.
    checkpoint: str = ""
    depends_on: List[str] = Field(default_factory=list)
    acceptance: List[str] = Field(default_factory=list)
    status: TaskStatus = "pending"
    attempts: int = 0
    max_attempts: int = 3
    feedback: List[str] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    verdict: Optional[Verdict] = None
    owner_message: str = ""
    # How the owner answered a checkpoint: "assistant" (through the host AI) or "dashboard" (owner's own click).
    owner_channel: str = ""
    # The task is skipped when an earlier task reported nothing found. No input means no work.
    skip_when_empty: bool = False
    skipped_empty: bool = False
    # The CEO already asked this task to widen its work once after an empty result.
    replans: int = 0
    # Editor loop round. 0 is the first pass.
    round: int = 0
    # Set when the task starts running. A task that stays running past the lease goes back to ready.
    started_at: float = 0.0
    tool_calls: int = 0
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


DirectiveStatus = Literal["open", "running", "waiting_owner", "needs_ceo", "completed", "failed", "cancelled"]


class Directive(BaseModel):
    """One request from the owner, planned by the CEO."""
    id: str = Field(default_factory=lambda: new_id("dir"))
    request: str
    intent: str = "custom"
    playbook: str = ""
    status: DirectiveStatus = "open"
    notes: List[str] = Field(default_factory=list)
    # Hard ceiling on tool calls for the whole directive. It stops a loop that burns money.
    tool_budget: int = 150
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class PlaybookStep(BaseModel):
    key: str
    role: str
    title: str
    instruction: str = ""
    depends_on: List[str] = Field(default_factory=list)
    acceptance: List[str] = Field(default_factory=list)
    kind: Literal["work", "checkpoint"] = "work"
    checkpoint: str = ""
    skip_when_empty: bool = False


class Playbook(BaseModel):
    name: str
    description: str = ""
    steps: List[PlaybookStep] = Field(default_factory=list)
    builtin: bool = True
