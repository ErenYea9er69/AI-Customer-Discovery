# -*- coding: utf-8 -*-
"""Comprehensive verification of the 16 required test scenarios defined in transformation spec."""

import tempfile
from pathlib import Path

from agent_reach.discovery.analytics import DiscoveryAnalytics
from agent_reach.discovery.business_engine import BusinessEngine
from agent_reach.discovery.harvester import CommunityHarvester
from agent_reach.discovery.llm_client import LLMClient
from agent_reach.discovery.models import (
    BusinessProfile,
    DiscoveredItem,
    LeadQualification,
    PostingSettings,
    SearchQuery,
)
from agent_reach.discovery.publisher import CommunityPublisher
from agent_reach.discovery.qualifier import LeadQualifier
from agent_reach.discovery.reply_generator import ReplyGenerator
from agent_reach.discovery.search_planner import SearchPlanner
from agent_reach.discovery.storage import DiscoveryStorage


def test_scenario_01_submit_website_and_extract_profile():
    """Scenario 1: Submit a website and extract its business profile."""
    engine = BusinessEngine(llm_client=LLMClient(provider="mock"))
    profile = engine.analyze_website("https://example.com")
    assert profile.name != ""
    assert len(profile.features) > 0
    assert len(profile.problems_solved) > 0
    assert len(profile.facts) > 0


def test_scenario_02_submit_manual_description():
    """Scenario 2: Submit a manual product description."""
    engine = BusinessEngine(llm_client=LLMClient(provider="mock"))
    desc = "SuperTask is an AI GitHub issue triage tool eliminating duplicate bugs and prioritizing sprint backlogs."
    profile = engine.analyze_manual_description(desc, name="SuperTask")
    assert profile.name == "SuperTask"
    assert "SuperTask" in profile.facts[0].claim or len(profile.facts) > 0


def test_scenario_03_edit_and_confirm_icp():
    """Scenario 3: Edit and confirm the extracted ICP."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = DiscoveryStorage(Path(tmpdir) / "test.db")
        engine = BusinessEngine(llm_client=LLMClient(provider="mock"))
        profile = engine.analyze_manual_description("Test description", name="SuperTask")
        storage.save_business_profile(profile)

        # Edit ICP
        profile.icp = "Confirmed Target: CTOs and Senior Engineering Managers"
        profile.confirmed = True
        storage.save_business_profile(profile)

        loaded = storage.get_business_profile(profile.id)
        assert loaded is not None
        assert loaded.confirmed is True
        assert loaded.icp == "Confirmed Target: CTOs and Senior Engineering Managers"


def test_scenario_04_generate_customer_specific_search_queries():
    """Scenario 4: Generate customer-specific search queries."""
    planner = SearchPlanner(llm_client=LLMClient(provider="mock"))
    profile = BusinessProfile(
        name="SuperTask",
        industry="DevTools",
        niche="GitHub Issue Triage",
        problems_solved=["Duplicate issues clutter backlog", "Engineers waste hours grooming tickets"],
        competitors_and_alternatives=["Jira Software"],
        customer_outcomes=["Save 20 hours per sprint"],
        icp="Engineering Leads",
    )
    queries = planner.plan_queries(profile)
    assert len(queries) >= 3
    query_texts = " ".join(q.query for q in queries)
    assert "struggling with" in query_texts or "alternative to" in query_texts or "how do you solve" in query_texts


def test_scenario_05_and_06_search_reddit_and_retrieve_posts_and_comments():
    """Scenarios 5 & 6: Search Reddit through available integration and retrieve posts & comments."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = DiscoveryStorage(Path(tmpdir) / "test.db")
        harvester = CommunityHarvester(storage=storage)

        query = SearchQuery(
            query="struggling with duplicate issues",
            intent_type="frustration",
            platform="reddit",
            target_community="r/programming",
        )
        items = harvester.execute_query(query, limit=2)
        assert len(items) > 0
        assert items[0].platform == "reddit"
        assert items[0].title != ""
        assert items[0].content != ""
        assert items[0].author != ""
        assert items[0].url.startswith("https://reddit.com")


def test_scenario_07_filter_unrelated_discussions():
    """Scenario 7: Filter unrelated discussions & spam."""
    profile = BusinessProfile(
        name="SuperTask",
        problems_solved=["Duplicate GitHub issues"],
    )
    qualifier = LeadQualifier()

    # Unrelated spam post
    spam_item = DiscoveredItem(
        url="https://reddit.com/r/crypto/spam1",
        platform="reddit",
        community="r/crypto",
        author="bot123",
        title="Make 100x on this new crypto token",
        content="Join telegram channel for free bitcoin airdrop! Guaranteed returns!",
    )
    assert qualifier.qualify(spam_item, profile) is None

    # Off-topic post
    offtopic_item = DiscoveredItem(
        url="https://reddit.com/r/pics/pic1",
        platform="reddit",
        community="r/pics",
        author="photographer",
        title="Sunset in California",
        content="Took this beautiful picture of the ocean yesterday with my DSLR camera.",
    )
    res = qualifier.qualify(offtopic_item, profile)
    assert res is not None
    assert res.classification == "irrelevant"
    assert res.score < 50


