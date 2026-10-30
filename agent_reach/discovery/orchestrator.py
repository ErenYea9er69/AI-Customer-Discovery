# -*- coding: utf-8 -*-
"""Discovery Orchestrator coordinating business profiling, queries, harvesting, and qualification."""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Dict, List, Optional

from agent_reach.discovery.analytics import DiscoveryAnalytics
from agent_reach.discovery.business_engine import BusinessEngine
from agent_reach.discovery.harvester import CommunityHarvester
from agent_reach.discovery.llm_client import LLMClient
from agent_reach.discovery.models import (
    BusinessProfile,
    Campaign,
    GeneratedReply,
    LeadQualification,
    PostingSettings,
    SearchQuery,
)
from agent_reach.discovery.publisher import CommunityPublisher
from agent_reach.discovery.qualifier import LeadQualifier
from agent_reach.discovery.reply_generator import ReplyGenerator
from agent_reach.discovery.storage import DiscoveryStorage


class DiscoveryOrchestrator:
    """Coordinates end-to-end discovery campaigns."""

    def __init__(self, storage: Optional[DiscoveryStorage] = None):
        self.storage = storage or DiscoveryStorage()
        self.llm = LLMClient()
        self.business_engine = BusinessEngine(self.llm)
        self.search_planner = None  # Lazy init
        self.harvester = CommunityHarvester(self.storage)
        self.qualifier = LeadQualifier(self.llm)
        self.reply_generator = ReplyGenerator(self.llm)
        self.publisher = CommunityPublisher(self.storage)
        self.analytics = DiscoveryAnalytics(self.storage)

    def run_campaign_sync(
        self,
        campaign_name: str = "Lead Discovery",
        platforms: Optional[List[str]] = None,
        max_leads: int = 15,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> Campaign:
        """Execute a discovery campaign synchronously."""
        from agent_reach.discovery.search_planner import SearchPlanner

        profile = self.storage.get_latest_business_profile()
        if not profile:
            raise ValueError("No business profile found. Please analyze a website or product description first.")

        campaign = Campaign(
            name=campaign_name,
            business_profile_id=profile.id,
            status="running",
            selected_platforms=platforms or ["reddit", "web"],
            current_step="Planning customer discovery queries...",
            progress_percentage=10,
        )
        self.storage.save_campaign(campaign)

        if progress_callback:
            progress_callback("Planning search queries", 15)

        # 1. Plan queries
        planner = SearchPlanner(self.llm)
        queries = planner.plan_queries(profile)
        # Filter queries to selected platforms
        if platforms:
            queries = [q for q in queries if q.platform in platforms]
        campaign.queries = queries
        campaign.current_step = f"Generated {len(queries)} targeted queries. Searching communities..."
        campaign.progress_percentage = 30
        self.storage.save_campaign(campaign)

        total_discovered = 0
        total_qualified = 0
        high_potential_count = 0

        # 2. Harvest & Qualify
        step_increment = 50 / max(1, len(queries))
        current_prog = 30.0

        for q in queries:
            if progress_callback:
                progress_callback(f"Searching {q.platform} for: {q.query[:30]}...", int(current_prog))

            items = self.harvester.execute_query(q, limit=5)
            total_discovered += len(items)

            for item in items:
                lead = self.qualifier.qualify(item, profile)
                if lead:
                    self.storage.save_lead(lead, campaign_id=campaign.id)
                    total_qualified += 1
                    if lead.classification == "high_potential":
                        high_potential_count += 1

                    # Generate reply draft for qualified leads
                    reply = self.reply_generator.generate_replies(lead, profile)
                    self.storage.save_reply(reply)

                    if total_qualified >= max_leads:
                        break

            current_prog += step_increment
            campaign.progress_percentage = min(90, int(current_prog))
            campaign.total_found = total_discovered
            campaign.total_qualified = total_qualified
            campaign.high_potential_count = high_potential_count
            self.storage.save_campaign(campaign)

            if total_qualified >= max_leads:
                break

        campaign.status = "completed"
        campaign.progress_percentage = 100
        campaign.current_step = f"Finished. Discovered {total_discovered} conversations, qualified {total_qualified} leads."
        campaign.completed_at = time.time()
        self.storage.save_campaign(campaign)

        if progress_callback:
            progress_callback("Campaign completed", 100)

        return campaign

    def run_campaign_background(
        self,
        campaign_name: str = "Lead Discovery",
        platforms: Optional[List[str]] = None,
        max_leads: int = 15,
    ) -> str:
        """Launch campaign in a background worker thread."""
        profile = self.storage.get_latest_business_profile()
        if not profile:
            raise ValueError("No business profile found. Please analyze a website or product description first.")

        campaign = Campaign(
            name=campaign_name,
            business_profile_id=profile.id,
            status="running",
            selected_platforms=platforms or ["reddit", "web"],
            current_step="Starting background campaign...",
            progress_percentage=5,
        )
        self.storage.save_campaign(campaign)

        def _worker():
            try:
                self.run_campaign_sync(
                    campaign_name=campaign_name,
                    platforms=platforms,
                    max_leads=max_leads,
                )
            except Exception as e:
                campaign.status = "failed"
                campaign.current_step = f"Failed: {str(e)}"
                self.storage.save_campaign(campaign)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return campaign.id

