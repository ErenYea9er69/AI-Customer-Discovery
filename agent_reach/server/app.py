# -*- coding: utf-8 -*-
"""FastAPI Backend for AI Customer Discovery & Lead Generation Dashboard."""

from __future__ import annotations

import hmac
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import time
from collections import defaultdict
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent_reach.discovery.llm_client import LLMProviderError
from agent_reach.discovery.models import (
    BusinessProfile,
    PostingSettings,
)
from agent_reach.discovery.orchestrator import DiscoveryOrchestrator, validate_platforms
from agent_reach.discovery.reply_generator import ReplyGenerationError
from agent_reach.discovery.search_planner import VALID_PLATFORMS
from agent_reach.discovery.storage import DiscoveryStorage

log = logging.getLogger("agent_reach.server")

app = FastAPI(
    title="Agent Reach - Customer Discovery & Lead Intelligence API",
    version="2.1.0",
)

# Configure secure CORS origins (default to local dashboard ports or explicit env)
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_raw.strip():
    allowed_origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

_LOOPBACK = {"127.0.0.1", "::1", "localhost", "testclient"}


@app.middleware("http")
async def api_security_middleware(request: Request, call_next):
    """Guard every /api/ route.

    With AGENT_REACH_API_KEY set, the key is required. With no key set, only
    loopback clients get in, so a server bound to 0.0.0.0 is never open by accident.
    """
    if request.url.path.startswith("/api/"):
        expected = os.getenv("AGENT_REACH_API_KEY")
        if expected:
            auth = request.headers.get("Authorization", "")
            bearer = auth[7:].strip() if auth.startswith("Bearer ") else ""
            token = request.headers.get("X-API-Key") or bearer
            if not token or not hmac.compare_digest(token.encode(), expected.encode()):
                return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key."})
        elif (request.client.host if request.client else "") not in _LOOPBACK:
            return JSONResponse(
                status_code=403,
                content={"detail": "Set AGENT_REACH_API_KEY to allow non-local access."},
            )
    return await call_next(request)


class InMemoryRateLimiter:
    """Sliding-window in-memory rate limiter to protect expensive/crawler endpoints from DoS."""
    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self.history = defaultdict(list)

    def check(self, key: str, max_requests: Optional[int] = None) -> bool:
        limit = max_requests or self.rpm
        now = time.time()
        window_start = now - 60.0
        if len(self.history) > 1000:  # drop idle clients so the dict cannot grow forever
            self.history = defaultdict(list, {k: v for k, v in self.history.items() if v and v[-1] > window_start})
        self.history[key] = [t for t in self.history[key] if t > window_start]
        if len(self.history[key]) >= limit:
            return False
        self.history[key].append(now)
        return True


rate_limiter = InMemoryRateLimiter()


storage = DiscoveryStorage()
orchestrator = DiscoveryOrchestrator(storage)
storage.mark_stale_campaigns_failed()


# ── Request / Response Schemas ──

class ExtractUrlRequest(BaseModel):
    url: str = Field(min_length=4, max_length=2048)


class ExtractManualRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    description: str = Field(min_length=10, max_length=50000)


class LaunchCampaignRequest(BaseModel):
    name: str = Field(default="Lead Discovery", max_length=200)
    platforms: List[str] = Field(default_factory=lambda: ["reddit", "hackernews", "web"], max_length=10)
    max_leads: int = Field(default=15, ge=1, le=100)


class ApproveReplyRequest(BaseModel):
    edited_reply: Optional[str] = None
    selected_version: Optional[str] = "value_first"


class UpdateSettingsRequest(BaseModel):
    posting_settings: Optional[PostingSettings] = None
    llm_settings: Optional[Dict[str, Any]] = None



# ── Endpoints: Business Profile ──

@app.get("/api/profile")
def get_profile():
    profile = storage.get_latest_business_profile()
    if not profile:
        return {"profile": None}
    return {"profile": profile.model_dump()}


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "local"


def _extract(fn, *args, **kwargs):
    """Run a profile extraction and map errors to honest HTTP codes."""
    try:
        profile = fn(*args, **kwargs)
    except ValueError as exc:            # unreadable site, unsafe URL, empty analysis
        raise HTTPException(status_code=400, detail=str(exc))
    except LLMProviderError as exc:      # no key, provider down
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception:
        log.exception("profile extraction failed")
        raise HTTPException(status_code=500, detail="Profile extraction failed. Check the server log.")
    storage.save_business_profile(profile)
    return {"ok": True, "profile": profile.model_dump()}


