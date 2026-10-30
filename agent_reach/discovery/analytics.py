# -*- coding: utf-8 -*-
"""Analytics engine aggregating customer pain points, competitor gaps, and actionable insights."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional

from agent_reach.discovery.storage import DiscoveryStorage


class DiscoveryAnalytics:
    """Aggregates pain points, competitor mentions, and marketing recommendations."""

    def __init__(self, storage: Optional[DiscoveryStorage] = None):
        self.storage = storage or DiscoveryStorage()

    def get_insights(self) -> Dict[str, Any]:
        """Aggregate insights across all stored qualified leads."""
        leads = self.storage.list_leads(limit=1000)
        total = len(leads)

        if total == 0:
            return {
                "total_leads": 0,
                "common_complaints": [],
                "high_urgency_problems": [],
                "competitor_intelligence": [],
                "intent_distribution": {},
                "platform_distribution": {},
                "recommendations": [
                    {
                        "type": "onboarding",
                        "title": "Launch your first discovery campaign",
                        "description": "Analyze your business website to begin uncovering customer problems.",
                    }
                ],
            }

        complaints_counter = Counter(l.customer_problem for l in leads if l.customer_problem)
        categories_counter = Counter(l.pain_point_category for l in leads if l.pain_point_category)
        competitors_counter = Counter(l.competitor_mentioned for l in leads if l.competitor_mentioned)
        intent_counter = Counter(l.purchase_intent for l in leads)
        platform_counter = Counter(l.platform for l in leads)
        urgency_counter = Counter(l.urgency for l in leads)

        high_urgency_list = [
            {"problem": l.customer_problem, "count": 1, "community": l.community, "excerpt": l.excerpt}
            for l in leads
            if l.urgency == "High"
        ]

        # Actionable suggestions
        recommendations = []
        top_complaint = complaints_counter.most_common(1)
        if top_complaint:
            recommendations.append({
                "type": "product",
                "title": f"Address top pain point: {top_complaint[0][0][:60]}",
                "description": f"Encountered in {top_complaint[0][1]} conversations. Make this capability prominent in onboarding.",
            })

        top_competitor = competitors_counter.most_common(1)
        if top_competitor:
            recommendations.append({
                "type": "marketing",
                "title": f"Target dissatisfied {top_competitor[0][0]} users",
                "description": f"Mentioned in {top_competitor[0][1]} discussions. Create a dedicated comparison landing page addressing their pricing and complexity.",
            })

        if intent_counter.get("High", 0) > 0:
            recommendations.append({
                "type": "sales",
                "title": f"Engage {intent_counter['High']} high-intent prospects",
                "description": "These users are actively asking for tool recommendations and ready to evaluate solutions.",
            })

        return {
            "total_leads": total,
            "common_complaints": [
                {"problem": prob, "count": count, "category": "Problem"}
                for prob, count in complaints_counter.most_common(5)
            ],
            "pain_point_categories": [
                {"category": cat, "count": count}
                for cat, count in categories_counter.most_common(5)
            ],
            "high_urgency_problems": high_urgency_list[:5],
            "competitor_intelligence": [
                {"competitor": comp, "mentions": count}
                for comp, count in competitors_counter.most_common(5)
            ],
            "intent_distribution": dict(intent_counter),
            "urgency_distribution": dict(urgency_counter),
            "platform_distribution": dict(platform_counter),
            "recommendations": recommendations,
        }

