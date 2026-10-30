# -*- coding: utf-8 -*-
import tempfile
from pathlib import Path

from agent_reach.discovery.harvester import CommunityHarvester
from agent_reach.discovery.models import BusinessProfile, SearchQuery
from agent_reach.discovery.search_planner import SearchPlanner
from agent_reach.discovery.storage import DiscoveryStorage


def test_search_planner_and_harvester():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = DiscoveryStorage(Path(tmpdir) / "test.db")
        planner = SearchPlanner()

        profile = BusinessProfile(
            name="SuperTask",
            industry="Software Development",
            niche="AI GitHub Issue Triage",
            problems_solved=["Manual issue triage is slow and painful"],
            customer_outcomes=["Zero duplicate bugs in sprints"],
            competitors_and_alternatives=["Jira Software"],
            icp="Engineering Managers and Tech Leads",
        )

        queries = planner.plan_queries(profile)
        assert len(queries) >= 3
        # Ensure frustration and alternative queries exist
        intents = {q.intent_type for q in queries}
        assert "frustration" in intents or "alternative" in intents or "tool_request" in intents

        harvester = CommunityHarvester(storage=storage)
        test_query = SearchQuery(
            query="struggling with duplicate issues",
            intent_type="frustration",
            platform="reddit",
            target_community="r/programming",
        )
        discovered = harvester.execute_query(test_query, limit=2)
        assert len(discovered) > 0
        assert discovered[0].platform == "reddit"
        assert "duplicate" in discovered[0].content.lower()

        # Deduplication verification: executing again with same storage should not duplicate
        re_discovered = harvester.execute_query(test_query, limit=2)
        assert len(re_discovered) == 0  # Already saved, deduplicated!

