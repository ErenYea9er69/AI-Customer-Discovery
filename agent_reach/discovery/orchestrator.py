# -*- coding: utf-8 -*-
"""Discovery orchestrator: profile, plan, harvest, qualify, draft."""

from __future__ import annotations

import logging
import threading
import time
from collections import Counter
from typing import Callable, Dict, List, Optional
from urllib.parse import urlsplit

from agent_reach.discovery.analytics import DiscoveryAnalytics
from agent_reach.discovery.business_engine import BusinessEngine
from agent_reach.discovery.harvester import CommunityHarvester
from agent_reach.discovery.llm_client import LLMClient
from agent_reach.discovery.models import BusinessProfile, Campaign
from agent_reach.discovery.publisher import CommunityPublisher
from agent_reach.discovery.qualifier import LeadQualifier
from agent_reach.discovery.reply_generator import ReplyGenerator
from agent_reach.discovery.search_planner import DEFAULT_PLATFORMS, VALID_PLATFORMS, SearchPlanner
from agent_reach.discovery.storage import DiscoveryStorage

log = logging.getLogger("agent_reach.discovery")

PER_QUERY_LIMIT = 5
REPLY_CLASSES = ("high_potential", "relevant_potential")


def validate_platforms(platforms: Optional[List[str]]) -> List[str]:
    """Lowercase, drop unknown ids, keep order. Falls back to the defaults."""
    clean = [p.lower() for p in (platforms or []) if isinstance(p, str) and p.lower() in VALID_PLATFORMS]
    return list(dict.fromkeys(clean)) or list(DEFAULT_PLATFORMS)


