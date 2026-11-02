# -*- coding: utf-8 -*-
"""Linked accounts: the owner's own established accounts.

The app stores a handle and a posting mode. It never stores a password or a
cookie. It reads public profile data to compute account health (age, karma,
product mention share) and to import voice samples from the owner's own
comments. Posting stays manual unless the owner configures approved API
credentials in the environment.
"""

from __future__ import annotations

import datetime
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import requests

from agent_reach.discovery.models import LinkedAccount
from agent_reach.discovery.storage import DiscoveryStorage
from agent_reach.discovery.thread_check import USER_AGENT

log = logging.getLogger("agent_reach.discovery")

SUPPORTED = ("reddit", "github", "hackernews", "twitter", "quora", "web")
_HANDLE_RE = {
    "reddit": re.compile(r"^[A-Za-z0-9_-]{3,20}$"),
    "github": re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$"),
    "hackernews": re.compile(r"^[A-Za-z0-9_-]{2,15}$"),
    "twitter": re.compile(r"^[A-Za-z0-9_]{1,15}$"),
    "quora": re.compile(r"^[A-Za-z0-9_-]{2,60}$"),
    "web": re.compile(r"^[\w.@-]{1,80}$"),
}
SETTINGS_KEY = "linked_accounts"


class AccountError(ValueError):
    """Bad platform, bad handle or an unreachable account."""


@dataclass
class AccountHealth:
    """What an account may do. Thresholds are the app's own defaults."""
    stage: int
    stage_name: str
    max_pitch_level: int
    suggested_daily_cap: int
    reasons: List[str] = field(default_factory=list)
    known: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "stage_name": self.stage_name,
            "max_pitch_level": self.max_pitch_level,
            "suggested_daily_cap": self.suggested_daily_cap,
            "reasons": self.reasons,
            "known": self.known,
        }


_STAGES = [
    (0, "build", 0, 2),
    (1, "trusted", 1, 3),
    (2, "established", 2, 5),
    (3, "veteran", 3, 5),
]


def compute_health(snapshot: Dict[str, Any], product_name: str = "", platform: str = "reddit") -> AccountHealth:
    """Map an account snapshot to a stage. Unknown data gives the safest stage."""
    if not snapshot or snapshot.get("error") or snapshot.get("supported") is False:
        return AccountHealth(0, "unknown", 0, 2, ["No readable account data. Use pitch level 0 until you refresh the account."], known=False)
    age = snapshot.get("age_days")
    karma = snapshot.get("comment_karma")
    reasons: List[str] = []
    if platform != "reddit":
        # Other platforms give age only. Use age for the stage and cap at level 2.
        if age is None:
            return AccountHealth(0, "unknown", 0, 2, ["Account age unknown."], known=False)
        stage = 2 if age >= 90 else 1 if age >= 30 else 0
        reasons.append(f"Account is {age} days old.")
        return AccountHealth(stage, _STAGES[stage][1], min(_STAGES[stage][2], 2), _STAGES[stage][3], reasons)
    if age is None or karma is None:
        return AccountHealth(0, "unknown", 0, 2, ["Reddit did not return age or karma."], known=False)
    stage = 0
    if age >= 30 and karma >= 100:
        stage = 1
    if age >= 90 and karma >= 300:
        stage = 2
    if age >= 180 and karma >= 500:
        stage = 3
    reasons.append(f"Account is {age} days old with {karma} comment karma.")
    ratio = snapshot.get("recent_mention_ratio")
    if product_name and ratio is not None and ratio > 0.10 and stage > 0:
        stage -= 1
        reasons.append(f"{int(ratio * 100)}% of recent comments name the product. Dropped one stage.")
    name, level, cap = _STAGES[stage][1], _STAGES[stage][2], _STAGES[stage][3]
    return AccountHealth(stage, name, level, cap, reasons)


