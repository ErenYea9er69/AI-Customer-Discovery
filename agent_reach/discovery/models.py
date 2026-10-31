# -*- coding: utf-8 -*-
"""Data models for AI Customer Discovery and Lead Generation."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class FactItem(BaseModel):
    """A verified fact extracted directly from the business website."""
    claim: str
    source_url: str
    category: str = "product"  # e.g., "pricing", "feature", "icp", "company"


class InferenceItem(BaseModel):
    """An AI-derived inference with an explicit confidence level."""
    insight: str
    confidence: float = Field(ge=0.0, le=1.0)
    basis: str


class BusinessProfile(BaseModel):
    """Structured understanding of the user's business."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    url: Optional[str] = None
    description: str = ""
    industry: str = ""
    niche: str = ""
    main_product_or_service: str = ""
    features: List[str] = Field(default_factory=list)
    problems_solved: List[str] = Field(default_factory=list)
    customer_outcomes: List[str] = Field(default_factory=list)
    icp: str = ""
    target_industries: List[str] = Field(default_factory=list)
    target_roles: List[str] = Field(default_factory=list)
    customer_demographics: List[str] = Field(default_factory=list)
    customer_frustrations: List[str] = Field(default_factory=list)
    competitors_and_alternatives: List[str] = Field(default_factory=list)
    unique_selling_points: List[str] = Field(default_factory=list)
    pricing_info: Optional[str] = None
    geographic_market: str = "Global"
    trigger_events: List[str] = Field(default_factory=list)
    facts: List[FactItem] = Field(default_factory=list)
    inferences: List[InferenceItem] = Field(default_factory=list)
    confirmed: bool = False
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class SearchQuery(BaseModel):
    """A planned customer discovery search query."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    intent_type: str = "frustration"  # frustration, alternative, recommendation, cost, tool_request
    platform: str = "reddit"  # reddit, web, github, twitter, quora
    target_community: Optional[str] = None  # e.g. "r/startups" or "owner/repo"
    rationale: str = ""


class DiscoveredItem(BaseModel):
    """Raw conversation or post discovered from a community."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    platform: str
    community: str = ""
    author: str = ""
    published_at: str = ""
    title: str = ""
    content: str = ""
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)


class ScoreBreakdown(BaseModel):
    """Explainable 100-point score breakdown."""
    icp_match: int = Field(ge=0, le=25)
    problem_fit: int = Field(ge=0, le=30)
    buying_intent: int = Field(ge=0, le=20)
    urgency: int = Field(ge=0, le=15)
    recency: int = Field(ge=0, le=10)
    total: int = Field(ge=0, le=100)
    explanation: str = ""


LeadClassification = Literal[
    "high_potential",
    "relevant_potential",
    "customer_insight",
    "competitor_intel",
    "irrelevant",
]


class LeadQualification(BaseModel):
    """Qualified lead intelligence with supporting evidence and scoring."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    discovered_item_id: str
    title: str
    url: str
    platform: str
    community: str
    author: str
    published_at: str
    excerpt: str
    customer_problem: str
    pain_point_category: str
    profile_match: str
    competitor_mentioned: Optional[str] = None
    purchase_intent: Literal["High", "Medium", "Low", "None"] = "Medium"
    urgency: Literal["High", "Medium", "Low"] = "Medium"
    product_fit_explanation: str
    evidence: str
    score: int = Field(ge=0, le=100)
    score_breakdown: ScoreBreakdown
    classification: LeadClassification = "relevant_potential"
    confidence: float = Field(ge=0.0, le=1.0, default=0.85)
    created_at: float = Field(default_factory=time.time)


class GeneratedReply(BaseModel):
    """Value-first and product-aware response for a qualified lead."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str
    value_first: str
    product_aware: str
    edited_reply: Optional[str] = None
    selected_version: Literal["value_first", "product_aware", "custom"] = "value_first"
    status: Literal["draft", "approved", "pending_manual_post", "published", "rejected"] = "draft"
    published_at: Optional[float] = None
    platform: str = "reddit"
    target_url: str = ""
    affiliation_disclosure: str = "Disclosure: I am associated with this product."
    error_message: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class PostingSettings(BaseModel):
    """Safety and control configuration for response publishing."""
    mode: Literal["draft", "manual", "automatic"] = "manual"
    daily_limit: int = 5
    min_interval_seconds: int = 600  # 10 minutes between posts
    allowed_communities: List[str] = Field(
        default_factory=lambda: [
            "r/startups",
            "r/SaaS",
            "r/Entrepreneur",
            "r/programming",
            "r/devops",
            "r/webdev",
            "r/softwaredevelopment",
        ]
    )
    emergency_stop: bool = False
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_username: Optional[str] = None
    reddit_password: Optional[str] = None
    github_token: Optional[str] = None


class Campaign(BaseModel):
    """A customer discovery campaign."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Default Campaign"
    business_profile_id: str = ""
    status: Literal["idle", "running", "completed", "failed", "cancelled"] = "idle"
    selected_platforms: List[str] = Field(default_factory=lambda: ["reddit", "web"])
    queries: List[SearchQuery] = Field(default_factory=list)
    total_found: int = 0
    total_qualified: int = 0
    high_potential_count: int = 0
    progress_percentage: int = 0
    current_step: str = ""
    created_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None
