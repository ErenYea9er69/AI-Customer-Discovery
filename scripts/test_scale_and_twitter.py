# -*- coding: utf-8 -*-
"""Scale Lead Discovery & Verified Twitter/X Scraping for Taskly."""

import datetime
import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_reach.discovery.business_engine import BusinessEngine
from agent_reach.discovery.harvester import CommunityHarvester
from agent_reach.discovery.models import SearchQuery
from agent_reach.discovery.search_planner import SearchPlanner
from agent_reach.discovery.storage import DiscoveryStorage

def run_test():
    curr_year = datetime.date.today().year
    print(f"[*] Starting Scaled Discovery for Taskly (Rolling 2-Year Window: [{curr_year-1}, {curr_year}])\n")

    db_file = Path("discovery_taskly_scaled.db").resolve()
    if db_file.exists():
        try:
            db_file.unlink()
        except Exception:
            pass

    storage = DiscoveryStorage(db_file)
    engine = BusinessEngine()
    harvester = CommunityHarvester(storage=storage)

    # 1. Profile Taskly
    profile = engine.analyze_manual_description(
        "An AI-powered productivity app that helps freelancers organize tasks, manage deadlines, and automate repetitive work from one simple dashboard.",
        name="Taskly"
    )

    # 2. STEP 1: Dynamically Discover Niche Subreddits (NOT from static placeholders)
    print("[1/3] Dynamically discovering niche subreddits for Taskly...")
    discovered_subs = harvester.discover_subreddits(
        "freelance organize tasks deadlines OR productivity tools solopreneur",
        limit=10
    )
    print(f" -> Found {len(discovered_subs)} active niche communities: {discovered_subs}\n")

    # 3. STEP 2: Multi-Platform Query Generation across Discovered Subreddits + Quora + Twitter + Web
    queries = []

    # Reddit: Run targeted searches across the discovered subreddits
    for sub in discovered_subs[:6]:
        queries.append(SearchQuery(
            query="cannot focus OR missed deadlines",
            platform="reddit",
            target_community=sub,
            intent_type="frustration",
            rationale=f"Fresh deadline & focus pain points in {sub}"
        ))
        queries.append(SearchQuery(
            query="organize multiple clients tasks and deadlines",
            platform="reddit",
            target_community=sub,
            intent_type="tool_request",
            rationale=f"Workflow and task organization requests in {sub}"
        ))

    # Quora
    queries.append(SearchQuery(
        query="freelancer managing multiple clients projects without feeling overwhelmed AI tools",
        platform="quora",
        intent_type="tool_request",
        rationale="Quora questions from freelancers seeking multi-client management systems"
    ))
    queries.append(SearchQuery(
        query="how to track and manage your tasks as a freelancer",
        platform="quora",
        intent_type="tool_request",
        rationale="Quora task management discussions"
    ))

    # Twitter / X (strictly verified direct x.com status URLs with @handles & authentic posts)
    queries.append(SearchQuery(
        query="freelance missed deadline client",
        platform="twitter",
        intent_type="frustration",
        rationale="Verified Twitter/X tweets regarding missed client deadlines"
    ))
    queries.append(SearchQuery(
        query="freelance task organization productivity",
        platform="twitter",
        intent_type="recommendation",
        rationale="Verified Twitter/X tweets discussing freelance productivity systems"
    ))
    queries.append(SearchQuery(
        query="freelance client deadlines overwhelm burnout",
        platform="twitter",
        intent_type="frustration",
        rationale="Twitter/X complaints about client overload and deadline burnout"
    ))
    queries.append(SearchQuery(
        query="freelance tasks focus productivity apps",
        platform="twitter",
        intent_type="tool_request",
        rationale="Twitter/X posts about focus and task management apps"
    ))

    # Web / Forums
    queries.append(SearchQuery(
        query="freelance project management weekly planning system dashboard",
        platform="web",
        intent_type="recommendation",
        rationale="Freelance community planning dashboards"
    ))

    print(f"[2/3] Executing scraping across {len(queries)} dynamic query angles...")
    all_leads = []

    for q in queries:
        try:
            time.sleep(0.5)
            items = harvester.execute_query(q, limit=3)
            for it in items:
                context = it.raw_data.get("context_analysis") or harvester.analyze_lead_context(it.content, it.published_at)

                lead_record = {
                    "id": it.id,
                    "platform": it.platform,
                    "community": it.community,
                    "author": it.author,
                    "published_at": it.published_at,
                    "recency_tier": context["recency_tier"],
                    "title": it.title,
                    "url": it.url,
                    "prospect_intent_type": q.intent_type,
                    "query_matched": q.query,
                    "commenters_involved": context["commenters_found"],
                    "extracted_complaints_and_struggles": context["extracted_complaints"],
                    "full_content_and_comments": it.content,
                }
                all_leads.append(lead_record)
        except Exception as e:
            print(f"    Error scraping {q.platform}: {e}")

    # 4. Save results to JSON
    output_path = Path("taskly_scraped_leads_scaled.json").resolve()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "product": "Taskly",
            "description": "An AI-powered productivity app that helps freelancers organize tasks, manage deadlines, and automate repetitive work from one simple dashboard.",
            "test_type": "Scaled Discovery with Dynamic Subreddit Auto-Discovery & Verified Twitter/X",
            "active_window": f"{curr_year-1} - {curr_year} (Automated)",
            "dynamically_discovered_subreddits": discovered_subs,
            "total_leads_found": len(all_leads),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "leads": all_leads
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[3/3] Done! Discovered {len(all_leads)} leads across {len(discovered_subs)} dynamic subreddits, Quora, Twitter/X, and Web.")
    print(f"Saved to: {output_path}")
    return all_leads, discovered_subs

if __name__ == "__main__":
    run_test()

