# -*- coding: utf-8 -*-
"""Business Understanding Engine for analyzing websites and manual product descriptions."""

from __future__ import annotations

import ipaddress
import logging
import re
import socket
import urllib.parse
from typing import Any, Dict, List, Optional, Set

import requests
from bs4 import BeautifulSoup

from agent_reach.discovery import skillpack
from agent_reach.discovery.llm_client import LLMClient
from agent_reach.discovery.models import (
    BusinessProfile,
    FactItem,
    InferenceItem,
)
from agent_reach.discovery.security import injection_flags, sanitize
from agent_reach.utils.url import create_safe_session, normalize_public_http_url

log = logging.getLogger("agent_reach.discovery")

# Crawl order matters. Pages that name customers and problems come first.
PRIORITY_PATHS = [
    "/use-cases",
    "/solutions",
    "/features",
    "/product",
    "/customers",
    "/case-studies",
    "/pricing",
    "/about",
    "/faq",
]
_MAX_PAGE_BYTES = 1_500_000
_MIN_USABLE_TEXT = 200

_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


class BusinessEngine:
    """Extracts verified facts, ICP, and problems from business websites or manual descriptions."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = (llm_client or LLMClient()).for_tier("smart")

    SCHEMA = """{
  "name": "Product or business name",
  "industry": "Industry category, or empty",
  "niche": "Narrow market niche",
  "main_product_or_service": "One line on the core offering",
  "features": [],
  "problems_solved": ["3 to 7 problems, in the customer's words"],
  "customer_outcomes": [],
  "icp": "Role, size or stage, situation, trigger in one sentence",
  "target_industries": [],
  "target_roles": [],
  "customer_demographics": [],
  "customer_frustrations": [],
  "pain_vocabulary": ["8 to 15 short phrases a customer types, no product names"],
  "competitors_and_alternatives": [],
  "not_for": ["3 to 6 kinds of people who should not become leads"],
  "unique_selling_points": [],
  "pricing_info": "what a page states, otherwise not stated",
  "geographic_market": "Global or a region",
  "trigger_events": [],
  "facts": [{"claim": "...", "source_url": "a listed page URL or user_input", "category": "feature|pricing|company|icp|problem"}],
  "inferences": [{"insight": "...", "confidence": 0.0, "basis": "..."}]
}"""

    def _system(self) -> str:
        return skillpack.prompt("business-intelligence")

    def analyze_website(self, url: str) -> BusinessProfile:
        """Crawl homepage and priority subpages, extracting structured business profile."""
        clean_url = self._clean_url(url)
        page_contents = self._crawl_site(clean_url)  # raises ValueError when the site is unreadable

        # Aggregate scraped text with URL references
        combined_text_blocks = []
        for page_url, text in page_contents.items():
            trimmed = text[:3000].strip()
            if trimmed:
                combined_text_blocks.append(f"--- SOURCE PAGE: {page_url} ---\n{trimmed}")

        scraped_corpus = "\n\n".join(combined_text_blocks)

        flags = injection_flags(scraped_corpus)
        listed = "\n".join(f"- {u}" for u in page_contents)
        prompt = f"""
Build the profile for the website {clean_url}.

Pages you may cite as source_url:
{listed}

<untrusted_scraped_corpus>
{sanitize(scraped_corpus, 16000)}
</untrusted_scraped_corpus>

Output one JSON object with this schema:
{self.SCHEMA}
"""
        data = self.llm.complete_json(prompt, system_prompt=self._system())
        profile = self._build_profile_from_data(data, url=clean_url, known_pages=set(page_contents))
        if flags:
            profile.inferences.append(InferenceItem(
                insight="The website text contains instruction-like phrases. The analysis ignored them.",
                confidence=0.9, basis="Pattern check found: " + ", ".join(flags),
            ))
        return profile

    def analyze_manual_description(self, description: str, name: Optional[str] = None) -> BusinessProfile:
        """Extract structured business profile from a user-supplied product/service description."""
        flags = injection_flags(description)
        prompt = f"""
Build the profile for a product the founder describes by hand. Business name: {sanitize(name or "unspecified", 120)}

