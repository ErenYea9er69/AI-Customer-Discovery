# -*- coding: utf-8 -*-
"""Intelligent customer discovery search query planner."""

from __future__ import annotations

import re
from typing import List, Optional

from agent_reach.discovery.llm_client import LLMClient
from agent_reach.discovery.models import BusinessProfile, SearchQuery

EXPRESSION_TEMPLATES = [
    ("struggle", 'I\'m struggling with "{topic}"'),
    ("alternative", 'looking for an alternative to "{competitor}"'),
    ("frustration", 'I hate having to "{frustration}"'),
    ("tool_request", 'is there a tool that "{outcome}"'),
    ("recommendation", 'can anyone recommend "{topic}"'),
    ("cost", '"{competitor}" is too expensive'),
    ("indirect", 'how do you solve "{problem}"'),
]

SUBREDDIT_MAP = {
    "developer": ["r/programming", "r/devops", "r/webdev", "r/softwaredevelopment", "r/SideProject", "r/coding", "r/learnprogramming", "r/golang", "r/Python", "r/javascript"],
    "b2b": ["r/SaaS", "r/startups", "r/Entrepreneur", "r/smallbusiness", "r/business", "r/GrowthHacking", "r/sales"],
    "marketing": ["r/marketing", "r/growthhacking", "r/sales", "r/digitalmarketing", "r/content_marketing", "r/SEO", "r/socialmediamarketing"],
    "design": ["r/UI_Design", "r/web_design", "r/userexperience", "r/graphic_design", "r/FigmaDesign", "r/ProductManagement"],
    "productivity": ["r/productivity", "r/notion", "r/automation", "r/GetDisciplined", "r/time_management", "r/selfimprovement", "r/zenhabits"],
    "freelance": ["r/freelance", "r/Freelancers", "r/productivity", "r/digitalnomad", "r/Upwork", "r/WorkOnline", "r/fiverr", "r/consulting"],
    "ecommerce": ["r/ecommerce", "r/shopify", "r/dropship", "r/FulfillmentByAmazon", "r/smallbusiness"],
    "finance": ["r/personalfinance", "r/FinancialPlanning", "r/smallbusiness", "r/Accounting", "r/Bookkeeping"],
    "ai_tools": ["r/ArtificialInteligence", "r/ChatGPT", "r/OpenAI", "r/Productivity", "r/SideProject", "r/LocalLLaMA", "r/ClaudeAI"],
    "creators": ["r/contentcreation", "r/YouTube", "r/podcasting", "r/videography", "r/Blogging", "r/freelance"],
}