@app.post("/api/profile/extract-url")
def extract_from_url(req: ExtractUrlRequest, request: Request):
    if not rate_limiter.check(f"extract:{_client_ip(request)}", max_requests=15):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for profile extraction.")
    return _extract(orchestrator.business_engine.analyze_website, req.url)


@app.post("/api/profile/extract-manual")
def extract_from_manual(req: ExtractManualRequest, request: Request):
    if not rate_limiter.check(f"extract:{_client_ip(request)}", max_requests=15):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for profile extraction.")
    return _extract(orchestrator.business_engine.analyze_manual_description, req.description, name=req.name)


@app.post("/api/profile/update")
def update_profile(profile: BusinessProfile):
    storage.save_business_profile(profile)
    return {"ok": True, "profile": profile.model_dump()}


@app.post("/api/profile/confirm")
def confirm_profile():
    profile = storage.get_latest_business_profile()
    if not profile:
        raise HTTPException(status_code=404, detail="No profile to confirm.")
    profile.confirmed = True
    storage.save_business_profile(profile)
    return {"ok": True, "profile": profile.model_dump()}


# ── Endpoints: Campaigns ──

@app.get("/api/campaigns")
def list_campaigns():
    return {"campaigns": [c.model_dump() for c in storage.list_campaigns()]}


@app.post("/api/campaigns/launch")
def launch_campaign(req: LaunchCampaignRequest, request: Request):
    client_ip = request.client.host if request.client else "local"
    if not rate_limiter.check(f"launch_campaign:{client_ip}", max_requests=15):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for campaign launches.")
    profile = storage.get_latest_business_profile()
    if profile and not profile.confirmed:
        raise HTTPException(status_code=400, detail="Confirm the business profile before launching a campaign.")
    try:
        campaign_id = orchestrator.run_campaign_background(
            campaign_name=req.name,
            platforms=validate_platforms(req.platforms),
            max_leads=req.max_leads,
        )
        return {"ok": True, "campaign_id": campaign_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.get("/api/campaigns/{campaign_id}")
def get_campaign(campaign_id: str):
    c = storage.get_campaign(campaign_id)
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"campaign": c.model_dump()}


@app.post("/api/campaigns/{campaign_id}/cancel")
def cancel_campaign(campaign_id: str):
    campaign = storage.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if not orchestrator.cancel_campaign(campaign_id):
        raise HTTPException(status_code=409, detail="Campaign is not running")
    return {"ok": True, "message": "Cancellation requested."}


# ── Endpoints: Leads ──

