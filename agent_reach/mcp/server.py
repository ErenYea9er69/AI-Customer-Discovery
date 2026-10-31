# -*- coding: utf-8 -*-
"""FastMCP Model Context Protocol (MCP) server for Agent Reach.

Provides universal MCP tools for Antigravity, Claude Code, Cursor, and VS Code.
Enables host AI reasoning without external LLM API keys, automated task batching,
flexible Markdown and JSON exports, and on-demand dashboard controls.
"""

from __future__ import annotations

import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from agent_reach.discovery.harvester import CommunityHarvester
from agent_reach.discovery.models import (
    BusinessProfile,
    Campaign,
    DiscoveredItem,
    GeneratedReply,
    LeadQualification,
    ScoreBreakdown,
    SearchQuery,
)
from agent_reach.discovery.qualifier import LeadQualifier
from agent_reach.discovery.search_planner import DEFAULT_PLATFORMS, SearchPlanner
from agent_reach.discovery.storage import DiscoveryStorage
from agent_reach.mcp.helpers import (
    ensure_dashboard_running,
    export_results_files,
    get_or_init_mcp_settings,
    is_port_in_use,
    update_mcp_settings,
)

log = logging.getLogger("agent_reach.mcp")

# Shared storage instance provider
_storage_instance: Optional[DiscoveryStorage] = None


def get_storage() -> DiscoveryStorage:
    """Return the active DiscoveryStorage instance."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = DiscoveryStorage()
    return _storage_instance


# Initialize FastMCP Server
mcp = FastMCP(
    "AgentReach",
    instructions=(
        "Agent Reach Model Context Protocol server. Provides customer intelligence, "
        "community thread discovery (Reddit, Hacker News, GitHub, Web), lead qualification, "
        "personalized value-first reply drafting, and CRM dashboard control."
    ),
)


# ── Profile Management ──


@mcp.tool()
def reach_get_or_create_profile(
    name: Optional[str] = None,
    url: Optional[str] = None,
    description: Optional[str] = None,
    problems_solved: Optional[List[str]] = None,
    icp: Optional[str] = None,
    target_roles: Optional[List[str]] = None,
    competitors: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Get active business profile, or create/update one in SQLite.

    When called with no parameters, returns the latest business profile.
    When called with parameters, creates or updates the business profile.
    """
    storage = get_storage()
    if not name and not description and not url:
        prof = storage.get_latest_business_profile()
        if prof:
            return prof.model_dump()
        return {"id": None, "message": "No profile exists yet. Provide name and description to create one."}

    prof = storage.get_latest_business_profile() or BusinessProfile()
    if name:
        prof.name = name
    if url:
        prof.url = url
    if description:
        prof.description = description
        prof.main_product_or_service = description
    if problems_solved:
        prof.problems_solved = problems_solved
    if icp:
        prof.icp = icp
    if target_roles:
        prof.target_roles = target_roles
    if competitors:
        prof.competitors_and_alternatives = competitors

    prof.confirmed = True
    prof.updated_at = time.time()
    storage.save_business_profile(prof)
    return prof.model_dump()


# ── Query Planning ──