def _days_since(ts: Optional[float]) -> Optional[int]:
    if not ts:
        return None
    return int((time.time() - float(ts)) // 86400)


def _iso_days(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    try:
        day = datetime.date.fromisoformat(text[:10])
    except ValueError:
        return None
    return (datetime.date.today() - day).days


class AccountService:
    """Link accounts, read public data, import voice samples."""

    def __init__(self, storage: Optional[DiscoveryStorage] = None, session: Optional[requests.Session] = None):
        self.storage = storage or DiscoveryStorage()
        self.session = session or requests.Session()

    # ── Storage ──

    def list(self) -> List[LinkedAccount]:
        raw = self.storage.get_setting(SETTINGS_KEY, []) or []
        out = []
        for item in raw:
            try:
                out.append(LinkedAccount.model_validate(item))
            except Exception:
                continue
        return out

    def _save(self, accounts: List[LinkedAccount]) -> None:
        self.storage.set_setting(SETTINGS_KEY, [a.model_dump() for a in accounts])

    def get(self, platform: str, handle: Optional[str] = None) -> Optional[LinkedAccount]:
        for acc in self.list():
            if acc.platform == platform and (handle is None or acc.handle.lower() == handle.lower()):
                return acc
        return None

    @staticmethod
    def clean_handle(platform: str, handle: str) -> str:
        platform = (platform or "").lower()
        if platform not in SUPPORTED:
            raise AccountError(f"Unsupported platform '{platform}'. Use one of: {', '.join(SUPPORTED)}.")
        h = (handle or "").strip()
        h = re.sub(r"^(?:https?://)?(?:www\.|old\.)?(?:reddit\.com/(?:user|u)/|github\.com/|x\.com/|twitter\.com/)", "", h)
        h = h.strip("/@ ").removeprefix("u/")
        if not _HANDLE_RE[platform].match(h):
            raise AccountError(f"'{handle}' is not a valid {platform} handle.")
        return h

    def link(self, platform: str, handle: str, mode: str = "manual") -> LinkedAccount:
        platform = platform.lower()
        h = self.clean_handle(platform, handle)
        if mode not in ("manual", "api"):
            raise AccountError("mode must be 'manual' or 'api'.")
        accounts = [a for a in self.list() if not (a.platform == platform and a.handle.lower() == h.lower())]
        acc = LinkedAccount(platform=platform, handle=h, mode=mode)  # type: ignore[arg-type]
        accounts.append(acc)
        self._save(accounts)
        return acc

    def unlink(self, platform: str, handle: str) -> bool:
        before = self.list()
        after = [a for a in before if not (a.platform == platform.lower() and a.handle.lower() == handle.lower().lstrip("@"))]
        self._save(after)
        return len(after) < len(before)

    # ── Public data ──

    def _get_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Any], str]:
        try:
            resp = self.session.get(url, params=params, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, timeout=12)
        except requests.RequestException as exc:
            return None, f"request failed: {type(exc).__name__}"
        if resp.status_code != 200:
            return None, f"http {resp.status_code}"
        try:
            return resp.json(), ""
        except ValueError:
            return None, "not json"

    def fetch_reddit(self, handle: str, product_name: str = "") -> Tuple[Dict[str, Any], List[str]]:
        """Return (snapshot, comment_bodies). Public JSON only. Reddit may block it."""
        about, err = self._get_json(f"https://www.reddit.com/user/{handle}/about.json", {"raw_json": 1})
        if not about:
            return {"error": f"Reddit about.json: {err}"}, []
        data = about.get("data") or {}
        snap: Dict[str, Any] = {
            "supported": True,
            "created_utc": data.get("created_utc"),
            "age_days": _days_since(data.get("created_utc")),
            "comment_karma": int(data.get("comment_karma") or 0),
            "link_karma": int(data.get("link_karma") or 0),
            "is_suspended": bool(data.get("is_suspended")),
        }
        listing, err2 = self._get_json(
            f"https://www.reddit.com/user/{handle}/comments.json", {"limit": 100, "raw_json": 1, "sort": "new"}
        )
        bodies: List[str] = []
        subs: Dict[str, int] = {}
        if listing:
            for child in (listing.get("data") or {}).get("children", []):
                d = child.get("data") or {}
                body = (d.get("body") or "").strip()
                if not body or body in ("[removed]", "[deleted]"):
                    continue
                bodies.append(body)
                subs[d.get("subreddit", "")] = subs.get(d.get("subreddit", ""), 0) + 1
        else:
            snap["comments_error"] = err2
        snap["recent_comment_count"] = len(bodies)
        snap["top_subreddits"] = sorted(subs, key=lambda k: -subs[k])[:6]
        if product_name and bodies:
            hits = sum(1 for b in bodies if re.search(rf"\b{re.escape(product_name)}\b", b, re.I))
            snap["recent_mention_ratio"] = round(hits / len(bodies), 3)
        return snap, bodies

    def fetch_github(self, handle: str) -> Tuple[Dict[str, Any], List[str]]:
        user, err = self._get_json(f"https://api.github.com/users/{handle}")
        if not user:
            return {"error": f"GitHub users API: {err}"}, []
        snap = {
            "supported": True,
            "age_days": _iso_days(user.get("created_at")),
            "public_repos": user.get("public_repos"),
            "followers": user.get("followers"),
        }
        events, _ = self._get_json(f"https://api.github.com/users/{handle}/events/public", {"per_page": 100})
        bodies = []
        for ev in events or []:
            if ev.get("type") == "IssueCommentEvent":
                body = ((ev.get("payload") or {}).get("comment") or {}).get("body") or ""
                if body.strip():
                    bodies.append(body.strip())
        return snap, bodies

    def fetch_hackernews(self, handle: str) -> Tuple[Dict[str, Any], List[str]]:
        user, err = self._get_json(f"https://hacker-news.firebaseio.com/v0/user/{handle}.json")
        if not user:
            return {"error": f"HN user API: {err or 'not found'}"}, []
        return {"supported": True, "age_days": _days_since(user.get("created")), "karma": user.get("karma")}, []

    def refresh(self, platform: str, handle: str, product_name: str = "") -> LinkedAccount:
        """Fetch public data for a linked account and store the snapshot."""
        acc = self.get(platform, handle)
        if acc is None:
            raise AccountError(f"{platform}/{handle} is not linked. Link it first.")
        snap, _ = self._fetch(acc, product_name)
        acc.snapshot, acc.snapshot_at = snap, time.time()
        self._replace(acc)
        return acc

    def _fetch(self, acc: LinkedAccount, product_name: str = "") -> Tuple[Dict[str, Any], List[str]]:
        if acc.platform == "reddit":
            return self.fetch_reddit(acc.handle, product_name)
        if acc.platform == "github":
            return self.fetch_github(acc.handle)
        if acc.platform == "hackernews":
            return self.fetch_hackernews(acc.handle)
        return {"supported": False, "note": f"{acc.platform} has no public history API. Paste samples by hand."}, []

    def _replace(self, acc: LinkedAccount) -> None:
        accounts = [a for a in self.list() if not (a.platform == acc.platform and a.handle.lower() == acc.handle.lower())]
        accounts.append(acc)
        self._save(accounts)

    def import_voice_samples(self, platform: str, handle: str, limit: int = 40) -> List[str]:
        """Return up to `limit` of the owner's own comments, filtered for style value."""
        acc = self.get(platform, handle)
        if acc is None:
            raise AccountError(f"{platform}/{handle} is not linked. Link it first.")
        snap, bodies = self._fetch(acc)
        samples = filter_samples(bodies)[:limit]
        acc.voice_imported_at = time.time()
        if snap and not snap.get("error"):
            acc.snapshot, acc.snapshot_at = snap, time.time()
        self._replace(acc)
        return samples

    def health(self, platform: str, handle: Optional[str] = None, product_name: str = "") -> AccountHealth:
        acc = self.get(platform, handle)
        if acc is None:
            return AccountHealth(0, "unlinked", 0, 2, ["No linked account for this platform. Link one for a real health check."], known=False)
        return compute_health(acc.snapshot, product_name, acc.platform)


def filter_samples(bodies: List[str]) -> List[str]:
    """Drop quotes, link-heavy and tiny comments. Keep first-person prose of 12 words or more."""
    out: List[str] = []
    seen = set()
    for body in bodies:
        text = re.sub(r"^>.*$", "", body, flags=re.M).strip()
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        words = text.split()
        if len(words) < 12 or len(words) > 400:
            continue
        if len(re.findall(r"https?://", text)) > 1:
            continue
        key = text[:60].lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out
