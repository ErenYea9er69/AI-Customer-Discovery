# -*- coding: utf-8 -*-
import tempfile
from pathlib import Path

from agent_reach.discovery.analytics import DiscoveryAnalytics
from agent_reach.discovery.models import LeadQualification, ScoreBreakdown
from agent_reach.discovery.storage import DiscoveryStorage


def test_discovery_analytics_aggregation():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = DiscoveryStorage(Path(tmpdir) / "test.db")
        analytics = DiscoveryAnalytics(storage=storage)

        # Empty state
        empty_insights = analytics.get_insights()
        assert empty_insights["total_leads"] == 0

        # Add sample leads
        breakdown = ScoreBreakdown(
            icp_match=25, problem_fit=28, buying_intent=18, urgency=14, recency=9, total=94
        )
        lead1 = LeadQualification(
            discovered_item_id="item_01",
            title="Tired of duplicate issues in GitHub",
            url="https://reddit.com/r/devops/1",
            platform="reddit",
            community="r/devops",
            author="dev_lead",
            published_at="2026-10-28",
            excerpt="Our engineers waste hours every Monday...",
            customer_problem="Manual issue triage is slow and painful",
            pain_point_category="Developer Productivity",
            profile_match="Matches ICP",
            competitor_mentioned="Jira",
            purchase_intent="High",
            urgency="High",
            product_fit_explanation="Direct fit",
            evidence="Author stated: waste hours every Monday",
            score=94,
            score_breakdown=breakdown,
            classification="high_potential",
        )
        storage.save_lead(lead1)

        insights = analytics.get_insights()
        assert insights["total_leads"] == 1
        assert len(insights["common_complaints"]) == 1
        assert insights["common_complaints"][0]["problem"] == "Manual issue triage is slow and painful"
        assert len(insights["competitor_intelligence"]) == 1
        assert insights["competitor_intelligence"][0]["competitor"] == "Jira"
        assert len(insights["recommendations"]) >= 1

