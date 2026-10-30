# -*- coding: utf-8 -*-
"""AI Reply Generator creating value-first and product-aware community responses."""

from __future__ import annotations

import time
from typing import Optional

from agent_reach.discovery.llm_client import LLMClient
from agent_reach.discovery.models import (
    BusinessProfile,
    GeneratedReply,
    LeadQualification,
)


class ReplyGenerator:
    """Generates thoughtful, value-first and compliant community replies."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def generate_replies(
        self,
        lead: LeadQualification,
        profile: BusinessProfile,
    ) -> GeneratedReply:
        """Generate both value-first and product-aware responses for a qualified lead."""
        disclosure = f"Disclosure: I am affiliated with {profile.name}."

        prompt = f"""
You are an authentic, deeply knowledgeable community participant and technical contributor.
A potential user posted this discussion in {lead.community} on {lead.platform}:

Title: {lead.title}
Author: {lead.author}
Excerpt: {lead.excerpt}
Identified Customer Problem: {lead.customer_problem}

Product Info:
Name: {profile.name}
Niche: {profile.niche}
Core Solution: {profile.main_product_or_service}
Features: {profile.features}

TASK:
Generate TWO distinct, high-quality responses:

1. VALUE-FIRST RESPONSE:
- Directly answer their question or solve their problem.
- Give concrete, actionable advice, best practices, open-source tools, or process tweaks.
- DO NOT MENTION {profile.name} AT ALL.
- Zero self-promotion. Pure value.

2. PRODUCT-AWARE RESPONSE:
- Provide helpful advice or technical context first.
- Naturally mention {profile.name} as one option designed specifically for this use case.
- Transparently include the disclosure: "{disclosure}"
- NEVER pretend to be a random customer ("I stumbled across this tool...").
- NEVER invent personal stories or capabilities that {profile.name} does not have.
- Tone must be helpful, collegial, and respectful of community anti-spam norms.

Respond in JSON matching:
{{
  "value_first": "Full text of value-first reply",
  "product_aware": "Full text of product-aware reply",
  "disclosure": "{disclosure}"
}}
"""
        resp = self.llm.complete_json(prompt, system_prompt="You generate helpful, non-spammy community replies.")

        value_first = resp.get(
            "value_first",
            "Here is a practical workflow to solve this: 1. Set up strict issue labeling in your project settings. 2. Implement a rotating triage duty where one person reviews inbound tickets before backlog grooming.",
        )
        product_aware = resp.get(
            "product_aware",
            f"A common workaround is setting up automated issue templates and triage rotations. If you want automated semantic duplicate detection, we built {profile.name} to solve this directly in GitHub Actions ({disclosure}). Hope this helps!",
        )

        return GeneratedReply(
            lead_id=lead.id,
            value_first=value_first,
            product_aware=product_aware,
            edited_reply=None,
            selected_version="value_first",
            status="draft",
            platform=lead.platform,
            target_url=lead.url,
            affiliation_disclosure=disclosure,
        )

    def approve_reply(
        self,
        reply: GeneratedReply,
        edited_text: Optional[str] = None,
        selected_version: Optional[str] = None,
    ) -> GeneratedReply:
        """Approve a reply for posting or manual copy."""
        if edited_text is not None:
            reply.edited_reply = edited_text
        if selected_version is not None:
            reply.selected_version = selected_version  # type: ignore
        reply.status = "approved"
        reply.updated_at = time.time()
        return reply