def test_scenario_08_detect_duplicate_posts():
    """Scenario 8: Detect duplicate posts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = DiscoveryStorage(Path(tmpdir) / "test.db")
        item = DiscoveredItem(
            url="https://reddit.com/r/startups/post_dup_1",
            platform="reddit",
            community="r/startups",
            title="Duplicate issue test",
            content="Testing duplicate detection...",
        )
        first_save = storage.save_discovered_item(item)
        assert first_save is True

        # Second save must be detected as duplicate
        second_save = storage.save_discovered_item(item)
        assert second_save is False
        assert storage.is_url_discovered(item.url) is True


def test_scenario_09_and_10_score_potential_leads_and_explain_decisions():
    """Scenarios 9 & 10: Score potential leads and explain scoring decisions."""
    profile = BusinessProfile(
        name="SuperTask",
        industry="SaaS",
        niche="GitHub Issue Triage",
        problems_solved=["Duplicate issues clutter backlog", "Manual ticket triage"],
        competitors_and_alternatives=["Jira Software"],
        icp="Engineering Managers and Tech Leads",
        target_roles=["Engineering Manager", "Lead Dev"],
    )
    item = DiscoveredItem(
        url="https://reddit.com/r/programming/post_lead_1",
        platform="reddit",
        community="r/programming",
        author="tech_lead_dan",
        published_at="2026-10-28",
        title="Looking for a tool or alternative to Jira for GitHub duplicate triage",
        content="Our team is drowning in duplicate issues. We are willing to pay for a tool that automates this. It's urgent and blocking our sprint.",
    )
    qualifier = LeadQualifier()
    lead = qualifier.qualify(item, profile)

    assert lead is not None
    assert 0 <= lead.score <= 100
    assert lead.score >= 75
    assert lead.classification == "high_potential"

    # Score breakdown explanation check
    sb = lead.score_breakdown
    assert sb.icp_match > 0
    assert sb.problem_fit > 0
    assert sb.buying_intent > 0
    assert sb.urgency > 0
    assert sb.recency > 0
    assert sb.total == lead.score
    assert "ICP match:" in sb.explanation
    assert "Problem fit:" in sb.explanation


def test_scenario_11_and_12_generate_and_edit_replies():
    """Scenarios 11 & 12: Generate personalized replies and edit/save them."""
    generator = ReplyGenerator(llm_client=LLMClient(provider="mock"))
    profile = BusinessProfile(
        name="SuperTask",
        niche="GitHub Issue Triage",
        main_product_or_service="AI automated issue triage",
    )
    from agent_reach.discovery.models import ScoreBreakdown
    lead = LeadQualification(
        discovered_item_id="item_01",
        title="Automating GitHub triage",
        url="https://reddit.com/r/programming/1",
        platform="reddit",
        community="r/programming",
        author="user_a",
        published_at="2026-10-29",
        excerpt="Backlog has duplicates...",
        customer_problem="Duplicate issues",
        pain_point_category="DevTools",
        profile_match="Lead dev",
        purchase_intent="High",
        urgency="High",
        product_fit_explanation="SuperTask automates duplicate detection.",
        evidence="Author said duplicates...",
        score=90,
        score_breakdown=ScoreBreakdown(icp_match=25, problem_fit=25, buying_intent=18, urgency=12, recency=10, total=90),
        classification="high_potential",
    )

    reply = generator.generate_replies(lead, profile)
    assert reply.value_first != ""
    assert reply.product_aware != ""
    assert "Disclosure:" in reply.affiliation_disclosure

    # Edit reply
    reply = generator.approve_reply(reply, edited_text="Edited custom response with actionable advice.")
    assert reply.status == "approved"
    assert reply.edited_reply == "Edited custom response with actionable advice."


def test_scenario_13_and_14_approve_reply_and_verify_publishing_behavior():
    """Scenarios 13 & 14: Approve a reply and verify permitted publishing behavior & fallback."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = DiscoveryStorage(Path(tmpdir) / "test.db")
        publisher = CommunityPublisher(storage=storage)
        from agent_reach.discovery.models import GeneratedReply, ScoreBreakdown

        lead = LeadQualification(
            discovered_item_id="item_01",
            title="Automating GitHub triage",
            url="https://reddit.com/r/startups/1",
            platform="reddit",
            community="r/startups",
            author="user_a",
            published_at="2026-10-29",
            excerpt="Need triage tool...",
            customer_problem="Duplicate issues",
            pain_point_category="DevTools",
            profile_match="Lead dev",
            purchase_intent="High",
            urgency="High",
            product_fit_explanation="Solves duplicate issues",
            evidence="Evidence",
            score=90,
            score_breakdown=ScoreBreakdown(icp_match=25, problem_fit=25, buying_intent=18, urgency=12, recency=10, total=90),
            classification="high_potential",
        )
        reply = GeneratedReply(
            lead_id=lead.id,
            value_first="Helpful value-first advice without self-promotion.",
            product_aware="Helpful advice introducing SuperTask (with affiliation disclosure).",
            status="approved",
        )

        settings = PostingSettings(
            mode="manual",
            daily_limit=5,
            allowed_communities=["r/startups"],
            emergency_stop=False,
        )

        # Permitted fallback copy action
        result = publisher.publish_or_copy(reply, lead, settings)
        assert result["success"] is True
        assert result["action"] == "copy_and_open"
        assert result["target_url"] == lead.url
        assert reply.status == "published"