@mcp.tool()
def reach_plan_queries(
    profile_id: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    custom_pains: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Plan customer pain and intent search queries from profile or pain points.

    Returns structured queries ready for community harvesting.
    """
    storage = get_storage()
    profile = (
        storage.get_business_profile(profile_id)
        if profile_id
        else storage.get_latest_business_profile()
    )
    if not profile:
        profile = BusinessProfile(
            name="General Product",
            problems_solved=custom_pains or ["manual customer discovery"],
            icp="Founders and builders",
        )
    elif custom_pains:
        profile.problems_solved = list(set(profile.problems_solved + custom_pains))

    planner = SearchPlanner()
    target_platforms = platforms or DEFAULT_PLATFORMS
    queries = planner.plan_queries(profile, platforms=target_platforms)
    return [q.model_dump() for q in queries]


# ── Community Harvesting (No LLM API required) ──


@mcp.tool()
def reach_harvest_threads(
    queries: List[str],
    platforms: Optional[List[str]] = None,
    limit_per_query: int = 10,
) -> List[Dict[str, Any]]:
    """Scrape online communities (Reddit, Hacker News, GitHub, Web) for candidate threads.

    Runs direct HTTP scraping with zero external LLM API keys required.
    Returns verified DiscoveredItems ready for host AI analysis.
    """
    storage = get_storage()
    harvester = CommunityHarvester(storage)
    target_platforms = platforms or ["reddit", "hackernews", "web"]
    results: List[Dict[str, Any]] = []

    for q_text in queries:
        for plat in target_platforms:
            q_obj = SearchQuery(
                query=q_text,
                platform=plat,
                intent_type="frustration",
            )
            items = harvester.execute_query(q_obj, limit=limit_per_query)
            for item in items:
                storage.save_discovered_item(item)
                results.append(item.model_dump())

    return results


# ── Lead Qualification & Storage ──


@mcp.tool()
def reach_save_lead(
    title: str,
    url: str,
    platform: str,
    community: str,
    customer_problem: str,
    pain_point_category: str = "general",
    buying_intent: str = "Medium",
    urgency: str = "Medium",
    score: int = 70,
    classification: str = "relevant_potential",
    confidence: float = 0.85,
    score_breakdown: Optional[Dict[str, int]] = None,
    evidence: str = "",
    author: str = "",
    campaign_id: str = "",
) -> Dict[str, Any]:
    """Store a qualified lead into SQLite.

    Used by the host AI to persist qualified leads after analyzing community threads.
    """
    storage = get_storage()
    breakdown_data = score_breakdown or {
        "icp_match": 20,
        "problem_fit": 20,
        "buying_intent": 15,
        "urgency": 10,
        "recency": 5,
        "total": score,
        "explanation": "Qualified via host AI analysis",
    }
    if "total" not in breakdown_data:
        breakdown_data["total"] = score

    # Normalize intent & urgency to Allowed Literals ("High", "Medium", "Low", "None")
    def _norm(val: str, allowed: set, default: str) -> str:
        v = (val or "").strip().capitalize()
        return v if v in allowed else default

    intent_val = _norm(buying_intent, {"High", "Medium", "Low", "None"}, "Medium")
    urgency_val = _norm(urgency, {"High", "Medium", "Low"}, "Medium")

    lead = LeadQualification(
        id=str(uuid.uuid4()),
        discovered_item_id=str(uuid.uuid4()),
        title=title,
        url=url,
        platform=platform,
        community=community,
        author=author or "anonymous",
        published_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        excerpt=evidence[:300] if evidence else title,
        customer_problem=customer_problem,
        pain_point_category=pain_point_category,
        profile_match="Analyzed by Host AI",
        purchase_intent=intent_val,  # type: ignore[arg-type]
        urgency=urgency_val,  # type: ignore[arg-type]
        product_fit_explanation="Fits target customer profile",
        evidence=evidence,
        score=max(0, min(100, score)),
        score_breakdown=ScoreBreakdown(**breakdown_data),
        classification=classification,  # type: ignore[arg-type]
        confidence=confidence,
        judged_by="llm",
    )
    storage.save_lead(lead, campaign_id=campaign_id)
    return lead.model_dump()


@mcp.tool()
def reach_list_leads(
    min_score: int = 0,
    platform: Optional[str] = None,
    classification: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """List qualified leads from SQLite filtered by minimum score, platform, or classification."""
    storage = get_storage()
    leads = storage.list_leads(
        min_score=min_score,
        platform=platform,
        classification=classification,
        limit=limit,
    )
    return [l.model_dump() for l in leads]


# ── AI Reply Drafting ──


@mcp.tool()
def reach_save_reply(
    lead_id: str,
    value_first: str,
    product_aware: str,
    status: str = "draft",
) -> Dict[str, Any]:
    """Save value-first and product-aware AI reply drafts for a qualified lead into SQLite."""
    storage = get_storage()
    reply = GeneratedReply(
        id=str(uuid.uuid4()),
        lead_id=lead_id,
        value_first=value_first,
        product_aware=product_aware,
        status=status if status in ("draft", "approved") else "draft",  # type: ignore[arg-type]
    )
    storage.save_reply(reply)
    return reply.model_dump()


# ── Autonomous Batch Execution ──


@mcp.tool()
def reach_run_autonomous_batch(
    queries: Optional[List[str]] = None,
    platforms: Optional[List[str]] = None,
    min_score: int = 70,
    max_leads: int = 5,
    campaign_name: str = "MCP Autonomous Hunt",
) -> Dict[str, Any]:
    """Execute automated discovery: plan queries, harvest threads, qualify, and persist in one step.

    Runs the complete discovery loop using the built-in qualification engine.
    """
    storage = get_storage()
    profile = storage.get_latest_business_profile()
    if not profile:
        profile = BusinessProfile(
            name="Autonomous Agent",
            problems_solved=["customer lead generation"],
            icp="B2B buyers",
        )
        storage.save_business_profile(profile)

    campaign = Campaign(
        id=str(uuid.uuid4()),
        name=campaign_name,
        business_profile_id=profile.id,
        status="running",
    )
    storage.save_campaign(campaign)

    target_platforms = platforms or ["reddit", "hackernews", "web"]
    harvester = CommunityHarvester(storage)
    qualifier = LeadQualifier()

    search_queries: List[SearchQuery] = []
    if queries:
        for q in queries:
            search_queries.append(SearchQuery(query=q, platform=target_platforms[0], intent_type="frustration"))
    else:
        planner = SearchPlanner()
        search_queries = planner.plan_queries(profile, platforms=target_platforms)

    discovered_items: List[DiscoveredItem] = []
    for q_obj in search_queries[:6]:
        items = harvester.execute_query(q_obj, limit=10)
        for it in items:
            storage.save_discovered_item(it)
            discovered_items.append(it)

    qualified_leads: List[LeadQualification] = []
    for item in discovered_items:
        if len(qualified_leads) >= max_leads:
            break
        lead = qualifier.qualify(item, profile)
        if lead and lead.score >= min_score:
            storage.save_lead(lead, campaign_id=campaign.id)
            qualified_leads.append(lead)

    campaign.status = "completed"
    campaign.completed_at = time.time()
    storage.save_campaign(campaign)

    return {
        "campaign_id": campaign.id,
        "total_harvested": len(discovered_items),
        "total_qualified": len(qualified_leads),
        "leads": [l.model_dump() for l in qualified_leads],
    }


# ── Settings Management ──


@mcp.tool()
def reach_get_settings() -> Dict[str, Any]:
    """Get current MCP settings (discovery mode, default export format, min score threshold)."""
    return get_or_init_mcp_settings(get_storage())


@mcp.tool()
def reach_update_settings(
    discovery_mode: Optional[str] = None,
    default_output_format: Optional[str] = None,
    default_min_score: Optional[int] = None,
    default_export_path: Optional[str] = None,
    emergency_stop: Optional[bool] = None,
    auto_launch_dashboard: Optional[bool] = None,
) -> Dict[str, Any]:
    """Update MCP settings in SQLite.

    Arguments:
    - discovery_mode: 'host_driven' (host AI reasons) or 'built_in_auto' (built-in engine runs)
    - default_output_format: 'markdown', 'json', or 'both'
    - default_min_score: minimum score filter (0-100)
    - default_export_path: default directory for file exports
    - emergency_stop: halt all background actions immediately
    - auto_launch_dashboard: open dashboard browser window automatically
    """
    storage = get_storage()
    updates: Dict[str, Any] = {}
    if discovery_mode is not None:
        updates["discovery_mode"] = discovery_mode
    if default_output_format is not None:
        updates["default_output_format"] = default_output_format
    if default_min_score is not None:
        updates["default_min_score"] = default_min_score
    if default_export_path is not None:
        updates["default_export_path"] = default_export_path
    if emergency_stop is not None:
        updates["emergency_stop"] = emergency_stop
    if auto_launch_dashboard is not None:
        updates["auto_launch_dashboard"] = auto_launch_dashboard

    return update_mcp_settings(storage, updates)


# ── File Exports ──


@mcp.tool()
def reach_export_results(
    formats: str = "both",
    output_dir: Optional[str] = None,
    min_score: int = 0,
) -> Dict[str, str]:
    """Export qualified leads into Markdown report, JSON dataset, or both.

    Arguments:
    - formats: 'markdown', 'json', or 'both' (default: 'both')
    - output_dir: directory path to write the files (default: './discovery_exports')
    - min_score: filter leads by minimum score
    """
    storage = get_storage()
    settings = get_or_init_mcp_settings(storage)
    target_dir = Path(output_dir or settings.get("default_export_path", "./discovery_exports"))
    fmt = formats or settings.get("default_output_format", "both")
    return export_results_files(storage, target_dir, formats=fmt, min_score=min_score)


# ── Dashboard & Frontend Control ──


@mcp.tool()
def reach_control_dashboard(
    action: str = "status",
    port: int = 8000,
    host: str = "127.0.0.1",
    open_browser: bool = True,
) -> Dict[str, Any]:
    """Inspect or launch the FastAPI & React Customer Discovery Dashboard.

    Arguments:
    - action: 'status' (check if running) or 'launch' (start server & optionally open browser)
    - port: dashboard port (default 8000)
    - host: host interface (default 127.0.0.1)
    - open_browser: whether to open the UI in user's default browser
    """
    url = f"http://{host}:{port}"
    if action == "status":
        in_use = is_port_in_use(port, host)
        return {
            "is_running": in_use,
            "url": url if in_use else None,
            "port": port,
        }

    return ensure_dashboard_running(port=port, host=host, open_browser=open_browser)


def create_mcp_server() -> FastMCP:
    """Factory returning the configured FastMCP server instance."""
    return mcp


def main() -> None:
    """Run FastMCP over standard I/O (stdio)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
