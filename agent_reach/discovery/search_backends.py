# -*- coding: utf-8 -*-
"""Web search backends for the harvester.

Order of use: keyed providers the owner configured (Serper, Brave, Tavily), then
Exa's free hosted endpoint, then DuckDuckGo's HTML page. The first backend that
returns results wins. Every backend returns dicts with the keys title, url,
text, published_at and author.

Request and response shapes follow each vendor's public API docs. Keyed
providers were not called live while this module was written, so the unit tests
use recorded response shapes. Run `agent-reach discovery check search` to test
your keys.
"""

from __future__ import annotations

import datetime
import json
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


_EXA_MCP = "https://mcp.exa.ai/mcp"
_EXA_HEADER_RE = re.compile(r"^(Title|URL|Published|Author):\s*(.*)$")
_EXA_MAX_BYTES = 2 * 1024 * 1024


def parse_exa_text(text: str) -> List[Dict[str, Any]]:
    """Split Exa's `Title: / URL: / Published: / Author:` blocks into search items."""
    items: List[Dict[str, Any]] = []
    for block in re.split(r"\n(?=Title: )", "\n" + (text or "").strip()):
        block = block.strip()
        if not block.startswith("Title:"):
            continue
        fields: Dict[str, str] = {}
        lines = block.splitlines()
        i = 0
        while i < len(lines):
            m = _EXA_HEADER_RE.match(lines[i])
            if not m:
                break
            fields[m.group(1).lower()] = m.group(2).strip()
            i += 1
        body = [ln for ln in lines[i:] if ln.strip() not in ("Highlights:", "Text:")]

        def clean(value: Optional[str]) -> Optional[str]:
            return None if value in (None, "", "N/A") else value

        url = clean(fields.get("url"))
        if not url:
            continue
        items.append({
            "title": clean(fields.get("title")) or "",
            "url": url,
            "text": "\n".join(body).strip(),
            "published_at": parse_date(clean(fields.get("published"))),
            "author": clean(fields.get("author")),
        })
    return items


class ExaSearch(SearchBackend):
    """Exa's free hosted MCP endpoint. It needs no key and rate limits quickly."""

    name = "exa"

    def search(self, query, limit, days=None):
        body = {
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "web_search_exa", "arguments": {"query": query, "objective": query, "numResults": limit}},
        }
        resp = self.session.post(
            _EXA_MCP, json=body, timeout=12,
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream", "User-Agent": USER_AGENT},
        )
        if resp.status_code == 429:
            raise requests.HTTPError("exa rate limited (http 429)")
        if resp.status_code != 200:
            raise requests.HTTPError(f"exa http {resp.status_code}")
        if len(resp.content) > _EXA_MAX_BYTES:
            raise requests.HTTPError("exa response too large")
        text = resp.content.decode("utf-8", errors="replace")
        payloads = [ln[5:].strip() for ln in text.splitlines() if ln.startswith("data:")] or [text]
        try:
            msg = json.loads(payloads[-1])
        except ValueError as exc:
            raise requests.HTTPError("exa returned a body that is not JSON") from exc
        if "error" in msg:
            raise requests.HTTPError(f"exa: {str((msg['error'] or {}).get('message', msg['error']))[:200]}")
        result = msg.get("result") or {}
        if result.get("isError"):
            raise requests.HTTPError("exa tool error")
        content = "\n".join(c.get("text", "") for c in result.get("content", []) if c.get("type") == "text")
        return parse_exa_text(content)[:limit]


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
