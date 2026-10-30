# -*- coding: utf-8 -*-
"""Business Understanding Engine for analyzing websites and manual product descriptions."""

from __future__ import annotations

import re
import urllib.parse
from typing import Any, Dict, List, Optional, Set
import requests
from bs4 import BeautifulSoup

from agent_reach.discovery.llm_client import LLMClient
from agent_reach.discovery.models import (
    BusinessProfile,
    FactItem,
    InferenceItem,
)
from agent_reach.utils.url import normalize_public_http_url

PRIORITY_PATHS = [
    "/pricing",
    "/features",
    "/product",
    "/about",
    "/faq",
    "/solutions",
    "/case-studies",
]

_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


class BusinessEngine:
    """Extracts verified facts, ICP, and problems from business websites or manual descriptions."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def analyze_website(self, url: str) -> BusinessProfile:
        """Crawl homepage and priority subpages, extracting structured business profile."""
        clean_url = self._clean_url(url)
        page_contents = self._crawl_site(clean_url)

        # Aggregate scraped text with URL references
        combined_text_blocks = []
        for page_url, text in page_contents.items():
            trimmed = text[:3000].strip()
            if trimmed:
                combined_text_blocks.append(f"--- SOURCE PAGE: {page_url} ---\n{trimmed}")

        scraped_corpus = "\n\n".join(combined_text_blocks)

        prompt = f"""
You are an expert B2B and SaaS market researcher.
Analyze the following scraped content from website: {clean_url}

Scraped Content:
{scraped_corpus}

Extract a comprehensive, highly accurate business profile.
IMPORTANT RULES:
1. Do NOT invent features, pricing, or guarantees that are not mentioned.
2. Separate VERIFIED FACTS (with exact source URLs from the provided pages) from AI INFERENCES.
3. For every inference (ICP, trigger events, frustrations), assign a confidence score between 0.0 and 1.0 and explain the basis.

Output valid JSON matching this schema:
{{
  "name": "Product/Business Name",
  "industry": "Industry category",
  "niche": "Specific market niche",
  "main_product_or_service": "One-line core offering",
  "features": ["feature 1", "feature 2"],
  "problems_solved": ["problem 1", "problem 2"],
  "customer_outcomes": ["outcome 1", "outcome 2"],
  "icp": "Ideal customer profile description",
  "target_industries": ["industry 1"],
  "target_roles": ["role 1", "role 2"],
  "customer_demographics": ["demographic info if relevant"],
  "customer_frustrations": ["frustration 1", "frustration 2"],
  "competitors_and_alternatives": ["competitor 1", "competitor 2"],
  "unique_selling_points": ["usp 1", "usp 2"],
  "pricing_info": "pricing summary or tier details",
  "geographic_market": "e.g. Global or regional",
  "trigger_events": ["trigger event 1", "trigger event 2"],
  "facts": [
    {{
      "claim": "Verified factual statement",
      "source_url": "{clean_url}",
      "category": "feature|pricing|company|icp"
    }}
  ],
  "inferences": [
    {{
      "insight": "AI inference about ICP or market",
      "confidence": 0.85,
      "basis": "Why this inference was made based on page evidence"
    }}
  ]
}}
"""
        data = self.llm.complete_json(prompt, system_prompt="You extract business profile data into strict JSON.")
        return self._build_profile_from_data(data, url=clean_url)

    def analyze_manual_description(self, description: str, name: Optional[str] = None) -> BusinessProfile:
        """Extract structured business profile from a user-supplied product/service description."""
        prompt = f"""
You are an expert market researcher.
Analyze the following manual product or service description provided by the founder/creator:

Business Name: {name or 'Unspecified'}
Description:
{description}

Extract a comprehensive business profile.
Identify problems solved, ideal customer profile (ICP), target roles, customer frustrations, competitor alternatives, and buying triggers.
Separate facts explicitly stated by the user from AI inferences.

