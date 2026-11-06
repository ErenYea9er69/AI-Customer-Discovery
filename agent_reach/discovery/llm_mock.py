# -*- coding: utf-8 -*-
"""Deterministic mock LLM for tests and offline demos.

Never used unless LLM_PROVIDER=mock is set on purpose. The canned answers
describe made-up products, so real campaigns must not run on this provider.
"""

from __future__ import annotations

import json
import re
from typing import Optional


def mock_completion(prompt: str, system_prompt: Optional[str] = None) -> str:
    lower = prompt.lower()
    if "business profile" in lower:
        # Deterministic business profile response
        # Check if prompt specifies a business name
        name_match = re.search(r'Business Name:\s*([^\n]+)', prompt)
        business_name = name_match.group(1).strip() if name_match and name_match.group(1).strip() != "Unspecified" else "SuperTask"

        if "freelance" in lower or "taskly" in lower or "productivity" in lower and "engineer" not in lower:
            return json.dumps({
                "name": business_name if business_name != "SuperTask" else "Taskly",
                "industry": "Freelance Productivity & Workflow Automation",
                "niche": "Task, Deadline & Automation Dashboard for Freelancers",
                "main_product_or_service": "AI productivity dashboard that organizes tasks, manages deadlines, and automates repetitive freelance work",
                "features": [
                    "Multi-client task organization & prioritization",
                    "Smart deadline management & buffer time alerts",
                    "Automated repetitive workflow routines",
                    "Unified simple freelance dashboard",
                ],
                "problems_solved": [
                    "Freelancers struggle to focus and juggle multiple conflicting client deadlines",
                    "Manual and repetitive administrative tasks eat up billable hours",
                    "Scattered tasks and lost client communications across too many apps",
                ],
                "customer_outcomes": [
                    "Hit 100% of client deadlines without burnout",
                    "Reclaim 10+ hours weekly on automated admin tasks",
                    "Clear single-dashboard focus every morning",
                ],
                "icp": "Freelancers, Solo Consultants, and Independent Contractors juggling multiple clients",
                "target_industries": ["Freelance / Creative Services", "Independent Consulting", "Remote Knowledge Work"],
                "target_roles": ["Freelancer", "Independent Contractor", "Solo Consultant", "Creative Professional"],
                "customer_demographics": ["Solo professionals managing 2-10 active client accounts"],
                "customer_frustrations": [
                    "Missing deadlines due to fragmented client requests",
                    "Losing focus and feeling paralyzed by chaotic task lists",
                    "Spending mornings organizing tools instead of doing billable work",
                ],
                "competitors_and_alternatives": ["Notion", "ClickUp", "Todoist", "Trello", "Asana"],
                "unique_selling_points": [
                    "Built specifically for solo freelancers managing multiple deadlines, not bloated corporate teams",
                    "Automates repetitive client admin out of the box",
                ],
                "pricing_info": "$12/month with a 14-day free trial",
                "geographic_market": "Global",
                "trigger_events": [
                    "Missed a deadline and risked losing a paying client",
                    "Taking on multiple clients and feeling overwhelmed by admin chaos",
                ],
                "facts": [
                    {
                        "claim": "Taskly organizes tasks, manages deadlines, and automates repetitive work from one simple dashboard",
                        "source_url": "user_input",
                        "category": "feature",
                    },
                ],
                "inferences": [
                    {
                        "insight": "Freelancers managing 3+ simultaneous client deadlines experience the highest pain and conversion urgency",
                        "confidence": 0.94,
                        "basis": "Context switching and deadline anxiety scale sharply with client count",
                    },
                ],
            })
        return json.dumps({
            "name": business_name,
            "industry": "Developer Productivity Software",
            "niche": "Automated Backlog Triage for Engineering Teams",
            "main_product_or_service": "AI-powered GitHub issue and sprint backlog manager",
            "features": [
                "Automatic bug duplicate detection",
                "Sprint backlog prioritization",
                "Slack & Discord issue notifications",
            ],
            "problems_solved": [
                "Engineers spend 5+ hours weekly triaging stale tickets",
                "Duplicate issues fragment customer reports",
                "Unclear backlog priority causes sprint delays",
            ],
            "customer_outcomes": [
                "Save 20 hours per sprint",
                "Zero duplicate bug tickets",
                "Faster PR merges",
            ],
            "icp": "VP of Engineering, Lead Developer, or Technical Product Manager at high-growth tech companies",
            "target_industries": ["Software / SaaS", "FinTech", "DevOps"],
            "target_roles": ["Engineering Manager", "Tech Lead", "CTO", "Scrum Master"],
            "customer_demographics": ["Remote or hybrid engineering teams of 10-200 developers"],
            "customer_frustrations": [
                "Tired of manually labeling and assigning GitHub issues",
                "Jira backlog grooming meetings take forever",
                "Engineers miss critical customer-reported regressions",
            ],
            "competitors_and_alternatives": ["Linear", "Jira Software", "GitHub Projects", "Shortcut"],
            "unique_selling_points": [
                "True AI-native triage that runs in GitHub Actions with zero setup",
                "Self-hosted privacy-first architecture",
            ],
            "pricing_info": "$19/seat/month with a 14-day free trial",
            "geographic_market": "Global",
            "trigger_events": [
                "Sprint planning is derailed by stale backlog tickets",
                "Major customer bug is filed as a duplicate and ignored",
            ],
            "facts": [
                {
                    "claim": "SuperTask integrates natively with GitHub Actions and Jira",
                    "source_url": "https://supertask.example.com/features",
                    "category": "feature",
                },
                {
                    "claim": "Pricing starts at $19 per user per month",
                    "source_url": "https://supertask.example.com/pricing",
                    "category": "pricing",
                },
            ],
            "inferences": [
                {
                    "insight": "Target teams likely have between 10 and 200 software engineers",
                    "confidence": 0.88,
                    "basis": "Feature set and per-seat pricing cater to mid-sized engineering teams",
                },
                {
                    "insight": "Highest conversion occurs when engineering teams switch from Jira to lighter tools",
                    "confidence": 0.75,
                    "basis": "Pain points focus heavily on backlog grooming friction",
                },
            ],
        })

    if "generate search queries" in lower or "search planning" in lower:
        return json.dumps({
            "queries": [
                {
                    "query": "hate backlog grooming Jira",
                    "intent_type": "frustration",
                    "platform": "reddit",
                    "target_community": "r/programming",
                    "rationale": "Direct frustration with existing alternative backlog management",
                },
                {
                    "query": "looking for alternative to Jira issue triage",
                    "intent_type": "alternative",
                    "platform": "reddit",
                    "target_community": "r/softwaredevelopment",
                    "rationale": "High buying intent seeking modern replacement",
                },
                {
                    "query": "how do you handle duplicate GitHub issues",
                    "intent_type": "tool_request",
                    "platform": "reddit",
                    "target_community": "r/devops",
                    "rationale": "Specific problem that the product directly solves",
                },
                {
                    "query": "automate GitHub issue triage duplicate detection",
                    "intent_type": "recommendation",
                    "platform": "web",
                    "target_community": "",
                    "rationale": "Developers searching web discussions for automation tools",
                },
            ]
        })

    if "qualify lead" in lower or "lead qualification" in lower:
        return json.dumps({
            "customer_problem": "Our team wastes hours every Monday manually deduplicating GitHub bug reports and prioritizing sprint tickets.",
            "pain_point_category": "Backlog Inefficiency",
            "profile_match": "High match: Engineering Lead managing active GitHub repo",
            "competitor_mentioned": "Jira and GitHub Projects",
            "purchase_intent": "High",
            "urgency": "High",
            "product_fit_explanation": "SuperTask specifically eliminates manual triage and deduplicates issues automatically.",
            "evidence": "Author asked: 'Is there any tool that connects to GitHub and automatically detects duplicate issues before sprint planning?'",
            "score_breakdown": {
                "icp_match": 24,
                "problem_fit": 29,
                "buying_intent": 18,
                "urgency": 14,
                "recency": 9,
                "total": 94,
                "explanation": "Clear role match (Engineering Lead), acute stated problem (duplicate triage), asking for tool recommendations with high urgency.",
            },
            "score": 94,
            "classification": "high_potential",
            "confidence": 0.92,
        })

    if "generate replies" in lower or "reply generation" in lower:
        return json.dumps({
            "value_first": "One quick way to tackle this without adding heavy tools is using GitHub Issue Templates with strict required labels and GitHub CLI scripts in your CI to grep existing open issue titles. Also, establishing a strict triage rotation where only one developer handles incoming issues each sprint prevents everyone's focus from being fragmented.",
            "product_aware": "We ran into this exact headache with GitHub issue duplication, which is why we built SuperTask (disclosure: I'm part of the team). It runs automatically via GitHub Actions to scan incoming issues against existing open/closed tickets and flags semantic duplicates instantly. Even if you don't use a dedicated tool, setting up GitHub label automation in CI can save a ton of time.",
            "disclosure": "Disclosure: I am affiliated with SuperTask.",
        })

    return json.dumps({"status": "ok", "message": "Mock completion response"})