# -*- coding: utf-8 -*-
import tempfile
from pathlib import Path

from agent_reach.discovery.models import (
    BusinessProfile,
    DiscoveredItem,
    GeneratedReply,
    LeadQualification,
    ScoreBreakdown,
)
from agent_reach.discovery.storage import DiscoveryStorage


def test_discovery_storage_crud():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_discovery.db"
        storage = DiscoveryStorage(db_path)

        # 1. Business Profile
        profile = BusinessProfile(
            name="ReachAI",
            url="https://reachai.example.com",
            description="Autonomous customer discovery",
            industry="SaaS",
            niche="AI Growth Tools",
            problems_solved=["Manual prospecting takes hours"],
            icp="Founders and Sales Leaders",
        )
        storage.save_business_profile(profile)
        retrieved = storage.get_business_profile(profile.id)
        assert retrieved is not None
        assert retrieved.name == "ReachAI"
        assert retrieved.niche == "AI Growth Tools"

        # 2. Discovered Item & Deduplication
        item1 = DiscoveredItem(
            url="https://reddit.com/r/startups/123",
            platform="reddit",
            community="r/startups",
            title="Need a better lead gen tool",
            content="I spend all day searching forums manually...",
        )
        assert storage.save_discovered_item(item1) is True
        # Duplicate check
        assert storage.is_url_discovered("https://reddit.com/r/startups/123") is True
        assert storage.save_discovered_item(item1) is False

        # 3. Lead Qualification
        score_breakdown = ScoreBreakdown(
            icp_match=25,
            problem_fit=28,
            buying_intent=18,
            urgency=12,
            recency=8,
            total=91,
            explanation="Strong founder ICP, acute manual prospecting pain point.",
        )
        lead = LeadQualification(
            discovered_item_id=item1.id,
            title=item1.title,
            url=item1.url,
            platform=item1.platform,
            community=item1.community,
            author="startup_founder_99",
            published_at="2026-10-28",
            excerpt=item1.content,
            customer_problem="Manual forum prospecting is slow and ineffective.",
            pain_point_category="Time Consumption",
            profile_match="Matches B2B founder ICP",
            purchase_intent="High",
            urgency="High",
            product_fit_explanation="Automates forum problem discovery.",
            evidence="Author stated: I spend all day searching forums manually",
            score=91,
            score_breakdown=score_breakdown,
            classification="high_potential",
        )
        storage.save_lead(lead)

        leads = storage.list_leads(min_score=80)
        assert len(leads) == 1
        assert leads[0].score == 91
        assert leads[0].classification == "high_potential"

        counts = storage.count_leads()
        assert counts["total"] == 1
        assert counts["high_potential"] == 1

        # 4. Reply
        reply = GeneratedReply(
            lead_id=lead.id,
            value_first="Here are 3 community search queries you can use directly...",
            product_aware="ReachAI automates customer discovery across Reddit and GitHub...",
            selected_version="value_first",
            status="draft",
        )
        storage.save_reply(reply)
        saved_reply = storage.get_reply_by_lead_id(lead.id)
        assert saved_reply is not None
        assert saved_reply.selected_version == "value_first"

        # 5. Export
        json_export = storage.export_leads_json()
        assert "startup_founder_99" in json_export
        csv_export = storage.export_leads_csv()
        assert "Time Consumption" in csv_export

