import sys
import time
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent_reach.discovery.models import (  # noqa: E402
    BusinessProfile,
    LeadQualification,
    ScoreBreakdown,
)
from agent_reach.discovery.storage import DiscoveryStorage  # noqa: E402

VALUE_FIRST = (
    "I stopped chasing by hand when I set one rule: every invoice gets a due date and a reminder "
    "three days before it. A calendar repeat does it for free. It breaks down past twenty clients, "
    "because nobody checks the calendar anymore."
)
PRODUCT_AWARE = VALUE_FIRST + " I built Acme for that stage, so I am biased."


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Tests never touch the internet. A test that needs HTTP passes a fake session."""
    def blocked(*a, **k):
        raise requests.ConnectionError("network blocked in tests")
    monkeypatch.setattr(requests.Session, "request", blocked)
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY",
                "DEEPSEEK_API_KEY", "LLM_PROVIDER", "LLM_MODEL", "SERPER_API_KEY", "BRAVE_API_KEY",
                "TAVILY_API_KEY", "AGENT_REACH_ALLOW_AUTOPOST", "REDDIT_CLIENT_ID"):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def storage(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_REACH_DISCOVERY_DB", str(tmp_path / "t.db"))
    return DiscoveryStorage(tmp_path / "t.db")


@pytest.fixture
def profile():
    return BusinessProfile(
        name="Acme", main_product_or_service="invoice reminders", features=["auto reminders"],
        problems_solved=["chasing late invoices from clients"], pain_vocabulary=["clients pay late every month"],
        icp="freelance designers", competitors_and_alternatives=["FreshBooks"], url="https://acme.test",
    )


def make_lead(**kw):
    base = dict(
        discovered_item_id="i", title="Chasing invoices", url="https://www.reddit.com/r/freelance/comments/abc/x/",
        platform="reddit", community="r/freelance", author="u", published_at="",
        excerpt="I keep forgetting to chase late invoices.", customer_problem="forgets to chase invoices",
        pain_point_category="c", profile_match="m", product_fit_explanation="z", evidence="e", score=60,
        score_breakdown=ScoreBreakdown(icp_match=10, problem_fit=10, buying_intent=10, urgency=10, recency=10, total=50),
    )
    base.update(kw)
    return LeadQualification(**base)


@pytest.fixture
def lead():
    return make_lead()


class FakeLLM:
    """Scripted model. `outputs` is a list of dicts returned in order; the last repeats."""
    is_mock = False
    is_configured = True

    def __init__(self, *outputs):
        self.outputs = list(outputs) or [{}]
        self.calls = []

    def for_tier(self, tier):
        return self

    def complete_json(self, prompt, system_prompt=None):
        self.calls.append((prompt, system_prompt))
        i = min(len(self.calls) - 1, len(self.outputs) - 1)
        return self.outputs[i]


@pytest.fixture
def now():
    return time.time()
