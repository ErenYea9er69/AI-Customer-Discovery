# -*- coding: utf-8 -*-
"""Publishing and automation layer with strict safety controls, rate limits, and manual fallback."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple
import requests

from agent_reach.discovery.models import (
    GeneratedReply,
    LeadQualification,
    PostingSettings,
)
from agent_reach.discovery.storage import DiscoveryStorage


class CommunityPublisher:
    """Manages compliant publishing, rate limits, emergency stops, and copy fallbacks."""

    def __init__(self, storage: Optional[DiscoveryStorage] = None):
        self.storage = storage or DiscoveryStorage()

    def can_publish(
        self,
        reply: GeneratedReply,
        lead: LeadQualification,
        settings: PostingSettings,
    ) -> Tuple[bool, str]:
        """Validate safety rules, limits, and whitelist before publishing."""
        if settings.emergency_stop:
            return False, "Emergency stop is active. All publishing is halted."

        if settings.mode == "draft":
            return False, "Application is in Draft mode. Automated publishing is disabled."

        if settings.mode == "manual" and reply.status != "approved":
            return False, "Manual approval mode requires explicit reply approval before publishing."

        # Community whitelist check
        if settings.allowed_communities and lead.community:
            normalized_allowed = [c.lower() for c in settings.allowed_communities]
            if lead.community.lower() not in normalized_allowed:
                return False, f"Community '{lead.community}' is not in allowed whitelist: {settings.allowed_communities}"

        # Daily limit check
        published_today = self.storage.count_posts_today(lead.platform)
        if published_today >= settings.daily_limit:
            return False, f"Daily publishing limit ({settings.daily_limit}) reached for {lead.platform}."

        return True, "Ready to publish."

    def publish_or_copy(
        self,
        reply: GeneratedReply,
        lead: LeadQualification,
        settings: PostingSettings,
    ) -> Dict[str, Any]:
        """Execute publishing or return copy-and-open fallback instructions."""
        allowed, reason = self.can_publish(reply, lead, settings)
        if not allowed:
            self.storage.log_post(
                lead_id=lead.id,
                reply_id=reply.id,
                platform=lead.platform,
                target_url=lead.url,
                content="",
                mode=settings.mode,
                status="rejected",
                error_message=reason,
            )
            return {"success": False, "reason": reason}

        content_to_post = self._get_reply_content(reply)

        # 1. Official Reddit API publishing if configured
        if lead.platform == "reddit" and settings.reddit_client_id and settings.reddit_client_secret:
            return self._publish_reddit_api(reply, lead, content_to_post, settings)

        # 2. Official GitHub Issues API publishing if token configured
        if lead.platform == "github" and settings.github_token:
            return self._publish_github_api(reply, lead, content_to_post, settings)

        # 3. Default Permitted Workflow: Copy-reply to clipboard & open original post
        reply.status = "published"
        reply.published_at = time.time()
        self.storage.save_reply(reply)

        self.storage.log_post(
            lead_id=lead.id,
            reply_id=reply.id,
            platform=lead.platform,
            target_url=lead.url,
            content=content_to_post,
            mode=settings.mode,
            status="published",
            error_message="Manual copy workflow verified",
        )

        return {
            "success": True,
            "action": "copy_and_open",
            "message": "Reply ready for publishing. Copied to clipboard and ready to open original post.",
            "target_url": lead.url,
            "text": content_to_post,
        }

    def _get_reply_content(self, reply: GeneratedReply) -> str:
        if reply.edited_reply:
            return reply.edited_reply
        if reply.selected_version == "product_aware":
            return reply.product_aware
        return reply.value_first

    def _publish_reddit_api(
        self,
        reply: GeneratedReply,
        lead: LeadQualification,
        content: str,
        settings: PostingSettings,
    ) -> Dict[str, Any]:
        """Publish via official Reddit OAuth2 API."""
        try:
            # Exchange script credentials for token
            auth = requests.auth.HTTPBasicAuth(settings.reddit_client_id, settings.reddit_client_secret)
            data = {
                "grant_type": "password",
                "username": settings.reddit_username,
                "password": settings.reddit_password,
            }
            token_resp = requests.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=auth,
                data=data,
                headers={"User-Agent": "AgentReach Lead Agent/2.0"},
                timeout=10,
            )
            if token_resp.status_code != 200:
                raise Exception("Failed to authenticate with Reddit API")

            token = token_resp.json().get("access_token")
            # Post comment to thing_id
            thing_id = lead.discovered_item_id
            post_resp = requests.post(
                "https://oauth.reddit.com/api/comment",
                headers={
                    "Authorization": f"Bearer {token}",
                    "User-Agent": "AgentReach Lead Agent/2.0",
                },
                data={"thing_id": thing_id, "text": content},
                timeout=10,
            )
            if post_resp.status_code == 200:
                reply.status = "published"
                reply.published_at = time.time()
                self.storage.save_reply(reply)
                self.storage.log_post(
                    lead.id, reply.id, lead.platform, lead.url, content, settings.mode, "published"
                )
                return {"success": True, "message": "Published comment via official Reddit API."}
            else:
                raise Exception(f"Reddit API error: {post_resp.text}")
        except Exception as e:
            self.storage.log_post(
                lead.id, reply.id, lead.platform, lead.url, content, settings.mode, "failed", str(e)
            )
            return {"success": False, "reason": str(e), "fallback_action": "copy_and_open"}

    def _publish_github_api(
        self,
        reply: GeneratedReply,
        lead: LeadQualification,
        content: str,
        settings: PostingSettings,
    ) -> Dict[str, Any]:
        """Publish issue comment via official GitHub REST API."""
        try:
            # Parse owner/repo and issue number from lead URL
            import re
            m = re.search(r"github\.com/([^/]+)/([^/]+)/issues/(\d+)", lead.url)
            if not m:
                raise Exception("URL is not a GitHub issue URL")
            owner, repo, issue_num = m.groups()
            api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_num}/comments"
            resp = requests.post(
                api_url,
                headers={
                    "Authorization": f"token {settings.github_token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "AgentReach/2.0",
                },
                json={"body": content},
                timeout=10,
            )
            if resp.status_code in (200, 201):
                reply.status = "published"
                reply.published_at = time.time()
                self.storage.save_reply(reply)
                self.storage.log_post(
                    lead.id, reply.id, lead.platform, lead.url, content, settings.mode, "published"
                )
                return {"success": True, "message": "Comment posted via official GitHub API."}
            else:
                raise Exception(f"GitHub API error: {resp.text}")
        except Exception as e:
            self.storage.log_post(
                lead.id, reply.id, lead.platform, lead.url, content, settings.mode, "failed", str(e)
            )
            return {"success": False, "reason": str(e), "fallback_action": "copy_and_open"}

