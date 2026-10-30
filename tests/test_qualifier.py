# -*- coding: utf-8 -*-
from agent_reach.discovery.models import BusinessProfile, DiscoveredItem
from agent_reach.discovery.qualifier import LeadQualifier


def test_lead_qualifier_high_potential():
    profile = BusinessProfile(
        name="SuperTask",
        industry="SaaS",
        niche="GitHub Issue Triage",
        problems_solved=["Manual issue triage is slow and painful", "Duplicate issues"],
        competitors_and_alternatives=["Jira Software"],
        icp="Engineering Managers and Tech Leads",
        target_roles=["Engineering Lead", "CTO"],
    )

    item = DiscoveredItem(
        url="https://reddit.com/r/programming/1",
        platform="reddit",
        community="r/programming",
        author="lead_dev",
        published_at="2026-10-25",
        title="Looking for a tool to automate GitHub issue duplicate triage",
        content="Our engineering lead and I spend 4 hours every Monday manually checking duplicate issues. We are willing to pay for a tool or alternative to Jira that actually solves this. It's urgent and blocking our sprints.",
    )

    qualifier = LeadQualifier()
    lead = qualifier.qualify(item, profile)

    assert lead is not None
    assert lead.score >= 75
    assert lead.classification == "high_potential"
    assert lead.purchase_intent == "High"
    assert lead.urgency == "High"
    assert lead.score_breakdown.icp_match > 0
    assert lead.score_breakdown.problem_fit > 0
    assert lead.score_breakdown.buying_intent > 0
    assert lead.score_breakdown.total == lead.score
    assert lead.competitor_mentioned == "Jira Software"


def test_lead_qualifier_spam_filter():
    profile = BusinessProfile(name="SuperTask")
    spam_item = DiscoveredItem(
        url="https://reddit.com/r/crypto/1",
        platform="reddit",
        title="Join telegram channel for free bitcoin airdrop",
        content="DM me for rates on crypto casino tokens! Guaranteed returns!",
    )
    qualifier = LeadQualifier()
    result = qualifier.qualify(spam_item, profile)
    assert result is None  # Filtered as spam!

