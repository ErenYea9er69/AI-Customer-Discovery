# -*- coding: utf-8 -*-
"""FastAPI Backend for AI Customer Discovery & Lead Generation Dashboard."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent_reach.discovery.models import (
    BusinessProfile,
    PostingSettings,
)
from agent_reach.discovery.orchestrator import DiscoveryOrchestrator
from agent_reach.discovery.storage import DiscoveryStorage

app = FastAPI(
    title="Agent Reach - Customer Discovery & Lead Intelligence API",
    version="2.0.0",
)

# Enable CORS for local Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

storage = DiscoveryStorage()
orchestrator = DiscoveryOrchestrator(storage)


# ── Request / Response Schemas ──

class ExtractUrlRequest(BaseModel):
    url: str


class ExtractManualRequest(BaseModel):
    name: Optional[str] = None
    description: str


class LaunchCampaignRequest(BaseModel):
    name: str = "Lead Discovery"
    platforms: List[str] = ["reddit", "web"]
    max_leads: int = 15


class ApproveReplyRequest(BaseModel):
    edited_reply: Optional[str] = None
    selected_version: Optional[str] = "value_first"


# ── Endpoints: Business Profile ──

@app.get("/api/profile")
def get_profile():
    profile = storage.get_latest_business_profile()
    if not profile:
        return {"profile": None}
    return {"profile": profile.model_dump()}


@app.post("/api/profile/extract-url")
def extract_from_url(req: ExtractUrlRequest):
    try:
        profile = orchestrator.business_engine.analyze_website(req.url)
        storage.save_business_profile(profile)
        return {"ok": True, "profile": profile.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/profile/extract-manual")
def extract_from_manual(req: ExtractManualRequest):
    try:
        profile = orchestrator.business_engine.analyze_manual_description(req.description, name=req.name)
        storage.save_business_profile(profile)
        return {"ok": True, "profile": profile.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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
def launch_campaign(req: LaunchCampaignRequest):
    try:
        campaign_id = orchestrator.run_campaign_background(
            campaign_name=req.name,
            platforms=req.platforms,
            max_leads=req.max_leads,
        )
        return {"ok": True, "campaign_id": campaign_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/campaigns/{campaign_id}")
def get_campaign(campaign_id: str):
    c = storage.get_campaign(campaign_id)
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"campaign": c.model_dump()}


# ── Endpoints: Leads ──

@app.get("/api/leads")
def list_leads(
    min_score: int = Query(0),
    platform: Optional[str] = Query(None),
    classification: Optional[str] = Query(None),
    pain_point_category: Optional[str] = Query(None),
    buying_intent: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
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
def generate_reply(lead_id: str):
    lead = storage.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    profile = storage.get_latest_business_profile()
    if not profile:
        raise HTTPException(status_code=400, detail="Business profile required to generate replies.")
    reply = orchestrator.reply_generator.generate_replies(lead, profile)
    storage.save_reply(reply)
    return {"ok": True, "reply": reply.model_dump()}


@app.post("/api/replies/{lead_id}/approve")
def approve_reply(lead_id: str, req: ApproveReplyRequest):
    reply = storage.get_reply_by_lead_id(lead_id)
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")
    reply = orchestrator.reply_generator.approve_reply(
        reply, edited_text=req.edited_reply, selected_version=req.selected_version
    )
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


# ── Endpoints: Analytics ──

@app.get("/api/analytics")
def get_analytics():
    return orchestrator.analytics.get_insights()


# ── Endpoints: Settings ──

@app.get("/api/settings")
def get_settings():
    posting = storage.get_setting("posting_settings", PostingSettings().model_dump())
    llm = storage.get_setting(
        "llm_settings",
        {
            "provider": os.getenv("LLM_PROVIDER", "mock"),
            "model": os.getenv("LLM_MODEL", ""),
            "has_api_key": bool(os.getenv("LLM_API_KEY")),
        },
    )
    return {"posting_settings": posting, "llm_settings": llm}


@app.post("/api/settings")
def update_settings(data: Dict[str, Any]):
    if "posting_settings" in data:
        storage.set_setting("posting_settings", data["posting_settings"])
    if "llm_settings" in data:
        storage.set_setting("llm_settings", data["llm_settings"])
    return {"ok": True}


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

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")

