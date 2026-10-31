# -*- coding: utf-8 -*-
"""Customer discovery query planner.

Turns a business profile into search queries in the words a customer would use.
Nothing here assumes a niche. Every query comes from the profile.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, Iterable, List, Optional, Sequence

from agent_reach.discovery.llm_client import LLMClient, LLMProviderError
from agent_reach.discovery.models import BusinessProfile, SearchQuery

log = logging.getLogger("agent_reach.discovery")

DEFAULT_PLATFORMS = ["reddit", "hackernews", "web"]
VALID_PLATFORMS = {"reddit", "hackernews", "web", "quora", "twitter", "github"}
MAX_QUERIES = 24
MAX_PER_PLATFORM = 8

_STOPWORDS = frozenset(
    "a an the and or but of to in on for with at by from as is are was were be been being it its this "
    "these those i we you they them our your their my me us not no so if then than too very can could "
    "will would should may might do does did have has had how what when where why which who whom into "
    "out up down over under more most some any each every just also only own same such other about "
    "using use used get gets got make makes made need needs want wants help helps helping across".split()
)

# Subreddits grouped by who asks questions there. Rules differ per sub and change
# over time, so treat these as search scopes and not as posting permission.
SUBREDDIT_MAP: Dict[str, List[str]] = {
    "developer": ["r/devops", "r/webdev", "r/softwaredevelopment", "r/ExperiencedDevs"],
    "b2b": ["r/SaaS", "r/startups", "r/Entrepreneur", "r/smallbusiness"],
    "marketing": ["r/marketing", "r/digital_marketing", "r/sales", "r/SEO", "r/content_marketing"],
    "design": ["r/web_design", "r/userexperience", "r/UI_Design", "r/ProductManagement"],
    "productivity": ["r/productivity", "r/notion", "r/automation", "r/GetDisciplined"],
    "freelance": ["r/freelance", "r/Freelancers", "r/consulting", "r/digitalnomad"],
    "ecommerce": ["r/ecommerce", "r/shopify", "r/dropship", "r/FulfillmentByAmazon"],
    "finance": ["r/Accounting", "r/Bookkeeping", "r/smallbusiness", "r/FinancialPlanning"],
    "ai_tools": ["r/ArtificialInteligence", "r/ChatGPT", "r/LocalLLaMA", "r/ClaudeAI"],
    "creators": ["r/NewTubers", "r/podcasting", "r/videography", "r/Blogging"],
}

# Scopes that rarely hold a buyer asking for help.
LOW_SIGNAL_SUBS = frozenset(
    s.lower()
    for s in (
        "r/all", "r/popular", "r/AskReddit", "r/IAmA", "r/reddit", "r/programming",
        "r/learnprogramming", "r/SideProject", "r/coding", "r/Python", "r/javascript", "r/golang",
    )
)

_TOPIC_TERMS: Dict[str, Sequence[str]] = {
    "developer": ("developer", "developers", "github", "engineering", "engineer", "devops", "api", "code", "software"),
    "ai_tools": ("ai", "llm", "gpt", "automation", "automate", "chatbot"),
    "freelance": ("freelance", "freelancer", "freelancers", "contractor", "solopreneur", "consultant"),
    "productivity": ("productivity", "organize", "task", "tasks", "deadline", "deadlines", "focus"),
    "marketing": ("marketing", "growth", "lead", "leads", "sales", "outreach", "seo"),
    "design": ("design", "designer", "ux", "figma", "prototype"),
    "ecommerce": ("shop", "shopify", "ecommerce", "store", "dropshipping", "merchant"),
    "creators": ("creator", "creators", "youtube", "podcast", "writer", "blogger"),
    "finance": ("finance", "invoice", "invoices", "accounting", "bookkeeping", "billing", "payroll"),
}

_SUB_RE = re.compile(r"^r/[A-Za-z0-9_]{3,21}$")


def keywords(text: str, limit: int = 4) -> str:
    """Pick the first few content words, the way a person types a search."""
    words = re.findall(r"[a-z0-9][a-z0-9'-]*", (text or "").lower())
    picked: List[str] = []
    for w in words:
        if len(w) > 2 and w not in _STOPWORDS and w not in picked:
            picked.append(w)
        if len(picked) >= limit:
            break
    return " ".join(picked)


def _has_term(text: str, terms: Iterable[str]) -> bool:
    return any(re.search(rf"\b{re.escape(t)}\b", text) for t in terms)


class SearchPlanner:
    """Plans multi-angle customer discovery queries from business profiles."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    # ── Public ──

    def plan_queries(
        self, profile: BusinessProfile, platforms: Optional[Sequence[str]] = None
    ) -> List[SearchQuery]:
        chosen = [p for p in (platforms or DEFAULT_PLATFORMS) if p in VALID_PLATFORMS]
        if not chosen:
            chosen = list(DEFAULT_PLATFORMS)

        profile_text = self._profile_text(profile)
        is_dev = _has_term(profile_text, _TOPIC_TERMS["developer"])
        llm_extra = self._llm_plan(profile, chosen)
        subs = self._select_subreddits(profile_text, is_dev, llm_extra["subreddits"])

        per_platform: Dict[str, List[SearchQuery]] = {p: [] for p in chosen}
        self._pain_queries(profile, chosen, subs, per_platform)
        self._competitor_queries(profile, chosen, per_platform)
        self._outcome_queries(profile, chosen, subs, per_platform)
        for q in llm_extra["queries"]:
            if q.platform in per_platform:
                per_platform[q.platform].append(q)

        return self._balance(per_platform, chosen)

    # ── Query builders ──

    def _pain_queries(self, profile, chosen, subs, out) -> None:
        pains = list(profile.problems_solved[:3]) + list(profile.customer_frustrations[:2])
        for i, pain in enumerate(pains):
            kw = keywords(pain)
            if not kw:
                continue
            if "reddit" in chosen:
                out["reddit"].append(self._q(f"struggling with {kw}", "frustration", "reddit", None, pain))
                if subs:
                    sub = subs[i % len(subs)]
                    out["reddit"].append(self._q(f"how do you handle {kw}", "indirect", "reddit", sub, pain))
            if "hackernews" in chosen:
                out["hackernews"].append(self._q(kw, "indirect", "hackernews", None, pain))
            if "web" in chosen:
                out["web"].append(self._q(f"people asking how to solve {kw}", "indirect", "web", None, pain))
            if "quora" in chosen:
                out["quora"].append(self._q(f"how to deal with {kw}", "tool_request", "quora", None, pain))
            if "twitter" in chosen:
                out["twitter"].append(self._q(f"struggling with {kw}", "frustration", "twitter", None, pain))
            if "github" in chosen and i == 0:
                out["github"].append(self._q(kw, "tool_request", "github", None, pain))

    def _competitor_queries(self, profile, chosen, out) -> None:
        for comp in profile.competitors_and_alternatives[:3]:
            name = re.sub(r"[^\w\s.+-]", "", comp).strip()
            if not name:
                continue
            why = f"Switching intent: {name}"
            if "reddit" in chosen:
                out["reddit"].append(self._q(f"alternative to {name}", "alternative", "reddit", None, why))
                out["reddit"].append(self._q(f"{name} too expensive", "cost", "reddit", None, f"Price complaint: {name}"))
            if "hackernews" in chosen:
                out["hackernews"].append(self._q(f"alternative to {name}", "alternative", "hackernews", None, why))
            if "quora" in chosen:
                out["quora"].append(self._q(f"alternative to {name}", "alternative", "quora", None, why))

    def _outcome_queries(self, profile, chosen, subs, out) -> None:
        for outcome in profile.customer_outcomes[:2]:
            kw = keywords(outcome)
            if kw and "reddit" in chosen:
                out["reddit"].append(
                    self._q(f"is there a tool to {kw}", "tool_request", "reddit", subs[0] if subs else None, outcome)
                )

    @staticmethod
    def _q(query: str, intent: str, platform: str, community: Optional[str], why: str) -> SearchQuery:
        return SearchQuery(
            query=query.strip(),
            intent_type=intent,
            platform=platform,
            target_community=community,
            rationale=why,
        )

    # ── Subreddits ──

    @staticmethod
    def _profile_text(profile: BusinessProfile) -> str:
        return " ".join(
            [profile.industry, profile.niche, profile.icp, profile.main_product_or_service]
            + list(profile.problems_solved)
            + list(profile.target_roles)
        ).lower()

    def _select_subreddits(self, text: str, is_dev: bool, llm_subs: Sequence[str]) -> List[str]:
        picked: List[str] = list(llm_subs)
        for group, terms in _TOPIC_TERMS.items():
            if group == "developer":
                if is_dev:
                    picked.extend(SUBREDDIT_MAP["developer"])
            elif _has_term(text, terms):
                picked.extend(SUBREDDIT_MAP[group])
        if len(picked) < 3:
            picked.extend(SUBREDDIT_MAP["b2b"])

        seen, unique = set(), []
        for sub in picked:
            low = sub.lower()
            if low in seen or low in LOW_SIGNAL_SUBS:
                continue
            seen.add(low)
            unique.append(sub)
        return unique[:8]

    # ── LLM enrichment ──

    def _llm_plan(self, profile: BusinessProfile, platforms: Sequence[str]) -> Dict[str, list]:
        empty: Dict[str, list] = {"queries": [], "subreddits": []}
        if self.llm.is_mock or not self.llm.is_configured:
            return empty
        usable = [p for p in platforms if p in ("reddit", "hackernews", "web")]
        prompt = f"""
You plan customer discovery searches for this business.

Niche: {profile.niche}
ICP: {profile.icp}
Problems solved: {profile.problems_solved}
Customer frustrations: {profile.customer_frustrations}
Competitors: {profile.competitors_and_alternatives}

Write 4 search queries in the exact words a frustrated customer types when asking for help.
Each query is 3 to 8 words. No product names unless it is a competitor. No quotation marks.
Allowed platforms: {usable}.

Also name up to 5 real, active subreddits where this ICP asks for help. Skip subreddits that
exist to show off products. If you are unsure a subreddit exists, leave it out.

Output JSON:
{{"queries": [{{"query": "...", "intent_type": "frustration|alternative|recommendation|tool_request",
  "platform": "reddit|hackernews|web", "target_community": "r/... or empty", "rationale": "..."}}],
 "subreddits": ["r/..."]}}
"""
        try:
            data = self.llm.complete_json(prompt, system_prompt="You plan search queries for customer research.")
        except LLMProviderError as exc:
            log.warning("LLM query planning skipped: %s", exc)
            return empty

        queries: List[SearchQuery] = []
        for item in data.get("queries", []) or []:
            if not isinstance(item, dict):
                continue
            text = re.sub(r"[\"']", "", str(item.get("query", ""))).strip()
            platform = str(item.get("platform", "reddit")).lower()
            if not (8 <= len(text) <= 120) or platform not in usable or platform not in platforms:
                continue
            community = str(item.get("target_community") or "").strip() or None
            if community and not _SUB_RE.match(community):
                community = None
            if platform != "reddit":
                community = None
            queries.append(
                self._q(text, str(item.get("intent_type", "frustration")), platform, community, str(item.get("rationale", "")))
            )
        subs = [s for s in (data.get("subreddits") or []) if isinstance(s, str) and _SUB_RE.match(s.strip())]
        return {"queries": queries[:6], "subreddits": [s.strip() for s in subs[:5]]}

    # ── Balance ──

    @staticmethod
    def _balance(per_platform: Dict[str, List[SearchQuery]], order: Sequence[str]) -> List[SearchQuery]:
        """Interleave platforms so none starves, drop duplicates, cap the total."""
        seen = set()
        lists: List[List[SearchQuery]] = []
        for platform in order:
            unique = []
            for q in per_platform.get(platform, []):
                key = (q.platform, q.query.lower(), (q.target_community or "").lower())
                if q.query and key not in seen:
                    seen.add(key)
                    unique.append(q)
            lists.append(unique[:MAX_PER_PLATFORM])
        result: List[SearchQuery] = []
        for rank in range(MAX_PER_PLATFORM):
            for lst in lists:
                if rank < len(lst):
                    result.append(lst[rank])
        return result[:MAX_QUERIES]
