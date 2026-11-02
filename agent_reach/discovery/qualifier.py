# -*- coding: utf-8 -*-
"""Explainable lead qualification.

Two stages. A cheap rule pass drops spam, sellers and off-topic posts. A model
then judges the survivors against the business profile. When no model is
available the rules alone score the thread, mark it `judged_by="heuristic"`,
and cap it below `high_potential`, because keywords cannot prove buying intent.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from agent_reach.discovery import skillpack
from agent_reach.discovery.llm_client import LLMClient, LLMProviderError
from agent_reach.discovery.models import (
    BusinessProfile,
    DiscoveredItem,
    LeadQualification,
    ScoreBreakdown,
)
from agent_reach.discovery.platform_policy import get_policy
from agent_reach.discovery.security import injection_flags, sanitize
from agent_reach.discovery.thread_check import CROWDED_COMMENTS, age_in_days, is_promotional

log = logging.getLogger("agent_reach.discovery")

SPAM_PATTERNS = [
    r"\b(?:crypto|bitcoin|airdrop|casino|telegram channel|whatsapp group|free robux)\b",
    r"\b(?:dm me for rates|whatsapp me|invest now|guaranteed returns)\b",
]

BUYING_SIGNALS = [
    (r"\b(?:willing to pay|budget|purchase|pricing|subscription|pay for)\b", 8),
    (r"\b(?:looking for (?:a |an )?(?:tool|software|app|service|alternative|solution)|recommend (?:a |an )?(?:tool|software|app|service))\b", 7),
    (r"\b(?:anyone know (?:a )?(?:better )?(?:way|tool)|what do you (?:guys )?use for)\b", 5),
    (r"\b(?:hate having to|struggling with|tired of)\b", 3),
]
COMPLAINT_SIGNALS = [
    (r"\b(?:cannot keep up|can't keep up|behind schedule|falling behind)\b", 5),
    (r"\b(?:drowning in|overwhelmed (?:with|by)|burnout|exhausted)\b", 5),
    (r"\b(?:hate (?:using|having to|managing|dealing)|frustrated (?:with|by)|nightmare)\b", 5),
    (r"\b(?:headache|waste of time|wasting (?:hours|time))\b", 3),
]
URGENCY_SIGNALS = [
    (r"\b(?:blocking|critical|urgent|asap|every single day|every week|wasting hours)\b", 6),
    (r"\b(?:drowning in|nightmare|disaster|cannot stand|pulling my hair out)\b", 5),
    (r"\b(?:frustrated|annoying|painful)\b", 3),
]
HELP_SEEKING = re.compile(
    r"\?|\b(?:looking for|any recommendations?|recommend|how do (?:i|you|we)|anyone (?:know|use|tried)|"
    r"what do you use|need (?:a|help)|help me|advice)\b",
    re.I,
)

_STOP = frozenset(
    "the and for are but not you your with this that have from they them been were was will would can "
    "could should about into over under more most some any each every just also only own same such other "
    "what when where which while who how why our out use using used make made need needs want wants".split()
)


def _stem(word: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def _tokens(text: str) -> Set[str]:
    return {_stem(w) for w in re.findall(r"[a-z][a-z0-9]{2,}", (text or "").lower()) if w not in _STOP}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def classify(
    total: int,
    fit: int,
    intent: int,
    competitor: Optional[str],
    commentable: Optional[bool],
    verified: bool,
) -> Optional[str]:
    """Map scores to a class. `verified` means a model judged it and its evidence quote was found in the post.

    The pipeline and the MCP server both call this, so a lead gets the same class on either path.
    Returns None when the thread is not worth keeping.
    """
    if competitor and intent < 8 and fit < 15:
        return "competitor_intel"
    if total >= 75 and intent >= 8 and commentable is not False and verified:
        return "high_potential"
    if total >= 50:
        return "relevant_potential"
    if total >= 30 and fit > 0:
        return "customer_insight"
    return None


def intent_label(intent: int) -> str:
    return "High" if intent >= 14 else "Medium" if intent >= 9 else "Low" if intent >= 5 else "None"


def urgency_label(urgency: int) -> str:
    return "High" if urgency >= 9 else "Medium" if urgency >= 6 else "Low"


@dataclass
class _Signals:
    matched_problems: List[str]
    best_overlap: float
    icp_hits: int
    help_seeking: bool
    intent_pts: int
    urgency_pts: int
    competitor: Optional[str]


class LeadQualifier:
    """Turns discovered threads into scored, explainable leads."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        base = llm_client or LLMClient()
        # Qualification runs once per thread, so it uses the fast tier unless the owner sets another.
        self.llm = base.for_tier(os.getenv("LLM_QUALIFY_TIER", "fast"))
        self.max_llm_calls = int(os.getenv("LLM_QUALIFY_MAX", "80"))
        self.llm_calls = 0
        self.last_rejection: Optional[str] = None

    def reset_budget(self) -> None:
        self.llm_calls = 0

    # ── Entry point ──

    def qualify(self, item: DiscoveredItem, profile: BusinessProfile) -> Optional[LeadQualification]:
        """Return a lead, or None. `last_rejection` explains a None."""
        self.last_rejection = None
        text = sanitize(f"{item.title}\n{item.content}")
        lowered = text.lower()

        flags = injection_flags(text)
        if flags:
            return self._reject("prompt_injection:" + ",".join(flags))

        if any(re.search(p, lowered) for p in SPAM_PATTERNS):
            return self._reject("spam")
        if is_promotional(item.title, item.content):
            return self._reject("promotional")

        sig = self._signals(text, lowered, profile)
        use_llm = self._llm_available()
        # Without a model, keywords must prove the topic. With one, a light overlap is enough.
        if not sig.matched_problems and not (use_llm and sig.icp_hits >= 1):
            return self._reject("off_topic")

        verdict = self._llm_verdict(item, profile) if use_llm else None
        if verdict is not None and not verdict["is_lead"]:
            return self._reject("llm_not_a_lead")
        return self._build(item, profile, sig, verdict)

    def _reject(self, reason: str) -> Optional[LeadQualification]:
        self.last_rejection = reason
        return None

    def _llm_available(self) -> bool:
        return (
            self.llm.is_configured
            and not self.llm.is_mock
            and self.llm_calls < self.max_llm_calls
        )

    # ── Heuristic signals ──

    def _signals(self, text: str, lowered: str, profile: BusinessProfile) -> _Signals:
        text_tokens = _tokens(text)
        phrases = (
            list(profile.problems_solved) + list(profile.customer_frustrations) + list(profile.pain_vocabulary)
        )
        matched: List[str] = []
        best = 0.0
        for phrase in phrases:
            need = _tokens(phrase)
            if not need:
                continue
            hit = len(need & text_tokens)
            overlap = hit / len(need)
            if (hit >= 2 and overlap >= 0.4) or (len(need) <= 2 and overlap == 1.0):
                matched.append(phrase)
                best = max(best, overlap)

        icp_tokens = _tokens(f"{profile.icp} {' '.join(profile.target_roles)}")
        icp_hits = len(icp_tokens & text_tokens)

        intent = 4
        urgency = 3
        for pat, pts in BUYING_SIGNALS:
            if re.search(pat, lowered):
                intent += pts
        for pat, pts in URGENCY_SIGNALS:
            if re.search(pat, lowered):
                urgency += pts
        for pat, pts in COMPLAINT_SIGNALS:
            if re.search(pat, lowered):
                intent += pts
                urgency += pts

        return _Signals(
            matched_problems=matched,
            best_overlap=best,
            icp_hits=icp_hits,
            help_seeking=bool(HELP_SEEKING.search(text[:600])),
            intent_pts=min(20, intent),
            urgency_pts=min(15, urgency),
            competitor=self._competitor(lowered, profile),
        )

    @staticmethod
    def _competitor(lowered: str, profile: BusinessProfile) -> Optional[str]:
        for comp in profile.competitors_and_alternatives:
            name = comp.lower().strip()
            if name and re.search(rf"\b{re.escape(name)}\b", lowered):
                return comp
        return None

    # ── Reply opportunity (0 to 10) ──

    @staticmethod
    def _opportunity_points(item: DiscoveredItem) -> int:
        health = item.thread_health or {}
        age = health.get("age_days")
        if age is None:
            age = age_in_days(item.published_at)
        if age is None:
            pts = 3
        elif age <= 7:
            pts = 10
        elif age <= 30:
            pts = 8
        elif age <= 90:
            pts = 6
        elif age <= 150:
            pts = 4
        else:
            pts = 2
        if (health.get("num_comments") or 0) >= CROWDED_COMMENTS:
            pts -= 3
        if "unverified_comment_state" in (health.get("warnings") or []):
            pts -= 1
        return max(0, min(10, pts))

    # ── LLM judge ──

    def _llm_verdict(self, item: DiscoveredItem, profile: BusinessProfile) -> Optional[Dict[str, Any]]:
        self.llm_calls += 1
        body = sanitize(item.content, 2500)
        health = item.thread_health or {}
        prompt = f"""
<business>
Product: {profile.main_product_or_service or profile.name}
Niche: {profile.niche}
Problems it solves: {profile.problems_solved}
Customer words: {profile.pain_vocabulary[:10]}
Ideal customer: {profile.icp}
Not for: {profile.not_for}
Competitors and alternatives: {profile.competitors_and_alternatives}
</business>

<untrusted_post platform="{item.platform}" community="{item.community}" author="{item.author}">
Title: {sanitize(item.title, 300)}
Body: {body}
</untrusted_post>

<thread_facts>
age_days: {health.get("age_days")}
num_comments: {health.get("num_comments")}
commentable: {health.get("commentable")}
</thread_facts>

Judge the post with the rules in your instructions. Output the JSON object only.
"""
        try:
            data = self.llm.complete_json(prompt, system_prompt=skillpack.prompt("lead-qualification"))
        except LLMProviderError as exc:
            log.warning("LLM qualification failed, using rules: %s", str(exc)[:200])
            return None

        def num(key: str, cap: int) -> int:
            try:
                return max(0, min(cap, int(float(data.get(key, 0)))))
            except (TypeError, ValueError):
                return 0

        post_type = str(data.get("post_type", "other"))
        is_lead = bool(data.get("author_is_potential_customer")) and post_type in (
            "asking_for_help", "complaint", "recommendation_request", "discussion"
        )
        quote = str(data.get("evidence_quote") or "").strip()[:200]
        verified = bool(quote) and _norm(quote) in _norm(f"{item.title} {item.content}")
        return {
            "post_type": post_type,
            "is_lead": is_lead,
            "fit": num("problem_fit", 30),
            "icp": num("icp_match", 25),
            "intent": num("buying_intent", 20),
            "urgency": num("urgency", 15),
            "problem": str(data.get("customer_problem") or "").strip()[:300],
            "quote": quote if verified else "",
            "quote_verified": verified,
            "competitor": data.get("competitor_mentioned") or None,
            "reason": str(data.get("reason") or "").strip()[:300],
        }

    # ── Assembly ──

    def _build(
        self,
        item: DiscoveredItem,
        profile: BusinessProfile,
        sig: _Signals,
        verdict: Optional[Dict[str, Any]],
    ) -> Optional[LeadQualification]:
        opportunity = self._opportunity_points(item)

        if verdict:
            fit, icp = verdict["fit"], verdict["icp"]
            intent, urgency = verdict["intent"], verdict["urgency"]
            judged_by = "llm"
            confidence = 0.9 if verdict["quote_verified"] else 0.7
            competitor = verdict["competitor"] or sig.competitor
        else:
            fit = min(30, 12 + 9 * len(sig.matched_problems)) if sig.matched_problems else 0
            icp = min(25, 5 + 4 * sig.icp_hits)
            intent, urgency = sig.intent_pts, sig.urgency_pts
            if not sig.help_seeking:
                intent = max(2, intent - 6)
            judged_by = "heuristic"
            confidence = 0.5
            competitor = sig.competitor

        total = min(100, fit + icp + intent + urgency + opportunity)
        intent_text, urgency_text = intent_label(intent), urgency_label(urgency)

        commentable = (item.thread_health or {}).get("commentable")
        verified = bool(judged_by == "llm" and verdict is not None and verdict["quote_verified"])
        classification = classify(total, fit, intent, competitor, commentable, verified)
        if classification is None:
            return self._reject("low_score")

        body = item.content
        if body.startswith(item.title):
            body = body[len(item.title):]
        body = body.strip()
        excerpt = body[:240].strip() + ("..." if len(body) > 240 else "")
        if not excerpt:
            excerpt = item.title

        problem = (
            (verdict or {}).get("problem")
            or (sig.matched_problems[0] if sig.matched_problems else item.title)
        )
        if verdict and verdict["quote_verified"]:
            evidence = f"Author wrote: '{verdict['quote']}'"
        else:
            evidence = f"Post excerpt: '{excerpt}'"

        reason = (verdict or {}).get("reason") or (
            f"Post overlaps the problem '{sig.matched_problems[0]}'." if sig.matched_problems else "Weak topic overlap."
        )
        explanation = (
            f"Problem fit {fit}/30. ICP match {icp}/25. Buying intent {intent}/20 ({intent_text}). "
            f"Urgency {urgency}/15 ({urgency_text}). Reply opportunity {opportunity}/10. "
            f"Judged by {judged_by}."
        )
        return LeadQualification(
            discovered_item_id=item.id,
            title=item.title,
            url=item.url,
            platform=item.platform,
            community=item.community,
            author=item.author,
            published_at=item.published_at,
            excerpt=excerpt,
            customer_problem=problem,
            pain_point_category=(sig.matched_problems[0][:60] if sig.matched_problems else profile.niche),
            profile_match=f"{item.community}: {reason}",
            competitor_mentioned=competitor,
            purchase_intent=intent_text,  # type: ignore[arg-type]
            urgency=urgency_text,  # type: ignore[arg-type]
            product_fit_explanation=reason,
            evidence=evidence,
            score=total,
            score_breakdown=ScoreBreakdown(
                icp_match=icp, problem_fit=fit, buying_intent=intent, urgency=urgency,
                recency=opportunity, total=total, explanation=explanation,
            ),
            classification=classification,  # type: ignore[arg-type]
            confidence=confidence,
            judged_by=judged_by,  # type: ignore[arg-type]
            thread_health=item.thread_health or {},
            post_type=(verdict or {}).get("post_type", ""),
            evidence_verified=bool(verdict and verdict["quote_verified"]),
            reply_policy="draft" if get_policy(item.platform).draft == "allowed" else "human_only",
        )
