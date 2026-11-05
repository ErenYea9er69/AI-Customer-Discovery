"""Shared fixtures. Nothing here touches the network or the real home directory."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Callable, Dict, List

import pytest

from agent_reach.discovery.models import (
    BusinessProfile,
    DiscoveredItem,
    LeadQualification,
    ScoreBreakdown,
)
from agent_reach.discovery.orchestrator import DiscoveryOrchestrator
from agent_reach.discovery.storage import DiscoveryStorage
from agent_reach.team.engine import TeamEngine
from agent_reach.team.toolbox import Toolbox, ToolDef, _def_from
from agent_reach.team.verifier import Verifier


VALUE_FIRST = (
    "I stopped chasing by hand when I set one rule: every invoice gets a due date and a reminder "
    "three days before it. A calendar repeat does it for free. It breaks down past twenty clients, "
    "because nobody checks the calendar anymore."
)
PRODUCT_AWARE = VALUE_FIRST + " I built Tidewatch for that stage, so I am biased."


def make_lead(**kw):
    base = dict(
        discovered_item_id="i",
        title="Chasing invoices",
        url="https://www.reddit.com/r/freelance/comments/abc/x/",
        platform="reddit",
        community="r/freelance",
        author="u",
        published_at="",
        excerpt="I keep forgetting to chase late invoices.",
        customer_problem="forgets to chase invoices",
        pain_point_category="c",
        profile_match="m",
        product_fit_explanation="z",
        evidence="e",
        score=60,
        score_breakdown=ScoreBreakdown(
            icp_match=10, problem_fit=10, buying_intent=10, urgency=10, recency=10, total=50
        ),
    )
    base.update(kw)
    return LeadQualification(**base)


@pytest.fixture
def lead():
    return make_lead()


class FakeLLM:
    """A scripted model. Each call pops the next reply. A callable reply receives the prompt."""

    is_configured = True
    is_mock = False
    provider = "fake"

    def __init__(self, script: List[Any] | None = None):
        self.script: List[Any] = list(script or [])
        self.prompts: List[str] = []

    def for_tier(self, tier: str) -> "FakeLLM":
        return self

    def complete_json(self, prompt: str, system_prompt: str | None = None) -> Dict[str, Any]:
        self.prompts.append(prompt)
        if not self.script:
            raise AssertionError("FakeLLM ran out of scripted replies")
        item = self.script.pop(0)
        return item(prompt) if callable(item) else item


SITE_TEXT = (
    "Tidewatch tracks invoices for freelancers. Features: automatic invoice reminders, client payment dashboard. "
    "Pricing: 12 dollars per month. Tidewatch helps freelancers who chase late invoices."
)


def fake_fetch(url: str) -> Dict[str, Any]:
    """Stands in for reach_fetch_site_text."""
    return {"site": url, "pages": [{"url": url, "text": SITE_TEXT}]}


@pytest.fixture()
def storage(tmp_path: Path) -> DiscoveryStorage:
    return DiscoveryStorage(tmp_path / "test.db")


@pytest.fixture()
def svc(storage: DiscoveryStorage, monkeypatch: pytest.MonkeyPatch) -> DiscoveryOrchestrator:
    from agent_reach.mcp import server

    service = DiscoveryOrchestrator(storage)
    monkeypatch.setattr(server, "_storage_instance", storage)
    monkeypatch.setattr(server, "_service", service)
    return service


@pytest.fixture()
def make_engine(svc: DiscoveryOrchestrator) -> Callable[..., TeamEngine]:
    def build(llm: Any = None, audit: bool = False) -> TeamEngine:
        if llm is not None:
            svc.llm = llm
        extra: Dict[str, ToolDef] = {"reach_fetch_site_text": _def_from("reach_fetch_site_text", fake_fetch)}
        return TeamEngine(lambda: svc, toolbox=Toolbox(lambda: svc, extra=extra), verifier=Verifier(lambda: svc, audit=audit))

    return build


@pytest.fixture()
def profile(storage: DiscoveryStorage) -> BusinessProfile:
    p = BusinessProfile(
        name="Tidewatch", url="https://tidewatch.example", description="Invoice tracking for freelancers",
        problems_solved=["late invoices"], pain_vocabulary=["client paid me late again", "chasing invoices every month"],
        features=["automatic invoice reminders"], confirmed=True,
    )
    storage.save_business_profile(p)
    return p


@pytest.fixture()
def thread(storage: DiscoveryStorage) -> DiscoveredItem:
    item = DiscoveredItem(
        url="https://www.reddit.com/r/freelance/comments/abc123/late_invoices/", platform="reddit",
        community="r/freelance", author="someone", title="My clients pay late every month",
        content="I keep chasing invoices every month and my clients pay late. Is there a tool that reminds them for me?",
        thread_health={"commentable": True, "num_comments": 4, "age_days": 2},
    )
    storage.save_discovered_item(item)
    return item


def run(coro: Any) -> Any:
    return asyncio.run(coro)