Output valid JSON matching this schema:
{{
  "name": "{name or 'Product Name'}",
  "industry": "Industry category",
  "niche": "Specific market niche",
  "main_product_or_service": "Core offering",
  "features": ["feature 1", "feature 2"],
  "problems_solved": ["problem 1", "problem 2"],
  "customer_outcomes": ["outcome 1", "outcome 2"],
  "icp": "Ideal customer profile",
  "target_industries": ["industry 1"],
  "target_roles": ["role 1", "role 2"],
  "customer_demographics": ["demographics"],
  "customer_frustrations": ["frustration 1", "frustration 2"],
  "competitors_and_alternatives": ["competitor 1", "competitor 2"],
  "unique_selling_points": ["usp 1"],
  "pricing_info": "pricing summary or N/A",
  "geographic_market": "Global",
  "trigger_events": ["trigger 1", "trigger 2"],
  "facts": [
    {{
      "claim": "Direct claim from description",
      "source_url": "user_input",
      "category": "feature|problem"
    }}
  ],
  "inferences": [
    {{
      "insight": "AI inference about ICP",
      "confidence": 0.85,
      "basis": "Inferred from description"
    }}
  ]
}}
"""
        data = self.llm.complete_json(prompt, system_prompt="You extract business profile data into strict JSON.")
        return self._build_profile_from_data(data, url=None, manual_desc=description)

    # ── Helpers ──

    def _clean_url(self, raw: str) -> str:
        s = raw.strip()
        if not s.startswith("http://") and not s.startswith("https://"):
            s = "https://" + s
        return normalize_public_http_url(s)

    def _crawl_site(self, root_url: str) -> Dict[str, str]:
        """Fetch root page and key priority subpages."""
        pages: Dict[str, str] = {}
        headers = {"User-Agent": _USER_AGENT}

        try:
            resp = requests.get(root_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                pages[root_url] = self._extract_clean_text(soup)

                # Find subpages
                discovered_links = self._find_priority_links(root_url, soup)
                for link in discovered_links[:4]:  # Crawl up to 4 priority subpages
                    try:
                        sub_resp = requests.get(link, headers=headers, timeout=8)
                        if sub_resp.status_code == 200:
                            sub_soup = BeautifulSoup(sub_resp.text, "html.parser")
                            pages[link] = self._extract_clean_text(sub_soup)
                    except Exception:
                        continue
        except Exception:
            # Fallback if live fetch fails
            pages[root_url] = f"Website homepage: {root_url}"

        return pages

    def _find_priority_links(self, root_url: str, soup: BeautifulSoup) -> List[str]:
        base_domain = urllib.parse.urlparse(root_url).netloc
        found = set()
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            full_url = urllib.parse.urljoin(root_url, href)
            parsed = urllib.parse.urlparse(full_url)
            if parsed.netloc == base_domain:
                path = parsed.path.lower()
                for prio in PRIORITY_PATHS:
                    if prio in path and full_url != root_url:
                        found.add(full_url)
                        break
        return list(found)

    def _extract_clean_text(self, soup: BeautifulSoup) -> str:
        for element in soup(["script", "style", "nav", "footer", "noscript", "svg"]):
            element.extract()
        text = soup.get_text(separator=" ", strip=True)
        # Collapse whitespace
        return re.sub(r"\s+", " ", text)

    def _build_profile_from_data(
        self,
        data: Dict[str, Any],
        url: Optional[str] = None,
        manual_desc: Optional[str] = None,
    ) -> BusinessProfile:
        facts = [
            FactItem(
                claim=f.get("claim", ""),
                source_url=f.get("source_url", url or "user_input"),
                category=f.get("category", "general"),
            )
            for f in data.get("facts", [])
            if isinstance(f, dict) and f.get("claim")
        ]
        inferences = [
            InferenceItem(
                insight=i.get("insight", ""),
                confidence=float(i.get("confidence", 0.8)),
                basis=i.get("basis", ""),
            )
            for i in data.get("inferences", [])
            if isinstance(i, dict) and i.get("insight")
        ]

        return BusinessProfile(
            name=data.get("name", "My Product"),
            url=url,
            description=manual_desc or data.get("main_product_or_service", ""),
            industry=data.get("industry", "Technology"),
            niche=data.get("niche", "SaaS"),
            main_product_or_service=data.get("main_product_or_service", ""),
            features=data.get("features", []),
            problems_solved=data.get("problems_solved", []),
            customer_outcomes=data.get("customer_outcomes", []),
            icp=data.get("icp", ""),
            target_industries=data.get("target_industries", []),
            target_roles=data.get("target_roles", []),
            customer_demographics=data.get("customer_demographics", []),
            customer_frustrations=data.get("customer_frustrations", []),
            competitors_and_alternatives=data.get("competitors_and_alternatives", []),
            unique_selling_points=data.get("unique_selling_points", []),
            pricing_info=data.get("pricing_info"),
            geographic_market=data.get("geographic_market", "Global"),
            trigger_events=data.get("trigger_events", []),
            facts=facts,
            inferences=inferences,
            confirmed=False,
        )

