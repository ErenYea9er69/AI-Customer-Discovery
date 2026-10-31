# -*- coding: utf-8 -*-
import socket

import pytest
from fastapi.testclient import TestClient

from agent_reach.discovery.business_engine import BusinessEngine
from agent_reach.discovery.llm_client import LLMClient
from agent_reach.discovery.models import BusinessProfile, GeneratedReply, LeadQualification, ScoreBreakdown
from agent_reach.server import app as server

client = TestClient(server.app)


def seed_lead(status="pending_manual_post"):
    lead = LeadQualification(
        discovered_item_id="d", title="t", url="https://reddit.com/r/x/comments/abc", platform="reddit", community="r/x",
        author="a", published_at="2026-10-01", excerpt="e", customer_problem="p", pain_point_category="c",
        profile_match="m", product_fit_explanation="f", evidence="ev", score=80,
        score_breakdown=ScoreBreakdown(icp_match=1, problem_fit=1, buying_intent=1, urgency=1, recency=1, total=5))
    reply = GeneratedReply(lead_id=lead.id, value_first="v", product_aware="p", status=status, platform="reddit",
                           target_url=lead.url)
    server.storage.save_lead(lead)
    server.storage.save_reply(reply)
    return lead, reply


def test_remote_client_blocked_without_key():
    remote = TestClient(server.app, client=("8.8.8.8", 5000))
    assert remote.get("/api/profile").status_code == 403


def test_api_key_required_when_set(monkeypatch):
    monkeypatch.setenv("AGENT_REACH_API_KEY", "secret")
    remote = TestClient(server.app, client=("8.8.8.8", 5000))
    assert remote.get("/api/profile").status_code == 401
    assert remote.get("/api/profile", headers={"X-API-Key": "wrong"}).status_code == 401
    assert remote.get("/api/profile", headers={"X-API-Key": "secret"}).status_code == 200
    assert remote.get("/api/profile", headers={"Authorization": "Bearer secret"}).status_code == 200


def test_confirm_published_endpoint_works():
    lead, _ = seed_lead()
    res = client.post(f"/api/replies/{lead.id}/confirm-published")   # raised AttributeError before
    assert res.status_code == 200 and res.json()["reply"]["status"] == "published"
    assert client.post(f"/api/replies/{lead.id}/confirm-published").status_code == 409


def test_launch_needs_confirmed_profile():
    p = BusinessProfile(name="X", problems_solved=["a b c"], confirmed=False)
    server.storage.save_business_profile(p)
    assert client.post("/api/campaigns/launch", json={}).status_code == 400
    assert client.post("/api/profile/confirm").status_code == 200


def test_extract_without_llm_returns_clear_error():
    res = client.post("/api/profile/extract-manual", json={"description": "We sell invoicing software to plumbers."})
    assert res.status_code == 502 and "No LLM is configured" in res.json()["detail"]


def test_platform_list_and_limit_validation():
    assert "hackernews" in client.get("/api/platforms").json()["platforms"]
    assert client.get("/api/leads?limit=100000").status_code == 422


def test_settings_secrets_are_masked():
    client.post("/api/settings", json={"posting_settings": {"reddit_password": "hunter2"}})
    body = client.get("/api/settings").json()["posting_settings"]
    assert body["reddit_password"] == "***" and body["has_reddit_password"] is True


# ── Business engine ──

def test_ssrf_host_resolving_to_private_ip_is_blocked(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("169.254.169.254", 0))])
    with pytest.raises(ValueError, match="public"):
        BusinessEngine(LLMClient(provider="none"))._safe_fetch("https://metadata.attacker.example/", {})


def test_unreadable_site_never_reaches_the_model(monkeypatch):
    engine = BusinessEngine(LLMClient(provider="none"))
    monkeypatch.setattr(engine, "_safe_fetch", lambda *a, **k: "<html><body>hi</body></html>")
    with pytest.raises(ValueError, match="Could not read enough text"):
        engine.analyze_website("https://example.com")


def test_priority_links_are_deterministic():
    from bs4 import BeautifulSoup
    html = '<a href="/pricing">p</a><a href="/features">f</a><a href="/use-cases">u</a><a href="https://other.com/features">x</a>'
    links = BusinessEngine(LLMClient(provider="none"))._find_priority_links("https://example.com", BeautifulSoup(html, "html.parser"))
    assert links == ["https://example.com/use-cases", "https://example.com/features", "https://example.com/pricing"]


def test_profile_without_problems_is_rejected():
    engine = BusinessEngine(LLMClient(provider="none"))
    with pytest.raises(ValueError, match="no problems"):
        engine._build_profile_from_data({"name": "X", "problems_solved": []})


def test_fact_sources_must_be_crawled_pages():
    engine = BusinessEngine(LLMClient(provider="none"))
    prof = engine._build_profile_from_data(
        {"problems_solved": ["a"], "facts": [{"claim": "c", "source_url": "https://invented.example/x"}]},
        url="https://real.com", known_pages={"https://real.com"})
    assert prof.facts[0].source_url == "https://real.com"
