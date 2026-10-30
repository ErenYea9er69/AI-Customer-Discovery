# -*- coding: utf-8 -*-
"""Configurable LLM client supporting OpenAI, Gemini, Groq, Anthropic, and local heuristic mock."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional


class LLMClient:
    """Configurable LLM interface with fallback heuristic engine."""

    def __init__(
        self,
        provider: str = "mock",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.provider = (provider or os.getenv("LLM_PROVIDER", "mock")).lower()
        self.api_key = api_key or os.getenv("LLM_API_KEY")
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
        if self.provider == "mock" or not self.api_key:
            return self._mock_completion(prompt, system_prompt)

        if self.provider == "openai":
            return self._call_openai(prompt, system_prompt)
        elif self.provider == "gemini":
            return self._call_gemini(prompt, system_prompt)
        elif self.provider == "groq":
            return self._call_groq(prompt, system_prompt)
        elif self.provider == "anthropic":
            return self._call_anthropic(prompt, system_prompt)
        else:
            return self._mock_completion(prompt, system_prompt)

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
            # Return fallback empty structure
            return {"error": "Failed to decode JSON", "raw": raw}

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
            return self._mock_completion(prompt, system_prompt)

    def _call_gemini(self, prompt: str, system_prompt: Optional[str]) -> str:
        try:
            import urllib.request

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model or 'gemini-1.5-flash'}:generateContent?key={self.api_key}"
            text = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            data = json.dumps({"contents": [{"parts": [{"text": text}]}]}).encode("utf-8")
            req = urllib.request.Request(
                url, data=data, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return self._mock_completion(prompt, system_prompt)

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
        except Exception:
            return self._mock_completion(prompt, system_prompt)

    def _call_anthropic(self, prompt: str, system_prompt: Optional[str]) -> str:
        try:
            import urllib.request

            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": self.api_key or "",
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
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res["content"][0]["text"]
        except Exception:
            return self._mock_completion(prompt, system_prompt)

    # ── Heuristic Mock Engine (for testing & offline execution) ──

    def _mock_completion(self, prompt: str, system_prompt: Optional[str]) -> str:
        lower = prompt.lower()
        if "business profile" in lower:
            # Deterministic business profile response
            # Check if prompt specifies a business name
            name_match = re.search(r'Business Name:\s*([^\n]+)', prompt)
            business_name = name_match.group(1).strip() if name_match and name_match.group(1).strip() != "Unspecified" else "SuperTask"
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