<untrusted_description>
{sanitize(description, 8000)}
</untrusted_description>

Every fact uses source_url "user_input".

Output one JSON object with this schema:
{self.SCHEMA}
"""
        data = self.llm.complete_json(prompt, system_prompt=self._system())
        if name and not data.get("name"):
            data["name"] = name
        profile = self._build_profile_from_data(data, url=None, manual_desc=description)
        if name:
            profile.name = name
        if flags:
            profile.inferences.append(InferenceItem(
                insight="The description contains instruction-like phrases. The analysis ignored them.",
                confidence=0.9, basis="Pattern check found: " + ", ".join(flags),
            ))
        return profile

    # ── Helpers ──

    def _clean_url(self, raw: str) -> str:
        s = raw.strip()
        if not s.startswith("http://") and not s.startswith("https://"):
            s = "https://" + s
        return normalize_public_http_url(s)

    @staticmethod
    def _assert_public_host(url: str) -> None:
        """Resolve the host and reject private, loopback or link-local addresses.

        normalize_public_http_url only checks literal IPs. A hostname that
        resolves to 127.0.0.1 or 169.254.169.254 would pass it.
        """
        host = urllib.parse.urlsplit(url).hostname or ""
        try:
            infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
        except socket.gaierror as exc:
            raise ValueError(f"Cannot resolve host {host}.") from exc
        for info in infos:
            if not ipaddress.ip_address(info[4][0]).is_global:
                raise ValueError("Only public websites are allowed.")

    def _safe_fetch(self, target_url: str, headers: Dict[str, str], timeout: float = 10) -> Optional[str]:
        """Fetch page text with SSRF checks on every redirect hop and a size cap."""
        current_url = normalize_public_http_url(target_url)
        session = create_safe_session()
        for _ in range(4):
            try:
                self._assert_public_host(current_url)
                with session.get(
                    current_url, headers=headers, timeout=timeout, allow_redirects=False, stream=True
                ) as resp:
                    if resp.status_code in (301, 302, 303, 307, 308):
                        location = resp.headers.get("Location")
                        if not location:
                            return None
                        current_url = normalize_public_http_url(urllib.parse.urljoin(current_url, location))
                        continue
                    if resp.status_code != 200:
                        return None
                    if "html" not in resp.headers.get("Content-Type", "html").lower():
                        return None
                    raw = b""
                    for chunk in resp.iter_content(65536):
                        raw += chunk
                        if len(raw) > _MAX_PAGE_BYTES:
                            break
                    return raw.decode(resp.encoding or "utf-8", errors="replace")
            except ValueError:
                raise
            except requests.RequestException as exc:
                log.warning("fetch failed for %s: %s", current_url, type(exc).__name__)
                return None
        return None

    def _crawl_site(self, root_url: str) -> Dict[str, str]:
        """Fetch root page and key priority subpages safely."""
        pages: Dict[str, str] = {}
        headers = {"User-Agent": _USER_AGENT}

        html_text = self._safe_fetch(root_url, headers=headers, timeout=10)
        if html_text:
            soup = BeautifulSoup(html_text, "html.parser")
            links = self._find_priority_links(root_url, soup)
            pages[root_url] = self._meta_text(soup) + self._extract_clean_text(soup)
            for link in links[:4]:  # up to 4 priority subpages
                try:
                    sub_html = self._safe_fetch(link, headers=headers, timeout=8)
                except ValueError:
                    continue
                if sub_html:
                    sub_soup = BeautifulSoup(sub_html, "html.parser")
                    pages[link] = self._meta_text(sub_soup) + self._extract_clean_text(sub_soup)

        if sum(len(t) for t in pages.values()) < _MIN_USABLE_TEXT:
            # Never ask the model to describe a site it could not read. It would invent one.
            raise ValueError(
                "Could not read enough text from that website. It may need JavaScript to render. "
                "Paste a product description instead."
            )
        return pages

    def _find_priority_links(self, root_url: str, soup: BeautifulSoup) -> List[str]:
        base_domain = urllib.parse.urlparse(root_url).netloc
        ranked: Dict[str, int] = {}
        for a in soup.find_all("a", href=True):
            full_url = urllib.parse.urljoin(root_url, str(a["href"]).strip()).split("#")[0]
            parsed = urllib.parse.urlparse(full_url)
            if parsed.netloc != base_domain or full_url.rstrip("/") == root_url.rstrip("/"):
                continue
            path = parsed.path.lower()
            for rank, prio in enumerate(PRIORITY_PATHS):
                if prio in path:
                    ranked[full_url] = min(rank, ranked.get(full_url, rank))
                    break
        # Sorted, so two runs crawl the same pages.
        return [u for u, _ in sorted(ranked.items(), key=lambda kv: (kv[1], kv[0]))]

    @staticmethod
    def _meta_text(soup: BeautifulSoup) -> str:
        """Title and meta description usually state the offer in one line."""
        parts: List[str] = []
        if soup.title and soup.title.string:
            parts.append(f"Title: {str(soup.title.string).strip()}.")
        wanted: List[Dict[str, Any]] = [{"name": "description"}, {"property": "og:description"}]
        for attrs in wanted:
            tag = soup.find("meta", attrs=attrs)
            if tag and tag.get("content"):
                parts.append(f"Description: {str(tag['content']).strip()}.")
                break
        return (" ".join(parts) + " ") if parts else ""

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
        known_pages: Optional[Set[str]] = None,
    ) -> BusinessProfile:
        def as_list(key: str) -> List[str]:
            raw = data.get(key) or []
            return [str(x).strip() for x in raw if str(x).strip()] if isinstance(raw, list) else []

        def as_conf(value: Any) -> float:
            try:
                return max(0.0, min(1.0, float(value)))
            except (TypeError, ValueError):
                return 0.5

        facts = [
            FactItem(
                claim=str(f.get("claim", "")),
                # The model may invent a source. Keep only URLs we really crawled.
                source_url=(
                    f.get("source_url")
                    if (not url or f.get("source_url") in (known_pages or {url}))
                    else (url or "user_input")
                ) or (url or "user_input"),
                category=str(f.get("category", "general")),
            )
            for f in (data.get("facts") or [])
            if isinstance(f, dict) and f.get("claim")
        ]
        inferences = [
            InferenceItem(
                insight=str(i.get("insight", "")),
                confidence=as_conf(i.get("confidence", 0.5)),
                basis=str(i.get("basis", "")),
            )
            for i in (data.get("inferences") or [])
            if isinstance(i, dict) and i.get("insight") and as_conf(i.get("confidence", 0.5)) >= 0.3
        ]
        vocab = [v for v in as_list("pain_vocabulary") if 2 <= len(v.split()) <= 12]
        if not vocab:
            # Fall back to the frustration phrases. Search then still has customer words.
            vocab = [f for f in as_list("customer_frustrations") if len(f.split()) <= 12][:8]
        if not as_list("problems_solved"):
            raise ValueError(
                "The analysis found no problems this product solves. Add more detail to the description."
            )

        return BusinessProfile(
            name=str(data.get("name") or "My Product"),
            url=url,
            description=manual_desc or data.get("main_product_or_service", ""),
            industry=str(data.get("industry") or ""),
            niche=str(data.get("niche") or ""),
            main_product_or_service=str(data.get("main_product_or_service") or ""),
            features=as_list("features"),
            problems_solved=as_list("problems_solved"),
            customer_outcomes=as_list("customer_outcomes"),
            icp=str(data.get("icp", "")),
            target_industries=as_list("target_industries"),
            target_roles=as_list("target_roles"),
            customer_demographics=as_list("customer_demographics"),
            customer_frustrations=as_list("customer_frustrations"),
            pain_vocabulary=vocab,
            not_for=as_list("not_for"),
            competitors_and_alternatives=as_list("competitors_and_alternatives"),
            unique_selling_points=as_list("unique_selling_points"),
            pricing_info=data.get("pricing_info"),
            geographic_market=str(data.get("geographic_market") or "Global"),
            trigger_events=as_list("trigger_events"),
            facts=facts,
            inferences=inferences,
            confirmed=False,
        )

