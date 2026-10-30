# -*- coding: utf-8 -*-
from agent_reach.discovery.business_engine import BusinessEngine
from agent_reach.discovery.llm_client import LLMClient


def test_business_engine_manual_description():
    engine = BusinessEngine(llm_client=LLMClient(provider="mock"))
    desc = """
    SuperTask is an AI-powered GitHub issue triage tool. It automatically identifies duplicate
    issues and prioritizes tickets for engineering teams so they don't spend hours grooming Jira backlogs.
    Pricing starts at $19/seat/month.
    """
    profile = engine.analyze_manual_description(desc, name="SuperTask")

    assert profile.name == "SuperTask"
    assert len(profile.problems_solved) > 0
    assert len(profile.facts) > 0
    assert len(profile.inferences) > 0
    assert profile.confirmed is False

    # Verify editing & confirming
    profile.icp = "Confirmed ICP: Senior Engineering Managers"
    profile.confirmed = True
    assert profile.confirmed is True
    assert profile.icp == "Confirmed ICP: Senior Engineering Managers"


def test_business_engine_website():
    engine = BusinessEngine(llm_client=LLMClient(provider="mock"))
    profile = engine.analyze_website("https://example.com")
    assert profile.url == "https://example.com"
    assert profile.name != ""
    assert len(profile.features) > 0

