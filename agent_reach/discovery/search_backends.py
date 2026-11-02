# -*- coding: utf-8 -*-
"""Web search backends for the harvester.

Order of use: keyed providers the owner configured (Serper, Brave, Tavily), then
Exa's free hosted endpoint, then DuckDuckGo's HTML page. The first backend that
returns results wins. Every backend returns dicts with the keys title, url,
text, published_at and author.

Request and response shapes follow each vendor's public API docs. Keyed
providers were not called live while this module was written, so the unit tests
use recorded response shapes. Run `agent-reach discovery search-check` to test
your keys.
"""

from __future__ import annotations

import datetime
import logging
import os
import re
import urllib.parse
from collections import Counter
from typing import Any, Dict, List, Optional

import requests

log = logging.getLogger("agent_reach.discovery")

USER_AGENT = "Mozilla/5.0 (compatible; AgentReachLeadAgent/2.2)"
_TAG_RE = re.compile(r"<[^>]+>")
_DATE_FORMATS = ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%b %d, %Y", "%B %d, %Y", "%d %b %Y")
_REL_RE = re.compile(r"(\d+)\s+(minute|hour|day|week|month|year)s?\s+ago", re.I)


def parse_date(raw: Optional[str], now: Optional[datetime.date] = None) -> Optional[str]:
    """Best effort. Returns an ISO date string or None."""
    if not raw:
        return None
    text = str(raw).strip()
    today = now or datetime.date.today()
    rel = _REL_RE.search(text)
    if rel:
        n, unit = int(rel.group(1)), rel.group(2).lower()
        days = {"minute": 0, "hour": 0, "day": n, "week": 7 * n, "month": 30 * n, "year": 365 * n}[unit]
        return (today - datetime.timedelta(days=days)).isoformat()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.datetime.strptime(text[:len(text)], fmt).date().isoformat()
        except ValueError:
            continue
    iso = re.match(r"(\d{4}-\d{2}-\d{2})", text)
    return iso.group(1) if iso else None


def _freshness_days(days: Optional[int]) -> str:
    if not days:
        return "py"
    if days <= 1:
        return "pd"
    if days <= 7:
        return "pw"
    if days <= 31:
        return "pm"
    return "py"


class SearchBackend:
    name = "base"

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()

    def available(self) -> bool:
        return True

    def search(self, query: str, limit: int, days: Optional[int] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError


class SerperSearch(SearchBackend):
    name = "serper"

    def available(self) -> bool:
        return bool(os.getenv("SERPER_API_KEY"))

    def search(self, query, limit, days=None):
        payload: Dict[str, Any] = {"q": query, "num": min(limit, 20)}
        if days:
            payload["tbs"] = "qdr:d" if days <= 1 else "qdr:w" if days <= 7 else "qdr:m" if days <= 31 else "qdr:y"
        resp = self.session.post(
            "https://google.serper.dev/search",
            json=payload,
            headers={"X-API-KEY": os.getenv("SERPER_API_KEY", ""), "Content-Type": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("link", ""),
                "text": r.get("snippet", ""),
                "published_at": parse_date(r.get("date")),
                "author": None,
            }
            for r in (resp.json().get("organic") or [])
            if r.get("link")
        ][:limit]


class BraveSearch(SearchBackend):
    name = "brave"

    def available(self) -> bool:
        return bool(os.getenv("BRAVE_API_KEY"))

    def search(self, query, limit, days=None):
        resp = self.session.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": min(limit, 20), "freshness": _freshness_days(days)},
            headers={"X-Subscription-Token": os.getenv("BRAVE_API_KEY", ""), "Accept": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        results = (resp.json().get("web") or {}).get("results") or []
        return [
            {
                "title": _TAG_RE.sub("", r.get("title", "")),
                "url": r.get("url", ""),
                "text": _TAG_RE.sub("", r.get("description", "")),
                "published_at": parse_date(r.get("page_age") or r.get("age")),
                "author": None,
            }
            for r in results
            if r.get("url")
        ][:limit]


class TavilySearch(SearchBackend):
    name = "tavily"

    def available(self) -> bool:
        return bool(os.getenv("TAVILY_API_KEY"))

    def search(self, query, limit, days=None):
        payload: Dict[str, Any] = {"query": query, "max_results": min(limit, 20), "search_depth": "basic"}
        if days:
            payload["time_range"] = "day" if days <= 1 else "week" if days <= 7 else "month" if days <= 31 else "year"
        resp = self.session.post(
            "https://api.tavily.com/search",
            json=payload,
            headers={"Authorization": f"Bearer {os.getenv('TAVILY_API_KEY', '')}", "Content-Type": "application/json"},
            timeout=20,
        )
        resp.raise_for_status()
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "text": r.get("content", ""),
                "published_at": parse_date(r.get("published_date")),
                "author": None,
            }
            for r in (resp.json().get("results") or [])
            if r.get("url")
        ][:limit]


class ExaSearch(SearchBackend):
    name = "exa"

    def search(self, query, limit, days=None):
        from agent_reach.channels.web import WebChannel

        return WebChannel()._exa_search(query=query, limit=limit, timeout=12) or []


class DuckDuckGoSearch(SearchBackend):
    name = "duckduckgo"
    _PATTERN = re.compile(
        r'<h2 class="result__title">\s*<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>\s*</h2>'
        r'.*?<a class="result__snippet"[^>]*>(.*?)</a>',
        re.DOTALL,
    )

    def search(self, query, limit, days=None):
        resp = self.session.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        if resp.status_code != 200:
            raise requests.HTTPError(f"duckduckgo http {resp.status_code}")
        items: List[Dict[str, Any]] = []
        for m in self._PATTERN.finditer(resp.text):
            uddg = re.search(r"uddg=([^&]+)", m.group(1))
            items.append({
                "title": _TAG_RE.sub("", m.group(2)).strip(),
                "url": urllib.parse.unquote(uddg.group(1)) if uddg else m.group(1),
                "text": _TAG_RE.sub("", m.group(3)).strip(),
                "published_at": None,
                "author": None,
            })
            if len(items) >= limit:
                break
        return items


class SearchChain:
    """Try backends in order. Count failures in `diagnostics`."""

    def __init__(self, session: Optional[requests.Session] = None, diagnostics: Optional[Counter] = None):
        self.session = session or requests.Session()
        self.diagnostics = diagnostics if diagnostics is not None else Counter()
        self.backends: List[SearchBackend] = [
            b for b in (
                SerperSearch(self.session), BraveSearch(self.session), TavilySearch(self.session),
                ExaSearch(self.session), DuckDuckGoSearch(self.session),
            ) if b.available()
        ]

    def search(self, query: str, limit: int, days: Optional[int] = None) -> List[Dict[str, Any]]:
        for backend in self.backends:
            try:
                results = backend.search(query, limit, days)
            except Exception as exc:  # each backend fails in its own way
                log.warning("search backend %s failed: %s %s", backend.name, type(exc).__name__, str(exc)[:160])
                self.diagnostics[f"search_error:{backend.name}"] += 1
                continue
            if results:
                self.diagnostics[f"search_ok:{backend.name}"] += 1
                return results
        self.diagnostics["search_empty"] += 1
        return []