class SearchPlanner:
    """Plans multi-angle customer discovery queries from business profiles."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def plan_queries(self, profile: BusinessProfile) -> List[SearchQuery]:
        """Generate targeted search queries across chosen platforms."""
        queries: List[SearchQuery] = []

        # Determine target platforms based on profile
        platforms = ["reddit", "quora", "twitter", "web"]
        is_dev_tool = any(
            dev_term in f"{profile.industry} {profile.niche} {profile.icp}".lower()
            for dev_term in ["developer", "github", "engineering", "code", "software", "api", "devops"]
        )
        if is_dev_tool:
            platforms.append("github")

        # Select relevant subreddits
        target_subs = self._select_target_subreddits(profile, is_dev_tool)

        # 1. Generate heuristic rule-based high-intent queries
        # Pain expressions across communities
        for prob in profile.problems_solved[:3]:
            short_prob = self._shorten_phrase(prob)
            queries.append(
                SearchQuery(
                    query=f'struggling with {short_prob}',
                    intent_type="frustration",
                    platform="reddit",
                    target_community=target_subs[0] if target_subs else "r/startups",
                    rationale=f"Direct customer pain signal matching problem: {prob}",
                )
            )
            queries.append(
                SearchQuery(
                    query=f'how do you solve {short_prob}',
                    intent_type="indirect",
                    platform="web",
                    rationale=f"Indirect problem search where user seeks solutions: {prob}",
                )
            )
            queries.append(
                SearchQuery(
                    query=f'{short_prob}',
                    intent_type="tool_request",
                    platform="quora",
                    rationale=f"Questions and solutions sought on Quora for: {prob}",
                )
            )
            queries.append(
                SearchQuery(
                    query=f'{short_prob} cannot focus OR miss deadlines',
                    intent_type="frustration",
                    platform="twitter",
                    rationale=f"Real-time customer vents and struggles on X/Twitter: {prob}",
                )
            )

        # Competitor alternatives
        for comp in profile.competitors_and_alternatives[:2]:
            queries.append(
                SearchQuery(
                    query=f'looking for an alternative to {comp}',
                    intent_type="alternative",
                    platform="reddit",
                    target_community=target_subs[1] if len(target_subs) > 1 else target_subs[0],
                    rationale=f"High buying intent from users dissatisfied with competitor: {comp}",
                )
            )
            queries.append(
                SearchQuery(
                    query=f'alternative to {comp}',
                    intent_type="alternative",
                    platform="quora",
                    rationale=f"Quora alternative recommendation requests: {comp}",
                )
            )

        # Tool requests
        for outcome in profile.customer_outcomes[:2]:
            short_outcome = self._shorten_phrase(outcome)
            queries.append(
                SearchQuery(
                    query=f'is there a tool that {short_outcome}',
                    intent_type="tool_request",
                    platform="reddit",
                    target_community=target_subs[0],
                    rationale=f"Active solution search seeking outcome: {outcome}",
                )
            )

        # GitHub issue search for dev tools
        if is_dev_tool and profile.problems_solved:
            queries.append(
                SearchQuery(
                    query=f'is:issue is:open "{self._shorten_phrase(profile.problems_solved[0])}"',
                    intent_type="tool_request",
                    platform="github",
                    rationale="GitHub issues detailing developer pain points",
                )
            )

        # 2. Enrich with LLM-generated nuance queries if available
        llm_queries = self._generate_llm_queries(profile, target_subs)
        queries.extend(llm_queries)

        # Deduplicate queries by query string
        seen = set()
        unique_queries = []
        for q in queries:
            normalized = q.query.lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                unique_queries.append(q)

        return unique_queries[:16]

    def _select_target_subreddits(self, profile: BusinessProfile, is_dev_tool: bool) -> List[str]:
        matched_subs: List[str] = []
        if is_dev_tool:
            matched_subs.extend(SUBREDDIT_MAP["developer"])

        text = f"{profile.industry} {profile.niche} {profile.icp} {' '.join(profile.problems_solved)}".lower()

        if any(w in text for w in ["ai", "llm", "gpt", "intelligent", "automate", "automation"]):
            matched_subs.extend(SUBREDDIT_MAP["ai_tools"])
        if any(w in text for w in ["freelance", "freelancer", "contractor", "solopreneur", "solo"]):
            matched_subs.extend(SUBREDDIT_MAP["freelance"])
        if any(w in text for w in ["productivity", "organize", "task", "deadline", "focus", "time"]):
            matched_subs.extend(SUBREDDIT_MAP["productivity"])
        if any(w in text for w in ["marketing", "growth", "lead", "sales", "outreach"]):
            matched_subs.extend(SUBREDDIT_MAP["marketing"])
        if any(w in text for w in ["design", "ui", "ux", "figma"]):
            matched_subs.extend(SUBREDDIT_MAP["design"])
        if any(w in text for w in ["shop", "ecommerce", "store", "product"]):
            matched_subs.extend(SUBREDDIT_MAP["ecommerce"])
        if any(w in text for w in ["creator", "video", "youtube", "podcast", "writer", "blog"]):
            matched_subs.extend(SUBREDDIT_MAP["creators"])
        if any(w in text for w in ["finance", "invoice", "accounting", "money", "billing"]):
            matched_subs.extend(SUBREDDIT_MAP["finance"])

        matched_subs.extend(SUBREDDIT_MAP["b2b"])

        # Deduplicate preserving order
        seen = set()
        unique = []
        for s in matched_subs:
            if s.lower() not in seen:
                seen.add(s.lower())
                unique.append(s)
        return unique

    def _shorten_phrase(self, text: str, max_words: int = 5) -> str:
        cleaned = re.sub(r"[^\w\s-]", "", text)
        words = cleaned.split()
        return " ".join(words[:max_words])

    def _generate_llm_queries(self, profile: BusinessProfile, subreddits: List[str]) -> List[SearchQuery]:
        prompt = f"""
Given this business:
Niche: {profile.niche}
ICP: {profile.icp}
Problems Solved: {profile.problems_solved}
Competitors: {profile.competitors_and_alternatives}
Subreddits: {subreddits}

Generate 4 high-converting search queries across Reddit and Web searching for people asking for solutions, complaining about existing tools, or expressing frustration.
Output JSON:
{{
  "queries": [
    {{
      "query": "exact search query text",
      "intent_type": "frustration|alternative|recommendation|tool_request",
      "platform": "reddit|web",
      "target_community": "r/...",
      "rationale": "why this targets buyers"
    }}
  ]
}}
"""
        resp = self.llm.complete_json(prompt)
        items = resp.get("queries", [])
        return [
            SearchQuery(
                query=item.get("query", ""),
                intent_type=item.get("intent_type", "frustration"),
                platform=item.get("platform", "reddit"),
                target_community=item.get("target_community"),
                rationale=item.get("rationale", ""),
            )
            for item in items
            if item.get("query")
        ]

