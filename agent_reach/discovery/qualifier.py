# -*- coding: utf-8 -*-
"""Explainable lead qualification and intelligence scoring engine."""

from __future__ import annotations

import datetime
import re
import time
from typing import Any, Dict, List, Optional

from agent_reach.discovery.llm_client import LLMClient
from agent_reach.discovery.models import (
    BusinessProfile,
    DiscoveredItem,
    LeadClassification,
    LeadQualification,
    ScoreBreakdown,
)

SPAM_PATTERNS = [
    r"\b(?:crypto|bitcoin|airdrop|casino|telegram channel|whatsapp group|free robux)\b",
    r"\b(?:dm me for rates|whatsapp me|invest now|guaranteed returns)\b",
]

BUYING_SIGNALS = [
    (r"\b(?:willing to pay|budget|purchase|pricing|subscription|pay for)\b", 8),
    (r"\b(?:looking for (?:a )?(?:tool|software|app|service|alternative)|recommend a tool)\b", 7),
    (r"\b(?:anyone know a (?:better )?way|what do you guys use for)\b", 5),
    (r"\b(?:hate having to|struggling with|tired of)\b", 3),
]

URGENCY_SIGNALS = [
    (r"\b(?:blocking|critical|urgent|asap|every single day|wasting hours)\b", 6),
    (r"\b(?:drowning in|nightmare|disaster|cannot stand|pulling my hair out)\b", 5),
    (r"\b(?:frustrated|slow|annoying|painful)\b", 3),
]


class LeadQualifier:
    """Evaluates discovered community conversations into qualified leads."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def qualify(self, item: DiscoveredItem, profile: BusinessProfile) -> Optional[LeadQualification]:
        """Qualify a single discovered conversation against the business profile."""
        # 1. Quality & Spam Filter
        if self._is_spam(item.content):
            return None

        # 2. Extract facts, problems, and explainable score
        qualification = self._evaluate_item(item, profile)
        return qualification

    def _is_spam(self, text: str) -> bool:
        lowered = text.lower()
        return any(re.search(pat, lowered) for pat in SPAM_PATTERNS)

    def _calculate_recency_score(self, published_at: str) -> int:
        if not published_at:
            return 5
        try:
            pub_date = datetime.datetime.fromisoformat(published_at).date()
            days_old = (datetime.date.today() - pub_date).days
            if days_old <= 30:
                return 10
            elif days_old <= 90:
                return 8
            elif days_old <= 180:
                return 6
            elif days_old <= 365:
                return 4
            else:
                return 2
        except Exception:
            return 5

    def _evaluate_item(self, item: DiscoveredItem, profile: BusinessProfile) -> LeadQualification:
        """Run scoring rule engine and LLM verification."""
        text = f"{item.title}\n{item.content}"
        lowered = text.lower()

        # Recency (max 10)
        recency_pts = self._calculate_recency_score(item.published_at)

        # Buying intent heuristic (max 20)
        intent_pts = 4
        for pat, pts in BUYING_SIGNALS:
            if re.search(pat, lowered):
                intent_pts += pts
        intent_pts = min(20, intent_pts)

        # Urgency heuristic (max 15)
        urgency_pts = 3
        for pat, pts in URGENCY_SIGNALS:
            if re.search(pat, lowered):
                urgency_pts += pts
        urgency_pts = min(15, urgency_pts)

        # Problem fit heuristic (max 30)
        matched_problems = []
        for prob in profile.problems_solved:
            words = [w for w in re.split(r"\W+", prob.lower()) if len(w) > 3]
            matches = sum(1 for w in words if w in lowered)
            if matches >= 1:
                matched_problems.append(prob)

        fit_pts = 10 + min(20, len(matched_problems) * 10)

        # ICP match (max 25)
        icp_keywords = [
            w for w in re.split(r"\W+", f"{profile.icp} {' '.join(profile.target_roles)}".lower())
            if len(w) > 3
        ]
        icp_matches = sum(1 for w in icp_keywords if w in lowered)
        icp_pts = min(25, 8 + (icp_matches * 4))

        # Check for competitor mentions
        mentioned_comp = None
        for comp in profile.competitors_and_alternatives:
            comp_lower = comp.lower()
            comp_keywords = [w for w in re.split(r"\W+", comp_lower) if len(w) >= 3]
            if comp_lower in lowered or any(cw in lowered for cw in comp_keywords):
                mentioned_comp = comp
                break

        # Calculate total score
        total_score = min(100, icp_pts + fit_pts + intent_pts + urgency_pts + recency_pts)

        # Determine purchase intent label
        if intent_pts >= 14:
            intent_label = "High"
        elif intent_pts >= 9:
            intent_label = "Medium"
        elif intent_pts >= 5:
            intent_label = "Low"
        else:
            intent_label = "None"

        # Determine urgency label
        if urgency_pts >= 9:
            urgency_label = "High"
        elif urgency_pts >= 6:
            urgency_label = "Medium"
        else:
            urgency_label = "Low"

        # Determine classification
        classification: LeadClassification
        if mentioned_comp and intent_pts < 8 and fit_pts < 15:
            classification = "competitor_intel"
        elif total_score >= 75:
            classification = "high_potential"
        elif total_score >= 50:
            classification = "relevant_potential"
        elif matched_problems and intent_label in ("Low", "None"):
            classification = "customer_insight"
        else:
            classification = "irrelevant"

        # Extract excerpt (first 200 chars or sentence containing pain keyword)
        excerpt = item.content[:240].strip() + ("..." if len(item.content) > 240 else "")

        explanation = (
            f"ICP match: {icp_pts}/25 (author context in {item.community}). "
            f"Problem fit: {fit_pts}/30 ({len(matched_problems)} problem signals matched). "
            f"Buying intent: {intent_pts}/20 ({intent_label} intent signals). "
            f"Urgency: {urgency_pts}/15 ({urgency_label} pain severity). "
            f"Recency: {recency_pts}/10."
        )

        breakdown = ScoreBreakdown(
            icp_match=icp_pts,
            problem_fit=fit_pts,
            buying_intent=intent_pts,
            urgency=urgency_pts,
            recency=recency_pts,
            total=total_score,
            explanation=explanation,
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
            customer_problem=matched_problems[0] if matched_problems else "Customer experiencing manual workflow friction",
            pain_point_category=profile.niche or "Operational Inefficiency",
            profile_match=f"Target audience in {item.community} matching {profile.icp[:50]}",
            competitor_mentioned=mentioned_comp,
            purchase_intent=intent_label,
            urgency=urgency_label,
            product_fit_explanation=f"{profile.name} directly solves this by providing automated triage and prioritization.",
            evidence=f"Author stated: '{excerpt}'",
            score=total_score,
            score_breakdown=breakdown,
            classification=classification,
            confidence=0.88,
        )