@app.get("/api/leads")
def list_leads(
    min_score: int = Query(0),
    platform: Optional[str] = Query(None),
    classification: Optional[str] = Query(None),
    pain_point_category: Optional[str] = Query(None),
    buying_intent: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    leads = storage.list_leads(
        min_score=min_score,
        platform=platform,
        classification=classification,
        pain_point_category=pain_point_category,
        buying_intent=buying_intent,
        query=query,
        limit=limit,
        offset=offset,
    )
    return {"leads": [l.model_dump() for l in leads]}


@app.get("/api/leads/counts")
def get_lead_counts():
    return storage.count_leads()


@app.get("/api/leads/{lead_id}")
def get_lead(lead_id: str):
    lead = storage.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    reply = storage.get_reply_by_lead_id(lead_id)
    return {
        "lead": lead.model_dump(),
        "reply": reply.model_dump() if reply else None,
    }


# ── Endpoints: Replies ──

@app.get("/api/replies/{lead_id}")
def get_reply(lead_id: str):
    reply = storage.get_reply_by_lead_id(lead_id)
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found for lead")
    return {"reply": reply.model_dump()}


@app.post("/api/replies/{lead_id}/generate")
def generate_reply(lead_id: str, request: Request):
    client_ip = request.client.host if request.client else "local"
    if not rate_limiter.check(f"generate_reply:{client_ip}", max_requests=30):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for reply generation.")
    lead = storage.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    profile = storage.get_latest_business_profile()
    if not profile:
        raise HTTPException(status_code=400, detail="Business profile required to generate replies.")
    try:
        reply = orchestrator.reply_generator.generate_replies(lead, profile)
    except (LLMProviderError, ReplyGenerationError) as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    storage.save_reply(reply)
    return {"ok": True, "reply": reply.model_dump()}


@app.post("/api/replies/{lead_id}/approve")
def approve_reply(lead_id: str, req: ApproveReplyRequest):
    reply = storage.get_reply_by_lead_id(lead_id)
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")
    try:
        reply = orchestrator.reply_generator.approve_reply(
            reply, edited_text=req.edited_reply, selected_version=req.selected_version
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    storage.save_reply(reply)
    return {"ok": True, "reply": reply.model_dump()}


@app.post("/api/replies/{lead_id}/publish")
def publish_reply(lead_id: str):
    lead = storage.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    reply = storage.get_reply_by_lead_id(lead_id)
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")

    settings_dict = storage.get_setting("posting_settings", PostingSettings().model_dump())
    settings = PostingSettings.model_validate(settings_dict)

    result = orchestrator.publisher.publish_or_copy(reply, lead, settings)
    return result


@app.post("/api/replies/{lead_id}/confirm-published")
def confirm_published_reply(lead_id: str):
    lead = storage.get_lead(lead_id)
    reply = storage.get_reply_by_lead_id(lead_id)
    if not lead or not reply:
        raise HTTPException(status_code=404, detail="Lead or reply not found")
    try:
        return orchestrator.publisher.confirm_manual_post(reply, lead)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


# ── Endpoints: Analytics ──

@app.get("/api/analytics")
def get_analytics():
    return orchestrator.analytics.get_insights()


# ── Endpoints: Settings ──

MASKED_SECRET = "***"


def _mask_posting_settings(settings_dict: Dict[str, Any]) -> Dict[str, Any]:
    masked = dict(settings_dict)
    for field in ("reddit_password", "reddit_client_secret", "github_token"):
        val = masked.get(field)
        masked[f"has_{field}"] = bool(val and str(val).strip())
        if val:
            masked[field] = MASKED_SECRET
    return masked


@app.get("/api/settings")
def get_settings():
    raw_posting = storage.get_setting("posting_settings", PostingSettings().model_dump())
    masked_posting = _mask_posting_settings(raw_posting)
    llm = storage.get_setting(
        "llm_settings",
        {
            "provider": orchestrator.llm.provider,
            "model": orchestrator.llm.model or "",
            "has_api_key": bool(orchestrator.llm.api_key),
            "configured": orchestrator.llm.is_configured,
        },
    )
    if isinstance(llm, dict) and "api_key" in llm:
        llm["has_api_key"] = bool(llm.get("api_key"))
        llm["api_key"] = MASKED_SECRET
    return {"posting_settings": masked_posting, "llm_settings": llm}


@app.post("/api/settings")
def update_settings(data: UpdateSettingsRequest):
    if data.posting_settings is not None:
        new_dict = data.posting_settings.model_dump()
        existing_dict = storage.get_setting("posting_settings", {})
        # Preserve existing secrets if incoming is masked or omitted
        for field in ("reddit_password", "reddit_client_secret", "github_token"):
            if new_dict.get(field) in (MASKED_SECRET, None) and existing_dict.get(field):
                new_dict[field] = existing_dict[field]
        storage.set_setting("posting_settings", new_dict)
    if data.llm_settings is not None:
        new_llm = dict(data.llm_settings)
        existing_llm = storage.get_setting("llm_settings", {})
        if new_llm.get("api_key") in (MASKED_SECRET, None) and existing_llm.get("api_key"):
            new_llm["api_key"] = existing_llm["api_key"]
        storage.set_setting("llm_settings", new_llm)
        orchestrator.reload_llm()   # new provider or key applies without a restart
    return {"ok": True}


@app.get("/api/platforms")
def list_platforms():
    """Platforms the planner accepts. The first three are on by default."""
    return {
        "platforms": sorted(VALID_PLATFORMS),
        "default": ["reddit", "hackernews", "web"],
        "weak": ["twitter", "github"],
    }


# ── Endpoints: Export ──

@app.get("/api/export")
def export_leads(format: str = Query("json"), min_score: int = Query(0)):
    if format.lower() == "csv":
        csv_data = storage.export_leads_csv(min_score=min_score)
        return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=leads.csv"})
    else:
        json_data = storage.export_leads_json(min_score=min_score)
        return Response(content=json_data, media_type="application/json", headers={"Content-Disposition": "attachment; filename=leads.json"})


# ── Serve Built Frontend if Present ──

FRONTEND_DIST = (Path(__file__).resolve().parent.parent.parent / "frontend" / "dist").resolve()
if FRONTEND_DIST.exists():
    @app.get("/{path:path}")
    def spa_fallback(path: str):
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        try:
            # Canonicalize and verify path stays strictly inside FRONTEND_DIST
            requested_file = (FRONTEND_DIST / path).resolve()
            if requested_file.is_relative_to(FRONTEND_DIST) and requested_file.is_file():
                return FileResponse(requested_file)
        except (ValueError, OSError):
            pass
        return FileResponse(FRONTEND_DIST / "index.html")

    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")


