# -*- coding: utf-8 -*-
"""Analytics engine aggregating customer pain points, competitor gaps, and actionable insights."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Optional

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

        complaints_counter = Counter(lead.customer_problem for lead in leads if lead.customer_problem)
        categories_counter = Counter(lead.pain_point_category for lead in leads if lead.pain_point_category)
        competitors_counter = Counter(lead.competitor_mentioned for lead in leads if lead.competitor_mentioned)
        intent_counter = Counter(lead.purchase_intent for lead in leads)
        platform_counter = Counter(lead.platform for lead in leads)
        urgency_counter = Counter(lead.urgency for lead in leads)

        high_urgency_list = [
            {"problem": lead.customer_problem, "count": 1, "community": lead.community, "excerpt": lead.excerpt}
            for lead in leads
            if lead.urgency == "High"
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

        community_counter = Counter(lead.community for lead in leads if lead.community)
        strong = Counter(lead.community for lead in leads if lead.classification == "high_potential" and lead.community)
        kinds = self.storage.recent_published_kinds(limit=100, since_days=90)
        reply_mix: Dict[str, Any] = {
            "published_last_90_days": len(kinds),
            "product_aware": sum(1 for k in kinds if k == "product_aware"),
            "value_first": sum(1 for k in kinds if k == "value_first"),
        }
        if kinds:
            reply_mix["product_share"] = round(reply_mix["product_aware"] / len(kinds), 3)
            if reply_mix["product_share"] > 0.1:
                recommendations.append({
                    "type": "safety",
                    "title": "Too many product replies",
                    "description": "More than 10 percent of your recent replies name the product. Post helpful replies without it first.",
                })
        return {
            "total_leads": total,
            "top_communities": [
                {"community": c, "leads": n, "high_potential": strong.get(c, 0)}
                for c, n in community_counter.most_common(6)
            ],
            "reply_mix": reply_mix,
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

