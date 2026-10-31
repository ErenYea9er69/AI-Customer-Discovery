# -*- coding: utf-8 -*-
"""Publishing with hard safety limits.

Rules enforced here, in order: emergency stop, draft mode, human approval,
Reddit community whitelist, daily cap, minimum gap between posts, and a live
check that the thread is still open. Manual mode never calls a platform API. It
returns text to copy, and the reply counts as published only after the person
confirms.
"""

from __future__ import annotations

import os
import re
import time
from typing import Any, Dict, Optional, Tuple

import requests

from agent_reach.discovery.models import GeneratedReply, LeadQualification, PostingSettings
from agent_reach.discovery.storage import DiscoveryStorage
from agent_reach.discovery.thread_check import RedditMeta, judge_reddit, reddit_post_id

_GITHUB_ISSUE = re.compile(r"github\.com/([^/]+)/([^/]+)/issues/(\d+)")


def _short(err: object) -> str:
    return str(err)[:200]


class CommunityPublisher:
    """Manages compliant publishing, rate limits, emergency stops and copy fallbacks."""

    def __init__(self, storage: Optional[DiscoveryStorage] = None, session: Optional[requests.Session] = None):
        self.storage = storage or DiscoveryStorage()
        self.session = session or requests.Session()

    # ── Rules ──

    def can_publish(
        self, reply: GeneratedReply, lead: LeadQualification, settings: PostingSettings
    ) -> Tuple[bool, str]:
        if settings.emergency_stop:
            return False, "Emergency stop is active. All publishing is halted."
        if settings.mode == "draft":
            return False, "Draft mode is on. Publishing is disabled."
        if reply.status not in ("approved", "pending_manual_post"):
            return False, "Approve the reply before publishing."
        if not self._get_reply_content(reply).strip():
            return False, "The reply is empty."

        if lead.platform == "reddit" and settings.allowed_communities and lead.community:
            allowed = {c.lower().removeprefix("r/") for c in settings.allowed_communities}
            if lead.community.lower().removeprefix("r/") not in allowed:
                return False, f"{lead.community} is not in the allowed communities."

        if self.storage.count_posts_today(lead.platform) >= settings.daily_limit:
            return False, f"Daily limit of {settings.daily_limit} reached for {lead.platform}."

        last = self.storage.last_published_at(lead.platform)
        if last and settings.min_interval_seconds > 0:
            wait = int(settings.min_interval_seconds - (time.time() - last))
            if wait > 0:
                return False, f"Wait {wait} more seconds between posts on {lead.platform}."
        return True, "Ready to publish."

    # ── Publish ──

    def publish_or_copy(
        self, reply: GeneratedReply, lead: LeadQualification, settings: PostingSettings
    ) -> Dict[str, Any]:
        allowed, reason = self.can_publish(reply, lead, settings)
        if not allowed:
            self.storage.log_post(lead.id, reply.id, lead.platform, lead.url, "", settings.mode, "rejected", reason)
            return {"success": False, "reason": reason}

        content = self._final_content(reply)

        if settings.mode == "automatic":
            if lead.platform == "reddit" and self._reddit_creds(settings):
                return self._publish_reddit_api(reply, lead, content, settings)
            if lead.platform == "github" and (settings.github_token or os.getenv("GITHUB_TOKEN")):
                return self._publish_github_api(reply, lead, content, settings)

        # Manual path. Nothing is posted. The person posts it, then confirms.
        reply.status = "pending_manual_post"
        self.storage.save_reply(reply)
        self.storage.log_post(
            lead.id, reply.id, lead.platform, lead.url, content, settings.mode, "pending_manual_post"
        )
        return {
            "success": True,
            "action": "copy_and_open",
            "message": "Copy the reply, post it on the thread, then confirm.",
            "target_url": lead.url,
            "text": content,
        }

    def confirm_manual_post(self, reply: GeneratedReply, lead: LeadQualification) -> Dict[str, Any]:
        """The person says they posted the reply. Only now does it count as published."""
        if reply.status != "pending_manual_post":
            raise ValueError("Only a reply waiting for manual posting can be confirmed.")
        reply.status = "published"
        reply.published_at = time.time()
        self.storage.save_reply(reply)
        self.storage.log_post(
            lead.id, reply.id, lead.platform, lead.url, self._final_content(reply),
            "manual", "published", "Confirmed by the user",
        )
        return {"success": True, "reply": reply.model_dump()}

    # ── Content ──

    @staticmethod
    def _get_reply_content(reply: GeneratedReply) -> str:
        if reply.selected_version == "custom" or reply.edited_reply:
            return reply.edited_reply or ""
        if reply.selected_version == "product_aware":
            return reply.product_aware
        return reply.value_first

    def _final_content(self, reply: GeneratedReply) -> str:
        """Product-aware text always carries the disclosure, even after an edit."""
        text = self._get_reply_content(reply).strip()
        if reply.selected_version == "product_aware":
            low = text.lower()
            if "disclos" not in low and "affiliat" not in low:
                text = f"{text}\n\n{reply.affiliation_disclosure}"
        return text

    # ── Reddit ──

    @staticmethod
    def _reddit_creds(settings: PostingSettings) -> Optional[Dict[str, str]]:
        creds = {
            "client_id": settings.reddit_client_id or os.getenv("REDDIT_CLIENT_ID") or "",
            "client_secret": settings.reddit_client_secret or os.getenv("REDDIT_CLIENT_SECRET") or "",
            "username": settings.reddit_username or os.getenv("REDDIT_USERNAME") or "",
            "password": settings.reddit_password or os.getenv("REDDIT_PASSWORD") or "",
        }
        return creds if all(creds.values()) else None

    def _fail(self, lead, reply, content, settings, reason: str) -> Dict[str, Any]:
        self.storage.log_post(lead.id, reply.id, lead.platform, lead.url, content, settings.mode, "failed", reason)
        return {"success": False, "reason": reason, "fallback_action": "copy_and_open"}

    def _publish_reddit_api(self, reply, lead, content, settings) -> Dict[str, Any]:
        creds = self._reddit_creds(settings)
        pid = reddit_post_id(lead.url)
        if not creds or not pid:
            return self._fail(lead, reply, content, settings, "Missing Reddit credentials or post id.")
        ua = f"script:agent-reach-lead:2.1 (by /u/{creds['username']})"
        try:
            token_resp = self.session.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=(creds["client_id"], creds["client_secret"]),
                data={"grant_type": "password", "username": creds["username"], "password": creds["password"]},
                headers={"User-Agent": ua},
                timeout=10,
            )
            token = token_resp.json().get("access_token") if token_resp.status_code == 200 else None
            if not token:
                return self._fail(lead, reply, content, settings, "Reddit login failed.")

            # Check the thread is still open before spending a post.
            meta = RedditMeta(creds["client_id"], creds["client_secret"], session=self.session).fetch([pid])
            health = judge_reddit(meta.get(pid))
            if health.reject in ("archived", "locked", "removed"):
                return self._fail(lead, reply, content, settings, f"Thread is {health.reject}.")

            resp = self.session.post(
                "https://oauth.reddit.com/api/comment",
                headers={"Authorization": f"Bearer {token}", "User-Agent": ua},
                data={"api_type": "json", "thing_id": f"t3_{pid}", "text": content},
                timeout=10,
            )
            # Reddit answers 200 even when it refuses. Read the error list.
            body = resp.json() if resp.status_code == 200 else {}
            errors = (body.get("json") or {}).get("errors") or []
            if resp.status_code != 200 or errors:
                return self._fail(lead, reply, content, settings, f"Reddit refused the comment: {_short(errors or resp.status_code)}")
        except (requests.RequestException, ValueError) as exc:
            return self._fail(lead, reply, content, settings, f"Reddit request failed: {type(exc).__name__}")

        return self._mark_published(reply, lead, content, settings, "Published through the Reddit API.")

    # ── GitHub ──

    def _publish_github_api(self, reply, lead, content, settings) -> Dict[str, Any]:
        m = _GITHUB_ISSUE.search(lead.url)
        if not m:
            return self._fail(lead, reply, content, settings, "Not a GitHub issue URL.")
        owner, repo, number = m.groups()
        token = settings.github_token or os.getenv("GITHUB_TOKEN")
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "agent-reach-lead/2.1",
        }
        base = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
        try:
            issue = self.session.get(base, headers=headers, timeout=10)
            if issue.status_code == 200 and (issue.json().get("locked") or issue.json().get("state") != "open"):
                return self._fail(lead, reply, content, settings, "Issue is closed or locked.")
            resp = self.session.post(f"{base}/comments", headers=headers, json={"body": content}, timeout=10)
            if resp.status_code not in (200, 201):
                return self._fail(lead, reply, content, settings, f"GitHub returned {resp.status_code}.")
        except (requests.RequestException, ValueError) as exc:
            return self._fail(lead, reply, content, settings, f"GitHub request failed: {type(exc).__name__}")
        return self._mark_published(reply, lead, content, settings, "Published through the GitHub API.")

    def _mark_published(self, reply, lead, content, settings, message: str) -> Dict[str, Any]:
        reply.status = "published"
        reply.published_at = time.time()
        self.storage.save_reply(reply)
        self.storage.log_post(lead.id, reply.id, lead.platform, lead.url, content, settings.mode, "published")
        return {"success": True, "message": message}
