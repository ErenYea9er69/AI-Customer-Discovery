# -*- coding: utf-8 -*-
import tempfile
from pathlib import Path

from agent_reach.discovery.models import (
    BusinessProfile,
    GeneratedReply,
    LeadQualification,
    PostingSettings,
    ScoreBreakdown,
)
from agent_reach.discovery.publisher import CommunityPublisher
from agent_reach.discovery.reply_generator import ReplyGenerator
from agent_reach.discovery.storage import DiscoveryStorage


def test_reply_generation_and_publishing_controls():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = DiscoveryStorage(Path(tmpdir) / "test.db")
        generator = ReplyGenerator()
        publisher = CommunityPublisher(storage=storage)

        profile = BusinessProfile(
            name="SuperTask",
            industry="Developer Tools",
            niche="GitHub Issue Triage",
            main_product_or_service="AI automated issue triage",
            features=["Duplicate detection", "Backlog grooming"],
        )

        breakdown = ScoreBreakdown(
            icp_match=25, problem_fit=28, buying_intent=18, urgency=12, recency=9, total=92
        )
        lead = LeadQualification(
            discovered_item_id="item_01",
            title="Need automated duplicate triage",
            url="https://reddit.com/r/startups/comments/123",
            platform="reddit",
            community="r/startups",
            author="founder_bob",
            published_at="2026-10-29",
            excerpt="Our backlog has 100 duplicates...",
            customer_problem="Duplicate issue triage takes hours",
            pain_point_category="Developer Productivity",
            profile_match="Founder / Lead dev",
            purchase_intent="High",
            urgency="High",
            product_fit_explanation="SuperTask eliminates duplicate issues.",
            evidence="Author stated: backlog has 100 duplicates",
            score=92,
            score_breakdown=breakdown,
            classification="high_potential",
        )

        # 1. Generate replies
        reply = generator.generate_replies(lead, profile)
        assert reply.value_first != ""
        assert reply.product_aware != ""
        assert reply.status == "draft"
        assert "SuperTask" in reply.affiliation_disclosure

        # 2. Test publishing guardrails in Manual mode when not yet approved
        settings = PostingSettings(
            mode="manual",
            daily_limit=5,
            allowed_communities=["r/startups", "r/programming"],
            emergency_stop=False,
        )
        can_pub, reason = publisher.can_publish(reply, lead, settings)
        assert can_pub is False
        assert "requires explicit reply approval" in reason

        # 3. Test Emergency Stop
        settings.emergency_stop = True
        can_pub, reason = publisher.can_publish(reply, lead, settings)
        assert can_pub is False
        assert "Emergency stop" in reason
        settings.emergency_stop = False

        # 4. Approve reply and test Allowed Community Whitelist
        reply = generator.approve_reply(reply, edited_text="Custom approved reply text")
        assert reply.status == "approved"
        assert reply.edited_reply == "Custom approved reply text"

        settings.allowed_communities = ["r/othercommunity"]
        can_pub, reason = publisher.can_publish(reply, lead, settings)
        assert can_pub is False
        assert "whitelist" in reason
        settings.allowed_communities = ["r/startups"]

        # 5. Verify permitted copy fallback
        res = publisher.publish_or_copy(reply, lead, settings)
        assert res["success"] is True
        assert res["action"] == "copy_and_open"
        assert res["text"] == "Custom approved reply text"
        assert reply.status == "published"