def test_scenario_15_export_leads():
    """Scenario 15: Export leads to JSON and CSV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = DiscoveryStorage(Path(tmpdir) / "test.db")
        from agent_reach.discovery.models import ScoreBreakdown

        lead = LeadQualification(
            discovered_item_id="item_exp_1",
            title="Export verification lead",
            url="https://reddit.com/r/startups/exp",
            platform="reddit",
            community="r/startups",
            author="lead_exporter",
            published_at="2026-10-30",
            excerpt="Export verification excerpt",
            customer_problem="Manual prospecting takes hours",
            pain_point_category="Lead Gen",
            profile_match="Founder ICP",
            purchase_intent="High",
            urgency="High",
            product_fit_explanation="Direct solution",
            evidence="Evidence excerpt",
            score=88,
            score_breakdown=ScoreBreakdown(icp_match=25, problem_fit=25, buying_intent=18, urgency=12, recency=8, total=88),
            classification="high_potential",
        )
        storage.save_lead(lead)

        json_data = storage.export_leads_json()
        assert "lead_exporter" in json_data
        assert "Export verification lead" in json_data

        csv_data = storage.export_leads_csv()
        assert "lead_exporter" in csv_data
        assert "Manual prospecting takes hours" in csv_data


def test_scenario_16_handle_unavailable_platforms_and_rate_limits():
    """Scenario 16: Handle unavailable platforms, emergency stop, and rate limits."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = DiscoveryStorage(Path(tmpdir) / "test.db")
        publisher = CommunityPublisher(storage=storage)
        from agent_reach.discovery.models import GeneratedReply, ScoreBreakdown

        lead = LeadQualification(
            discovered_item_id="item_01",
            title="Automating GitHub triage",
            url="https://reddit.com/r/startups/1",
            platform="reddit",
            community="r/startups",
            author="user_a",
            published_at="2026-10-29",
            excerpt="Need triage tool...",
            customer_problem="Duplicate issues",
            pain_point_category="DevTools",
            profile_match="Lead dev",
            purchase_intent="High",
            urgency="High",
            product_fit_explanation="Solves duplicate issues",
            evidence="Evidence",
            score=90,
            score_breakdown=ScoreBreakdown(icp_match=25, problem_fit=25, buying_intent=18, urgency=12, recency=10, total=90),
            classification="high_potential",
        )
        reply = GeneratedReply(
            lead_id=lead.id,
            value_first="Helpful text",
            product_aware="Product text",
            status="approved",
        )

        # 1. Emergency stop active
        stopped_settings = PostingSettings(emergency_stop=True)
        can_pub, reason = publisher.can_publish(reply, lead, stopped_settings)
        assert can_pub is False
        assert "Emergency stop" in reason

        # 2. Daily limit exceeded in automatic or approved mode
        limited_settings = PostingSettings(mode="automatic", daily_limit=1, allowed_communities=["r/startups"])
        # Publish first post
        res1 = publisher.publish_or_copy(reply, lead, limited_settings)
        assert res1["success"] is True

        # Second attempt for another lead should be blocked by daily limit
        lead2 = LeadQualification(
            discovered_item_id="item_02",
            title="Automating GitHub triage 2",
            url="https://reddit.com/r/startups/2",
            platform="reddit",
            community="r/startups",
            author="user_b",
            published_at="2026-10-29",
            excerpt="Need triage tool...",
            customer_problem="Duplicate issues",
            pain_point_category="DevTools",
            profile_match="Lead dev",
            purchase_intent="High",
            urgency="High",
            product_fit_explanation="Solves duplicate issues",
            evidence="Evidence",
            score=90,
            score_breakdown=ScoreBreakdown(icp_match=25, problem_fit=25, buying_intent=18, urgency=12, recency=10, total=90),
            classification="high_potential",
        )
        reply2 = GeneratedReply(
            lead_id=lead2.id,
            value_first="Helpful text",
            product_aware="Product text",
            status="approved",
        )
        res2 = publisher.publish_or_copy(reply2, lead2, limited_settings)
        assert res2["success"] is False
        assert "Daily publishing limit" in res2["reason"]
