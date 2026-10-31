# -*- coding: utf-8 -*-
"""CLI interface for AI Customer Discovery and Lead Generation."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from agent_reach.discovery.analytics import DiscoveryAnalytics
from agent_reach.discovery.models import PostingSettings
from agent_reach.discovery.orchestrator import DiscoveryOrchestrator
from agent_reach.discovery.storage import DiscoveryStorage


def cmd_dashboard(args: Sequence[str]) -> int:
    """Launch the Customer Discovery & Lead Intelligence Dashboard server."""
    parser = argparse.ArgumentParser(prog="agent-reach dashboard")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the dashboard server on (default: 8000)")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    ns = parser.parse_args(list(args))

    import uvicorn
    print(f"Starting Customer Discovery Dashboard at http://{ns.host}:{ns.port}")
    uvicorn.run("agent_reach.server.app:app", host=ns.host, port=ns.port, log_level="info")
    return 0


def cmd_discovery(args: Sequence[str]) -> int:
    """CLI discovery management: profile, plan, search, leads, reply, export."""
    if not args:
        print("Usage: agent-reach discovery <profile|plan|search|leads|reply|export|analytics> [args]")
        return 1

    sub, rest = args[0], args[1:]
    storage = DiscoveryStorage()
    orchestrator = DiscoveryOrchestrator(storage)

    if sub == "profile":
        parser = argparse.ArgumentParser(prog="agent-reach discovery profile")
        parser.add_argument("--url", help="Website URL to extract business profile from")
        parser.add_argument("--name", help="Business or product name")
        parser.add_argument("--desc", help="Manual product description")
        ns = parser.parse_args(list(rest))

        if ns.url:
            profile = orchestrator.business_engine.analyze_website(ns.url)
        elif ns.desc:
            profile = orchestrator.business_engine.analyze_manual_description(ns.desc, name=ns.name)
        else:
            profile = storage.get_latest_business_profile()
            if not profile:
                print(json.dumps({"error": "No business profile found. Provide --url or --desc"}))
                return 1

        storage.save_business_profile(profile)
        print(json.dumps(profile.model_dump(), indent=2))
        return 0

    elif sub == "plan":
        from agent_reach.discovery.search_planner import SearchPlanner
        profile = storage.get_latest_business_profile()
        if not profile:
            print(json.dumps({"error": "No business profile found. Run `agent-reach discovery profile` first."}))
            return 1
        planner = SearchPlanner(orchestrator.llm)
        queries = planner.plan_queries(profile)
        print(json.dumps([q.model_dump() for q in queries], indent=2))
        return 0

    elif sub == "search":
        parser = argparse.ArgumentParser(prog="agent-reach discovery search")
        parser.add_argument("--max", type=int, default=10, help="Max leads to qualify")
        parser.add_argument("--name", default="CLI Campaign", help="Campaign name")
        parser.add_argument(
            "--platforms", default="reddit,hackernews,web",
            help="Comma list: reddit, hackernews, web, quora, twitter, github",
        )
        ns = parser.parse_args(list(rest))

        try:
            campaign = orchestrator.run_campaign_sync(
                campaign_name=ns.name,
                platforms=[p.strip() for p in ns.platforms.split(",") if p.strip()],
                max_leads=ns.max,
                progress_callback=lambda msg, pct: sys.stderr.write(f"[{pct}%] {msg}\n"),
            )
            print(json.dumps(campaign.model_dump(), indent=2))
            return 0
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            return 1

    elif sub == "leads":
        parser = argparse.ArgumentParser(prog="agent-reach discovery leads")
        parser.add_argument("--min-score", type=int, default=50, help="Minimum score threshold (0-100)")
        parser.add_argument("--platform", help="Filter by platform (reddit, hackernews, web, github, twitter, quora)")
        ns = parser.parse_args(list(rest))

        leads = storage.list_leads(min_score=ns.min_score, platform=ns.platform)
        print(json.dumps([l.model_dump() for l in leads], indent=2))
        return 0

    elif sub == "reply":
        parser = argparse.ArgumentParser(prog="agent-reach discovery reply")
        parser.add_argument("lead_id", help="Lead ID to generate or fetch reply for")
        ns = parser.parse_args(list(rest))

        reply = storage.get_reply_by_lead_id(ns.lead_id)
        if not reply:
            lead = storage.get_lead(ns.lead_id)
            if not lead:
                print(json.dumps({"error": f"Lead {ns.lead_id} not found."}))
                return 1
            profile = storage.get_latest_business_profile()
            reply = orchestrator.reply_generator.generate_replies(lead, profile)
            storage.save_reply(reply)

        print(json.dumps(reply.model_dump(), indent=2))
        return 0

    elif sub == "export":
        parser = argparse.ArgumentParser(prog="agent-reach discovery export")
        parser.add_argument("--format", choices=("csv", "json"), default="json")
        parser.add_argument("--min-score", type=int, default=0)
        ns = parser.parse_args(list(rest))

        if ns.format == "csv":
            print(storage.export_leads_csv(min_score=ns.min_score))
        else:
            print(storage.export_leads_json(min_score=ns.min_score))
        return 0

    elif sub == "analytics":
        analytics = DiscoveryAnalytics(storage)
        print(json.dumps(analytics.get_insights(), indent=2))
        return 0

    else:
        print(f"Unknown discovery command: {sub}")
        return 1

