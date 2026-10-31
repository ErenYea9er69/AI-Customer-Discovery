# -*- coding: utf-8 -*-
"""Configurable LLM client supporting OpenAI, Gemini, Groq, Anthropic, and local heuristic mock."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional


class LLMProviderError(RuntimeError):
    """Raised when a configured provider fails; mock is opt-in only."""


class LLMClient:
    """Configurable LLM interface with an explicit, deterministic mock provider."""

    def __init__(
        self,
        provider: str = "mock",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        env_provider = os.getenv("LLM_PROVIDER")
        if not env_provider and not provider:
            if os.getenv("GROQ_API_KEY"):
                env_provider = "groq"
            elif os.getenv("OPENAI_API_KEY"):
                env_provider = "openai"
            elif os.getenv("GEMINI_API_KEY"):
                env_provider = "gemini"
            elif os.getenv("ANTHROPIC_API_KEY"):
                env_provider = "anthropic"
            else:
                env_provider = "mock"

        self.provider = (provider or env_provider or "mock").lower()

        if not api_key:
            if self.provider == "groq":
                self.api_key = os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY")
            elif self.provider == "openai":
                self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
            elif self.provider == "gemini":
                self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
            elif self.provider == "anthropic":
                self.api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("LLM_API_KEY")
            else:
                self.api_key = os.getenv("LLM_API_KEY")
        else:
            self.api_key = api_key

        self.model = model or os.getenv("LLM_MODEL")

        if self.provider == "openai" and not self.model:
            self.model = "gpt-4o"
        elif self.provider == "gemini" and not self.model:
            self.model = "gemini-1.5-flash"
        elif self.provider == "groq" and not self.model:
            self.model = "llama-3.3-70b-versatile"
        elif self.provider == "anthropic" and not self.model:
            self.model = "claude-3-5-sonnet-20241022" 
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Get completion from selected provider or mock engine."""
        if self.provider == "mock":
            return self._mock_completion(prompt, system_prompt)
        if not self.api_key:
            raise LLMProviderError(f"Provider '{self.provider}' is configured but no API key is available.")

        if self.provider == "openai":
            return self._call_openai(prompt, system_prompt)
        elif self.provider == "gemini":
            return self._call_gemini(prompt, system_prompt)
        elif self.provider == "groq":
            return self._call_groq(prompt, system_prompt)
        elif self.provider == "anthropic":
            return self._call_anthropic(prompt, system_prompt)
        else:
            raise LLMProviderError(f"Unsupported LLM provider: {self.provider}")

    def complete_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Request structured JSON completion and parse safely."""
        json_system = (
            (system_prompt or "")
            + "\nRespond ONLY with a valid JSON object. Do not include markdown commentary."
        ).strip()
        raw = self.complete(prompt, json_system)
        return self._extract_json(raw)

    def _extract_json(self, raw: str) -> Dict[str, Any]:
        """Extract and parse JSON from potential markdown wrapping or text."""
        cleaned = raw.strip()
        # Strip ```json ... ```
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to find { ... } block
            match = re.search(r"(\{[\s\S]*\})", cleaned)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            raise LLMProviderError("Configured LLM returned invalid JSON.")

    # ── Providers ──

    def _call_openai(self, prompt: str, system_prompt: Optional[str]) -> str:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            resp = client.chat.completions.create(
                model=self.model or "gpt-4o",
                messages=messages,
                response_format={"type": "json_object"} if "json" in prompt.lower() else None,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            raise LLMProviderError(f"OpenAI request failed: {e}") from e

    def _call_gemini(self, prompt: str, system_prompt: Optional[str]) -> str:
        try:
            import requests

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model or 'gemini-1.5-flash'}:generateContent"
            text = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            payload = {"contents": [{"parts": [{"text": text}]}]}
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": str(self.api_key),
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            if resp.status_code != 200:
                raise LLMProviderError(f"Gemini API returned status {resp.status_code}: {resp.text}")
            result = resp.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except LLMProviderError:
            raise
        except Exception as e:
            raise LLMProviderError(f"Gemini request failed: {e}") from e

    def _call_groq(self, prompt: str, system_prompt: Optional[str]) -> str:
        try:
            from groq import Groq

            client = Groq(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            resp = client.chat.completions.create(
                model=self.model or "llama-3.3-70b-versatile",
                messages=messages,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            raise LLMProviderError(f"Groq request failed: {e}") from e

    def _call_anthropic(self, prompt: str, system_prompt: Optional[str]) -> str:
        try:
            import requests

            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": str(self.api_key or ""),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            payload: Dict[str, Any] = {
                "model": self.model or "claude-3-5-sonnet-20241022",
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system_prompt:
                payload["system"] = system_prompt
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            if resp.status_code != 200:
                raise LLMProviderError(f"Anthropic API returned status {resp.status_code}: {resp.text}")
            res = resp.json()
            return res["content"][0]["text"]
        except LLMProviderError:
            raise
        except Exception as e:
            raise LLMProviderError(f"Anthropic request failed: {e}") from e

    # ── Heuristic Mock Engine (for testing & offline execution) ──

    def _mock_completion(self, prompt: str, system_prompt: Optional[str]) -> str:
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
                "profile_match": "High match - Engineering Lead managing active GitHub repo",
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