class DiscoveryOrchestrator:
    """Coordinates end-to-end discovery campaigns."""

    def __init__(self, storage: Optional[DiscoveryStorage] = None):
        self.storage = storage or DiscoveryStorage()
        self.active_tasks: Dict[str, threading.Event] = {}
        self._launch_lock = threading.Lock()
        self.harvester = CommunityHarvester(self.storage)
        self.publisher = CommunityPublisher(self.storage)
        self.analytics = DiscoveryAnalytics(self.storage)
        self.reload_llm()

    def reload_llm(self) -> None:
        """Rebuild every LLM-backed component. Call after settings change."""
        cfg = self.storage.get_setting("llm_settings", {}) or {}
        self.llm = LLMClient(
            provider=cfg.get("provider") or None,
            model=cfg.get("model") or None,
            api_key=cfg.get("api_key") or None,
        )
        self.business_engine = BusinessEngine(self.llm)
        self.qualifier = LeadQualifier(self.llm)
        self.reply_generator = ReplyGenerator(self.llm)

    # ── Campaign ──

    @staticmethod
    def _exclusions(profile: BusinessProfile) -> List[str]:
        """Hosts to skip: the user's own site. Competitor sites are guessed from their names."""
        hosts = []
        if profile.url:
            host = (urlsplit(profile.url).hostname or "").lower()
            hosts.append(host[4:] if host.startswith("www.") else host)
        return [h for h in hosts if h]

    def run_campaign_sync(
        self,
        campaign_name: str = "Lead Discovery",
        platforms: Optional[List[str]] = None,
        max_leads: int = 15,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        campaign_id: Optional[str] = None,
    ) -> Campaign:
        profile = self.storage.get_latest_business_profile()
        if not profile:
            raise ValueError("No business profile found. Analyze a website or product description first.")
        chosen = validate_platforms(platforms)

        campaign = self.storage.get_campaign(campaign_id) if campaign_id else None
        if campaign is None:
            campaign = Campaign(
                name=campaign_name, business_profile_id=profile.id, status="running",
                selected_platforms=chosen, current_step="Planning queries...", progress_percentage=10,
            )
            self.storage.save_campaign(campaign)
        cancel_event = self.active_tasks.get(campaign.id)

        def cancelled() -> bool:
            return bool(cancel_event and cancel_event.is_set())

        def note(step: str, pct: int) -> None:
            campaign.current_step, campaign.progress_percentage = step, pct
            self.storage.save_campaign(campaign)
            if progress_callback:
                progress_callback(step, pct)

        note("Planning search queries", 15)
        queries = SearchPlanner(self.llm).plan_queries(profile, chosen)
        campaign.queries = queries
        note(f"Planned {len(queries)} queries. Searching...", 30)

        self.harvester.diagnostics = Counter()
        self.harvester.set_exclusions(self._exclusions(profile))
        self.qualifier.reset_budget()

        found = qualified = high = 0
        rejections: Counter = Counter()
        step = 55 / max(1, len(queries))
        progress = 30.0

        for q in queries:
            if cancelled():
                campaign.status = "cancelled"
                note("Cancelled by the operator.", int(progress))
                return campaign
            items = self.harvester.execute_query(q, limit=PER_QUERY_LIMIT)
            found += len(items)

            for item in items:
                if cancelled():
                    break
                lead = self.qualifier.qualify(item, profile)
                if lead is None:
                    rejections[f"qualifier:{self.qualifier.last_rejection}"] += 1
                    continue
                self.storage.save_lead(lead, campaign_id=campaign.id)
                qualified += 1
                high += lead.classification == "high_potential"
                if lead.classification in REPLY_CLASSES:
                    try:
                        self.storage.save_reply(self.reply_generator.generate_replies(lead, profile))
                    except Exception as exc:  # a failed draft must not lose the lead
                        log.warning("reply draft failed for %s: %s", lead.id, str(exc)[:200])
                        rejections["reply_draft_failed"] += 1
                if qualified >= max_leads:
                    break

            progress += step
            campaign.progress_percentage = min(90, int(progress))
            campaign.total_found, campaign.total_qualified = found, qualified
            campaign.high_potential_count = high
            campaign.current_step = f"Searched {q.platform}: {q.query[:40]}"
            campaign.diagnostics = dict(self.harvester.diagnostics + rejections)
            self.storage.save_campaign(campaign)
            if qualified >= max_leads:
                break

        campaign.status = "completed"
        campaign.completed_at = time.time()
        campaign.diagnostics = dict(self.harvester.diagnostics + rejections)
        note(f"Finished. {found} open threads checked, {qualified} qualified leads.", 100)
        return campaign

    def cancel_campaign(self, campaign_id: str) -> bool:
        event = self.active_tasks.get(campaign_id)
        if not event:
            return False
        event.set()
        return True

    def run_campaign_background(
        self,
        campaign_name: str = "Lead Discovery",
        platforms: Optional[List[str]] = None,
        max_leads: int = 15,
    ) -> str:
        profile = self.storage.get_latest_business_profile()
        if not profile:
            raise ValueError("No business profile found. Analyze a website or product description first.")
        chosen = validate_platforms(platforms)
        with self._launch_lock:
            if self.active_tasks:
                raise RuntimeError("A campaign is already running. Cancel it or wait for it to finish.")
            campaign = Campaign(
                name=campaign_name, business_profile_id=profile.id, status="running",
                selected_platforms=chosen, current_step="Starting...", progress_percentage=5,
            )
            self.storage.save_campaign(campaign)
            self.active_tasks[campaign.id] = threading.Event()

        def _worker() -> None:
            try:
                self.run_campaign_sync(campaign_name, chosen, max_leads, campaign_id=campaign.id)
            except Exception as exc:
                log.exception("campaign %s failed", campaign.id)
                latest = self.storage.get_campaign(campaign.id) or campaign
                latest.status = "failed"
                latest.current_step = f"Failed: {type(exc).__name__}: {str(exc)[:200]}"
                self.storage.save_campaign(latest)
            finally:
                self.active_tasks.pop(campaign.id, None)

        threading.Thread(target=_worker, daemon=True).start()
        return campaign.id
